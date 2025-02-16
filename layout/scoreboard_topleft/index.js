(($) => {
  var ASSET_TO_USE = "base_files/icon";
  var ZOOM = 1;

  if (window.PORTRAITS) ASSET_TO_USE = "portrait";

  gsap.config({ nullTargetWarn: false, trialWarn: false });

  let startingAnimation = gsap
    .timeline({ paused: true })
    .from([".logo"], { duration: 0.5, autoAlpha: 0, ease: "power2.inOut" }, 0.5)
    .from(
      [".anim_container_outer"],
      {
        duration: 1,
        width: "0",
        ease: "power2.inOut",
      },
      1
    )
    .from(
      [".base_container_outer"],
      {
        duration: 1,
        width: 0,
        ease: "power2.inOut",
      },
      1
    )
    .from(
      [".fgc .top", ".fgc .player"],
      {
        duration: 1,
        y: "-100px",
        ease: "power2.inOut",
      },
      0
    )
    .from(
      [".fgc:not(.bblue) .bottom"],
      {
        duration: 1,
        y: "+100px",
        ease: "power2.inOut",
      },
      0
    )
    .from(
      [".fgc.bblue .bottom"],
      {
        duration: 1,
        autoAlpha: 0,
        ease: "power2.inOut",
      },
      0.2
    );

  function Start() {
    startingAnimation.restart();
  }

  var data = {};
  var oldData = {};

  async function Update() {
    oldData = data;
    data = await getData();

    if (Object.keys(data.score.team["1"].player).length == 1) {
      [data.score.team["1"], data.score.team["2"]].forEach((team, t) => {
        [team.player["1"]].forEach((player, p) => {
          if (player) {
            SetInnerHtml(
              $(`.p${t + 1}.container .name`),
              `
                <span class="sponsor">
                  ${player.team ? player.team : ""}
                </span>
                ${player.name}
                <span class="pronoun">
                  ${player.pronoun ? player.pronoun : ""}
                </span>
                ${team.losers ? "<span class='losers'>L</span>" : ""}
              `
            );

            SetInnerHtml(
              $(`.p${t + 1}.container .flagcountry`),
              player.country.asset
                ? `<div class='flag' style='background-image: url(../../${player.country.asset.toLowerCase()})'></div>`
                : ""
            );

            SetInnerHtml(
              $(`.p${t + 1}.container .flagstate`),
              player.state.asset
                ? `<div class='flag' style='background-image: url(../../${player.state.asset})'></div>`
                : ""
            );

            if (
              !oldData.score ||
              JSON.stringify(player.character) !=
                JSON.stringify(
                  oldData.score.team[`${t + 1}`].player[`${p + 1}`].character
                )
            ) {
              let charactersHtml = "";
              Object.values(player.character).forEach((character, index) => {
                if (character.assets[ASSET_TO_USE]) {
                  charactersHtml += `
                    <div class="icon stockicon">
                        <div style='background-image: url(../../${character.assets[ASSET_TO_USE].asset})'></div>
                    </div>
                    `;
                }
              });
              SetInnerHtml(
                $(`.p${t + 1}.container .character_container`),
                charactersHtml,
                undefined,
                0.5,
                () => {
                  $(
                    `.p${t + 1}.container .character_container .stockicon div`
                  ).each((i, e) => {
                    CenterImage(
                      $(e),
                      Object.values(player.character)[i].assets[ASSET_TO_USE],
                      ZOOM
                    );
                  });
                }
              );
            }

            SetInnerHtml(
              $(`.p${t + 1}.container .sponsor_icon`),
              player.sponsor_logo
                ? `<div style='background-image: url(../../${player.sponsor_logo})'></div>`
                : ""
            );

            SetInnerHtml(
              $(`.p${t + 1}.container .avatar`),
              player.avatar
                ? `<div style="background-image: url('../../${player.avatar}')"></div>`
                : ""
            );

            SetInnerHtml(
              $(`.p${t + 1}.container .online_avatar`),
              player.online_avatar
                ? `<div style="background-image: url('${player.online_avatar}')"></div>`
                : ""
            );

            SetInnerHtml(
              $(`.p${t + 1}.container .twitter`),
              player.twitter
                ? `<span class="twitter_logo"></span>${String(player.twitter)}`
                : ""
            );

            let score = [data.score.score_left, data.score.score_right];

            SetInnerHtml($(`.p${t + 1}.container .score`), String(team.score));

            SetInnerHtml(
              $(`.p${t + 1}.container .sponsor-container`),
              `<div class='sponsor-logo' style='background-image: url(../../${player.sponsor_logo})'></div>`
            );
          }
        });
      });
    } else {
      [data.score.team["1"], data.score.team["2"]].forEach((team, t) => {
        let teamName = "";

        if (!team.teamName || team.teamName == "") {
          let names = [];
          Object.values(team.player).forEach((player, p) => {
            if (player) {
              names.push(player.name);
            }
          });
          teamName = names.join(" / ");
        } else {
          teamName = team.teamName;
        }

        SetInnerHtml(
          $(`.p${t + 1}.container .name`),
          `
            ${teamName}
            ${team.losers ? "<span class='losers'>L</span>" : ""}
          `
        );

        let player = team.player["1"];

        SetInnerHtml(
          $(`.p${t + 1}.container .flagcountry`),
          player.country.asset ? `` : ""
        );

        SetInnerHtml(
          $(`.p${t + 1}.container .flagstate`),
          player.state.asset ? `` : ""
        );

        let oldCharacters = oldData.score
          ? Object.values(oldData.score.team[`${t + 1}`].player)
              .map((p) => Object.values(p.character))
              .map((p) => p[0])
          : null;

        let characters = Object.values(team.player)
          .map((p) => Object.values(p.character))
          .map((p) => p[0]);

        if (JSON.stringify(oldCharacters) != JSON.stringify(characters)) {
          let charactersHtml = "";
          characters.forEach((character, index) => {
            if (character.assets[ASSET_TO_USE]) {
              charactersHtml += `
                <div class="icon stockicon">
                    <div style='background-image: url(../../${character.assets[ASSET_TO_USE].asset})'></div>
                </div>
                `;
            }
          });
          SetInnerHtml(
            $(`.p${t + 1}.container .character_container`),
            charactersHtml,
            undefined,
            0.5,
            () => {
              $(
                `.p${t + 1}.container .character_container .stockicon div`
              ).each((i, e) => {
                CenterImage($(e), characters[i].assets[ASSET_TO_USE], ZOOM);
              });
            }
          );
        }

        SetInnerHtml(
          $(`.p${t + 1}.container .sponsor_icon`),
          player.sponsor_logo ? `` : ""
        );

        SetInnerHtml(
          $(`.p${t + 1}.container .avatar`),
          player.avatar ? `` : ""
        );

        SetInnerHtml(
          $(`.p${t + 1}.container .online_avatar`),
          player.online_avatar ? `` : ""
        );

        SetInnerHtml(
          $(`.p${t + 1}.container .twitter`),
          player.twitter
            ? `<span class="twitter_logo"></span>${String(player.twitter)}`
            : ""
        );

        let score = [data.score.score_left, data.score.score_right];

        SetInnerHtml($(`.p${t + 1}.container .score`), String(team.score));

        SetInnerHtml(
          $(`.p${t + 1}.container .sponsor-container`),
          `<div class='sponsor-logo' style='background-image: url(../../${player.sponsor_logo})'></div>`
        );
      });
    }

    SetInnerHtml($(".tournament_name"), data.tournamentInfo.tournamentName);

    SetInnerHtml($(".event_name"), data.tournamentInfo.eventName);

    SetInnerHtml($(".phase"), data.score.phase);
    SetInnerHtml($(".match"), data.score.match);
    SetInnerHtml($(".best_of"), data.score.best_of_text);

    $(".text").each(function (e) {
      FitText($($(this)[0].parentNode));
    });

    $(".container div:has(>.text:empty)").css("margin-right", "0");
    $(".container div:not(:has(>.text:empty))").css("margin-right", "");
    $(".container div:has(>.text:empty)").css("margin-left", "0");
    $(".container div:not(:has(>.text:empty))").css("margin-left", "");
  }

  Update();
  $(window).on("load", () => {
    $("body").fadeTo(1, 1, async () => {
      Update();
      Start();
      setInterval(Update, 100);
    });
  });
})(jQuery);
