/* =============================================================
   nvidia-exam/js/app.js —— 页面逻辑

   1. 中英双语切换（data-i18n 属性 + i18n 表，键必须两种语言完全一致）
   2. 配色切换（html[data-theme] + localStorage，键与 hub 全站共享）
   3. 四个视图：模拟考试 / 练习 / 题库 / 统计（含错题本）
   ============================================================= */
(function () {
  "use strict";

  var LANG_KEY = "lg_lang";
  var THEME_KEY = "lg_theme";

  /* ---------------- 题库 ---------------- */
  var BANK = window.NVIDIA_BANK;
  var EXAM = BANK.exams[0];
  var DOMAINS = EXAM.domains;
  var QUESTIONS = EXAM.questions;
  var QMAP = {};
  QUESTIONS.forEach(function (q) { QMAP[q.id] = q; });

  var $ = function (id) { return document.getElementById(id); };
  var lang = "zh";
  var currentView = "exam";

  /* ---------------- 词典 ---------------- */
  var I18N = {
    zh: {
      "brand.name": "NVIDIA 认证",
      "brand.note": "AI 基础设施与运维模拟考试",
      "nav.exam": "模拟考试",
      "nav.practice": "练习",
      "nav.browse": "题库",
      "nav.stats": "统计",

      "exam.title": "模拟考试",
      "exam.desc": "按官方大纲三个知识域的比例随机抽题组卷，倒计时、答题卡、及格线（70%）全部照正式考试来。",
      "exam.length": "题量",
      "exam.domain": "知识域",
      "exam.start": "开始考试",
      "exam.sheet": "答题卡",
      "exam.submit": "交卷",
      "exam.cardCount": "正式考试题量",
      "exam.cardTime": "考试时长",
      "exam.cardPass": "及格线",
      "exam.cardBank": "本题库题量",

      "q.prev": "上一题",
      "q.next": "下一题",
      "q.check": "提交答案",
      "q.multi": "多选",

      "result.title": "考试结果",
      "result.review": "查看错题",
      "result.again": "再考一次",
      "result.pass": "通过",
      "result.fail": "未通过",
      "result.your": "你的答案",
      "result.correct": "正确答案",
      "result.none": "未作答",

      "practice.title": "练习",
      "practice.desc": "按知识域顺序练习，每题即时反馈对错与解析；答错的题自动进入错题本。",
      "practice.domain": "知识域",
      "practice.order": "顺序",
      "practice.seq": "顺序",
      "practice.rand": "随机",
      "practice.start": "开始练习",
      "practice.end": "结束练习",
      "practice.score": "正确 {r} / {n}",

      "browse.title": "题库",
      "browse.domain": "知识域",
      "browse.search": "搜索",
      "browse.searchPh": "搜索题干关键词…",
      "browse.empty": "没有匹配的题目。",

      "stats.title": "统计",
      "stats.domains": "分知识域正确率",
      "stats.history": "最近考试",
      "stats.cellAnswered": "已作答题数",
      "stats.cellAccuracy": "总正确率",
      "stats.cellExams": "考试次数",
      "stats.cellBest": "最佳成绩",
      "stats.noHistory": "还没有考试记录。",

      "wrong.title": "错题本",
      "wrong.practice": "错题重练",
      "wrong.clear": "清空错题本",
      "wrong.summary": "错题本共 {n} 题。答错的题会自动收录，重练答对后移除。",
      "wrong.empty": "错题本是空的，去练习或考试吧。",
      "wrong.times": "错 {n} 次",
      "wrong.confirm": "确定要清空错题本吗？",

      "footer.note": "题库按 NVIDIA 官方公开考试大纲生成，仅用于内网学习自测，可随时扩充。"
    },
    en: {
      "brand.name": "NVIDIA Cert",
      "brand.note": "AI Infrastructure & Operations mock exam",
      "nav.exam": "Exam",
      "nav.practice": "Practice",
      "nav.browse": "Bank",
      "nav.stats": "Stats",

      "exam.title": "Mock Exam",
      "exam.desc": "Questions are drawn proportionally from the three blueprint domains, with countdown, answer sheet and the 70% pass line — just like the real exam.",
      "exam.length": "Questions",
      "exam.domain": "Domain",
      "exam.start": "Start exam",
      "exam.sheet": "Answer sheet",
      "exam.submit": "Submit",
      "exam.cardCount": "Official question count",
      "exam.cardTime": "Official duration",
      "exam.cardPass": "Pass line",
      "exam.cardBank": "Bank size",

      "q.prev": "Prev",
      "q.next": "Next",
      "q.check": "Check answer",
      "q.multi": "Multi",

      "result.title": "Exam Result",
      "result.review": "Review mistakes",
      "result.again": "Retake",
      "result.pass": "PASS",
      "result.fail": "FAIL",
      "result.your": "Your answer",
      "result.correct": "Correct answer",
      "result.none": "Not answered",

      "practice.title": "Practice",
      "practice.desc": "Practice by domain with instant feedback and explanations; wrong answers go into the wrong-answer book automatically.",
      "practice.domain": "Domain",
      "practice.order": "Order",
      "practice.seq": "Sequential",
      "practice.rand": "Random",
      "practice.start": "Start practice",
      "practice.end": "End practice",
      "practice.score": "Correct {r} / {n}",

      "browse.title": "Question Bank",
      "browse.domain": "Domain",
      "browse.search": "Search",
      "browse.searchPh": "Search by keyword…",
      "browse.empty": "No matching questions.",

      "stats.title": "Stats",
      "stats.domains": "Accuracy by domain",
      "stats.history": "Recent exams",
      "stats.cellAnswered": "Questions answered",
      "stats.cellAccuracy": "Overall accuracy",
      "stats.cellExams": "Exams taken",
      "stats.cellBest": "Best score",
      "stats.noHistory": "No exam history yet.",

      "wrong.title": "Wrong-answer Book",
      "wrong.practice": "Re-practice",
      "wrong.clear": "Clear book",
      "wrong.summary": "{n} questions in the book. Wrong answers are added automatically and removed after you answer them correctly.",
      "wrong.empty": "The book is empty. Go practice or take an exam.",
      "wrong.times": "wrong ×{n}",
      "wrong.confirm": "Clear the wrong-answer book?",

      "footer.note": "Questions are generated from the official NVIDIA public exam blueprint for intranet study only."
    }
  };

  function t(key, vars) {
    var s = (I18N[lang] && I18N[lang][key]) || I18N.zh[key] || key;
    if (vars) {
      Object.keys(vars).forEach(function (k) {
        s = s.replace("{" + k + "}", vars[k]);
      });
    }
    return s;
  }

  function domainName(id) {
    for (var i = 0; i < DOMAINS.length; i++) {
      if (DOMAINS[i].id === id) return lang === "en" ? DOMAINS[i].en : DOMAINS[i].zh;
    }
    return id;
  }

  /* ---------------- 语言与配色 ---------------- */
  var PALETTES = [
    { key: "indigo",   zh: "靛蓝 · 雪白", en: "Indigo · Snow",    main: "#4F46E5", bg: "#F4F6FB" },
    { key: "ink",      zh: "墨绿 · 玄夜", en: "Ink · Obsidian",   main: "#34D399", bg: "#0C1210" },
    { key: "amber",    zh: "琥珀 · 米白", en: "Amber · Cream",    main: "#B45309", bg: "#FBF6EC" },
    { key: "lotus",    zh: "绯红 · 藕白", en: "Crimson · Lotus",  main: "#DB2777", bg: "#FDF4F6" },
    { key: "obsidian", zh: "鎏金 · 曜黑", en: "Gilded · Obsidian", main: "#D4AF37", bg: "#08080A" }
  ];

  function store(key, val) {
    try {
      if (val === undefined) return localStorage.getItem(key);
      localStorage.setItem(key, val);
    } catch (e) { return null; }
  }

  function applyLanguage(l) {
    lang = l === "en" ? "en" : "zh";
    document.documentElement.lang = lang === "en" ? "en" : "zh-CN";
    document.querySelectorAll("[data-i18n]").forEach(function (el) {
      el.textContent = t(el.getAttribute("data-i18n"));
    });
    document.querySelectorAll("[data-i18n-ph]").forEach(function (el) {
      el.setAttribute("placeholder", t(el.getAttribute("data-i18n-ph")));
    });
    var langBtn = $("langBtn");
    if (langBtn) {
      langBtn.classList.toggle("is-en", lang === "en");
      langBtn.setAttribute("data-tooltip-zh", "切换到 English");
      langBtn.setAttribute("data-tooltip-en", "Switch to 中文");
    }
    store(LANG_KEY, lang);
    renderDynamic();
    /* 共享页眉里的身份条（/shared/module-progress.js 放的）靠这个事件重画 */
    window.dispatchEvent(new CustomEvent("portal-lang-change", { detail: { lang: lang } }));
  }

  function applyTheme(theme) {
    if (!PALETTES.some(function (p) { return p.key === theme; })) theme = "indigo";
    document.documentElement.dataset.theme = theme;
    document.querySelectorAll(".portal-theme-chip").forEach(function (chip) {
      chip.setAttribute("aria-pressed", String(chip.dataset.themeVal === theme));
    });
    store(THEME_KEY, theme);
  }

  function buildPicker() {
    var picker = $("themePicker");
    picker.innerHTML = PALETTES.map(function (p) {
      return '<button type="button" class="portal-theme-chip" data-theme-val="' + p.key + '"' +
        ' data-tooltip-zh="' + p.zh + '" data-tooltip-en="' + p.en + '"' +
        ' aria-label="' + p.zh + '" aria-pressed="false">' +
        '<span class="portal-swatch" style="--swatch-main:' + p.main + ';--swatch-bg:' + p.bg + '"></span>' +
        '</button>';
    }).join("");
    picker.querySelectorAll(".portal-theme-chip").forEach(function (chip) {
      chip.addEventListener("click", function () { applyTheme(chip.dataset.themeVal); });
    });
  }

  /* ---------------- 通用渲染 ---------------- */
  function fmtTime(sec) {
    var m = Math.floor(sec / 60), s = sec % 60;
    return (m < 10 ? "0" + m : m) + ":" + (s < 10 ? "0" + s : s);
  }

  function shuffle(arr) {
    var a = arr.slice();
    for (var i = a.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var tmp = a[i]; a[i] = a[j]; a[j] = tmp;
    }
    return a;
  }

  function sameSet(sel, ans) {
    if (!sel || sel.length !== ans.length) return false;
    var a = sel.slice().sort(), b = ans.slice().sort();
    for (var i = 0; i < a.length; i++) if (a[i] !== b[i]) return false;
    return true;
  }

  function optLabel(i) { return String.fromCharCode(65 + i); }

  function renderOpts(container, q, opts) {
    opts = opts || {};
    container.innerHTML = "";
    q.o.forEach(function (text, i) {
      var label = document.createElement("label");
      label.className = "opt" + (opts.picked && opts.picked.indexOf(i) >= 0 ? " picked" : "");
      var input = document.createElement("input");
      input.type = q.multi ? "checkbox" : "radio";
      input.name = "opt-" + container.id + "-" + q.id;
      input.value = String(i);
      if (opts.picked && opts.picked.indexOf(i) >= 0) input.checked = true;
      if (opts.reveal) {
        input.disabled = true;
        if (q.a.indexOf(i) >= 0) label.classList.add("right");
        else if (opts.picked && opts.picked.indexOf(i) >= 0) label.classList.add("wrong");
        label.classList.add("disabled");
      } else {
        input.addEventListener("change", function () { opts.onChange && opts.onChange(collectPicks(container)); });
      }
      var span = document.createElement("span");
      span.textContent = optLabel(i) + ". " + (lang === "en" ? text : (q.oZh ? q.oZh[i] : text));
      label.appendChild(input);
      label.appendChild(span);
      container.appendChild(label);
    });
  }

  function collectPicks(container) {
    var picks = [];
    container.querySelectorAll("input:checked").forEach(function (input) {
      picks.push(Number(input.value));
    });
    return picks;
  }

  function showExplanation(el, q) {
    el.classList.remove("hidden");
    el.textContent = (lang === "en" ? q.e : (q.eZh || q.e));
  }

  /* ---------------- 视图切换 ---------------- */
  function switchView(name) {
    currentView = name;
    document.querySelectorAll(".nav-btn").forEach(function (btn) {
      btn.classList.toggle("active", btn.dataset.view === name);
    });
    ["exam", "practice", "browse", "stats"].forEach(function (v) {
      $("view-" + v).classList.toggle("hidden", v !== name);
    });
    if (name === "browse") renderBrowse();
    if (name === "stats") renderStats();
  }

  /* ---------------- 模拟考试 ---------------- */
  var examState = null;

  function buildRuleCards() {
    var cards = [
      { b: "50", s: t("exam.cardCount") },
      { b: "60 min", s: t("exam.cardTime") },
      { b: "70%", s: t("exam.cardPass") },
      { b: String(QUESTIONS.length), s: t("exam.cardBank") }
    ];
    $("examRuleCards").innerHTML = cards.map(function (c) {
      return '<div class="rule-card"><b>' + c.b + "</b><span>" + c.s + "</span></div>";
    }).join("");
  }

  function fillDomainSelect(select, allLabel) {
    select.innerHTML = "";
    var all = document.createElement("option");
    all.value = "all";
    all.textContent = allLabel;
    select.appendChild(all);
    DOMAINS.forEach(function (d) {
      var opt = document.createElement("option");
      opt.value = d.id;
      opt.textContent = lang === "en" ? d.en : d.zh;
      select.appendChild(opt);
    });
  }

  function sampleExam(length, domain) {
    var pool = domain === "all" ? QUESTIONS : QUESTIONS.filter(function (q) { return q.domain === domain; });
    if (length >= pool.length) return shuffle(pool);
    if (domain !== "all") return shuffle(pool).slice(0, length);
    /* 按大纲权重比例抽题 */
    var picked = [];
    DOMAINS.forEach(function (d, idx) {
      var n = Math.round(length * d.weight / 100);
      if (idx === DOMAINS.length - 1) n = length - picked.length - DOMAINS.slice(0, idx).reduce(function (acc, dd) {
        return acc + Math.round(length * dd.weight / 100);
      }, 0);
      var sub = shuffle(QUESTIONS.filter(function (q) { return q.domain === d.id; })).slice(0, n);
      picked = picked.concat(sub);
    });
    return shuffle(picked);
  }

  function startExam() {
    var length = Number($("examLength").value);
    var domain = $("examDomain").value;
    var qs = sampleExam(length, domain);
    if (!qs.length) return;
    examState = {
      qs: qs,
      picks: qs.map(function () { return []; }),
      cur: 0,
      total: qs.length * EXAM.durationMinPerQuestion * 60,
      left: Math.round(qs.length * EXAM.durationMinPerQuestion * 60),
      timer: null,
      done: false
    };
    $("examSetup").classList.add("hidden");
    $("examResult").classList.add("hidden");
    $("examRun").classList.remove("hidden");
    renderExamQuestion();
    examState.timer = setInterval(function () {
      examState.left--;
      updateTimer();
      if (examState.left <= 0) finishExam();
    }, 1000);
    updateTimer();
    updateExamProgress();
  }

  function updateTimer() {
    var el = $("examTimer");
    el.textContent = fmtTime(Math.max(0, examState.left));
    el.classList.toggle("warn", examState.left <= 60);
  }

  function updateExamProgress() {
    var answered = examState.picks.filter(function (p) { return p.length; }).length;
    $("examProgress").textContent = (examState.cur + 1) + " / " + examState.qs.length + " · " +
      answered + " / " + examState.qs.length;
    renderExamSheet();
  }

  function renderExamQuestion() {
    var q = examState.qs[examState.cur];
    var meta = "#" + (examState.cur + 1) + " · " + domainName(q.domain) + (q.multi ? " · " + t("q.multi") : "");
    $("examQMeta").textContent = meta;
    $("examQText").textContent = lang === "en" ? q.q : q.qZh;
    renderOpts($("examOpts"), q, {
      picked: examState.picks[examState.cur],
      onChange: function (picks) {
        examState.picks[examState.cur] = picks;
        updateExamProgress();
        renderExamQuestion();
      }
    });
    $("examExplain").classList.add("hidden");
    $("examPrevBtn").disabled = examState.cur === 0;
    $("examNextBtn").disabled = examState.cur === examState.qs.length - 1;
  }

  function renderExamSheet() {
    var sheet = $("examSheet");
    if (sheet.classList.contains("hidden")) return;
    sheet.innerHTML = "";
    examState.qs.forEach(function (q, i) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = i + 1;
      if (examState.picks[i].length) btn.classList.add("answered");
      if (i === examState.cur) btn.style.outline = "2px solid var(--accent)";
      btn.addEventListener("click", function () {
        examState.cur = i;
        renderExamQuestion();
        updateExamProgress();
      });
      sheet.appendChild(btn);
    });
  }

  function finishExam() {
    if (examState.done) return;
    examState.done = true;
    clearInterval(examState.timer);
    var right = 0;
    var byDomain = {};
    examState.qs.forEach(function (q, i) {
      var ok = sameSet(examState.picks[i], q.a);
      if (ok) right++;
      var d = byDomain[q.domain] = byDomain[q.domain] || { r: 0, n: 0 };
      d.n++; if (ok) d.r++;
      window.NXStore.record(q.id, ok);
    });
    var pct = Math.round(right / examState.qs.length * 100);
    var pass = pct >= EXAM.passPct;
    window.NXStore.addHistory({ ts: Date.now(), mode: "exam", score: right, total: examState.qs.length, pct: pct, pass: pass });
    if (window.WPModule) window.WPModule.reportNow();

    $("examRun").classList.add("hidden");
    $("examResult").classList.remove("hidden");
    $("resultScore").innerHTML =
      '<div class="pct">' + pct + "%</div>" +
      '<div class="verdict ' + (pass ? "pass" : "fail") + '">' +
      right + " / " + examState.qs.length + " · " + (pass ? t("result.pass") : t("result.fail")) +
      " (" + t("exam.cardPass") + " " + EXAM.passPct + "%)</div>";
    $("resultDomains").innerHTML = DOMAINS.filter(function (d) { return byDomain[d.id]; }).map(function (d) {
      var s = byDomain[d.id];
      return '<div class="stat-cell"><b>' + (s.n ? Math.round(s.r / s.n * 100) : 0) + "%</b><span>" +
        domainName(d.id) + " (" + s.r + "/" + s.n + ")</span></div>";
    }).join("");
    $("resultReview").innerHTML = "";
    $("resultReview").classList.add("hidden");
    $("resultReviewBtn").textContent = t("result.review");
  }

  function toggleReview() {
    var list = $("resultReview");
    if (!list.classList.contains("hidden")) { list.classList.add("hidden"); return; }
    list.classList.remove("hidden");
    list.innerHTML = examState.qs.map(function (q, i) {
      var ok = sameSet(examState.picks[i], q.a);
      var your = examState.picks[i].length
        ? examState.picks[i].sort().map(function (j) { return optLabel(j); }).join(", ")
        : t("result.none");
      var corr = q.a.slice().sort().map(function (j) { return optLabel(j); }).join(", ");
      return '<div class="review-item">' +
        '<div class="rv-q">' + (i + 1) + ". " + (lang === "en" ? q.q : q.qZh) + "</div>" +
        '<div class="rv-line ' + (ok ? "ok" : "bad") + '">' + t("result.your") + ": " + your + "</div>" +
        (ok ? "" : '<div class="rv-line ok">' + t("result.correct") + ": " + corr + "</div>") +
        '<div class="rv-line">' + (lang === "en" ? q.e : q.eZh) + "</div>" +
        "</div>";
    }).join("");
  }

  /* ---------------- 练习 ---------------- */
  var practiceState = null;

  function startPractice(ids) {
    var domain = $("practiceDomain").value;
    var order = $("practiceOrder").value;
    var pool = ids ? ids.map(function (id) { return QMAP[id]; }).filter(Boolean)
      : (domain === "all" ? QUESTIONS : QUESTIONS.filter(function (q) { return q.domain === domain; }));
    if (!pool.length) return;
    practiceState = { qs: order === "rand" || ids ? shuffle(pool) : pool, cur: 0, right: 0, done: 0 };
    $("practiceSetup").classList.add("hidden");
    $("practiceRun").classList.remove("hidden");
    renderPracticeQuestion();
  }

  function renderPracticeQuestion() {
    var q = practiceState.qs[practiceState.cur];
    $("practiceQMeta").textContent = "#" + (practiceState.cur + 1) + " / " + practiceState.qs.length +
      " · " + domainName(q.domain) + (q.multi ? " · " + t("q.multi") : "");
    $("practiceQText").textContent = lang === "en" ? q.q : q.qZh;
    renderOpts($("practiceOpts"), q, {});
    $("practiceExplain").classList.add("hidden");
    $("practiceCheckBtn").classList.remove("hidden");
    $("practiceCheckBtn").disabled = false;
    $("practicePrevBtn").disabled = practiceState.cur === 0;
    $("practiceNextBtn").disabled = true;
    $("practiceScore").textContent = t("practice.score", { r: practiceState.right, n: practiceState.done });
  }

  function checkPracticeAnswer() {
    var q = practiceState.qs[practiceState.cur];
    var picks = collectPicks($("practiceOpts"));
    if (!picks.length) return;
    var ok = sameSet(picks, q.a);
    practiceState.done++;
    if (ok) practiceState.right++;
    window.NXStore.record(q.id, ok);
    renderOpts($("practiceOpts"), q, { picked: picks, reveal: true });
    showExplanation($("practiceExplain"), q);
    $("practiceCheckBtn").classList.add("hidden");
    $("practiceNextBtn").disabled = practiceState.cur === practiceState.qs.length - 1;
    $("practiceScore").textContent = t("practice.score", { r: practiceState.right, n: practiceState.done });
  }

  function endPractice() {
    practiceState = null;
    $("practiceRun").classList.add("hidden");
    $("practiceSetup").classList.remove("hidden");
    if (window.WPModule) window.WPModule.reportNow();
  }

  /* ---------------- 题库浏览 ---------------- */
  function renderBrowse() {
    var domain = $("browseDomain").value;
    var kw = ($("browseSearch").value || "").toLowerCase();
    var list = $("browseList");
    var items = QUESTIONS.filter(function (q) {
      if (domain !== "all" && q.domain !== domain) return false;
      if (kw) {
        var hay = (q.q + " " + q.qZh + " " + q.o.join(" ") + " " + q.oZh.join(" ")).toLowerCase();
        if (hay.indexOf(kw) < 0) return false;
      }
      return true;
    });
    if (!items.length) {
      list.innerHTML = '<div class="panel-desc">' + t("browse.empty") + "</div>";
      return;
    }
    list.innerHTML = items.map(function (q) {
      var body = q.o.map(function (o, i) {
        return "<div" + (q.a.indexOf(i) >= 0 ? ' style="color:var(--ok);font-weight:700"' : "") + ">" +
          optLabel(i) + ". " + (lang === "en" ? o : q.oZh[i]) + "</div>";
      }).join("");
      return '<details class="browse-item">' +
        "<summary><span class=\"b-tag\">#" + q.id + " · " + domainName(q.domain) + "</span>" +
        (lang === "en" ? q.q : q.qZh) + "</summary>" +
        '<div class="b-body">' + body +
        (q.multi ? "<div>" + t("q.multi") + "</div>" : "") +
        "<div>" + (lang === "en" ? q.e : q.eZh) + "</div></div></details>";
    }).join("");
  }

  /* ---------------- 统计与错题本 ---------------- */
  function renderStats() {
    var st = window.NXStore.getState();
    var answeredIds = Object.keys(st.answered);
    var r = 0, n = 0;
    var byDomain = {};
    answeredIds.forEach(function (id) {
      var a = st.answered[id];
      r += a.r; n += a.r + a.w;
      var q = QMAP[id];
      if (!q) return;
      var d = byDomain[q.domain] = byDomain[q.domain] || { r: 0, n: 0 };
      d.r += a.r; d.n += a.r + a.w;
    });
    var best = 0;
    st.history.forEach(function (h) { if (h.pct > best) best = h.pct; });
    $("statOverview").innerHTML = [
      { b: n, s: t("stats.cellAnswered") },
      { b: (n ? Math.round(r / n * 100) : 0) + "%", s: t("stats.cellAccuracy") },
      { b: st.history.length, s: t("stats.cellExams") },
      { b: best + "%", s: t("stats.cellBest") }
    ].map(function (c) { return '<div class="stat-cell"><b>' + c.b + "</b><span>" + c.s + "</span></div>"; }).join("");

    $("statDomains").innerHTML = DOMAINS.map(function (d) {
      var s = byDomain[d.id] || { r: 0, n: 0 };
      var pct = s.n ? Math.round(s.r / s.n * 100) : 0;
      return '<div class="dom-bar-row"><span>' + domainName(d.id) + "</span>" +
        '<div class="dom-bar-track"><div class="dom-bar-fill" style="width:' + pct + '%"></div></div>' +
        '<span class="dom-pct">' + (s.n ? pct + "%" : "–") + "</span></div>";
    }).join("");

    $("statHistory").innerHTML = st.history.length
      ? st.history.slice(0, 10).map(function (h) {
        var dt = new Date(h.ts);
        return '<div class="history-item"><b>' + dt.toLocaleString() + "</b><span>" +
          h.score + " / " + h.total + " · " + h.pct + "%</span>" +
          '<span style="color:' + (h.pass ? "var(--ok)" : "var(--bad)") + '">' +
          (h.pass ? t("result.pass") : t("result.fail")) + "</span></div>";
      }).join("")
      : '<div class="panel-desc">' + t("stats.noHistory") + "</div>";

    var wrongIds = window.NXStore.wrongIds();
    $("wrongSummary").textContent = wrongIds.length
      ? t("wrong.summary", { n: wrongIds.length })
      : t("wrong.empty");
    $("wrongPracticeBtn").disabled = !wrongIds.length;
    $("wrongList").innerHTML = wrongIds.map(function (id) {
      var q = QMAP[id];
      if (!q) return "";
      return '<div class="history-item"><span class="b-tag" style="padding:1px 8px;border-radius:999px;color:var(--accent-ink);background:var(--accent);font-size:11px;font-weight:700">#' +
        q.id + " " + domainName(q.domain) + "</span><span>" + (lang === "en" ? q.q : q.qZh) +
        '</span><span style="color:var(--bad)">' + t("wrong.times", { n: st.wrong[id].n }) + "</span></div>";
    }).join("");
  }

  /* ---------------- 动态部分（语言切换后重渲染） ---------------- */
  function renderDynamic() {
    buildRuleCards();
    fillDomainSelect($("examDomain"), t("exam.domain") + ": " + (lang === "en" ? "All" : "全部"));
    fillDomainSelect($("practiceDomain"), lang === "en" ? "All" : "全部");
    fillDomainSelect($("browseDomain"), lang === "en" ? "All" : "全部");
    var note = $("bankNote");
    if (note) note.textContent = t("brand.note");
    if (currentView === "browse" && !$("view-browse").classList.contains("hidden")) renderBrowse();
    if (currentView === "stats" && !$("view-stats").classList.contains("hidden")) renderStats();
  }

  /* ---------------- 向总后台上报练习小结 ---------------- */
  /* 没登录就不报：这个模块不要求登录，报不上去也不该影响练习本身。 */
  function practiceSummary() {
    var st = window.NXStore.getState();
    var r = 0, n = 0;
    Object.keys(st.answered).forEach(function (id) {
      var a = st.answered[id];
      r += a.r; n += a.r + a.w;
    });
    var best = 0;
    st.history.forEach(function (h) { if (h.pct > best) best = h.pct; });
    return {
      answered: n,
      accuracy: n ? Math.round(r / n * 100) : 0,
      exams: st.history.length,
      best: best,
      wrong: window.NXStore.wrongIds().length
    };
  }

  function startReporting() {
    if (!window.WPModule) return;
    window.WPModule.setSummary(practiceSummary);
    window.WPModule.reportNow();
  }

  /* ---------------- 事件绑定与初始化 ---------------- */
  function init() {
    buildPicker();
    applyTheme(store(THEME_KEY) || "indigo");
    applyLanguage(store(LANG_KEY) || "zh");
    startReporting();

    document.querySelectorAll(".nav-btn").forEach(function (btn) {
      btn.addEventListener("click", function () { switchView(btn.dataset.view); });
    });
    $("langBtn").addEventListener("click", function () {
      applyLanguage(lang === "en" ? "zh" : "en");
    });

    $("startExamBtn").addEventListener("click", startExam);
    $("examPrevBtn").addEventListener("click", function () {
      if (examState && examState.cur > 0) { examState.cur--; renderExamQuestion(); updateExamProgress(); }
    });
    $("examNextBtn").addEventListener("click", function () {
      if (examState && examState.cur < examState.qs.length - 1) { examState.cur++; renderExamQuestion(); updateExamProgress(); }
    });
    $("examSubmitBtn").addEventListener("click", finishExam);
    $("examSheetBtn").addEventListener("click", function () {
      $("examSheet").classList.toggle("hidden");
      updateExamProgress();
    });
    $("resultReviewBtn").addEventListener("click", toggleReview);
    $("resultAgainBtn").addEventListener("click", function () {
      $("examResult").classList.add("hidden");
      $("examSetup").classList.remove("hidden");
    });

    $("startPracticeBtn").addEventListener("click", function () { startPractice(null); });
    $("practicePrevBtn").addEventListener("click", function () {
      if (practiceState && practiceState.cur > 0) { practiceState.cur--; renderPracticeQuestion(); }
    });
    $("practiceNextBtn").addEventListener("click", function () {
      if (practiceState && practiceState.cur < practiceState.qs.length - 1) {
        practiceState.cur++;
        renderPracticeQuestion();
      } else if (practiceState) {
        endPractice();
      }
    });
    $("practiceCheckBtn").addEventListener("click", checkPracticeAnswer);
    $("practiceEndBtn").addEventListener("click", endPractice);

    $("browseDomain").addEventListener("change", renderBrowse);
    $("browseSearch").addEventListener("input", renderBrowse);

    $("wrongPracticeBtn").addEventListener("click", function () {
      startPractice(window.NXStore.wrongIds());
    });
    $("wrongClearBtn").addEventListener("click", function () {
      if (window.confirm(t("wrong.confirm"))) {
        window.NXStore.clearWrong();
        renderStats();
      }
    });
  }

  document.addEventListener("DOMContentLoaded", init);
})();
