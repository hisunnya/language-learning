/* 总后台（/backends/）的页面逻辑。
 *
 * 数据全部来自同一个后端：
 *   GET /word-puzzle/api/auth/me       当前是谁
 *   GET /word-puzzle/api/backoffice    模块概况 + 名下学生 + 最近记录（老师只看自己名下的人）
 * 页面本身是静态的：没有登录也拿得到 HTML，但接口要登录，所以数据不会泄露。
 */
(function () {
  'use strict';

  var API = '/word-puzzle/api';

  var COPY = {
    zh: {
      roleAdmin: '超级管理员', roleTeacher: '老师', roleStudent: '学生',
      staffOnly: '这个页面只给老师和超级管理员。请换一个老师账号登录。',
      scopeNote: '你看到的是你有权管理的范围：老师只有自己名下的学生，超级管理员是全部。',
      moduleNote: '「成绩条数」是这个模块存下来的练习小结条数，只统计你有权看到的学生。',
      studentNote: '这里列出你名下的学生；超级管理员看到全部未删除的学生。',
      countRecords: '条记录', countStudents: '名学生', lastActive: '最近活跃', never: '还没有记录',
      open: '打开',
      noRecords: '还没有记录。',
      noStudents: '还没有学生。',
      allModules: '全部模块',
      colModule: '模块', colWho: '学生', colKind: '类型', colTime: '时间', colDetail: '内容',
      guest: '未登录访客',
      signOut: '退出登录',
      failed: '读不到数据，请检查网络后重试。',
      foot: '总后台是老师用的工具，不在主页上链接（需要登录的页面不放公开入口）。数据范围由后端的 server/tenancy.py 决定。',
      links: [
        { path: '/word-puzzle/admin.html', zh: '账号管理', en: 'Accounts' },
        { path: '/word-puzzle/tenants.html', zh: '老师与分配', en: 'Teachers and sharing' },
        { path: '/word-puzzle/visits.html', zh: '访问记录', en: 'Access log' },
        { path: '/word-puzzle/leaderboard.html', zh: '排行榜', en: 'Leaderboard' },
        { path: '/word-puzzle/stats.html', zh: '我的成绩', en: 'My scores' }
      ]
    },
    en: {
      roleAdmin: 'Super administrator', roleTeacher: 'Teacher', roleStudent: 'Student',
      staffOnly: 'This page is for teachers and the super administrator. Please sign in with a teacher account.',
      scopeNote: 'You only see what you are allowed to manage: a teacher sees their own students, the super administrator sees everyone.',
      moduleNote: '“Records” counts the practice summaries this module stored, for the students you may see.',
      studentNote: 'Your students are listed here; the super administrator sees every account that is not deleted.',
      countRecords: 'records', countStudents: 'students', lastActive: 'Last activity', never: 'No records yet',
      open: 'Open',
      noRecords: 'No records yet.',
      noStudents: 'No students yet.',
      allModules: 'All modules',
      colModule: 'Module', colWho: 'Student', colKind: 'Kind', colTime: 'Time', colDetail: 'Detail',
      guest: 'Guest',
      signOut: 'Sign out',
      failed: 'Could not load the data. Check your connection and try again.',
      foot: 'The back office is a staff tool, so it is not linked from the homepage (pages that need a login stay out of the public entrance). Who sees what is decided by server/tenancy.py on the backend.',
      links: [
        { path: '/word-puzzle/admin.html', zh: '账号管理', en: 'Accounts' },
        { path: '/word-puzzle/tenants.html', zh: '老师与分配', en: 'Teachers and sharing' },
        { path: '/word-puzzle/visits.html', zh: '访问记录', en: 'Access log' },
        { path: '/word-puzzle/leaderboard.html', zh: '排行榜', en: 'Leaderboard' },
        { path: '/word-puzzle/stats.html', zh: '我的成绩', en: 'My scores' }
      ]
    }
  };

  var state = { data: null, subject: '', me: null };

  function $(id) { return document.getElementById(id); }
  function lang() { return document.documentElement.lang.indexOf('en') === 0 ? 'en' : 'zh'; }
  function copy() { return COPY[lang()]; }

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = text;
    return node;
  }

  function formatTime(stamp) {
    if (!stamp) return '';
    var d = new Date(Number(stamp) * 1000);
    if (isNaN(d.getTime())) return '';
    function pad(n) { return (n < 10 ? '0' : '') + n; }
    return (d.getMonth() + 1) + '-' + pad(d.getDate()) + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes());
  }

  function payloadText(payload) {
    if (!payload || typeof payload !== 'object') return '';
    var keys = Object.keys(payload);
    if (!keys.length) return '';
    return keys.map(function (key) {
      var value = payload[key];
      if (value && typeof value === 'object') value = JSON.stringify(value);
      return key + ': ' + value;
    }).join(' · ');
  }

  function request(path, options) {
    var opts = options || {};
    opts.credentials = 'same-origin';
    opts.headers = Object.assign({ 'Content-Type': 'application/json' }, opts.headers || {});
    return fetch(API + path, opts).then(function (response) {
      return response.json().catch(function () { return {}; }).then(function (body) {
        return { status: response.status, body: body };
      });
    });
  }

  function showGate(message) {
    $('main').hidden = true;
    $('gate').hidden = false;
    $('gateMsg').textContent = message || '';
  }

  function renderModuleCards() {
    var box = $('moduleCards');
    box.replaceChildren();
    var text = copy();
    state.data.modules.forEach(function (module) {
      var card = el('article', 'module-card' + (module.enabled ? '' : ' is-off'));
      card.append(el('h3', null, lang() === 'en' ? module.en : module.zh));
      card.append(el('p', 'module-en', module.en));
      var stats = el('div', 'module-stats');
      [[String(module.records), text.countRecords], [String(module.students), text.countStudents]].forEach(function (pair) {
        var cell = el('div');
        cell.append(el('b', null, pair[0]));
        cell.append(el('span', null, pair[1]));
        stats.append(cell);
      });
      card.append(stats);
      card.append(el('p', 'module-last', module.last_at
        ? text.lastActive + ': ' + formatTime(module.last_at)
        : text.never));
      var link = el('a', 'module-open', text.open + ' →');
      link.href = module.path;
      card.append(link);
      box.append(card);
    });
  }

  function renderRecords() {
    var box = $('recordTable');
    box.replaceChildren();
    var text = copy();
    var records = state.data.recent || [];
    if (!records.length) {
      box.append(el('p', 'empty-note', text.noRecords));
      return;
    }
    var table = el('table', 'data-table');
    var head = el('thead');
    var headRow = el('tr');
    [text.colModule, text.colWho, text.colKind, text.colTime, text.colDetail].forEach(function (label) {
      headRow.append(el('th', null, label));
    });
    head.append(headRow);
    table.append(head);
    var body = el('tbody');
    records.forEach(function (record) {
      var row = el('tr');
      var module = state.data.modules.filter(function (m) { return m.id === record.subject; })[0];
      row.append(el('td', null, module ? (lang() === 'en' ? module.en : module.zh) : record.subject));
      var who = record.name || record.student_no || record.device || text.guest;
      if (record.class_name) who += '（' + record.class_name + '）';
      row.append(el('td', null, who));
      row.append(el('td', null, record.kind || '—'));
      row.append(el('td', 'num', formatTime(record.created_at)));
      row.append(el('td', 'payload-cell', payloadText(record.payload) || '—'));
      body.append(row);
    });
    table.append(body);
    box.append(table);
  }

  function renderStudents() {
    var box = $('studentTable');
    box.replaceChildren();
    var students = state.data.students || [];
    if (!students.length) {
      box.append(el('p', 'empty-note', copy().noStudents));
      return;
    }
    var table = el('table', 'data-table');
    var body = el('tbody');
    students.forEach(function (student) {
      var row = el('tr');
      row.append(el('td', null, student.name || '—'));
      row.append(el('td', 'num', student.student_no || '—'));
      row.append(el('td', null, student.class_name || '—'));
      row.append(el('td', 'num', formatTime(student.last_login_at) || '—'));
      body.append(row);
    });
    table.append(body);
    box.append(table);
  }

  function renderLinks() {
    var box = $('linkList');
    box.replaceChildren();
    var text = copy();
    text.links.forEach(function (item) {
      var link = el('a');
      link.href = item.path;
      link.append(el('span', null, lang() === 'en' ? item.en : item.zh));
      link.append(el('span', 'arrow', '→'));
      box.append(link);
    });
  }

  function renderFilter() {
    var select = $('subjectFilter');
    var text = copy();
    var current = state.subject;
    select.replaceChildren();
    var all = el('option', null, text.allModules);
    all.value = '';
    select.append(all);
    state.data.modules.forEach(function (module) {
      var option = el('option', null, lang() === 'en' ? module.en : module.zh);
      option.value = module.id;
      select.append(option);
    });
    select.value = current;
  }

  function render() {
    var text = copy();
    var me = state.me || {};
    $('scopeNote').textContent = text.scopeNote;
    $('moduleNote').textContent = text.moduleNote;
    $('studentNote').textContent = text.studentNote;
    $('footNote').textContent = text.foot;
    var role = me.role === 'admin' ? text.roleAdmin : me.role === 'teacher' ? text.roleTeacher : text.roleStudent;
    var chip = $('userChip');
    chip.replaceChildren();
    chip.append(el('span', null, (me.name || me.student_no || '') + ' · ' + role));
    renderModuleCards();
    renderFilter();
    renderRecords();
    renderStudents();
    renderLinks();
    $('gate').hidden = true;
    $('main').hidden = false;
  }

  function load() {
    return request('/backoffice?limit=80').then(function (result) {
      if (result.status === 401) { showGate(''); return; }
      if (result.status === 403) { showGate(copy().staffOnly); return; }
      if (!result.body || !result.body.ok) { showGate(copy().failed); return; }
      state.data = result.body;
      state.me = result.body.me;
      render();
    });
  }

  function signIn(event) {
    event.preventDefault();
    var button = $('gateSubmit');
    var message = $('gateMsg');
    message.textContent = '';
    button.disabled = true;
    request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ student_no: $('gateNo').value.trim(), password: $('gatePw').value })
    }).then(function (result) {
      button.disabled = false;
      if (result.status !== 200) {
        message.textContent = (result.body && (result.body.message || result.body.error)) || copy().failed;
        return;
      }
      $('gatePw').value = '';
      if (!result.body.user || (result.body.user.role !== 'admin' && result.body.user.role !== 'teacher')) {
        showGate(copy().staffOnly);
        request('/auth/logout', { method: 'POST', body: '{}' });
        return;
      }
      load();
    });
  }

  function signOut() {
    request('/auth/logout', { method: 'POST', body: '{}' }).then(function () {
      state.data = null;
      state.me = null;
      showGate('');
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    $('gateForm').addEventListener('submit', signIn);
    $('logoutBtn').addEventListener('click', signOut);
    $('refreshBtn').addEventListener('click', function () { load(); });
    $('subjectFilter').addEventListener('change', function (event) {
      state.subject = event.target.value;
      request('/backoffice?limit=80' + (state.subject ? '&subject=' + encodeURIComponent(state.subject) : ''))
        .then(function (result) {
          if (result.body && result.body.ok) { state.data = result.body; renderRecords(); }
        });
    });
    window.addEventListener('portal-lang-change', function () {
      if (state.data) render();
    });
    request('/auth/me').then(function (result) {
      if (result.status !== 200 || !result.body || !result.body.user) { showGate(''); return; }
      if (result.body.user.role !== 'admin' && result.body.user.role !== 'teacher') {
        showGate(copy().staffOnly);
        return;
      }
      load();
    });
  });
})();
