class TournamentDataProvider:
    def __init__(self, url, threadpool) -> None:
        self.name = ""
        self.url = url
        self.entrants = []
        self.tournamentData = {}
        self.threadpool = threadpool

    def GetEntrants(self):
        pass

    def GetTournamentData(self):
        pass

    def GetMatch(self, setId):
        pass

    def GetMatches(self):
        pass

    def GetStreamMatchId(self, streamName):
        pass

    def GetUserMatchId(self, user):
        pass
