/* ============================================================
   game-adapter-online.js —— 在线版成绩存储
   ------------------------------------------------------------
   向后端申请轮次并提交结算报告。界面预览得分，后端重新计算后落库。
   ============================================================ */
(function (global) {
  'use strict';

  var DEVICE_KEY = 'wp_device_id';
  var pending = Promise.resolve();

  function serial(send) {
    pending = pending.then(send, send);
    return pending;
  }

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

    begin: function (meta, bank) {
      return API.post('/api/plays/start', Object.assign({ level: 0 }, meta, {
        bank_id: bank.bank_id, device: deviceId()
      }));
    },
    phase: function (playToken, phase) {
      return serial(function () {
        return API.post('/api/plays/phase', { play_token: playToken, phase: phase, device: deviceId() });
      });
    },
    progress: function (report) {
      var body = JSON.parse(JSON.stringify(Object.assign({}, report, { device: deviceId() })));
      return serial(function () { return API.post('/api/plays/progress', body); }).then(function () {
        return true;
      }, function () {
        API.toast(WPI18N.t('ig_scoreNotSaved'), 6000);
        return false;
      });
    },
    recording: function (id) {
      return API.get('/api/recordings/' + id).then(function (res) { return res.recording; });
    },

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
        level: report.level,
        rule_version: report.rule_version,
        combo_events: report.combo_events,
        time_left: report.time_left,
        initial_seconds: report.initial_seconds,
        bonus_seconds: report.bonus_seconds,
        play_token: report.play_token || ""
      };
      function notSaved() {
        try { API.toast(WPI18N.t('ig_scoreNotSaved'), 6000); } catch (e) { }
        return false;
      }
      return serial(function () {
        return fetch(API.path('/api/scores'), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body)
        }).then(function (res) { return res.ok ? true : notSaved(); });
      }).catch(notSaved);
    },

    history: function () {
      return fetch(API.path('/api/scores?limit=50')).then(function (r) { return r.json(); })
        .catch(function () { return []; });
    }
  };
})(window);
