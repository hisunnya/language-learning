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

    /** 存一次成绩。不影响游戏：失败时只弹一条提示（成绩没存上，比如登录过期、网络断了），返回 Promise<是否存上> */
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
        detail: report.detail,
        play_token: report.play_token || ""        /* 排排坐：服务器按它找到这一局的录音，重新算分 */
      };
      function notSaved() {
        try { API.toast(WPI18N.t('ig_scoreNotSaved'), 6000); } catch (e) { }
        return false;
      }
      try {
        return fetch(API.path('/api/scores'), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body)
        }).then(function (res) { return res.ok ? true : notSaved(); }, notSaved);
      } catch (e) {
        return Promise.resolve(notSaved());
      }
    },

    history: function () {
      return fetch(API.path('/api/scores?limit=50')).then(function (r) { return r.json(); })
        .catch(function () { return []; });
    }
  };
})(window);
