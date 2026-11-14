/* ============================================================
   page-play.js —— 在线游玩
   ------------------------------------------------------------
   从 /api/banks/{id} 取题库 → 交给 WPGame 运算 → WPGameUI 渲染
   成绩由 game-adapter-online.js 写回后端。
   ============================================================ */
(function () {
  'use strict';

  function qs(name) {
    var m = new RegExp('[?&]' + name + '=([^&]*)').exec(location.search);
    return m ? decodeURIComponent(m[1]) : '';
  }

  function t(key, params) { return WPI18N.t(key, params); }

  /* 出错页：msg 可以是词条键（我们自己的提示，随语言重画）或后端给的原文 */
  var failing = null;
  function fail(msg, isKey) {
    failing = { msg: msg, isKey: !!isKey };
    drawFail();
  }
  function drawFail() {
    document.body.innerHTML =
      '<div style="padding:40px;text-align:center;font-family:sans-serif">' +
      '<h2 style="color:#123a6b">' + API.esc(t('play_failTitle')) + '</h2>' +
      '<p style="color:#5b6d85">' + API.esc(failing.isKey ? t(failing.msg) : failing.msg) + '</p>' +
      '<a href="' + API.path('/') + '" style="display:inline-block;margin-top:12px;padding:10px 18px;' +
      'background:#1f7ae0;color:#fff;border-radius:12px;font-weight:700">' + API.esc(t('play_backHome')) + '</a>' +
      '</div>';
  }
  var bankTitle = '';
  WPI18N.onChange(function () {
    if (failing) drawFail();
    else if (bankTitle) document.title = t('play_title', { title: bankTitle });
  });

  document.addEventListener('DOMContentLoaded', function () {
    var bankId = qs('bank');
    if (!bankId) { fail('play_noBankId', true); return; }

    API.get('/api/banks/' + encodeURIComponent(bankId)).then(function (res) {
      var bank = res.bank;
      var levels = res.groups.map(function (g) {
        return { name: g.unit, words: g.words };
      });
      if (!levels.length) { fail('play_noWords', true); return; }

      bankTitle = bank.title;
      document.title = t('play_title', { title: bankTitle });

      var game = new WPGame.Game({ levels: levels });
      var ui = WPGameUI.init({
        game: game,
        title: bank.title,
        subtitle: [bank.level1, bank.level2, bank.level3, bank.level4].join(' · '),
        pickUnit: bank.unit_mode === 'per-unit',
        backHref: location.origin + '/',
        wordTotal: bank.word_count,
        /* 在线版使用服务端固定语音引擎；失败时提示，不切换本地声线。 */
        audioBase: API.path('/api/audio/'),
        onFinish: function (report) {
          WPAdapter.save(report, { bank_id: bank.id, title: bank.title });
          API.toast(t('play_saved'));
        }
      });
      /* 调试钩子：在控制台里可以直接看 game.state / ui.timer */
      window.WP_DEBUG = { game: game, ui: ui, bank: bank };
    }).catch(function (e) {
      fail(e.message);
    });
  });
})();
