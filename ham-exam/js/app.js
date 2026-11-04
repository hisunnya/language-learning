/* ============================================================
   app.js —— 主应用
   ============================================================ */
(function () {
  'use strict';

  var BANK = window.BANK;
  if (!BANK) { document.body.innerHTML = '<p style="padding:40px">题库数据未载入</p>'; return; }

  /* ---------------- 常量 ---------------- */
  var RULES = {
    A: { name: 'A 类', single: 32, multi: 8, minutes: 40, pass: 30 },
    B: { name: 'B 类', single: 45, multi: 15, minutes: 60, pass: 45 },
    C: { name: 'C 类', single: 70, multi: 20, minutes: 90, pass: 70 }
  };
  var LETTERS = ['A', 'B', 'C', 'D'];

  /* ---------------- 索引 ---------------- */
  var byId = {};
  var byCls = { A: [], B: [], C: [] };
  var byPoint = {};
  var cntByPoint = {};   // 知识点 -> {A:n,B:n,C:n}
  BANK.questions.forEach(function (q) {
    byId[q.id] = q;
    (byPoint[q.p] = byPoint[q.p] || []).push(q);
    q.cls.forEach(function (c) { if (byCls[c]) byCls[c].push(q); });
    var m = cntByPoint[q.p] = cntByPoint[q.p] || { A: 0, B: 0, C: 0 };
    q.cls.forEach(function (c) { if (m[c] != null) m[c]++; });
  });

  /* ---------------- 状态 ---------------- */
  var S = {
    view: 'exam',
    cls: Store.settings().cls || 'A',
    exam: null,      // {ids, ans, flags, idx, deadline, startedAt, cls, timer}
    practice: null,  // {ids, ans, idx, cls, results:[], scope}
    browse: { filter: 'all', point: null, search: '', shown: 60 },
    timerId: null
  };

  /* ---------------- 工具 ---------------- */
  function $(s, r) { return (r || document).querySelector(s); }
  function $$(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }
  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }
  function shuffle(a) {
    var r = a.slice();
    for (var i = r.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1)), t = r[i]; r[i] = r[j]; r[j] = t;
    }
    return r;
  }
  function fmtTime(sec) {
    sec = Math.max(0, Math.round(sec));
    var m = Math.floor(sec / 60), s = sec % 60;
    return (m < 10 ? '0' : '') + m + ':' + (s < 10 ? '0' : '') + s;
  }
  function fmtDate(ts) {
    var d = new Date(ts);
    function p(n) { return (n < 10 ? '0' : '') + n; }
    return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()) +
      ' ' + p(d.getHours()) + ':' + p(d.getMinutes());
  }
  function toast(msg) {
    var t = $('#toast'); t.textContent = msg; t.hidden = false;
    clearTimeout(t._t); t._t = setTimeout(function () { t.hidden = true; }, 2200);
  }
  function modal(title, bodyHtml, buttons) {
    $('#modalTitle').textContent = title;
    $('#modalBody').innerHTML = bodyHtml;
    var foot = $('#modalFoot'); foot.innerHTML = '';
    (buttons || []).forEach(function (b) {
      var btn = document.createElement('button');
      btn.className = 'btn' + (b.primary ? ' btn-primary' : '') + (b.danger ? ' btn-danger' : '');
      btn.textContent = b.text;
      btn.onclick = function () { if (!b.onClick || b.onClick() !== false) closeModal(); };
      foot.appendChild(btn);
    });
    $('#modalMask').hidden = false;
  }
  function closeModal() { $('#modalMask').hidden = true; }
  $('#modalClose').onclick = closeModal;
  $('#modalMask').onclick = function (e) { if (e.target === $('#modalMask')) closeModal(); };

  function pointName(code) { return BANK.points[code] || code; }
  function pointPath(code) {
    var p = code.split('.');
    var g = BANK.groups[p[0]] || '';
    var s = BANK.sections[code.slice(0, 3)] || '';
    return g + ' › ' + s + ' › ' + pointName(code);
  }
  function pointShort(code) {
    return (BANK.sections[code.slice(0, 3)] || '') + ' › ' + pointName(code);
  }

  /* ============================================================
     顶栏 / 导航
     ============================================================ */
  function buildClsSwitch() {
    var box = $('#clsSwitch'); box.innerHTML = '';
    ['A', 'B', 'C'].forEach(function (c) {
      var b = document.createElement('button');
      b.textContent = c + ' 类';
      b.className = S.cls === c ? 'on' : '';
      b.onclick = function () {
        S.cls = c; Store.setSettings({ cls: c });
        buildClsSwitch();
        if (S.view === 'exam') renderExamSetup();
        if (S.view === 'browse') renderBrowseList();
        if (S.view === 'stats') renderStats();
      };
      box.appendChild(b);
    });
  }

  function switchView(v) {
    S.view = v;
    $$('.nav-btn').forEach(function (b) { b.classList.toggle('active', b.dataset.view === v); });
    $$('.view').forEach(function (sec) { sec.hidden = sec.id !== 'view-' + v; });
    if (v === 'exam') { if (S.exam) renderExamRun(); else renderExamSetup(); }
    if (v === 'practice') { if (S.practice) renderPracticeRun(); else renderPracticeSetup(); }
    if (v === 'browse') { renderTree(); renderBrowseList(); }
    if (v === 'stats') renderStats();
    window.scrollTo(0, 0);
  }
  $$('.nav-btn').forEach(function (b) { b.onclick = function () { switchView(b.dataset.view); }; });

  /* 主题 */
  function applyTheme(t) {
    document.documentElement.setAttribute('data-theme', t);
    $('#themeBtn').textContent = t === 'dark' ? '☀️' : '🌙';
  }
  $('#themeBtn').onclick = function () {
    var t = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    Store.setSettings({ theme: t }); applyTheme(t);
  };

  /* ============================================================
     题目渲染（共用）
     ============================================================ */
  /* 原地刷新选项样式，避免整题重绘（多选连点时界面不会跳动） */
  function refreshOptionStates(sel, q, chosen, reveal) {
    $$(sel + ' .opt').forEach(function (b) {
      var L = b.dataset.opt;
      var isChosen = chosen && chosen.indexOf(L) >= 0;
      var isRight = reveal && q.a.indexOf(L) >= 0;
      var isWrong = reveal && isChosen && !isRight;
      b.className = 'opt' + (reveal && isRight ? ' right' : (reveal && isWrong ? ' wrong' : (isChosen ? ' sel' : '')));
      var mk = b.querySelector('.mark');
      if (reveal && (isRight || isWrong)) {
        if (!mk) { mk = document.createElement('span'); mk.className = 'mark'; b.appendChild(mk); }
        mk.textContent = isRight ? '✓ 正确' : '✗ 你选的';
      } else if (mk) { mk.remove(); }
    });
  }

  function optionsHTML(q, chosen, reveal) {
    var h = '';
    for (var i = 0; i < 4; i++) {
      var L = LETTERS[i];
      var isChosen = chosen && chosen.indexOf(L) >= 0;
      var isRight = reveal && q.a.indexOf(L) >= 0;
      var isWrong = reveal && isChosen && !isRight;
      var cls = 'opt';
      if (reveal && isRight) cls += ' right';
      else if (reveal && isWrong) cls += ' wrong';
      else if (isChosen) cls += ' sel';
      var mark = '';
      if (reveal && isRight) mark = '<span class="mark">✓ 正确</span>';
      else if (reveal && isWrong) mark = '<span class="mark">✗ 你选的</span>';
      h += '<button class="' + cls + '" data-opt="' + L + '">' +
        '<span class="k">' + L + '</span>' +
        '<span class="txt">' + esc(q.o[i]) + '</span>' + mark + '</button>';
    }
    return h;
  }

  function stemHTML(q) {
    var h = '<div class="q-head">' +
      '<span class="q-no" data-qid="' + esc(q.id) + '">' + esc(q.uid || q.no || q.id) + '</span>' +
      '<span class="q-type ' + (q.t === 'm' ? 'multi' : '') + '">' + (q.t === 'm' ? '多选' : '单选') + '</span>' +
      '<span class="q-point">' + esc(pointPath(q.p)) + '</span>' +
      '</div>';
    h += '<p class="q-stem">' + esc(q.q) + '</p>';
    if (q.img) h += '<img class="q-img" src="' + esc(q.img) + '" alt="附图" loading="lazy">';
    return h;
  }

  function explainHTML(q) {
    return '<div class="explain"><b>正确答案：' + esc(q.a) + '</b><br>' +
      '所属类别：' + esc(q.cls.join(' / ')) + ' 类　·　知识点：' + esc(pointPath(q.p)) +
      '<br>题目编号：' + esc(q.uid || q.no || q.id) +
      (q.no && q.no !== q.uid ? '（题库原编号 ' + esc(q.no) + '）' : '') + '</div>';
  }

  /* ============================================================
     模拟考试
     ============================================================ */
  function renderExamSetup() {
    $('#examSetup').hidden = false;
    $('#examRun').hidden = true;
    $('#examResult').hidden = true;
    var r = RULES[S.cls];
    var cards = [
      { k: '试卷题量', v: (r.single + r.multi) + '<small> 题</small>' },
      { k: '单选 / 多选', v: r.single + ' / ' + r.multi },
      { k: '考试时长', v: r.minutes + '<small> 分钟</small>' },
      { k: '合格标准', v: '答对 ' + r.pass + '<small> 题</small>' }
    ];
    $('#ruleCards').innerHTML = cards.map(function (c) {
      return '<div class="rule-card"><div class="k">' + c.k + '</div><div class="v">' + c.v + '</div></div>';
    }).join('');

    var draft = Store.getExamDraft();
    var btn = $('#resumeExamBtn');
    if (draft && draft.ids && draft.ids.length) {
      btn.hidden = false;
      btn.textContent = '继续上次未完成的考试（' + RULES[draft.cls].name + '，剩 ' +
        Math.max(0, Math.round((draft.deadline - Date.now()) / 1000)) + ' 秒）';
      btn.onclick = function () { resumeExam(draft); };
    } else { btn.hidden = true; }
  }

  function buildExamPaper(cls) {
    var r = RULES[cls];
    var pool = byCls[cls] || [];
    var singles = shuffle(pool.filter(function (q) { return q.t === 's'; }));
    var multis = shuffle(pool.filter(function (q) { return q.t === 'm'; }));
    var ids = singles.slice(0, r.single).concat(multis.slice(0, r.multi));
    return shuffle(ids).map(function (q) { return q.id; });
  }

  function startExam() {
    var cls = S.cls;
    var ids = buildExamPaper(cls);
    if (ids.length < RULES[cls].single + RULES[cls].multi) {
      toast('题库数量不足，无法生成试卷'); return;
    }
    S.exam = {
      cls: cls, ids: ids, ans: {}, flags: {}, idx: 0,
      startedAt: Date.now(),
      deadline: Date.now() + RULES[cls].minutes * 60000
    };
    Store.setExamDraft({ cls: cls, ids: ids, ans: {}, flags: {}, idx: 0, startedAt: S.exam.startedAt, deadline: S.exam.deadline });
    renderExamRun();
    startTimer();
  }

  function resumeExam(draft) {
    S.exam = {
      cls: draft.cls, ids: draft.ids, ans: draft.ans || {}, flags: draft.flags || {},
      idx: draft.idx || 0, startedAt: draft.startedAt, deadline: draft.deadline
    };
    if (S.exam.deadline < Date.now()) { toast('上次考试已超时，已直接交卷'); submitExam(true); return; }
    renderExamRun(); startTimer();
  }

  function startTimer() {
    stopTimer();
    S.timerId = setInterval(function () {
      if (!S.exam) return stopTimer();
      var left = Math.round((S.exam.deadline - Date.now()) / 1000);
      var t = $('#timer');
      if (t) {
        t.textContent = fmtTime(left);
        t.className = 'timer' + (left <= 60 ? ' danger' : (left <= 300 ? ' warn' : ''));
      }
      if (left <= 0) { stopTimer(); submitExam(true); }
    }, 500);
  }
  function stopTimer() { if (S.timerId) { clearInterval(S.timerId); S.timerId = null; } }

  function renderExamRun() {
    $('#examSetup').hidden = true;
    $('#examResult').hidden = true;
    $('#examRun').hidden = false;
    $('#examClsTag').textContent = RULES[S.exam.cls].name;
    drawExamQuestion();
    drawAnswerCard('#answerCard', 'exam');
  }

  function drawExamQuestion() {
    var ex = S.exam, id = ex.ids[ex.idx], q = byId[id];
    var chosen = ex.ans[id] || '';
    $('#examProgress').textContent = '第 ' + (ex.idx + 1) + ' / ' + ex.ids.length + ' 题';
    var html = stemHTML(q) + '<div class="opts" id="examOpts">' + optionsHTML(q, chosen, false) + '</div>';
    html += '<div class="q-foot">' +
      '<button class="btn btn-sm" id="flagBtn">' + (ex.flags[id] ? '★ 已标记' : '☆ 标记本题') + '</button>' +
      '<div class="row-btns">' +
      '<button class="btn btn-sm" id="prevBtn"' + (ex.idx === 0 ? ' disabled' : '') + '>上一题</button>' +
      '<button class="btn btn-sm btn-primary" id="nextBtn"' + (ex.idx === ex.ids.length - 1 ? ' disabled' : '') + '>下一题</button>' +
      '</div></div>';
    $('#examQ').innerHTML = html;

    $$('#examOpts .opt').forEach(function (b) {
      b.onclick = function () { pickExamOption(b.dataset.opt); };
    });
    $('#prevBtn').onclick = function () { if (ex.idx > 0) { ex.idx--; saveExamDraft(); drawExamQuestion(); drawAnswerCard('#answerCard', 'exam'); } };
    $('#nextBtn').onclick = function () { if (ex.idx < ex.ids.length - 1) { ex.idx++; saveExamDraft(); drawExamQuestion(); drawAnswerCard('#answerCard', 'exam'); } };
    $('#flagBtn').onclick = function () {
      if (ex.flags[id]) delete ex.flags[id]; else ex.flags[id] = 1;
      saveExamDraft();
      $('#flagBtn').textContent = ex.flags[id] ? '★ 已标记' : '☆ 标记本题';
      drawAnswerCard('#answerCard', 'exam');
    };
  }

  function pickExamOption(L) {
    var ex = S.exam, id = ex.ids[ex.idx], q = byId[id];
    var cur = ex.ans[id] || '';
    if (q.t === 'm') {
      var arr = cur.split('').filter(Boolean);
      var i = arr.indexOf(L);
      if (i >= 0) arr.splice(i, 1); else arr.push(L);
      arr.sort();
      if (arr.length) ex.ans[id] = arr.join(''); else delete ex.ans[id];
    } else {
      ex.ans[id] = (cur === L) ? '' : L;
      if (!ex.ans[id]) delete ex.ans[id];
    }
    saveExamDraft();
    refreshOptionStates('#examOpts', q, ex.ans[id] || '', false);
    drawAnswerCard('#answerCard', 'exam');
  }

  function saveExamDraft() {
    if (!S.exam) return;
    Store.setExamDraft({
      cls: S.exam.cls, ids: S.exam.ids, ans: S.exam.ans, flags: S.exam.flags,
      idx: S.exam.idx, startedAt: S.exam.startedAt, deadline: S.exam.deadline
    });
  }

  function drawAnswerCard(sel, src) {
    var box = $(sel);
    if (!box) return;
    var ex = src === 'practice' ? S.practice : (S.exam || S.practice);
    if (!ex) { box.innerHTML = ''; return; }
    var html = '<div class="ac-grid">';
    ex.ids.forEach(function (id, i) {
      var done = ex.ans[id] ? ' done' : '';
      var flag = ex.flags && ex.flags[id] ? ' flag' : '';
      var cur = i === ex.idx ? ' cur' : '';
      html += '<div class="ac-cell' + done + flag + cur + '" data-i="' + i + '">' + (i + 1) + '</div>';
    });
    html += '</div><div class="ac-legend">' +
      '<span><i style="background:var(--brand)"></i>已答</span>' +
      '<span><i style="background:var(--panel);border:1px solid var(--line)"></i>未答</span>' +
      '<span><i style="background:var(--warn-bg);border:1px solid var(--warn)"></i>已标记</span>' +
      '</div>';
    box.innerHTML = html;
    $$('.ac-cell', box).forEach(function (c) {
      c.onclick = function () {
        var i = +c.dataset.i;
        if (src === 'practice') {
          if (!S.practice) return;
          S.practice.idx = i; savePracticeDraft(); drawPracticeQuestion();
        } else {
          if (!S.exam) return;
          S.exam.idx = i; saveExamDraft(); drawExamQuestion();
        }
        drawAnswerCard(sel, src);
      };
    });
  }

  function submitExam(auto) {
    stopTimer();
    var ex = S.exam; if (!ex) return;
    var right = 0, wrongIds = [];
    ex.ids.forEach(function (id) {
      var q = byId[id], a = ex.ans[id] || '';
      if (a === q.a) right++; else wrongIds.push(id);
    });
    var sec = Math.round((Date.now() - ex.startedAt) / 1000);
    var pass = right >= RULES[ex.cls].pass;

    // 写入进度
    ex.ids.forEach(function (id) {
      var q = byId[id];
      Store.record(id, (ex.ans[id] || '') === q.a);
    });
    Store.addExam({
      id: 'E' + Date.now(), ts: Date.now(), cls: ex.cls, total: ex.ids.length,
      right: right, sec: sec, pass: pass, auto: !!auto, wrong: wrongIds,
      ans: JSON.parse(JSON.stringify(ex.ans))
    });
    Store.clearExamDraft();
    S.exam = null;
    renderExamResult(ex, right, sec, pass, wrongIds);
  }

  function renderExamResult(ex, right, sec, pass, wrongIds) {
    $('#examSetup').hidden = true;
    $('#examRun').hidden = true;
    $('#examResult').hidden = false;
    var total = ex.ids.length;
    var pct = Math.round(right / total * 100);
    var r = RULES[ex.cls];
    var html = '<h2 class="panel-title">' + r.name + ' 模拟考试结果</h2>' +
      '<p class="panel-desc">' + fmtDate(ex.startedAt) + ' 开始' + (ex._auto ? '（超时自动交卷）' : '') + '</p>' +
      '<div class="score-hero">' +
      '<div class="score-ring" style="--p:' + pct + '"><div class="inner"><div class="n">' + right + '/' + total + '</div><div class="d">答对题数</div></div></div>' +
      '<div class="stat-grid">' +
      '<div class="stat"><div class="k">得分</div><div class="v">' + right + '</div></div>' +
      '<div class="stat"><div class="k">正确率</div><div class="v">' + pct + '%</div></div>' +
      '<div class="stat"><div class="k">用时</div><div class="v">' + fmtTime(sec) + '</div></div>' +
      '<div class="stat"><div class="k">合格线</div><div class="v">' + r.pass + ' 题</div></div>' +
      '<div class="stat"><div class="k">结果</div><div class="v"><span class="badge ' + (pass ? 'pass' : 'fail') + '">' + (pass ? '合格' : '不合格') + '</span></div></div>' +
      '</div></div>';

    // 知识点统计
    html += '<div class="sec-title">本卷知识点表现</div><div class="card tbl-wrap"><table class="tbl"><thead><tr>' +
      '<th>知识点</th><th>题数</th><th>答对</th><th>正确率</th></tr></thead><tbody>';
    var groups = {};
    ex.ids.forEach(function (id) {
      var q = byId[id];
      var g = groups[q.p] = groups[q.p] || { n: 0, c: 0 };
      g.n++; if ((ex.ans[id] || '') === q.a) g.c++;
    });
    Object.keys(groups).sort(function (a, b) {
      var ga = groups[a].c / groups[a].n, gb = groups[b].c / groups[b].n;
      return ga - gb;
    }).forEach(function (p) {
      var g = groups[p], pc = Math.round(g.c / g.n * 100);
      var cls = pc >= 80 ? 'ok' : (pc >= 60 ? 'warn' : 'bad');
      html += '<tr><td>' + esc(pointPath(p)) + '</td><td>' + g.n + '</td><td>' + g.c + '</td>' +
        '<td><div style="display:flex;align-items:center;gap:9px"><div class="bar" style="flex:1"><i class="' + cls + '" style="width:' + pc + '%"></i></div><span style="font-family:var(--code)">' + pc + '%</span></div></td></tr>';
    });
    html += '</tbody></table></div>';

    // 逐题
    html += '<div class="sec-title">逐题回顾（' + wrongIds.length + ' 题错误）</div>';
    ex.ids.forEach(function (id, i) {
      var q = byId[id], chosen = ex.ans[id] || '';
      var ok = chosen === q.a;
      html += '<div class="review-item"><div class="review-head" data-rev="' + id + '">' +
        '<span class="idx">' + (i + 1) + '</span>' +
        '<span class="mini">' + esc(q.q) + '</span>' +
        '<span class="st ' + (ok ? 'ok' : 'no') + '">' + (ok ? '✓ 正确' : '✗ 错误') + '</span></div>' +
        '<div class="review-body" hidden><div class="q-stem">' + esc(q.q) + '</div>' +
        (q.img ? '<img class="q-img" src="' + esc(q.img) + '" alt="附图">' : '') +
        '<div class="opts">' + optionsHTML(q, chosen, true) + '</div>' +
        (chosen ? '' : '<div class="explain">本题<b>未作答</b>。</div>') +
        explainHTML(q) + '</div></div>';
    });
    html += '</div>';

    html += '<div class="row-btns" style="margin-top:20px">' +
      '<button class="btn btn-primary" id="againBtn">再考一次</button>' +
      '<button class="btn" id="wrongBtn">练习这 ' + wrongIds.length + ' 道错题</button>' +
      '<button class="btn" id="homeBtn">返回</button></div>';

    $('#examResult').innerHTML = html;
    $$('#examResult .review-head').forEach(function (h) {
      h.onclick = function () {
        var b = h.nextElementSibling; b.hidden = !b.hidden;
      };
    });
    $('#againBtn').onclick = function () { startExam(); };
    $('#homeBtn').onclick = function () { renderExamSetup(); };
    $('#wrongBtn').onclick = function () {
      if (!wrongIds.length) { toast('全部答对，没有错题'); return; }
      S.cls = ex.cls; buildClsSwitch();
      startPracticeWith(wrongIds.map(function (id) { return byId[id]; }), '本次错题');
    };
  }

  /* ============================================================
     练习模式
     ============================================================ */
  function fillPointSelect() {
    var sel = $('#prPoint');
    if (sel.dataset.filled) return;
    var codes = Object.keys(BANK.points).sort(function (a, b) {
      return a.split('.').map(Number).reduce(function (a, b) { return a * 10 + b; }) -
        b.split('.').map(Number).reduce(function (a, b) { return a * 10 + b; });
    });
    var groups = {};
    codes.forEach(function (c) {
      var g = c.split('.')[0];
      (groups[g] = groups[g] || []).push(c);
    });
    var html = '<option value="">全部知识点</option>';
    Object.keys(groups).forEach(function (g) {
      html += '<optgroup label="' + esc(BANK.groups[g] || g) + '">';
      groups[g].forEach(function (c) {
        html += '<option value="' + c + '">' + esc(c + ' ' + pointName(c)) + '</option>';
      });
      html += '</optgroup>';
    });
    sel.innerHTML = html; sel.dataset.filled = '1';
  }

  function renderPracticeSetup() {
    $('#practiceSetup').hidden = false;
    $('#practiceRun').hidden = true;
    fillPointSelect();
    var draft = Store.getPracticeDraft();
    var btn = $('#resumePracticeBtn');
    if (draft && draft.ids && draft.ids.length) {
      btn.hidden = false;
      btn.textContent = '继续上次练习（已答 ' + Object.keys(draft.ans || {}).length + ' / ' + draft.ids.length + '）';
      btn.onclick = function () {
        S.practice = { cls: draft.cls, ids: draft.ids, ans: draft.ans || {}, idx: draft.idx || 0, scope: draft.scope || '上次练习' };
        renderPracticeRun();
      };
    } else btn.hidden = true;
  }

  function startPractice() {
    var cls = S.cls, scope = $('#prScope').value, n = +$('#prCount').value;
    var point = $('#prPoint').value;
    var pool = (byCls[cls] || []).slice();
    if (scope === 'single') pool = pool.filter(function (q) { return q.t === 's'; });
    if (scope === 'multi') pool = pool.filter(function (q) { return q.t === 'm'; });
    if (scope === 'image') pool = pool.filter(function (q) { return !!q.img; });
    if (scope === 'wrong') pool = pool.filter(function (q) { var p = Store.progress(q.id); return p && p.w; });
    if (scope === 'undone') pool = pool.filter(function (q) { return !Store.progress(q.id); });
    if (scope === 'fav') pool = pool.filter(function (q) { return Store.isFav(q.id); });
    if (point) pool = pool.filter(function (q) { return q.p === point; });
    if (!pool.length) { toast('该范围下没有题目'); return; }
    pool = shuffle(pool);
    if (n > 0) pool = pool.slice(0, n);
    startPracticeWith(pool, scopeLabel(scope));
  }

  function scopeLabel(s) {
    return { all: '全部题目', single: '单选题', multi: '多选题', image: '附图题', wrong: '错题', undone: '未做过的题', fav: '收藏' }[s] || s;
  }

  function startPracticeWith(list, label) {
    var ids = list.map(function (q) { return q.id; });
    // 题目可能来自别的类别（如"错题重练"），据此推断实际类别
    var inferred = S.cls;
    if (list.length) {
      var inter = list[0].cls.filter(function (c) {
        return list.every(function (q) { return q.cls.indexOf(c) >= 0; });
      });
      if (inter.length) inferred = inter[0];
    }
    S.practice = { cls: inferred, ids: ids, ans: {}, idx: 0, scope: label || '练习' };
    Store.setPracticeDraft({ cls: inferred, ids: ids, ans: {}, idx: 0, scope: S.practice.scope });
    renderPracticeRun();
  }

  function renderPracticeRun() {
    $('#practiceSetup').hidden = true;
    $('#practiceRun').hidden = false;
    $('#prClsTag').textContent = RULES[S.practice.cls].name;
    drawPracticeQuestion();
    drawAnswerCard('#practiceCard', 'practice');
  }

  function drawPracticeQuestion() {
    var pr = S.practice, id = pr.ids[pr.idx], q = byId[id];
    var chosen = pr.ans[id] || '';
    var revealed = !!chosen && chosen.submitted;
    var sel = revealed ? chosen.pick : '';
    $('#prProgress').textContent = '第 ' + (pr.idx + 1) + ' / ' + pr.ids.length + ' 题　·　' + pr.scope;
    updatePracticeScore();

    var html = stemHTML(q) + '<div class="opts" id="prOpts">' + optionsHTML(q, sel, revealed) + '</div>';
    if (revealed) {
      var ok = sel === q.a;
      html += explainHTML(q);
      if (!ok) html = html.replace('<div class="explain"><b>正确答案', '<div class="explain"><b style="color:' + (ok ? 'var(--ok)' : 'var(--bad)') + '">' + (ok ? '✓ 答对了' : '✗ 答错了，正确答案') + '</b><br><b>正确答案');
    }
    if (q.t === 'm' && !revealed) {
      var curPick = (pr.ans[id] && pr.ans[id].pick) || '';
      html += '<div class="q-foot"><span class="eh-meta">多选题：选完后点右侧「提交本题」</span>' +
        '<div class="row-btns"><button class="btn btn-sm btn-primary" id="submitThis"' + (curPick ? '' : ' disabled') + '>提交本题</button></div></div>';
    } else {
      html += '<div class="q-foot">' +
        '<button class="btn btn-sm" id="prFlag">' + (pr.flags && pr.flags[id] ? '★ 已标记' : '☆ 标记') + '</button>' +
        '<div class="row-btns">' +
        '<button class="btn btn-sm" id="prPrev"' + (pr.idx === 0 ? ' disabled' : '') + '>上一题</button>' +
        '<button class="btn btn-sm btn-primary" id="prNext">下一题</button>' +
        '</div></div>';
    }
    $('#practiceQ').innerHTML = html;

    $$('#prOpts .opt').forEach(function (b) {
      b.onclick = function () { pickPracticeOption(b.dataset.opt); };
    });
    var st = $('#submitThis');
    if (st) st.onclick = submitPracticeAnswer;
    var np = $('#prNext');
    if (np) np.onclick = function () { pr.idx = Math.min(pr.idx + 1, pr.ids.length - 1); savePracticeDraft(); drawPracticeQuestion(); drawAnswerCard('#practiceCard', 'practice'); };
    var pv = $('#prPrev');
    if (pv) pv.onclick = function () { pr.idx = Math.max(pr.idx - 1, 0); savePracticeDraft(); drawPracticeQuestion(); drawAnswerCard('#practiceCard', 'practice'); };
    var fg = $('#prFlag');
    if (fg) fg.onclick = function () {
      pr.flags = pr.flags || {};
      if (pr.flags[id]) delete pr.flags[id]; else pr.flags[id] = 1;
      savePracticeDraft(); drawPracticeQuestion();
    };
  }

  function pickPracticeOption(L) {
    var pr = S.practice, id = pr.ids[pr.idx], q = byId[id];
    var rec = pr.ans[id];
    if (rec && rec.submitted) return;
    var cur = rec ? rec.pick : '';
    if (q.t === 'm') {
      var arr = cur.split('').filter(Boolean);
      var i = arr.indexOf(L);
      if (i >= 0) arr.splice(i, 1); else arr.push(L);
      arr.sort();
      cur = arr.join('');
    } else cur = L;
    pr.ans[id] = { pick: cur, submitted: false };
    if (!cur) delete pr.ans[id];
    savePracticeDraft();
    if (q.t === 's' && cur) { submitPracticeAnswer(); return; }
    // 多选：原地刷新，不重绘整题
    refreshOptionStates('#prOpts', q, cur, false);
    var st = $('#submitThis');
    if (st) st.disabled = !cur;
  }

  function submitPracticeAnswer() {
    var pr = S.practice, id = pr.ids[pr.idx], q = byId[id];
    var rec = pr.ans[id];
    if (!rec || !rec.pick) { toast('请先选择答案'); return; }
    rec.submitted = true;
    Store.record(id, rec.pick === q.a);
    savePracticeDraft();
    drawPracticeQuestion();
    drawAnswerCard('#practiceCard', 'practice');
  }

  function updatePracticeScore() {
    var pr = S.practice, tot = 0, ok = 0;
    Object.keys(pr.ans).forEach(function (id) {
      if (pr.ans[id].submitted) { tot++; if (pr.ans[id].pick === byId[id].a) ok++; }
    });
    $('#prScore').textContent = '正确 ' + ok + ' / ' + tot;
  }

  function savePracticeDraft() {
    if (!S.practice) return;
    Store.setPracticeDraft({
      cls: S.practice.cls, ids: S.practice.ids, ans: S.practice.ans,
      idx: S.practice.idx, scope: S.practice.scope, flags: S.practice.flags
    });
  }

  function endPractice() {
    var pr = S.practice; if (!pr) return;
    var tot = 0, ok = 0, wrongIds = [];
    Object.keys(pr.ans).forEach(function (id) {
      if (!pr.ans[id].submitted) return;
      tot++;
      if (pr.ans[id].pick === byId[id].a) ok++; else wrongIds.push(id);
    });
    Store.addPractice({
      id: 'P' + Date.now(), ts: Date.now(), cls: pr.cls, total: pr.ids.length,
      answered: tot, right: ok, scope: pr.scope, wrong: wrongIds
    });
    Store.clearPracticeDraft();
    var pct = tot ? Math.round(ok / tot * 100) : 0;
    S.practice = null;
    modal('练习结束', '<div class="stat-grid">' +
      '<div class="stat"><div class="k">已答</div><div class="v">' + tot + '</div></div>' +
      '<div class="stat"><div class="k">答对</div><div class="v">' + ok + '</div></div>' +
      '<div class="stat"><div class="k">正确率</div><div class="v">' + pct + '%</div></div>' +
      '<div class="stat"><div class="k">错题</div><div class="v">' + wrongIds.length + '</div></div>' +
      '</div>', [
      { text: '再练一轮', primary: true, onClick: function () { renderPracticeSetup(); } },
      { text: '查看统计', onClick: function () { switchView('stats'); } }
      ]);
    renderPracticeSetup();
  }

  $('#startPracticeBtn').onclick = startPractice;
  $('#endPracticeBtn').onclick = endPractice;
  $('#prToggleCardBtn').onclick = function () {
    var c = $('#practiceCard'); c.hidden = !c.hidden;
    if (!c.hidden) drawAnswerCard('#practiceCard', 'practice');
  };

  /* ============================================================
     题库浏览
     ============================================================ */
  function renderTree() {
    var tree = $('#pointTree');
    var groups = BANK.tree;
    var cls = S.cls;
    var html = '';
    Object.keys(groups).forEach(function (g) {
      var gc = 0;
      Object.keys(groups[g]).forEach(function (s) {
        Object.keys(groups[g][s]).forEach(function (p) {
          gc += (cntByPoint[p] && cntByPoint[p][cls]) || 0;
        });
      });
      html += '<details class="lv1" open><summary>' + esc(BANK.groups[g] || ('第 ' + g + ' 部分')) +
        '<span class="cnt" style="margin-left:auto;font-size:11.5px;opacity:.6">' + gc + '</span></summary>';
      Object.keys(groups[g]).forEach(function (s) {
        var sec = s;                       // s 形如 "1.1"
        var open = S.browse.point && S.browse.point.indexOf(sec + '.') === 0 ? ' open' : '';
        html += '<details class="lv2"' + open + '><summary>' + esc(BANK.sections[sec] || sec) + '</summary>';
        Object.keys(groups[g][s]).forEach(function (p) {
          var n = (cntByPoint[p] && cntByPoint[p][cls]) || 0;
          html += '<div class="leaf' + (S.browse.point === p ? ' on' : '') + (n ? '' : ' zero') + '" data-p="' + p + '">' +
            '<span>' + esc(p + ' ' + pointName(p)) + '</span><span class="cnt">' + n + '</span></div>';
        });
        html += '</details>';
      });
      html += '</details>';
    });
    tree.innerHTML = html;
    $$('.leaf', tree).forEach(function (l) {
      l.onclick = function () {
        S.browse.point = (S.browse.point === l.dataset.p) ? null : l.dataset.p;
        S.browse.shown = 60;
        renderTree(); renderBrowseList();
      };
    });
  }

  function expandTree(all) {
    $$('#pointTree details').forEach(function (d) { d.open = all; });
  }

  function filteredQuestions() {
    var f = S.browse.filter, p = S.browse.point, kw = S.browse.search.trim().toLowerCase();
    var list = (byCls[S.cls] || []).filter(function (q) {
      if (p && q.p !== p) return false;
      if (f === 'single' && q.t !== 's') return false;
      if (f === 'multi' && q.t !== 'm') return false;
      if (f === 'image' && !q.img) return false;
      if (f === 'fav' && !Store.isFav(q.id)) return false;
      var pr = Store.progress(q.id);
      if (f === 'undone' && pr && pr.n) return false;
      if (f === 'wrong' && !(pr && pr.w)) return false;
      if (kw) {
        var hay = (q.q + ' ' + q.o.join(' ') + ' ' + q.id + ' ' + q.no + ' ' + (q.uid || '')).toLowerCase();
        if (hay.indexOf(kw) < 0) return false;
      }
      return true;
    });
    return list;
  }

  function renderBrowseList() {
    fillBrowsePoint();
    var bp = $('#browsePoint'); if (bp && bp.value !== (S.browse.point || '')) bp.value = S.browse.point || '';
    var list = filteredQuestions();
    $('#browseCount').textContent = '共 ' + list.length + ' 题' +
      (S.browse.point ? '（知识点 ' + S.browse.point + ' ' + pointName(S.browse.point) + '）' : '') +
      (S.browse.search ? '（搜索：' + S.browse.search + '）' : '');
    var show = list.slice(0, S.browse.shown);
    var html = '';
    show.forEach(function (q, i) {
      var pr = Store.progress(q.id);
      var st = pr ? (pr.w ? '<span class="st no">曾错</span>' : '<span class="st ok">已对</span>') : '';
      html += '<div class="bq"><div class="bq-head" data-bq="' + q.id + '">' +
        '<span class="idx">' + (i + 1) + '</span>' +
        '<span class="st ' + (q.t === 'm' ? 'm' : 's') + '">' + (q.t === 'm' ? '多选' : '单选') + '</span>' +
        st +
        '<span class="mini">' + esc(q.q) + '</span>' +
        '<button class="fav' + (Store.isFav(q.id) ? ' on' : '') + '" data-fav="' + q.id + '" title="收藏">★</button>' +
        '</div><div class="bq-body" hidden>' +
        '<p class="q-stem">' + esc(q.q) + '</p>' +
        (q.img ? '<img class="q-img" src="' + esc(q.img) + '" alt="附图">' : '') +
        '<div class="opts">' + optionsHTML(q, '', true) + '</div>' +
        explainHTML(q) +
        '</div></div>';
    });
    if (!list.length) {
      var msg = '没有匹配的题目';
      if (S.browse.point) {
        var others = ['A', 'B', 'C'].filter(function (c) { return c !== S.cls && (cntByPoint[S.browse.point] || {})[c]; });
        msg = '知识点「' + S.browse.point + ' ' + pointName(S.browse.point) + '」在 <b>' + RULES[S.cls].name +
          '</b> 中没有题目' + (others.length ? '，该知识点属于 ' + others.join(' / ') + ' 类，切换类别可查看。' : '。');
      } else if (S.browse.search) {
        msg = '没有匹配「' + esc(S.browse.search) + '」的题目';
      }
      html = '<div class="empty">' + msg + '</div>';
    }
    if (show.length < list.length) {
      html += '<div style="text-align:center;padding:14px"><button class="btn" id="moreBtn">加载更多（还有 ' +
        (list.length - show.length) + ' 题）</button></div>';
    }
    $('#browseList').innerHTML = html;

    $$('#browseList .bq-head').forEach(function (h) {
      h.onclick = function (e) {
        if (e.target.dataset.fav) return;
        h.nextElementSibling.hidden = !h.nextElementSibling.hidden;
      };
    });
    $$('#browseList .fav').forEach(function (b) {
      b.onclick = function (e) {
        e.stopPropagation();
        var on = Store.toggleFav(b.dataset.fav);
        b.classList.toggle('on', on);
        toast(on ? '已收藏' : '已取消收藏');
      };
    });
    var mb = $('#moreBtn');
    if (mb) mb.onclick = function () { S.browse.shown += 60; renderBrowseList(); };
  }

  $$('#browseFilters .chip').forEach(function (c) {
    c.onclick = function () {
      $$('#browseFilters .chip').forEach(function (x) { x.classList.remove('active'); });
      c.classList.add('active');
      S.browse.filter = c.dataset.f; S.browse.shown = 60;
      renderBrowseList();
    };
  });
  $('#browseSearch').oninput = function (e) {
    S.browse.search = e.target.value; S.browse.shown = 60; renderBrowseList();
  };

  function fillBrowsePoint() {
    var sel = $('#browsePoint');
    if (sel.dataset.filled) return;
    var codes = Object.keys(BANK.points).sort(function (a, b) {
      var pa = a.split('.').map(Number), pb = b.split('.').map(Number);
      for (var i = 0; i < 3; i++) if (pa[i] !== pb[i]) return pa[i] - pb[i];
      return 0;
    });
    var cur = {};
    codes.forEach(function (c) { cur[c.split('.').slice(0, 2).join('.')] = true; });
    var html = '<option value="">按知识点快速定位…</option>';
    Object.keys(cur).forEach(function (sec) {
      html += '<optgroup label="' + esc(BANK.sections[sec] || sec) + '">';
      codes.filter(function (c) { return c.indexOf(sec + '.') === 0; }).forEach(function (c) {
        html += '<option value="' + c + '">' + esc(c + ' ' + pointName(c)) + '</option>';
      });
      html += '</optgroup>';
    });
    sel.innerHTML = html; sel.dataset.filled = '1';
  }
  $('#browsePoint').onchange = function (e) {
    S.browse.point = e.target.value || null;
    S.browse.shown = 60;
    renderTree(); renderBrowseList();
  };
  $('#expandAll').onclick = function () { $$('#browseList .bq-body').forEach(function (b) { b.hidden = false; }); };
  $('#collapseAll').onclick = function () { $$('#browseList .bq-body').forEach(function (b) { b.hidden = true; }); };
  $('#treeExpand').onclick = function () { expandTree(true); };
  $('#treeCollapse').onclick = function () { expandTree(false); };
  $('#practiceFiltered').onclick = function () {
    var list = filteredQuestions();
    if (!list.length) { toast('没有可练习的题目'); return; }
    switchView('practice');
    startPracticeWith(shuffle(list), '题库筛选（' + list.length + ' 题）');
  };

  /* ============================================================
     统计
     ============================================================ */
  function renderStats() {
    var cls = S.cls;
    var ids = (byCls[cls] || []).map(function (q) { return q.id; });
    var st = Store.stats(ids);
    var exams = Store.exams().filter(function (e) { return e.cls === cls; });
    var passCount = exams.filter(function (e) { return e.pass; }).length;
    var avg = exams.length ? Math.round(exams.reduce(function (a, e) { return a + e.right; }, 0) / exams.length) : 0;
    var cover = ids.length ? Math.round(st.done / ids.length * 100) : 0;

    var html = '<h2 class="panel-title">学习统计</h2>';
    html += '<p class="panel-desc">当前统计范围：' + RULES[cls].name + '（题库 ' + ids.length + ' 题）</p>';

    html += '<div class="stat-cards">' +
      card('题库总量', ids.length, RULES[cls].name + '全部题目') +
      card('已做题数', st.done, '覆盖 ' + cover + '%') +
      card('总正确率', (st.attempts ? Math.round(st.accuracy * 100) : 0) + '%', '按答题次数 ' + st.attempts + ' 次') +
      card('错题数', st.wrongIds.length, '需重点复习') +
      card('模拟考试', exams.length, '次（合格 ' + passCount + '）') +
      card('平均得分', avg, '合格线 ' + RULES[cls].pass + ' 题') +
      '</div>';

    /* 知识点掌握度 */
    var rows = [];
    var codes = Object.keys(BANK.points).sort();
    codes.forEach(function (p) {
      var list = (byPoint[p] || []).filter(function (q) { return q.cls.indexOf(cls) >= 0; });
      if (!list.length) return;
      var s = Store.stats(list.map(function (q) { return q.id; }));
      rows.push({ p: p, total: list.length, done: s.done, att: s.attempts, right: s.correct, acc: s.accuracy });
    });
    rows.sort(function (a, b) { return a.acc - b.acc; });

    html += '<div class="sec-title">知识点掌握度（正确率低的排在前面）</div>';
    html += '<div class="card tbl-wrap"><table class="tbl"><thead><tr><th>知识点</th><th>题数</th><th>已做</th><th>正确率</th><th></th></tr></thead><tbody>';
    rows.forEach(function (r) {
      var pc = r.att ? Math.round(r.acc * 100) : 0;
      var cls2 = !r.att ? '' : (pc >= 80 ? 'ok' : (pc >= 60 ? 'warn' : 'bad'));
      html += '<tr><td>' + esc(pointShort(r.p)) + '</td>' +
        '<td>' + r.total + '</td><td>' + r.done + '</td>' +
        '<td style="min-width:140px"><div style="display:flex;align-items:center;gap:9px"><div class="bar" style="flex:1"><i class="' + cls2 + '" style="width:' + pc + '%"></i></div><span style="font-family:var(--code);font-size:12px">' + (r.att ? pc + '%' : '—') + '</span></div></td>' +
        '<td><button class="btn btn-sm" data-prac="' + r.p + '">练这节</button></td></tr>';
    });
    html += '</tbody></table></div>';

    /* 考试记录 */
    html += '<div class="sec-title">模拟考试记录</div>';
    if (!exams.length) {
      html += '<div class="card empty">还没有考试记录，先去「模拟考试」做一套吧。</div>';
    } else {
      html += '<div class="card tbl-wrap"><table class="tbl"><thead><tr><th>时间</th><th>类别</th><th>得分</th><th>正确率</th><th>用时</th><th>结果</th><th></th></tr></thead><tbody>';
      exams.forEach(function (e) {
        html += '<tr><td>' + fmtDate(e.ts) + '</td><td>' + RULES[e.cls].name + '</td>' +
          '<td>' + e.right + '/' + e.total + '</td>' +
          '<td>' + Math.round(e.right / e.total * 100) + '%</td>' +
          '<td>' + fmtTime(e.sec) + '</td>' +
          '<td><span class="badge ' + (e.pass ? 'pass' : 'fail') + '">' + (e.pass ? '合格' : '不合格') + '</span></td>' +
          '<td><button class="btn btn-sm" data-rev-exam="' + e.id + '">错题重练</button></td></tr>';
      });
      html += '</tbody></table></div>';
    }

    /* 错题本 */
    html += '<div class="sec-title">错题本（' + st.wrongIds.length + ' 题）</div>';
    if (!st.wrongIds.length) {
      html += '<div class="card empty">暂无错题 —— 要么还没做，要么都做对了。</div>';
    } else {
      html += '<div class="card"><div class="row-btns" style="margin-bottom:14px">' +
        '<button class="btn btn-primary" id="practiceWrongAll">全部重练（' + st.wrongIds.length + ' 题）</button>' +
        '<button class="btn btn-sm" id="clearWrong">清空错题标记</button></div>' +
        '<div class="tbl-wrap"><table class="tbl"><thead><tr><th>编号</th><th>题干</th><th>知识点</th><th>答对/答题</th><th></th></tr></thead><tbody>';
      st.wrongIds.slice(0, 60).forEach(function (id) {
        var q = byId[id]; if (!q) return;
        var pr = Store.progress(id);
        html += '<tr><td style="font-family:var(--code);font-size:12px">' + esc(q.no || q.id) + '</td>' +
          '<td style="max-width:420px">' + esc(q.q.slice(0, 60)) + (q.q.length > 60 ? '…' : '') + '</td>' +
          '<td style="font-size:12px;color:var(--ink2)">' + esc(pointName(q.p)) + '</td>' +
          '<td style="font-family:var(--code)">' + pr.c + '/' + pr.n + '</td>' +
          '<td><button class="btn btn-sm" data-prac-one="' + id + '">看题</button></td></tr>';
      });
      html += '</tbody></table></div></div>';
    }

    /* 数据管理 */
    html += '<div class="sec-title">数据管理</div><div class="card">' +
      '<p style="margin:0 0 14px;color:var(--ink2);font-size:13.5px">所有数据只保存在这台设备的浏览器里（localStorage），不会上传。换个浏览器或清了缓存就会丢，建议定期导出备份。</p>' +
      '<div class="row-btns">' +
      '<button class="btn" id="exportBtn">导出备份（JSON）</button>' +
      '<button class="btn" id="importBtn">导入备份</button>' +
      '<button class="btn btn-danger" id="resetBtn">清空全部记录</button>' +
      '<input type="file" id="importFile" accept="application/json,.json" hidden>' +
      '</div></div>';

    $('#statsBody').innerHTML = html;

    /* 事件 */
    $$('#statsBody [data-prac]').forEach(function (b) {
      b.onclick = function () {
        var p = b.dataset.prac;
        var list = (byPoint[p] || []).filter(function (q) { return q.cls.indexOf(S.cls) >= 0; });
        switchView('practice');
        startPracticeWith(shuffle(list), '知识点 ' + p + ' ' + pointName(p));
      };
    });
    $$('#statsBody [data-prac-one]').forEach(function (b) {
      b.onclick = function () {
        var q = byId[b.dataset.pracOne];
        modal(q.no + '　' + pointName(q.p),
          '<p class="q-stem">' + esc(q.q) + '</p>' +
          (q.img ? '<img class="q-img" src="' + esc(q.img) + '">' : '') +
          '<div class="opts">' + optionsHTML(q, '', true) + '</div>' + explainHTML(q),
          [{ text: '关闭', primary: true }]);
      };
    });
    $$('#statsBody [data-rev-exam]').forEach(function (b) {
      b.onclick = function () {
        var rec = Store.exams().filter(function (e) { return e.id === b.dataset.revExam; })[0];
        if (!rec) return;
        var list = (rec.wrong || []).map(function (id) { return byId[id]; }).filter(Boolean);
        if (!list.length) { toast('这套没有错题'); return; }
        switchView('practice');
        startPracticeWith(shuffle(list), '考试错题重练');
      };
    });
    var pwa = $('#practiceWrongAll');
    if (pwa) pwa.onclick = function () {
      var list = st.wrongIds.map(function (id) { return byId[id]; }).filter(Boolean);
      switchView('practice');
      startPracticeWith(shuffle(list), '错题本重练');
    };
    var cw = $('#clearWrong');
    if (cw) cw.onclick = function () {
      modal('确认', '将把当前类别的错题标记全部清除（答题次数记录保留），继续？', [
        { text: '取消' },
        { text: '确定清除', danger: true, onClick: function () {
          var m = Store.progressMap();
          st.wrongIds.forEach(function (id) { if (m[id]) m[id].w = 0; });
          Store.save();
          renderStats(); toast('已清除错题标记');
        } }
      ]);
    };
    $('#exportBtn').onclick = function () {
      var blob = new Blob([Store.exportJSON()], { type: 'application/json' });
      var a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = 'ham-exam-data-' + new Date().toISOString().slice(0, 10) + '.json';
      a.click(); setTimeout(function () { URL.revokeObjectURL(a.href); }, 1000);
      toast('已导出');
    };
    $('#importBtn').onclick = function () { $('#importFile').click(); };
    $('#importFile').onchange = function (e) {
      var f = e.target.files[0]; if (!f) return;
      var fr = new FileReader();
      fr.onload = function () {
        try { Store.importJSON(fr.result); toast('导入成功'); renderStats(); }
        catch (err) { toast('导入失败：' + err.message); }
      };
      fr.readAsText(f);
      e.target.value = '';
    };
    $('#resetBtn').onclick = function () {
      modal('危险操作', '将删除全部答题记录、考试记录、错题本和收藏，且不可恢复。建议先导出备份。<br><br>确定要清空吗？', [
        { text: '取消' },
        { text: '确定清空', danger: true, onClick: function () { Store.resetAll(); toast('已清空'); renderStats(); } }
      ]);
    };
  }

  function card(k, v, d) {
    return '<div class="stat-card"><div class="k">' + esc(k) + '</div><div class="v">' + esc(v) + '</div><div class="d">' + esc(d) + '</div></div>';
  }

  /* ============================================================
     考试事件
     ============================================================ */
  $('#startExamBtn').onclick = startExam;
  $('#toggleCardBtn').onclick = function () {
    var c = $('#answerCard'); c.hidden = !c.hidden;
    if (!c.hidden) drawAnswerCard('#answerCard', 'exam');
  };
  $('#submitExamBtn').onclick = function () {
    var ex = S.exam;
    var answered = Object.keys(ex.ans).length;
    var left = ex.ids.length - answered;
    modal('确认交卷', '已作答 <b>' + answered + '</b> / ' + ex.ids.length + ' 题' +
      (left ? '，还有 <b>' + left + '</b> 题未作答（未答按错计）' : '') +
      '。<br>剩余时间 ' + fmtTime(Math.max(0, Math.round((ex.deadline - Date.now()) / 1000))) + '。<br><br>确定交卷吗？', [
      { text: '再想想' },
      { text: '确定交卷', primary: true, onClick: function () { submitExam(false); } }
    ]);
  };

  /* ============================================================
     键盘快捷键
     ============================================================ */
  document.addEventListener('keydown', function (e) {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT' || e.target.tagName === 'TEXTAREA') return;
    if (!$('#modalMask').hidden) {
      if (e.key === 'Escape') closeModal();
      return;
    }
    var inExam = S.view === 'exam' && S.exam;
    var inPrac = S.view === 'practice' && S.practice;
    if (!inExam && !inPrac) return;

    var idx = inExam ? S.exam.idx : S.practice.idx;
    var ids = inExam ? S.exam.ids : S.practice.ids;
    var id = ids[idx];
    var q = byId[id];

    if (e.key >= '1' && e.key <= '4') {
      var L = LETTERS[+e.key - 1];
      if (inExam) pickExamOption(L); else pickPracticeOption(L);
      e.preventDefault();
    } else if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
      if (inExam && S.exam.idx < ids.length - 1) { S.exam.idx++; saveExamDraft(); drawExamQuestion(); drawAnswerCard('#answerCard', 'exam'); }
      else if (inPrac && S.practice.idx < ids.length - 1) { S.practice.idx++; savePracticeDraft(); drawPracticeQuestion(); drawAnswerCard('#practiceCard', 'practice'); }
      e.preventDefault();
    } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
      if (inExam && S.exam.idx > 0) { S.exam.idx--; saveExamDraft(); drawExamQuestion(); drawAnswerCard('#answerCard', 'exam'); }
      else if (inPrac && S.practice.idx > 0) { S.practice.idx--; savePracticeDraft(); drawPracticeQuestion(); drawAnswerCard('#practiceCard', 'practice'); }
      e.preventDefault();
    } else if (e.key === 'Enter') {
      if (inPrac && !S.practice.ans[id]) { /* noop */ }
      else if (inPrac && S.practice.ans[id] && !S.practice.ans[id].submitted && q.t === 'm') { submitPracticeAnswer(); }
      else if (inPrac && S.practice.idx < ids.length - 1) { S.practice.idx++; savePracticeDraft(); drawPracticeQuestion(); drawAnswerCard('#practiceCard', 'practice'); }
      else if (inExam && S.exam.idx < ids.length - 1) { S.exam.idx++; saveExamDraft(); drawExamQuestion(); drawAnswerCard('#answerCard', 'exam'); }
      e.preventDefault();
    } else if (e.key === 'f' || e.key === 'F') {
      if (inExam) { if (S.exam.flags[id]) delete S.exam.flags[id]; else S.exam.flags[id] = 1; saveExamDraft(); drawExamQuestion(); }
    }
  });

  /* ============================================================
     启动
     ============================================================ */
  function boot() {
    applyTheme(Store.settings().theme || 'light');
    buildClsSwitch();
    $('#bankNote').textContent = BANK.meta.bank + '　·　' + BANK.meta.note;
    renderExamSetup();
    renderPracticeSetup();
    fillPointSelect();
    switchView('exam');
  }
  boot();
})();
