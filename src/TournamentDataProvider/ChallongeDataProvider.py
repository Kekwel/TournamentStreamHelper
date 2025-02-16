import requests
import os
import traceback
import re
import json
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from datetime import datetime
from dateutil.parser import parse
from ..Helpers.TSHDictHelper import deep_get
from ..TSHGameAssetManager import TSHGameAssetManager
from ..TSHPlayerDB import TSHPlayerDB
from .TournamentDataProvider import TournamentDataProvider
from PyQt5.QtCore import *
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from ..Workers import Worker
from ..Helpers.TSHLocaleHelper import TSHLocaleHelper
from ..TSHBracket import next_power_of_2
import math

def CHALLONGE_BRACKET_TYPE(bracketType: str):
    mapping = {
        "DoubleEliminationBracketPlotter": "DOUBLE_ELIMINATION"
    }
    if bracketType in mapping:
        return mapping[bracketType]
    else:
        return bracketType

class ChallongeDataProvider(TournamentDataProvider):

    def __init__(self, url, threadpool, parent) -> None:
        super().__init__(url, threadpool, parent)
        self.name = "Challonge"
    
    def GetSlug(self):
        # URL with language
        slug = re.findall(r"challonge\.com\/.*\/([^/]+)", self.url)

        if len(slug) > 0:
            return slug[0]
        
        # URL has no language in it
        slug = re.findall(r"challonge\.com\/([^/]+)", self.url)
        return slug[0]
    
    def GetCommunityPrefix(self):
        if "//challonge.com" in self.url:
            return ""
        else:
            # Tournament inside a Community
            prefix = re.findall(r"//([^.]+)", self.url)[0]
            return prefix

    def GetEnglishUrl(self):
        prefix = self.GetCommunityPrefix()
        if prefix:
            prefix = prefix+"."
        return f"https://{prefix}challonge.com/{self.GetSlug()}"

    def GetTournamentData(self, progress_callback=None):
        finalData = {}

        try:
            slug = self.GetSlug()

            data = requests.get(
                f"https://challonge.com/en/search/tournaments.json?filters%5B&page=1&per=1&q={slug}",
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
                    "sec-ch-ua": 'Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
                    "Accept-Encoding": "gzip, deflate, br"
                }
            )

            data = json.loads(data.text)
            collection = deep_get(data, "collection", [{}])[0]
            details = deep_get(collection, "details", [])

            videogame = collection.get("filter", {}).get("id", None)
            if videogame:
                self.videogame = videogame
                self.parent.signals.game_changed.emit(videogame)

            finalData["tournamentName"] = deep_get(collection, "name")

            # TODO necessary ?
            if len(details) > 3:
                startAtStr = deep_get(details[2], "text", "")
                try:
                    # test if date
                    parse(startAtStr, fuzzy=False)
                    # 'September 29, 2022'
                    element = datetime.strptime(startAtStr, "%B %d, %Y")
                    # to timestamp
                    timestamp = datetime.timestamp(element)
                    finalData["startAt"] = datetime.timestamp(element)
                except ValueError:
                    print('ChallongeDataProvider: No date defined')

            details = collection.get("details", [])
            participantsElement = next(
                (d for d in details if d.get("icon") == "fa fa-users"), None)
            if participantsElement:
                participants = int(
                    participantsElement.get("text").split(" ")[0])
                finalData["numEntrants"] = participants
            # finalData["address"] = deep_get(
            #     data, "data.event.tournament.venueAddress", "")
        except:
            traceback.print_exc()

        return finalData

    def GetMatch(self, setId, progress_callback):
        finalData = {}

        try:
            data = requests.get(
                self.GetEnglishUrl()+".json",
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
                    "sec-ch-ua": 'Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
                    "Accept-Encoding": "gzip, deflate, br"
                }
            )
            data = json.loads(data.text)

            all_matches = self.GetAllMatchesFromData(data)

            match = next((m for m in all_matches if str(
                m.get("id")) == str(setId)), None)

            if match:
                finalData = self.ParseMatchData(match)
        except:
            traceback.print_exc()

        return finalData

    def GetMatches(self, getFinished=False, progress_callback=None):
        final_data = []

        try:
            data = requests.get(
                self.GetEnglishUrl()+".json",
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
                    "sec-ch-ua": 'Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
                    "Accept-Encoding": "gzip, deflate, br"
                }
            )

            data = json.loads(data.text)

            all_matches = self.GetAllMatchesFromData(data)

            states = ["open", "pending"]

            if getFinished:
                states.append("complete")

            all_matches = [
                match for match in all_matches if match.get("state") in states and match.get("player1") and match.get("player2")]

            for match in all_matches:
                final_data.append(self.ParseMatchData(match))

            final_data.reverse()
        except Exception as e:
            traceback.print_exc()

        return final_data
    
    def GetTournamentPhases(self, progress_callback=None):
        phases = []

        try:
            data = requests.get(
                self.GetEnglishUrl()+".json",
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
                    "sec-ch-ua": 'Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
                    "Accept-Encoding": "gzip, deflate, br"
                }
            )
            data = json.loads(data.text)

            if len(deep_get(data, "groups", [])) > 0:
                phaseObj = {
                    "id": "group_stage",
                    "name": TSHLocaleHelper.phaseNames.get("group_stage"),
                    "groups": []
                }
                for g, group in enumerate(deep_get(data, "groups", [])):
                    groupIdentifier = group.get('name').replace("Group ", "") # Remove "Group " from "Group A"

                    phaseObj["groups"].append({
                        "id": f'group_stage_{g}',
                        "name": TSHLocaleHelper.phaseNames.get("group").format(groupIdentifier), 
                        "bracketType": CHALLONGE_BRACKET_TYPE(group.get("requested_plotter"))
                    })
                phases.append(phaseObj)
            
            phases.append({
                "id": "final_stage",
                "name": TSHLocaleHelper.phaseNames.get("final_stage"),
                "groups": [{
                        "id": "final_stage",
                        "name": TSHLocaleHelper.phaseNames.get("bracket"),
                        "bracketType": CHALLONGE_BRACKET_TYPE(data.get("requested_plotter"))
                    }
                ]
            })
        except:
            traceback.print_exc()

        return phases

    def GetTournamentPhaseGroup(self, id, progress_callback=None):
        finalData = {}
        try:
            data = requests.get(
                self.GetEnglishUrl()+".json",
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
                    "sec-ch-ua": 'Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
                    "Accept-Encoding": "gzip, deflate, br"
                }
            )
            data = json.loads(data.text)

            entrants = self.GetAllEntrantsFromData(data, id)
            entrants.sort(key=lambda e: e.get("seed"))

            finalData["entrants"] = entrants

            all_matches = self.GetAllMatchesFromData(data, id)

            parsed_matches = []

            for match in all_matches:
                parsed_matches.append(self.ParseMatchData(match))

            parsed_matches.sort(key=lambda match: abs(int(match.get("round"))), reverse=True)

            groups = deep_get(data, "groups", [])

            isPoolsPhase = id != None and id.startswith("group_stage")

            if not isPoolsPhase:
                # If we have GF and GFR, last winners rounds will have 2 sets
                # So we have to move the last one forward.
                # If there wasn't a reset, don't do anything
                lastWinnersMatch = parsed_matches[0]

                for match in parsed_matches:
                    if match.get("round") > lastWinnersMatch.get("round"):
                        lastWinnersMatch = match
                    elif match.get("round") == lastWinnersMatch.get("round") and match.get("identifier") > lastWinnersMatch.get("identifier"):
                        lastWinnersMatch = match
                
                hasReset = len([m for m in parsed_matches if m.get("round") == lastWinnersMatch.get("round")]) > 1

                if hasReset:
                    lastWinnersMatch["round"] = lastWinnersMatch["round"]+1
                
                if len(groups) > 0:
                    finalData["progressionsIn"] = [{}] * deep_get(groups[0], "tournament.participant_count_to_advance", 0) * len(groups)
            else:
                if id != None:
                    groupId = int(id.split("_")[-1])
                    groups = [groups[groupId]]
                

                if len(groups) > 0:
                    finalData["progressionsOut"] = [{}] * deep_get(groups[0], "tournament.participant_count_to_advance", 0)
            
            # If split_participants==True, half players start in losers
            # Force progressions
            isSplit = deep_get(data, "tournament.split_participants", False)

            if not isPoolsPhase and isSplit and len(finalData.get("progressionsIn", [])) == 0:
                finalData["progressionsIn"] = [{}] * len(entrants)

            rounds = {}

            # Detect if displayed bracket has LR1 cut out or not
            finalBracketSize = next_power_of_2(len(entrants))
            validWR1Sets = len(entrants) - finalBracketSize/2

            for match in parsed_matches:
                roundNum = match.get("round")

                score = [match.get("team1score", 0), match.get("team2score", 0)]
                finished = match.get("state", None) == "complete"
                
                if roundNum < 0:
                    roundNum -= 2

                # For first round, we work around the incomplete data Challonge gives us
                if roundNum == 1:
                    nextRoundMatches = [s for s in parsed_matches if s.get("round") == roundNum+1]
                    
                    # Initially, fill in the round with -1 scores
                    if not str(roundNum) in rounds:
                        rounds[str(roundNum)] = []

                        # Round 1 has 2x the number of sets that Round 2 has
                        for i in range(len(nextRoundMatches) * 2):
                            rounds[str(roundNum)].append({
                                "score": [-1, -1],
                                "finished": True
                            })
                    
                    roundY = 0

                    for m, roundMatch in enumerate(nextRoundMatches):
                        if roundMatch.get("player1_prereq_identifier") == match.get("identifier"):
                            roundY = 2*m
                            break
                        if roundMatch.get("player2_prereq_identifier") == match.get("identifier"):
                            roundY = 2*m+1
                            break

                    rounds[str(roundNum)][roundY] = {
                        "score": score,
                        "finished": finished
                    }
                # For first *losers* round, we work around the incomplete data Challonge gives us
                # (-1) - 2 = -3
                elif roundNum == -3:
                    nextRoundMatches = [s for s in parsed_matches if s.get("round") == -2]
                    
                    # Initially, fill in the round with -1 scores
                    if not str(roundNum) in rounds:
                        rounds[str(roundNum)] = []

                        # Round -1 has 2x the number of sets that Round -2 has
                        for i in range(len(nextRoundMatches) * 2):
                            rounds[str(roundNum)].append({
                                "score": [0, 0],
                                "finished": False
                            })
                    
                    roundY = 0

                    for m, roundMatch in enumerate(nextRoundMatches):
                        if roundMatch.get("player1_prereq_identifier") == match.get("identifier"):
                            roundY = m-1
                            break
                        if roundMatch.get("player2_prereq_identifier") == match.get("identifier"):
                            roundY = m
                            break

                    rounds[str(roundNum)][roundY] = {
                        "score": score,
                        "finished": finished
                    }
                else:
                    if not str(roundNum) in rounds:
                        rounds[str(roundNum)] = []
                    
                    rounds[str(roundNum)].append({
                        "score": score,
                        "finished": finished
                    })
            
            # In case LR1 was skipped, we move all sets back by one
            # It happens when the number of losers rounds is an odd number
            losersRoundKeys = [k for k in list(rounds.keys()) if int(k) < 0]
            losersRoundKeys.sort(key=lambda x: int(x))

            if len(losersRoundKeys) % 2 == 1:
                for s in rounds[str(losersRoundKeys[1])]:
                    s["score"].reverse()
                
                for r in losersRoundKeys:
                    if int(r) < 0:
                        rounds[int(r)-1] = rounds[r]
                        print(str(r), "=>", str(int(r)-2))

            # If we had progressions in, we have to add a fake R1 to send half players to losers side
            if len(finalData.get("progressionsIn", [])) > 0:
                sortedRounds = list(rounds.keys())
                sortedRounds.sort(key=lambda x: int(x), reverse=True)
                for r in sortedRounds:
                    if int(r) > 0:
                        rounds[int(r)+1] = rounds[r]
                        print(str(r), "=>", str(int(r)+2))
                
                rounds["1"] = []

                for s in range(int(finalBracketSize/2)):
                    rounds["1"].append({
                        "score": [-1, -1],
                        "finished": True
                    })
                
                rounds["2"] = []

                for s in range(int(finalBracketSize/2/2)):
                    rounds["2"].append({
                        "score": [-1, -1],
                        "finished": True
                    })

            finalData["sets"] = rounds
        except:
            traceback.print_exc()

        return finalData

    def GetAllMatchesFromData(self, data, phaseId=None):
        rounds = deep_get(data, "rounds", {})
        matches = deep_get(data, "matches_by_round", {})

        all_matches = []

        if phaseId in (None, "final_stage"):
            for r, round in enumerate(matches.values()):
                for m, match in enumerate(round):
                    # match["round_name"] = next(
                    #     r["title"] for r in rounds if r["number"] == match.get("round"))
                    match["round"] = match.get("round")
                    if data.get("tournament", {}).get("tournament_type") == "round robin":
                        match["phase"] = "Round Robin"
                    else:
                        match["phase"] = "Bracket"
                    if r == len(matches.values()) - 1:
                        if m == 0:
                            match["isGF"] = True
                        elif m == 1:
                            match["isGFR"] = True
                    match["round_name"] = ChallongeDataProvider.TranslateRoundName(match, rounds)
                    all_matches.append(match)

        if phaseId == None or phaseId.startswith("group_stage"):
            groups = deep_get(data, "groups", [])
            
            if phaseId != None:
                groupId = int(phaseId.split("_")[-1])
                groups = [groups[groupId]]

            for group in groups:
                rounds = deep_get(group, "rounds", {})
                matches = deep_get(group, "matches_by_round", {})

                for round in matches.values():
                    for match in round:
                        # match["round_name"] = next(
                        #     r["title"] for r in rounds if r["number"] == match.get("round"))
                        match["phase"] = group.get("name")
                        match["round_name"] = ChallongeDataProvider.TranslateRoundName(match, rounds)
                        all_matches.append(match)

        return all_matches

    def GetStreamMatchId(self, streamName):
        sets = self.GetMatches()

        streamSet = next(
            (s for s in sets if s.get("stream", None) ==
             streamName and s.get("is_current_stream_game")),
            None
        )

        return streamSet

    def GetUserMatchId(self, user):
        sets = self.GetMatches()

        userSet = next(
            (s for s in sets if s.get("p1_name")
             == user or s.get("p2_name") == user),
            None
        )

        if userSet and user == userSet.get("p2_name"):
            userSet["reverse"] = True

        return userSet
    
    def TranslateRoundName(match, rounds):
        roundNums = [r.get("number") for r in rounds]

        if match.get("round") > 0:
            lastWinnersRoundNum = max(roundNums)

            if match.get("round") == lastWinnersRoundNum:
                if match.get("isGFR"):
                    return TSHLocaleHelper.matchNames.get("grand_final_reset")
                else:
                    return TSHLocaleHelper.matchNames.get("grand_final")
            elif match.get("round") == lastWinnersRoundNum - 1:
                return TSHLocaleHelper.matchNames.get("winners_final")
            elif match.get("round") == lastWinnersRoundNum - 2:
                return TSHLocaleHelper.matchNames.get("winners_semi_final")
            elif match.get("round") == lastWinnersRoundNum - 3:
                return TSHLocaleHelper.matchNames.get("winners_quarter_final")
            else:
                return TSHLocaleHelper.matchNames.get("winners_round").format(match.get("round"))
        else:
            lastLosersRoundNum = min(roundNums)

            if match.get("round") == lastLosersRoundNum:
                return TSHLocaleHelper.matchNames.get("losers_final")
            elif match.get("round") == lastLosersRoundNum + 1:
                return TSHLocaleHelper.matchNames.get("losers_semi_final")
            elif match.get("round") == lastLosersRoundNum + 2:
                return TSHLocaleHelper.matchNames.get("losers_quarter_final")
            else:
                return TSHLocaleHelper.matchNames.get("losers_round").format(abs(match.get("round")))

    def ParseMatchData(self, match):
        stream = deep_get(match, "station.stream_url", None)

        if not stream:
            stream = deep_get(
                match, "queued_for_station.stream_url", None)

        if stream:
            stream = stream.split("twitch.tv/")[1].replace("/", "")

        team1losers = False
        team2losers = False

        if match.get("isGF"):
            team1losers = False
            team2losers = True
        elif match.get("isGFR"):
            team1losers = True
            team2losers = True

        scores = match.get("scores")
        if len(match.get("scores")) < 2:
            scores = [None, None]
        
        # If a match has a winner but no scores,
        # we're assuming it's a DQ
        p1_id = deep_get(match, "player1.id")
        p2_id = deep_get(match, "player2.id")

        if len(match.get("scores")) == 0 and match.get("state") == "complete":
            if match.get("winner_id") == p1_id:
                scores = [0, -1]
            if match.get("winner_id") == p2_id:
                scores = [-1, 0]
            
        return({
            "id": deep_get(match, "id"),
            "round_name": deep_get(match, "round_name"),
            "round": deep_get(match, "round"),
            "tournament_phase": match.get("phase"),
            "p1_name": deep_get(match, "player1.display_name"),
            "p2_name": deep_get(match, "player2.display_name"),
            "p1_seed": deep_get(match, "player1.seed"),
            "p2_seed": deep_get(match, "player2.seed"),
            "entrants": [
                self.ParseEntrant(deep_get(match, "player1")).get("players"),
                self.ParseEntrant(deep_get(match, "player2")).get("players"),
            ],
            "stream": stream,
            "is_current_stream_game": True if deep_get(match, "station.stream_url", None) else False,
            "team1score": scores[0],
            "team2score": scores[1],
            "team1losers": team1losers,
            "team2losers": team2losers,
            "identifier": match.get("identifier"),
            "player1_prereq_identifier": match.get("player1_prereq_identifier"),
            "player2_prereq_identifier": match.get("player2_prereq_identifier"),
            "state": match.get("state")
        })

    def GetEntrants(self):
        worker = Worker(self.GetEntrantsWorker)
        self.threadpool.start(worker)

    def GetEntrantsWorker(self, progress_callback):
        try:
            data = requests.get(
                self.GetEnglishUrl()+".json",
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
                    "sec-ch-ua": 'Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
                    "Accept-Encoding": "gzip, deflate, br"
                }
            )
            data = json.loads(data.text)

            entrants = self.GetAllEntrantsFromData(data)
            players = []

            for entrant in entrants:
                for player in entrant.get("players", []):
                    players.append(player)

            TSHPlayerDB.AddPlayers(players)
        except Exception as e:
            traceback.print_exc()

    def ParseEntrant(self, data):
        # Here we're only supporting a single player per entrant
        # Can be adapted later if we ever want to support more
        playerData = {}

        if data == None:
            return({})

        split = data.get("display_name", "").rsplit("|", 1)

        gamerTag = split[-1].strip()
        prefix = split[0].strip() if len(
            split) > 1 else None

        playerData["gamerTag"] = gamerTag
        playerData["prefix"] = prefix

        playerData["avatar"] = data.get("portrait_url")

        playerData["seed"] = data.get("seed")

        return({
            "players": [playerData],
            "seed": data.get("seed")
        })
    
    def GetAllEntrantsFromData(self, data, phaseId=None):
        final_data = []

        all_matches = self.GetAllMatchesFromData(data, phaseId)
        all_matches.sort(key=lambda m: abs(m.get("identifier")), reverse=True)

        # do not add duplicates
        added_list = []

        for m in all_matches:
            for p in ["player1", "player2"]:
                player = m.get(p)

                if player is not None and player.get("id", None) != None and not player.get("id") in added_list:
                    final_data.append(self.ParseEntrant(player))
                    added_list.append(player.get("id"))
        
        return(final_data)

    def GetStandings(self, playerNumber, progress_callback):
        final_data = []

        try:
            data = requests.get(
                self.GetEnglishUrl()+".json",
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
                    "sec-ch-ua": 'Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
                    "Accept-Encoding": "gzip, deflate, br"
                }
            )

            data = json.loads(data.text)

            all_matches = self.GetAllMatchesFromData(data)

            all_matches.sort(key=lambda m: abs(m.get("identifier")), reverse=True)

            # do not add duplicates
            added_list = []

            for m in all_matches:
                winner = m.get("player1")

                if m.get("winner_id") == m.get("player2").get("id"):
                    winner = m.get("player2")
                
                if not winner.get("id") in added_list:
                    final_data.append(self.ParseEntrant(winner))
                    added_list.append(winner.get("id"))

            return final_data
        except Exception as e:
            traceback.print_exc()
    
    def GetLastSets(self, playerID, playerNumber, callback, progress_callback):
        try:
            data = requests.get(
                self.GetEnglishUrl()+".json",
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
                    "sec-ch-ua": 'Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
                    "Accept-Encoding": "gzip, deflate, br"
                }
            )

            data = json.loads(data.text)

            set_data = []

            all_matches = self.GetAllMatchesFromData(data)

            all_matches = [
                match for match in all_matches if match.get("state") in ["complete"] and match.get("player1") and match.get("player2")]
            
            all_matches.sort(key=lambda m: abs(m.get("identifier")), reverse=True)

            for _set in all_matches:
                _set = self.ParseMatchData(_set)

                if not _set:
                    continue
                if not _set.get("team1score") and not _set.get("team2score"):
                    continue

                if _set.get("entrants")[0][0].get("id")[0] != playerID and _set.get("entrants")[1][0].get("id")[0] != playerID:
                    continue
            
                players = ["1", "2"]
                
                if _set.get("entrants")[0][0].get("id")[0] != playerID:
                    players.reverse()
                
                player_set = {
                    "phase_id": "",
                    "phase_name": _set.get("tournament_phase"),
                    "round_name": _set.get("round_name"),
                    f"player{players[0]}_score": _set.get("team1score"),
                    f"player{players[0]}_team": _set.get("entrants")[0][0].get("prefix"),
                    f"player{players[0]}_name": _set.get("entrants")[0][0].get("gamerTag"),
                    f"player{players[1]}_score": _set.get("team2score"),
                    f"player{players[1]}_team": _set.get("entrants")[1][0].get("prefix"),
                    f"player{players[1]}_name": _set.get("entrants")[1][0].get("gamerTag"),
                }

                set_data.append(player_set)

            callback.emit({"playerNumber": playerNumber, "last_sets": set_data})
        except Exception as e:
            traceback.print_exc()
            callback.emit({"playerNumber": playerNumber,"last_sets": []})