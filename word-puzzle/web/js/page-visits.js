/* ============================================================
   page-visits.js —— 访问记录（只有老师能看）
   ------------------------------------------------------------
   「访问」标签：一行 = 一次访问（同一个浏览器标签页里同一个账号先后打开的页面），点开看每一页、用的题库和停留时间。
   「页面浏览」标签：一行 = 打开一次页面（不按访问合并），找「谁看了读音练习」「谁用了哪个题库」用它。
   「登录记录」标签：每次登录（成功和失败）一行。
   筛选：对象、班级、搜索、日期；页面、题库、设备、从哪里打开（微信等）、系统、停留至少几秒。选项来自库里真有的值。
   时间在库里是 UTC 秒数，这里由浏览器换成本地时间。
   ============================================================ */
(function () {
  'use strict';

  function esc(s) { return API.esc(s); }
  function t(key, params) { return WPI18N.t(key, params); }
  function $(id) { return document.getElementById(id); }

  var PAGE = 100;
  var tab = 'visits';
  var state = { visits: { rows: [], total: 0, summary: null }, pages: { rows: [], total: 0, summary: null }, logins: { rows: [], total: 0, summary: null } };
  var opts = { pages: [], banks: [], os: [], apps: [] };      /* 筛选下拉框的选项（/api/admin/visits/options） */
  var ENDPOINT = { visits: '/api/admin/visits?', pages: '/api/admin/pageviews?', logins: '/api/admin/logins?' };
  var F = { who: '', class_name: '', page: '', bank: '', device: '', app: '', os: '', stay: '', failed: '' };   /* 表头下面一行的筛选值，三个标签共用 */
  var open = {};                 /* sid|uid -> true / 明细 */
  var pagesCache = {};

  function stamp(sec) { return sec ? API.fmtTime(sec * 1000) : ''; }
  function dur(sec) {
    sec = Math.max(0, Math.round(sec || 0));
    if (sec < 60) return t('visits_sec', { n: sec });
    if (sec < 3600) return t('visits_min', { m: Math.floor(sec / 60), s: sec % 60 });
    return t('visits_hour', { h: Math.floor(sec / 3600), m: Math.floor(sec % 3600 / 60) });
  }
  function deviceText(r) {
    var kind = { mobile: 'visits_dtMobile', tablet: 'visits_dtTablet', desktop: 'visits_dtDesktop', bot: 'visits_dtBot' }[r.device_type];
    return [kind ? t(kind) : '', r.device_model].filter(Boolean).join(' · ') + (r.in_app ? ' · ' + r.in_app : '');
  }
  function pageLabel(file) {
    var hit = opts.pages.filter(function (x) { return x.page === file; })[0];
    return hit ? (WPI18N.lang() === 'en' ? hit.en : hit.zh) : file;
  }
  function bankText(title, id) { return title || (id ? t('visits_bankGone', { id: id }) : ''); }
  function osText(r) { return [r.os, r.os_version].filter(Boolean).join(' '); }
  function browserText(r) { return [r.browser, (r.browser_version || '').split('.')[0]].filter(Boolean).join(' '); }
  function ipText(r) {
    if (!r.ips || r.ips.length < 2) return r.ip || t('visits_ipUnknown');
    return t('visits_ipMany', { ip: r.ip, n: r.ips.length });
  }
  function nameCell(r) { return r.role === 'admin' ? esc(r.name) + ' (' + esc(t('visits_roleAdmin')) + ')' : esc(r.name || (r.user_id ? '' : t('visits_anon'))); }

  function query(offset) {
    var p = ['limit=' + PAGE, 'offset=' + offset], v;
    if (v = F.who) p.push('role=' + encodeURIComponent(v));
    if (v = F.class_name.trim()) p.push('class_name=' + encodeURIComponent(v));
    if (v = $('fSearch').value.trim()) p.push('q=' + encodeURIComponent(v));
    if (tab !== 'logins') {
      if (v = F.page) p.push('page=' + encodeURIComponent(v));
      if (v = F.bank.trim()) p.push('bank=' + encodeURIComponent(v));
      if ((v = parseInt(F.stay, 10)) > 0) p.push('min_seconds=' + v);
    }
    if (v = F.device) p.push('device=' + encodeURIComponent(v));
    if (v = F.app) p.push('app=' + encodeURIComponent(v));
    if (v = F.os) p.push('os=' + encodeURIComponent(v));
    if (v = $('fSince').value) p.push('since=' + Math.floor(new Date(v + 'T00:00:00').getTime() / 1000));
    if (v = $('fUntil').value) p.push('until=' + (Math.floor(new Date(v + 'T00:00:00').getTime() / 1000) + 86400));
    if (tab === 'logins' && F.failed === '1') p.push('failed=1');
    return p.join('&');
  }

  function exportLink() {
    var p = query(0).split('&').filter(function (x) { return !/^(limit|offset|failed)=/.test(x); });
    $('btnExport').href = API.path('/api/admin/export/' + (tab === 'logins' ? 'logins' : 'page-views') + '.csv' + (p.length ? '?' + p.join('&') : ''));
  }

  function load(more) {
    var s = state[tab];
    var offset = more ? s.rows.length : 0;
    var which = tab;
    $('countHint').textContent = t('visits_loading');
    return API.get(ENDPOINT[tab] + query(offset)).then(function (res) {
      if (which !== tab) return;                          /* 等的时候已经切到别的标签了：这份结果不要 */
      var rows = { visits: res.sessions, pages: res.pageviews, logins: res.logins }[tab];
      s.rows = more ? s.rows.concat(rows) : rows;
      s.total = res.total;
      s.summary = res.summary || null;
      render();
    }).catch(function () { $('countHint').textContent = t('visits_fail'); });
  }

  var tip = null;
  function showTip(el) {
    if (el.scrollWidth <= el.clientWidth + 1) return;
    hideTip();
    tip = document.createElement('div');
    tip.className = 'clip-tip';
    tip.textContent = el.textContent;
    document.body.appendChild(tip);
    var r = el.getBoundingClientRect();
    var left = Math.max(8, Math.min(r.left, window.innerWidth - tip.offsetWidth - 8));
    var top = r.bottom + 6;
    if (top + tip.offsetHeight > window.innerHeight - 8) top = Math.max(8, r.top - tip.offsetHeight - 6);
    tip.style.left = left + 'px';
    tip.style.top = top + 'px';
  }
  function hideTip() { if (tip) { tip.remove(); tip = null; } }

  function key(r) { return r.sid + '|' + (r.user_id || 0); }

  function pagesHtml(k) {
    var d = pagesCache[k];
    if (!Array.isArray(d)) return '<div class="empty">' + esc(t(d === 'error' ? 'visits_fail' : 'visits_loading')) + '</div>';
    return '<div class="scroll"><table class="detail-table"><thead><tr>' + ['visits_dTime', 'visits_dPath', 'visits_dTitle', 'visits_dBank', 'visits_dStay', 'visits_dFrom']
      .map(function (x) { return '<th>' + esc(t(x)) + '</th>'; }).join('') + '</tr></thead><tbody>' +
      d.map(function (p) {
        var extra = { query: p.query, ip: p.ip, forwarded: p.forwarded, client: p.client_info, user_agent: p.user_agent, accept_language: p.accept_language };
        return '<tr><td>' + esc(stamp(p.started_at)) + '</td><td>' + esc(p.path) + '</td><td>' + esc(p.title) + '</td><td>' + esc(bankText(p.bank_title, p.bank_id)) + '</td><td>' + esc(dur(p.active_seconds)) +
          '</td><td>' + esc(p.referrer) + '</td></tr>' +
          '<tr class="raw-row"><td colspan="6"><details><summary>' + esc(t('visits_dMore')) + '</summary><pre>' + esc(JSON.stringify(extra, null, 1)) + '</pre></details></td></tr>';
      }).join('') + '</tbody></table></div>';
  }

  function renderVisits() {
    var body = document.querySelector('#visitTable tbody');
    var rows = state.visits.rows;
    if (!rows.length) { body.innerHTML = '<tr><td colspan="13" class="empty">' + esc(t('visits_empty')) + '</td></tr>'; return; }
    body.innerHTML = rows.map(function (r) {
      var k = key(r), isOpen = !!open[k];
      return '<tr class="sum-row" tabindex="0" role="button" aria-expanded="' + isOpen + '" data-key="' + esc(k) + '" aria-label="' + esc(t(isOpen ? 'visits_collapse' : 'visits_expand')) + '">' +
        '<td><span class="caret">▸</span></td><td>' + esc(stamp(r.first_at)) + '</td><td>' + esc(r.class_name) + '</td><td>' + esc(r.student_no) + '</td><td>' + nameCell(r) + '</td>' +
        '<td>' + esc(ipText(r)) + '</td><td>' + esc(deviceText(r)) + '</td><td>' + esc(osText(r)) + '</td><td>' + esc(browserText(r)) + '</td>' +
        '<td>' + esc((r.pages_seen || []).map(pageLabel).join('、')) + '</td><td>' + esc((r.banks || []).join('、')) + '</td>' +
        '<td class="num">' + r.pages + '</td><td>' + esc(dur(r.active_seconds)) + '</td></tr>' +
        (isOpen ? '<tr class="detail-row"><td colspan="13">' + pagesHtml(k) + '</td></tr>' : '');
    }).join('');
  }

  function renderPages() {
    var body = document.querySelector('#pageTable tbody');
    var rows = state.pages.rows;
    if (!rows.length) { body.innerHTML = '<tr><td colspan="11" class="empty">' + esc(t('visits_empty')) + '</td></tr>'; return; }
    body.innerHTML = rows.map(function (r) {
      return '<tr><td>' + esc(stamp(r.started_at)) + '</td><td>' + esc(r.class_name) + '</td><td>' + esc(r.student_no) + '</td><td>' + nameCell(r) + '</td>' +
        '<td>' + esc(pageLabel(r.page)) + '</td><td>' + esc(bankText(r.bank_title, r.bank_id)) + '</td>' +
        '<td>' + esc(dur(r.active_seconds)) + '</td><td>' + esc(deviceText(r)) + '</td><td>' + esc(osText(r)) + '</td><td>' + esc(browserText(r)) + '</td>' +
        '<td>' + esc(r.ip || t('visits_ipUnknown')) + '</td></tr>';
    }).join('');
  }

  function codeText(r) {
    if (r.success) return '';
    return { invalid_credentials: t('visits_codeBad'), rate_limited: t('visits_codeLimit'), missing: t('visits_codeMissing') }[r.code] || r.code;
  }
  function renderLogins() {
    var body = document.querySelector('#loginTable tbody');
    var rows = state.logins.rows;
    if (!rows.length) { body.innerHTML = '<tr><td colspan="10" class="empty">' + esc(t('visits_empty')) + '</td></tr>'; return; }
    body.innerHTML = rows.map(function (r) {
      return '<tr><td>' + esc(stamp(r.ts)) + '</td><td><span class="pill ' + (r.success ? 'good' : 'bad') + '">' + esc(t(r.success ? 'visits_resOk' : 'visits_resFail')) + '</span></td>' +
        '<td>' + esc(r.student_no) + '</td><td>' + esc(r.name) + '</td><td>' + esc(r.class_name) + '</td><td>' + esc(r.ip || t('visits_ipUnknown')) + '</td>' +
        '<td>' + esc(deviceText(r)) + '</td><td>' + esc(osText(r)) + '</td><td>' + esc(browserText(r)) + '</td><td>' + esc(codeText(r)) + '</td></tr>';
    }).join('');
  }

  /* 小计：整个筛选结果（不只是已显示的 100 条）的人数、IP 数、停留合计 */
  function summaryText(s) {
    var m = s.summary;
    if (!m) return '';
    if (tab === 'logins') return [t('visits_sumLogins', { ok: m.ok, failed: m.failed }), t('visits_sumLoginPeople', { n: m.people }), t('visits_sumIps', { n: m.ips })].join(' · ');
    var parts = [t('visits_sumViews', { views: m.views }), t('visits_sumPeople', { n: m.people })];
    if (m.anonymous) parts.push(t('visits_sumAnon', { n: m.anonymous }));
    parts.push(t('visits_sumIps', { n: m.ips }), t('visits_sumTime', { t: dur(m.seconds) }));
    return parts.join(' · ');
  }

  function render() {
    var s = state[tab];
    $('visitTable').hidden = tab !== 'visits';
    $('pageTable').hidden = tab !== 'pages';
    $('loginTable').hidden = tab !== 'logins';
    $('btnMore').hidden = s.rows.length >= s.total;
    $('countHint').textContent = t('visits_count', { n: s.total, shown: s.rows.length });
    $('sumLine').textContent = summaryText(s);
    var local = s.rows.length > 0 && s.rows.slice(0, 20).every(function (r) { return r.ip === '127.0.0.1' || r.ip === '::1'; });
    $('ipWarn').hidden = !local;
    $('ipWarn').textContent = local ? t('visits_proxyOnly') : '';
    ({ visits: renderVisits, pages: renderPages, logins: renderLogins })[tab]();
    exportLink();
  }

  function toggle(k) {
    var row = state.visits.rows.filter(function (r) { return key(r) === k; })[0];
    if (!row) return;
    if (open[k]) { delete open[k]; render(); return; }
    open[k] = true;
    if (!Array.isArray(pagesCache[k])) {
      API.get('/api/admin/visits/pages?sid=' + encodeURIComponent(row.sid) + (row.user_id ? '&user_id=' + row.user_id : ''))
        .then(function (res) { pagesCache[k] = res.pages || []; }).catch(function () { pagesCache[k] = 'error'; }).then(render);
    }
    render();
  }

  function setTab(name) {
    tab = name;
    [['tabVisits', 'visits'], ['tabPages', 'pages'], ['tabLogins', 'logins']].forEach(function (x) {
      $(x[0]).classList.toggle('active', name === x[1]);
      $(x[0]).setAttribute('aria-selected', String(name === x[1]));
    });
    render();                                            /* 先把筛选条件里这个标签用不到的收起来 */
    load(false);
  }

  /* ---------- 筛选下拉框 ---------- */

  function fill(field, first, items) {
    Array.prototype.forEach.call(document.querySelectorAll('select[data-f="' + field + '"]'), function (box) {
      box.innerHTML = '<option value="">' + esc(first) + '</option>' + items.map(function (x) {
        return '<option value="' + esc(x[0]) + '">' + esc(x[1]) + '</option>';
      }).join('');
      box.value = F[field];
    });
  }

  function fillOptions() {
    fill('page', t('visits_fAll'), opts.pages.map(function (p) { return [p.page, (WPI18N.lang() === 'en' ? p.en : p.zh) + ' (' + p.n + ')']; }));
    fill('device', t('visits_fAll'), [['mobile', t('visits_dtMobile')], ['tablet', t('visits_dtTablet')], ['desktop', t('visits_dtDesktop')], ['bot', t('visits_dtBot')]]);
    fill('app', t('visits_fAll'), [['any', t('visits_appAny')]].concat(opts.apps.map(function (a) { return [a, a]; })).concat([['none', t('visits_appNone')]]));
    fill('os', t('visits_fAll'), opts.os.map(function (o) { return [o, o]; }));
    fill('who', t('visits_fAll'), [['student', t('visits_whoStudent')], ['admin', t('visits_whoTeacher')], ['anonymous', t('visits_whoAnon')]]);
    fill('failed', t('visits_fAll'), [['1', t('visits_failedOnly')]]);
    Array.prototype.forEach.call(document.querySelectorAll('input[data-f]'), function (i) { i.placeholder = t(i.getAttribute('data-ph')); });
    var dl = $('bankList');
    if (dl) dl.innerHTML = opts.banks.map(function (b) { return '<option value="' + esc(b.title || b.id) + '"></option>'; }).join('');
  }

  function loadOptions() {
    return API.get('/api/admin/visits/options').then(function (res) {
      opts = { pages: res.pages || [], banks: res.banks || [], os: res.os || [], apps: res.apps || [] };
      fillOptions();
    }).catch(function () { /* 选项取不到也不影响查询 */ });
  }


  /* ---------- 像 Excel：筛选放在表头下面，列宽可拖，宽度记在本机 ---------- */

  /* 每个表每一列：[筛选字段或 null, 默认宽度 px]（visits 的第一列是展开箭头） */
  var COLS = {
    visitTable: [[null, 30], [null, 140], ['class_name', 100], [null, 100], ['who', 100], [null, 120], ['device', 130], ['os', 120], ['app', 130], ['page', 190], ['bank', 190], [null, 56], ['stay', 90]],
    pageTable: [[null, 140], ['class_name', 100], [null, 100], ['who', 100], ['page', 130], ['bank', 190], ['stay', 90], ['device', 130], ['os', 120], ['app', 130], [null, 120]],
    loginTable: [[null, 140], ['failed', 90], [null, 110], ['who', 100], ['class_name', 100], [null, 120], ['device', 130], ['os', 120], ['app', 130], [null, 130]]
  };
  var WKEY = 'wp_visits_colw';
  var saved = {};
  try { saved = JSON.parse(localStorage.getItem(WKEY) || '{}') || {}; } catch (e) { saved = {}; }

  function setWidths(table) {
    var cols = table.querySelectorAll('col'), sum = 0;
    Array.prototype.forEach.call(cols, function (c) { sum += parseInt(c.style.width, 10) || 0; });
    table.style.width = sum + 'px';
  }

  function onFilter(el) {
    var f = el.getAttribute('data-f');
    F[f] = el.value;
    Array.prototype.forEach.call(document.querySelectorAll('[data-f="' + f + '"]'), function (o) { if (o !== el) o.value = el.value; });
    refilter();
  }

  function buildGrid(id) {
    var table = $(id), spec = COLS[id], widths = saved[id] || [];
    var cg = document.createElement('colgroup');
    spec.forEach(function (c, i) {
      var col = document.createElement('col');
      col.style.width = (widths[i] || c[1]) + 'px';
      cg.appendChild(col);
    });
    table.insertBefore(cg, table.firstChild);
    var heads = table.querySelectorAll('thead tr:first-child th');
    var fr = document.createElement('tr');
    fr.className = 'filter-row';
    spec.forEach(function (c, i) {
      var th = heads[i], td = document.createElement('th');
      var grip = document.createElement('span');
      grip.className = 'col-grip';
      grip.setAttribute('role', 'separator');
      th.appendChild(grip);
      grip.addEventListener('pointerdown', function (ev) {
        ev.preventDefault();
        var col = cg.children[i], startX = ev.clientX, startW = parseInt(col.style.width, 10);
        grip.setPointerCapture(ev.pointerId);
        grip.classList.add('on');
        function move(e) { col.style.width = Math.max(36, startW + e.clientX - startX) + 'px'; setWidths(table); }
        function up() {
          grip.classList.remove('on');
          grip.removeEventListener('pointermove', move);
          grip.removeEventListener('pointerup', up);
          saved[id] = Array.prototype.map.call(cg.children, function (x) { return parseInt(x.style.width, 10); });
          try { localStorage.setItem(WKEY, JSON.stringify(saved)); } catch (e) { /* 存不了就算了 */ }
        }
        grip.addEventListener('pointermove', move);
        grip.addEventListener('pointerup', up);
      });
      grip.addEventListener('dblclick', function () {
        cg.children[i].style.width = c[1] + 'px';
        setWidths(table);
      });
      var f = c[0], el = null;
      if (f === 'class_name' || f === 'bank' || f === 'stay') {
        el = document.createElement('input');
        el.type = f === 'stay' ? 'number' : 'text';
        if (f === 'stay') { el.min = 0; el.max = 86400; el.setAttribute('inputmode', 'numeric'); }
        el.setAttribute('data-ph', { class_name: 'visits_phClass', bank: 'visits_phBank', stay: 'visits_phStay' }[f]);
        if (f === 'bank') el.setAttribute('list', 'bankList');
        el.maxLength = 60;
        el.addEventListener('input', function () { onFilter(el); });
      } else if (f) {
        el = document.createElement('select');
        el.addEventListener('change', function () { onFilter(el); });
      }
      if (el) {
        el.setAttribute('data-f', f);
        el.setAttribute('aria-label', th.textContent);
        el.value = F[f];
        td.appendChild(el);
      }
      fr.appendChild(td);
    });
    table.querySelector('thead').appendChild(fr);
    setWidths(table);
  }

  /* 被遮住的文字：指上去 / 聚焦时显示全文（悬浮窗自动换行）；点格子是选字，只有箭头和时间两格点了才展开 */
  var timer = null;
  function refilter() { clearTimeout(timer); timer = setTimeout(function () { load(false); }, 250); }

  function ymd(date) {
    var m = date.getMonth() + 1, d = date.getDate();
    return date.getFullYear() + '-' + (m < 10 ? '0' : '') + m + '-' + (d < 10 ? '0' : '') + d;
  }

  WPI18N.onChange(function () { fillOptions(); if (state[tab].rows.length || state[tab].total) render(); });

  document.addEventListener('DOMContentLoaded', function () {
    $('tabVisits').onclick = function () { setTab('visits'); };
    $('tabPages').onclick = function () { setTab('pages'); };
    $('tabLogins').onclick = function () { setTab('logins'); };
    Array.prototype.forEach.call(document.querySelectorAll('#quickRange [data-range]'), function (b) {
      b.onclick = function () {
        var now = new Date(), from = new Date(now.getFullYear(), now.getMonth(), now.getDate() - parseInt(b.getAttribute('data-range'), 10));
        $('fSince').value = ymd(from);
        $('fUntil').value = ymd(now);
        load(false);
      };
    });
    $('btnClear').onclick = function () {
      ['fSearch', 'fSince', 'fUntil'].forEach(function (id) { $(id).value = ''; });
      Object.keys(F).forEach(function (k) { F[k] = ''; });
      Array.prototype.forEach.call(document.querySelectorAll('[data-f]'), function (e) { e.value = ''; });
      load(false);
    };
    $('btnMore').onclick = function () { load(true); };
    ['fSearch', 'fSince', 'fUntil'].forEach(function (id) {
      $(id).addEventListener(id === 'fSearch' ? 'input' : 'change', refilter);
    });
    Object.keys(COLS).forEach(buildGrid);
    fillOptions();
    var body = document.querySelector('#visitTable tbody');
    body.addEventListener('click', function (ev) {
      if (ev.target.closest('.raw-row')) return;
      var td = ev.target.closest('td'), row = ev.target.closest('.sum-row');
      if (!row || !td || td.cellIndex > 1) return;           /* 其他格子点击 = 选字 */
      toggle(row.getAttribute('data-key'));
    });
    Array.prototype.forEach.call(document.querySelectorAll('table.grid tbody'), function (tb) {
      tb.addEventListener('mouseover', function (ev) { var c = ev.target.closest('td'); if (c && !c.closest('.detail-row')) showTip(c); });
      tb.addEventListener('mouseout', function (ev) { if (ev.target.closest('td')) hideTip(); });
    });
    window.addEventListener('scroll', hideTip, true);
    body.addEventListener('keydown', function (ev) {
      if (ev.key !== 'Enter' && ev.key !== ' ') return;
      if (ev.target !== ev.target.closest('.sum-row')) return;
      ev.preventDefault(); toggle(ev.target.getAttribute('data-key'));
    });
    AuthUI.ready.then(function () { fillOptions(); loadOptions(); return load(false); });
  });
})();
