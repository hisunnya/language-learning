/* =============================================================
   hub.js —— 语林 / Lingua Grove 总主页

   两件事：
   1. 中英双语切换（data-i18n 属性 + i18n 表）
   2. 配色切换（[data-theme] + localStorage）

   两个选择都存在 localStorage 里，刷新后还在，
   切换语言时 <html lang="…"> 也要跟着改。
   ============================================================= */
(function () {
  "use strict";

  var LANG_KEY = "lg_lang";
  var THEME_KEY = "lg_theme";
  var DEFAULT_LANG = "zh";

  /* ---------------- 词典 ---------------- */
  var I18N = {
    zh: {
      "brand.name": "语林",
      "hero.title": "学习工具集",

      "stat.words": "4791",
      "stat.words.label": "个词条",
      "stat.units": "84",
      "stat.units.label": "个单元",
      "stat.topics": "300+",
      "stat.topics.label": "个话题",
      "stat.questions": "1375",
      "stat.questions.label": "道真题",


      "lexica.name": "词境",
      "lexica.en": "Lexica",
      "lexica.tagline": "英语词汇练习",
      "lexica.desc": "练习英语词汇，听发音并完成中英配对。可按学段、年级、册别和单元选题，也可上传自己的资料或导出离线练习页。",
      "lexica.f1": "四级题库",
      "lexica.f2": "美式女声发音",
      "lexica.f3": "Word / PDF 上传",
      "lexica.f4": "离线单文件",
      "lexica.cta": "进入词境",

      "topics.name": "每日话题",
      "topics.en": "Daily Topics",
      "topics.tagline": "初中、高中与大学分龄话题",
      "topics.desc": "选择初中、高中或大学话题集，按分类抽题并查看讨论方向；记录交流历史，积分可解锁提示。",
      "topics.f1": "随机抽题",
      "topics.f2": "参考方向",
      "topics.f3": "历史记录",
      "topics.f4": "纯前端离线",
      "topics.cta": "开始讨论",

      "ham.name": "无线电执照",
      "ham.en": "Ham Exam",
      "ham.tagline": "业余无线电台操作证模拟考试",
      "ham.desc": "依据《业余无线电台操作技术能力验证题库（2025 年版）》的 1375 道真题，A / B / C 三类分别组卷，倒计时、交卷、答题卡、错题统计全部照正式考试来。",
      "ham.f1": "1375 道真题",
      "ham.f2": "A/B/C 分类",
      "ham.f3": "计时与答题卡",
      "ham.f4": "53 张电路附图",
      "ham.cta": "进入模拟考试",

      "chemistry.name": "化学探秘",
      "chemistry.en": "Chem Quest",
      "chemistry.tagline": "分龄化学挑战",
      "chemistry.desc": "从元素符号、化学式到反应推理，按学段闯关，在预测与解题中认识化学。",
      "chemistry.f1": "初中 · 元素配对",
      "chemistry.f2": "高中 · 反应配平",
      "chemistry.f3": "大学 · 浓度推理",
      "chemistry.f4": "纯前端练习",
      "chemistry.cta": "开始探索",

      "physics.name": "物理探秘",
      "physics.en": "Phys Quest",
      "physics.tagline": "分龄物理挑战",
      "physics.desc": "从物理量与单位、公式速算到现象判断，按学段闯关，每题都附解题步骤。",
      "physics.f1": "初中 · 量与单位",
      "physics.f2": "高中 · 公式速算",
      "physics.f3": "大学 · 概念辨析",
      "physics.f4": "每题附解题步骤",
      "physics.cta": "开始挑战",

      "notes.a.title": "全部本地运行",
      "notes.a.body": "词汇游戏用 Python 标准库加 SQLite，话题和考试是纯前端，不依赖任何云服务，也不需要大模型。",
      "notes.b.title": "局域网内直连",
      "notes.b.body": "家庭网络 10.0.0.0/20 内直接用浏览器打开，不需要 VPN。部署细节见仓库 README。",
      "notes.c.title": "随时能带走",
      "notes.c.body": "题库可以导出成单个 HTML 离线页，拷到任何电脑上双击就能继续做题。",

      "foot.left": "语林 Lingua Grove · 语言学习工具集",
      "foot.right": "家庭局域网 · 即开即用",

      "themePicker": "配色"
    },

    en: {
      "brand.name": "Lingua Grove",
      "hero.title": "Learning Toolkit",

      "stat.words": "4791",
      "stat.words.label": "entries",
      "stat.units": "84",
      "stat.units.label": "units",
      "stat.topics": "300+",
      "stat.topics.label": "topics",
      "stat.questions": "1375",
      "stat.questions.label": "questions",


      "lexica.name": "Lexica",
      "lexica.en": "词境",
      "lexica.tagline": "English vocabulary practice",
      "lexica.desc": "Practice English vocabulary with pronunciation and word matching. Choose a stage, grade, volume and unit, upload your own material, or export an offline practice page.",
      "lexica.f1": "Four-level banks",
      "lexica.f2": "American female voice",
      "lexica.f3": "Word / PDF upload",
      "lexica.f4": "Offline single file",
      "lexica.cta": "Enter Lexica",

      "topics.name": "Daily Topics",
      "topics.en": "每日话题",
      "topics.tagline": "Topics for middle school, high school and university",
      "topics.desc": "Choose an age group, draw a prompt by category and explore its discussion hints. Track past conversations and use points to reveal guidance.",
      "topics.f1": "Random prompt",
      "topics.f2": "Guidance hints",
      "topics.f3": "History",
      "topics.f4": "Runs fully offline",
      "topics.cta": "Start a discussion",

      "ham.name": "Ham Exam",
      "ham.en": "无线电执照",
      "ham.tagline": "Amateur radio operator licence mock exam",
      "ham.desc": "1375 real questions from the 2025 edition of the official verification question bank, split across class A, B and C papers — with the countdown, answer sheet and score breakdown of the real thing.",
      "ham.f1": "1375 real questions",
      "ham.f2": "Class A / B / C",
      "ham.f3": "Timer and answer sheet",
      "ham.f4": "53 circuit diagrams",
      "ham.cta": "Open the mock exam",

      "chemistry.name": "Chem Quest",
      "chemistry.en": "化学探秘",
      "chemistry.tagline": "Chemistry challenges by level",
      "chemistry.desc": "Explore chemistry through elements, formulas and reaction puzzles, with challenges matched to each learning stage.",
      "chemistry.f1": "Middle school · Elements",
      "chemistry.f2": "High school · Reactions",
      "chemistry.f3": "University · Solutions",
      "chemistry.f4": "Runs in your browser",
      "chemistry.cta": "Start exploring",

      "physics.name": "Phys Quest",
      "physics.en": "物理探秘",
      "physics.tagline": "Physics challenges by level",
      "physics.desc": "Practise quantities and units, quick calculations and concepts, matched to each learning stage. Every answer shows its working.",
      "physics.f1": "Middle school · Units",
      "physics.f2": "High school · Calculation",
      "physics.f3": "University · Concepts",
      "physics.f4": "Worked answers",
      "physics.cta": "Start the challenge",

      "notes.a.title": "Everything runs locally",
      "notes.a.body": "The vocabulary game is Python standard library plus SQLite; topics and the exam are pure front end. No cloud service, no language model.",
      "notes.b.title": "Straight over the LAN",
      "notes.b.body": "Open it from any browser inside the 10.0.0.0/20 home network — no VPN involved. Deployment details live in the repository README.",
      "notes.c.title": "Take it with you",
      "notes.c.body": "Any bank can be exported as one self-contained HTML page; copy it to any computer and keep playing by double-clicking.",

      "foot.left": "Lingua Grove · Language Learning Suite",
      "foot.right": "Home network · Ready to use",

      "themePicker": "Palettes"
    }
  };

  /* ---------------- 小工具 ---------------- */
  function store(key, value) {
    try {
      if (value === undefined) return window.localStorage.getItem(key);
      window.localStorage.setItem(key, value);
    } catch (e) { /* 隐私模式下 localStorage 可能不可用 */ }
    return null;
  }

  function $(sel, root) { return (root || document).querySelector(sel); }
  function $$(sel, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(sel));
  }

  /* ---------------- 语言 ---------------- */
  function currentLang() {
    var saved = store(LANG_KEY);
    return (saved === "zh" || saved === "en") ? saved : DEFAULT_LANG;
  }

  function applyLang(lang) {
    var dict = I18N[lang] || I18N[DEFAULT_LANG];

    $$("[data-i18n]").forEach(function (el) {
      var text = dict[el.getAttribute("data-i18n")];
      if (text !== undefined) el.textContent = text;
    });

    // 属性也要跟着换（目前只有 aria-label）
    $$("[data-i18n-attr]").forEach(function (el) {
      el.getAttribute("data-i18n-attr").split(";").forEach(function (pair) {
        var bits = pair.split(":");
        if (bits.length !== 2) return;
        var attr = bits[0].trim();
        var key = bits[1].trim();
        if (dict[key] !== undefined) el.setAttribute(attr, dict[key]);
      });
    });

    // 色块提示语
    $$(".theme-chip").forEach(function (chip) {
      var tip = chip.getAttribute(lang === "en" ? "data-tooltip-en" : "data-tooltip-zh");
      if (tip) chip.setAttribute("data-tooltip", tip);
    });

    document.documentElement.setAttribute("lang", lang === "en" ? "en" : "zh-CN");
    var btn = $("#langBtn");
    if (btn) {
      btn.classList.toggle("is-en", lang === "en");
      btn.setAttribute("aria-label", lang === "en" ? "Switch to 中文" : "切换到 English");
    }
    store(LANG_KEY, lang);
  }

  /* ---------------- 配色 ---------------- */
  function applyTheme(theme) {
    if (!theme) return;
    document.documentElement.setAttribute("data-theme", theme);
    $$(".theme-chip").forEach(function (chip) {
      var on = chip.getAttribute("data-theme-val") === theme;
      chip.setAttribute("aria-pressed", on ? "true" : "false");
    });
    store(THEME_KEY, theme);
  }

  /* ---------------- 项目链接 ---------------- */
  function applyProjectLinks() {
    var cfg = window.LINGUA_PROJECTS || {};
    $$("[data-project-link]").forEach(function (a) {
      var href = cfg[a.getAttribute("data-project-link")];
      if (href) a.setAttribute("href", href);
    });
  }

  /* ---------------- 启动 ---------------- */
  function init() {
    applyLang(currentLang());
    applyTheme(store(THEME_KEY) || document.documentElement.getAttribute("data-theme"));
    applyProjectLinks();

    var langBtn = $("#langBtn");
    if (langBtn) {
      langBtn.addEventListener("click", function () {
        applyLang(currentLang() === "zh" ? "en" : "zh");
      });
    }

    $$(".theme-chip").forEach(function (chip) {
      chip.addEventListener("click", function () {
        applyTheme(chip.getAttribute("data-theme-val"));
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
