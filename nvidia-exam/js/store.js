/* =============================================================
   nvidia-exam/js/store.js —— 本地状态持久化

   统计、错题本、考试历史都存 localStorage；键统一加 nx_ 前缀。
   语言与配色的键（lg_lang / lg_theme）与 hub 全站共享，不要改。
   ============================================================= */
(function () {
  "use strict";

  var STATE_KEY = "nx_state";

  function defaultState() {
    return {
      /* 错题本：qid -> { n: 累计错次, ts: 最近时间戳 } */
      wrong: {},
      /* 答题记录：qid -> { r: 正确次数, w: 错误次数 } */
      answered: {},
      /* 考试历史：[{ ts, mode, score, total, pct, pass }] */
      history: []
    };
  }

  function read() {
    try {
      var raw = localStorage.getItem(STATE_KEY);
      if (!raw) return defaultState();
      var st = JSON.parse(raw);
      var def = defaultState();
      for (var k in def) if (!(k in st)) st[k] = def[k];
      return st;
    } catch (e) {
      return defaultState();
    }
  }

  function write(state) {
    try { localStorage.setItem(STATE_KEY, JSON.stringify(state)); } catch (e) { /* 隐私模式忽略 */ }
  }

  var state = read();

  window.NXStore = {
    /** 记录一次作答结果（练习与考试共用） */
    record: function (qid, isRight) {
      var a = state.answered[qid] || { r: 0, w: 0 };
      if (isRight) a.r++; else { a.w++; state.wrong[qid] = { n: (state.wrong[qid] || { n: 0 }).n + 1, ts: Date.now() }; }
      state.answered[qid] = a;
      write(state);
    },
    /** 记录一场考试 */
    addHistory: function (entry) {
      state.history.unshift(entry);
      if (state.history.length > 50) state.history.length = 50;
      write(state);
    },
    /** 错题本 qid 列表，按最近出错时间倒序 */
    wrongIds: function () {
      return Object.keys(state.wrong)
        .sort(function (a, b) { return state.wrong[b].ts - state.wrong[a].ts; })
        .map(Number);
    },
    clearWrong: function () { state.wrong = {}; write(state); },
    getState: function () { return state; }
  };
})();
