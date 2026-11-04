/* ============================================================
   game-adapter-online.js —— 在线版成绩存储
   ------------------------------------------------------------
   只负责把结算报告 POST 给后端；计分完全在 game-core.js，
   两者互不影响。
   ============================================================ */
(function (global) {
  'use strict';

  var DEVICE_KEY = 'wp_device_id';

  function deviceId() {
    try {
      var id = localStorage.getItem(DEVICE_KEY);
      if (!id) {
        id = 'd-' + Date.now().toString(36) + '-' +
          Math.random().toString(36).slice(2, 10);
        localStorage.setItem(DEVICE_KEY, id);
      }
      return id;
    } catch (e) {
      return 'd-anon';
    }
  }

  global.WPAdapter = {
    mode: 'online',

    device: deviceId,

    /** 存一次成绩；失败静默（不影响游戏） */
    save: function (report, meta) {
      var body = {
        bank_id: (meta && meta.bank_id) || null,
        bank_title: (meta && meta.title) || '',
        device: deviceId(),
        nickname: (meta && meta.nickname) || '',
        mode: 'online',
        score: report.score,
        matched: report.matched,
        total_pairs: report.total_pairs,
        wrong: report.wrong,
        best_combo: report.best_combo,
        duration: report.duration,
        level_count: report.level_count,
        detail: report.detail
      };
      try {
        fetch('/api/scores', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body)
        }).catch(function () { /* 网络问题不影响游戏 */ });
      } catch (e) { }
      return true;
    },

    history: function () {
      return fetch('/api/scores?limit=50').then(function (r) { return r.json(); })
        .catch(function () { return []; });
    }
  };
})(window);
