(($) => {
  let startingAnimation = gsap
    .timeline({ paused: true })
    .from($(".recent_sets"), { autoAlpha: 0 });

  var playersRecentSets = null;
  var players = [];

  async function Start() {
    startingAnimation.restart();
  }

  var data = {};
  var oldData = {};

  async function Update() {
    oldData = data;
    data = await getData();

    if (
      !oldData.score ||
      JSON.stringify(oldData.score.recent_sets) !=
        JSON.stringify(data.score.recent_sets)
    ) {
      playersRecentSets = data.score.recent_sets;
      console.log(playersRecentSets);

      players = [];
      recentSetsHtml = "";

      if (
        playersRecentSets == null ||
        (playersRecentSets.state == "done" &&
          playersRecentSets.sets.length == 0)
      ) {
        recentSetsHtml += `No sets found`;
        players = [];
        $(`.recent_sets_content`).html(recentSetsHtml);
      } else if (playersRecentSets.state != "done") {
        recentSetsHtml += `<div class="lds-ring"><div></div><div></div><div></div><div></div></div>`;
        players = [];
        $(`.recent_sets_content`).html(recentSetsHtml);
      } else {
        if (
          !oldData.score ||
          JSON.stringify(oldData.score.recent_sets) !=
            JSON.stringify(data.score.recent_sets)
        ) {
          playersRecentSets = data.score.recent_sets;

          console.log(playersRecentSets);

          recentSetsHtml += '<div class="recent_sets_inner">';
          playersRecentSets.sets.slice(0, 5).forEach((_set, i) => {
            recentSetsHtml += `
                <div class="set_container set_${i}">
                  <div class="${_set.winner == 0 ? "set_winner" : "set_loser"}">
                    ${_set.score[0]}
                  </div>
                  <div class="set_info">
                    <div class="set_col col_1">
                        <div class="set_text"></div>
                        <div class="set_subtext"></div>
                    </div>
                    <div class="set_col col_2">
                        <div class="set_text"></div>
                        <div class="set_subtext"></div>
                    </div>
                  </div>
                  <div class="${_set.winner == 1 ? "set_winner" : "set_loser"}">
                    ${_set.score[1]}
                  </div>
                </div>
              `;
          });
          recentSetsHtml += "</div>";
        }

        $(`.recent_sets_content`).html(recentSetsHtml);

        playersRecentSets.sets.slice(0, 5).forEach((_set, i) => {
          SetInnerHtml(
            $(`.set_${i} .col_1 .set_text`),
            (_set.online ? `<div class="wifi_icon"></div>` : "") +
              _set.tournament
          );
          SetInnerHtml(
            $(`.set_${i} .col_1 .set_subtext`),
            new Date(_set.timestamp * 1000).toLocaleDateString("en-US", {
              month: "short",
              day: "2-digit",
              year: "numeric",
            })
          );
          SetInnerHtml(
            $(`.set_${i} .col_2 .set_text`),
            _set.event + " - " + _set.phase_id + _set.phase_name
          );
          SetInnerHtml($(`.set_${i} .col_2 .set_subtext`), _set.round);
        });
      }
    }

    [data.score.team["1"], data.score.team["2"]].forEach((team, t) => {
      [team.player["1"]].forEach((player, p) => {
        if (player) {
          SetInnerHtml(
            $(`.recent_sets_players .player_${t + 1} .sponsor`),
            player.team
          );
          SetInnerHtml(
            $(`.recent_sets_players .player_${t + 1} .name`),
            player.name
          );
        }
      });
    });
  }

  // Using update here to set images as soon as possible
  // so that on window.load they are already preloaded
  Update();
  $(window).on("load", () => {
    $("body").fadeTo(0, 1, async () => {
      Start();
      setInterval(Update, 500);
    });
  });
})(jQuery);
