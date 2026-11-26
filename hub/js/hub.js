/* =============================================================
   hub.js —— 词境 Lexica 主页（原「语林」）

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
      "brand.name": "词境",
      "brand.tagline": "寓教于乐的课本学习",
      "brand.en": "LEXICA",
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
      "lexica.tagline": "初中、高中英语词汇",
      "lexica.desc": "人教版初中、高中英语课本里的单词：听美式发音，完成中英配对闯关，也可以逐个单元练读音。不用注册，成绩记在你自己的设备上。",
      "lexica.f1": "初中 · 高中",
      "lexica.f2": "美式女声发音",
      "lexica.f3": "配对闯关",
      "lexica.f4": "读音练习",
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

      "nvidia.name": "NVIDIA 认证",
      "nvidia.en": "NVIDIA Exam",
      "nvidia.tagline": "AI 基础设施与运维",
      "nvidia.desc": "按 NVIDIA 官方公开大纲的三个知识域比例组卷，倒计时、答题卡、及格线 70% 都照正式考试来，答完附中英双语解析。",
      "nvidia.f1": "NCA-AIIO 大纲",
      "nvidia.f2": "三知识域组卷",
      "nvidia.f3": "计时与答题卡",
      "nvidia.f4": "中英双语解析",
      "nvidia.cta": "进入模拟考试",

      "notes.a.title": "内容来自课本",
      "notes.a.body": "英语词汇按人教版教材的学段、年级、册别和单元整理；化学、物理按初中、高中、大学分级出题。",
      "notes.b.title": "玩着学",
      "notes.b.body": "配对、闯关、计时和积分，把背单词、记公式、练题目变成一个个小游戏。",
      "notes.c.title": "打开就能用",
      "notes.c.body": "不需要注册，也不用安装，用浏览器打开就能练；手机、平板、电脑都可以。",

      "foot.left": "词境 Lexica · 把课本搬到网上，寓教于乐",
      "foot.right": "个人学习网站",

      "themePicker": "配色"
    },

    en: {
      "brand.name": "Lexica",
      "brand.tagline": "Learning from the textbook, playfully",
      "brand.en": "LEXICA",
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
      "lexica.tagline": "Middle and high school English words",
      "lexica.desc": "Words from the PEP middle and high school English textbooks: hear the American pronunciation, match each word with its meaning level by level, or practise pronunciation unit by unit. No sign-up; scores stay with your own device.",
      "lexica.f1": "Middle · High school",
      "lexica.f2": "American female voice",
      "lexica.f3": "Matching levels",
      "lexica.f4": "Pronunciation practice",
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

      "nvidia.name": "NVIDIA Exam",
      "nvidia.en": "NVIDIA 认证",
      "nvidia.tagline": "AI infrastructure and operations",
      "nvidia.desc": "Papers are drawn in the proportions of the three official NVIDIA blueprint domains, with countdown, answer sheet and the 70% pass line. Every answer comes with an explanation in both languages.",
      "nvidia.f1": "NCA-AIIO blueprint",
      "nvidia.f2": "Three domains",
      "nvidia.f3": "Timer and answer sheet",
      "nvidia.f4": "Bilingual explanations",
      "nvidia.cta": "Open the mock exam",

      "notes.a.title": "From the textbook",
      "notes.a.body": "English words follow the PEP textbooks by stage, grade, volume and unit; chemistry and physics are graded from middle school to university.",
      "notes.b.title": "Learn by playing",
      "notes.b.body": "Matching, levels, timers and points turn words, formulas and exercises into small games.",
      "notes.c.title": "Ready to use",
      "notes.c.body": "No sign-up and nothing to install: open it in a browser on a phone, tablet or computer.",

      "foot.left": "Lexica · Textbook material, learned through play",
      "foot.right": "A personal learning site",

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
