/* ============================================================
   store.js —— 本地数据层（localStorage，无后端、无数据库）
   ============================================================ */
(function (global) {
  'use strict';

  var KEY = 'ham_exam_data_v1';

  var DEFAULTS = {
    v: 1,
    progress: {},   // qid -> {n:答题次数, c:答对次数, t:最后时间戳, w:最近一次是否错}
    exams: [],      // 模拟考试记录
    practice: [],   // 练习记录（可续做）
    fav: [],        // 收藏题号
    examDraft: null,// 未完成的模拟考试
    practiceDraft: null,
    settings: { cls: 'A', theme: 'light' }
  };

  function clone(o) { return JSON.parse(JSON.stringify(o)); }

  function load() {
    try {
      var raw = localStorage.getItem(KEY);
      if (!raw) return clone(DEFAULTS);
      var d = JSON.parse(raw);
      // 兼容补齐
      for (var k in DEFAULTS) if (!(k in d)) d[k] = clone(DEFAULTS[k]);
      for (var s in DEFAULTS.settings) if (!(s in d.settings)) d.settings[s] = DEFAULTS.settings[s];
      return d;
    } catch (e) {
      console.warn('读取本地数据失败，已重置', e);
      return clone(DEFAULTS);
    }
  }

  var data = load();

  function save() {
    try {
      localStorage.setItem(KEY, JSON.stringify(data));
      return true;
    } catch (e) {
      console.error('保存失败（可能是存储空间已满）', e);
      return false;
    }
  }

  var Store = {
    /* ---- 读 ---- */
    all: function () { return data; },
    progress: function (qid) { return data.progress[qid] || null; },
    progressMap: function () { return data.progress; },
    exams: function () { return data.exams.slice().sort(function (a, b) { return b.ts - a.ts; }); },
    practices: function () { return data.practice.slice().sort(function (a, b) { return b.ts - a.ts; }); },
    favs: function () { return data.fav; },
    isFav: function (qid) { return data.fav.indexOf(qid) >= 0; },
    settings: function () { return data.settings; },
    getExamDraft: function () { return data.examDraft; },
    getPracticeDraft: function () { return data.practiceDraft; },

    /* ---- 写 ---- */
    save: save,
    setSettings: function (patch) {
      for (var k in patch) data.settings[k] = patch[k];
      save();
    },

    /* 记录一次答题：correct 为布尔 */
    record: function (qid, correct) {
      var p = data.progress[qid] || { n: 0, c: 0, t: 0, w: 0 };
      p.n++; if (correct) p.c++; else p.w = 1;
      p.t = Date.now();
      data.progress[qid] = p;
      save();
      return p;
    },

    toggleFav: function (qid) {
      var i = data.fav.indexOf(qid);
      if (i >= 0) data.fav.splice(i, 1); else data.fav.push(qid);
      save();
      return i < 0;
    },

    addExam: function (rec) {
      data.exams.push(rec);
      save();
    },
    clearExams: function () { data.exams = []; save(); },

    addPractice: function (rec) {
      data.practice.push(rec);
      if (data.practice.length > 60) data.practice = data.practice.slice(-60);
      save();
    },
    clearPractices: function () { data.practice = []; save(); },

    setExamDraft: function (d) { data.examDraft = d; save(); },
    clearExamDraft: function () { data.examDraft = null; save(); },

    setPracticeDraft: function (d) { data.practiceDraft = d; save(); },
    clearPracticeDraft: function () { data.practiceDraft = null; save(); },

    resetProgress: function () { data.progress = {}; save(); },
    resetAll: function () {
      data = clone(DEFAULTS);
      data.settings.theme = data.settings.theme; // 保留主题
      save();
    },

    /* ---- 导入导出 ---- */
    exportJSON: function () { return JSON.stringify(data, null, 1); },
    importJSON: function (text) {
      var d = JSON.parse(text);
      if (!d || typeof d !== 'object' || !d.progress) throw new Error('文件格式不正确');
      data = d;
      for (var k in DEFAULTS) if (!(k in data)) data[k] = clone(DEFAULTS[k]);
      save();
      return true;
    },

    /* ---- 统计 ---- */
    stats: function (questionIds) {
      var ids = questionIds || null;
      var p = data.progress;
      var total = 0, done = 0, attempts = 0, correct = 0, wrongIds = [];
      var keys = Object.keys(p);
      for (var i = 0; i < keys.length; i++) {
        var qid = keys[i];
        if (ids && ids.indexOf(qid) < 0) continue;
        total++;
        var rec = p[qid];
        attempts += rec.n; correct += rec.c;
        if (rec.n > 0) { done++; if (rec.w) wrongIds.push(qid); }
      }
      return {
        covered: total, done: done, attempts: attempts, correct: correct,
        accuracy: attempts ? correct / attempts : 0,
        wrongIds: wrongIds
      };
    }
  };

  global.Store = Store;
})(window);
