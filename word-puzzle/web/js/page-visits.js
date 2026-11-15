/* ============================================================
   page-visits.js —— 访问记录（只有老师能看）
   ------------------------------------------------------------
   「访问」标签：一行 = 一次访问（同一个浏览器标签页里同一个账号先后打开的页面），点开看每一页和停留时间。
   「登录记录」标签：每次登录（成功和失败）一行。
   时间在库里是 UTC 秒数，这里由浏览器换成本地时间。
   ============================================================ */
(function () {
  'use strict';

  function esc(s) { return API.esc(s); }
  function t(key, params) { return WPI18N.t(key, params); }
  function $(id) { return document.getElementById(id); }

  var PAGE = 100;
  var tab = 'visits';
  var state = { visits: { rows: [], total: 0 }, logins: { rows: [], total: 0 } };
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
  function osText(r) { return [r.os, r.os_version].filter(Boolean).join(' '); }
  function browserText(r) { return [r.browser, (r.browser_version || '').split('.')[0]].filter(Boolean).join(' '); }
  function ipText(r) {
    if (!r.ips || r.ips.length < 2) return r.ip || t('visits_ipUnknown');
    return t('visits_ipMany', { ip: r.ip, n: r.ips.length });
  }
  function nameCell(r) { return r.role === 'admin' ? esc(r.name) + ' (' + esc(t('visits_roleAdmin')) + ')' : esc(r.name || (r.user_id ? '' : t('visits_anon'))); }

  function query(offset) {
    var p = ['limit=' + PAGE, 'offset=' + offset], v;
    if (v = $('fWho').value) p.push('role=' + encodeURIComponent(v));
    if (v = $('fClass').value.trim()) p.push('class_name=' + encodeURIComponent(v));
    if (v = $('fSearch').value.trim()) p.push('q=' + encodeURIComponent(v));
    if (v = $('fSince').value) p.push('since=' + Math.floor(new Date(v + 'T00:00:00').getTime() / 1000));
    if (v = $('fUntil').value) p.push('until=' + (Math.floor(new Date(v + 'T00:00:00').getTime() / 1000) + 86400));
    if (tab === 'logins' && $('fFailed').checked) p.push('failed=1');
    return p.join('&');
  }

  function exportLink() {
    var p = query(0).split('&').filter(function (x) { return !/^(limit|offset|failed)=/.test(x); });
    $('btnExport').href = API.path('/api/admin/export/' + (tab === 'visits' ? 'page-views' : 'logins') + '.csv' + (p.length ? '?' + p.join('&') : ''));
  }

  function load(more) {
    var s = state[tab];
    var offset = more ? s.rows.length : 0;
    var path = tab === 'visits' ? '/api/admin/visits?' : '/api/admin/logins?';
    $('countHint').textContent = t('visits_loading');
    return API.get(path + query(offset)).then(function (res) {
      var rows = tab === 'visits' ? res.sessions : res.logins;
      s.rows = more ? s.rows.concat(rows) : rows;
      s.total = res.total;
      render();
    }).catch(function () { $('countHint').textContent = t('visits_fail'); });
  }

  function key(r) { return r.sid + '|' + (r.user_id || 0); }

  function pagesHtml(k) {
    var d = pagesCache[k];
    if (!Array.isArray(d)) return '<div class="empty">' + esc(t(d === 'error' ? 'visits_fail' : 'visits_loading')) + '</div>';
    return '<table class="detail-table"><thead><tr>' + ['visits_dTime', 'visits_dPath', 'visits_dTitle', 'visits_dStay', 'visits_dFrom']
      .map(function (x) { return '<th>' + esc(t(x)) + '</th>'; }).join('') + '</tr></thead><tbody>' +
      d.map(function (p) {
        var extra = { ip: p.ip, forwarded: p.forwarded, client: p.client_info, user_agent: p.user_agent, accept_language: p.accept_language };
        return '<tr><td>' + esc(stamp(p.started_at)) + '</td><td>' + esc(p.path) + '</td><td>' + esc(p.title) + '</td><td>' + esc(dur(p.active_seconds)) +
          '</td><td>' + esc(p.referrer) + '</td></tr>' +
          '<tr class="raw-row"><td colspan="5"><details><summary>' + esc(t('visits_dMore')) + '</summary><pre>' + esc(JSON.stringify(extra, null, 1)) + '</pre></details></td></tr>';
      }).join('') + '</tbody></table>';
  }

  function renderVisits() {
    var body = document.querySelector('#visitTable tbody');
    var rows = state.visits.rows;
    if (!rows.length) { body.innerHTML = '<tr><td colspan="11" class="empty">' + esc(t('visits_empty')) + '</td></tr>'; return; }
    body.innerHTML = rows.map(function (r) {
      var k = key(r), isOpen = !!open[k];
      return '<tr class="sum-row" tabindex="0" role="button" aria-expanded="' + isOpen + '" data-key="' + esc(k) + '" title="' + esc(t(isOpen ? 'visits_collapse' : 'visits_expand')) + '">' +
        '<td><span class="caret">▸</span></td><td>' + esc(stamp(r.first_at)) + '</td><td>' + esc(r.class_name) + '</td><td>' + esc(r.student_no) + '</td><td>' + nameCell(r) + '</td>' +
        '<td>' + esc(ipText(r)) + '</td><td>' + esc(deviceText(r)) + '</td><td>' + esc(osText(r)) + '</td><td>' + esc(browserText(r)) + '</td>' +
        '<td class="num">' + r.pages + '</td><td>' + esc(dur(r.active_seconds)) + '</td></tr>' +
        (isOpen ? '<tr class="detail-row"><td colspan="11">' + pagesHtml(k) + '</td></tr>' : '');
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

  function render() {
    var s = state[tab];
    $('visitTable').hidden = tab !== 'visits';
    $('loginTable').hidden = tab !== 'logins';
    $('failedBox').hidden = tab !== 'logins';
    $('btnMore').hidden = s.rows.length >= s.total;
    $('countHint').textContent = t('visits_count', { n: s.total, shown: s.rows.length });
    var local = s.rows.length > 0 && s.rows.slice(0, 20).every(function (r) { return r.ip === '127.0.0.1' || r.ip === '::1'; });
    $('ipWarn').hidden = !local;
    $('ipWarn').textContent = local ? t('visits_proxyOnly') : '';
    (tab === 'visits' ? renderVisits : renderLogins)();
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
    $('tabVisits').classList.toggle('active', name === 'visits');
    $('tabLogins').classList.toggle('active', name === 'logins');
    $('tabVisits').setAttribute('aria-selected', String(name === 'visits'));
    $('tabLogins').setAttribute('aria-selected', String(name === 'logins'));
    load(false);
  }

  WPI18N.onChange(function () { if (state[tab].rows.length || state[tab].total) render(); });

  document.addEventListener('DOMContentLoaded', function () {
    $('tabVisits').onclick = function () { setTab('visits'); };
    $('tabLogins').onclick = function () { setTab('logins'); };
    $('btnMore').onclick = function () { load(true); };
    var timer = null;
    function refilter() { clearTimeout(timer); timer = setTimeout(function () { load(false); }, 250); }
    ['fWho', 'fClass', 'fSearch', 'fSince', 'fUntil', 'fFailed'].forEach(function (id) { $(id).addEventListener(id === 'fWho' || id === 'fSince' || id === 'fUntil' || id === 'fFailed' ? 'change' : 'input', refilter); });
    var body = document.querySelector('#visitTable tbody');
    body.addEventListener('click', function (ev) {
      if (ev.target.closest('.raw-row')) return;
      var row = ev.target.closest('.sum-row');
      if (row) toggle(row.getAttribute('data-key'));
    });
    body.addEventListener('keydown', function (ev) {
      if (ev.key !== 'Enter' && ev.key !== ' ') return;
      var row = ev.target.closest('.sum-row');
      if (row) { ev.preventDefault(); toggle(row.getAttribute('data-key')); }
    });
    AuthUI.ready.then(function () { return load(false); });
  });
})();
