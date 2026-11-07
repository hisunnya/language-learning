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

  function fail(msg) {
    document.body.innerHTML =
      '<div style="padding:40px;text-align:center;font-family:sans-serif">' +
      '<h2 style="color:#123a6b">无法开始游戏</h2>' +
      '<p style="color:#5b6d85">' + API.esc(msg) + '</p>' +
      '<a href="' + API.path('/') + '" style="display:inline-block;margin-top:12px;padding:10px 18px;' +
      'background:#1f7ae0;color:#fff;border-radius:12px;font-weight:700">回到首页</a>' +
      '</div>';
  }

  document.addEventListener('DOMContentLoaded', function () {
    var bankId = qs('bank');
    if (!bankId) { fail('缺少题库参数'); return; }

    API.get('/api/banks/' + encodeURIComponent(bankId)).then(function (res) {
      var bank = res.bank;
      var levels = res.groups.map(function (g) {
        return { name: g.unit, words: g.words };
      });
      if (!levels.length) { fail('这个题库里没有单词'); return; }

      document.title = bank.title + ' · 词境 Lexica';

      var game = new WPGame.Game({ levels: levels });
      var ui = WPGameUI.init({
        game: game,
        title: bank.title,
        subtitle: [bank.level1, bank.level2, bank.level3, bank.level4].join(' · '),
        pickUnit: bank.unit_mode === 'per-unit',
        backHref: API.path('/'),
        wordTotal: bank.word_count,
        /* 在线版：发音优先使用后端 Edge Neural 美式女声，离线或不可用时使用浏览器 TTS。 */
        audioBase: API.path('/api/audio/'),
        onFinish: function (report) {
          WPAdapter.save(report, { bank_id: bank.id, title: bank.title });
          API.toast('成绩已保存');
        }
      });
      /* 调试钩子：在控制台里可以直接看 game.state / ui.timer */
      window.WP_DEBUG = { game: game, ui: ui, bank: bank };
    }).catch(function (e) {
      fail(e.message);
    });
  });
})();
