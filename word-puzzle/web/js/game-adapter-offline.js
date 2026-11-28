/* ============================================================
   game-adapter-offline.js —— 离线单文件版成绩存储
   ------------------------------------------------------------
   离线页面没有后端，成绩只存在浏览器 localStorage 里。
   玩法与在线版完全一致（运算都在 game-core.js）。
   ============================================================ */
(function (global) {
  'use strict';

  var KEY = 'wp_offline_scores_v1';
  var META_KEY = 'wp_offline_meta_v1';
  var plays = {};

  function read() {
    try {
      return JSON.parse(localStorage.getItem(KEY) || '[]');
    } catch (e) {
      return [];
    }
  }

  function write(list) {
    try {
      localStorage.setItem(KEY, JSON.stringify(list.slice(0, 200)));
      return true;
    } catch (e) {
      return false;
    }
  }

  global.WPAdapter = {
    mode: 'offline',

    begin: function (meta, bank) {
      try {
        var counts = JSON.parse(localStorage.getItem(META_KEY) || '{}');
        var key = [bank.bank_id || bank.title, bank.game_type || 'match',
          meta.ords ? meta.ords.slice().sort(function (a, b) { return a - b; }).join(',') : meta.level || 0].join(':');
        var n = (counts[key] || 0) + 1, tier = n <= 5 ? 0 : n <= 10 ? 1 : n <= 15 ? 2 : 3;
        var token = 'offline-' + Date.now() + '-' + Math.random().toString(36).slice(2);
        plays[token] = { key: key, saved: false };
        return Promise.resolve({ play_token: token, attempt: n, score_factor: [1, .75, .5, .2][tier],
          time_factor: [1, .8, .6, .4][tier], combo_seed: meta.combo_seed || 0 });
      } catch (err) {
        return Promise.reject(err);
      }
    },

    /** 存一次成绩 */
    save: function (report, meta) {
      var play = plays[report.play_token];
      if (play && play.saved) return true;
      var list = read();
      list.unshift({
        ts: Date.now(),
        title: (meta && meta.title) || '',
        score: report.score,
        matched: report.matched,
        total_pairs: report.total_pairs,
        wrong: report.wrong,
        best_combo: report.best_combo,
        duration: report.duration,
        level_count: report.level_count,
        detail: report.detail
      });
      if (!write(list)) return false;
      if (play) {
        try {
          var counts = JSON.parse(localStorage.getItem(META_KEY) || '{}');
          if (report.score > 0) counts[play.key] = (counts[play.key] || 0) + 1;
          localStorage.setItem(META_KEY, JSON.stringify(counts));
          play.saved = true;
        } catch (err) {
          return false;
        }
      }
      return true;
    },

    /** 本地历史 */
    history: function () {
      return read();
    },

    /** 最好成绩 */
    best: function () {
      var list = read();
      var best = 0;
      list.forEach(function (r) { if (r.score > best) best = r.score; });
      return best;
    }
  };
})(window);
