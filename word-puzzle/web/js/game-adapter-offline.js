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

    /** 存一次成绩 */
    save: function (report, meta) {
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
      write(list);
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
