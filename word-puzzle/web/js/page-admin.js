/* page-admin.js —— 管理员：导入名单、查看账号、重置密码、停用、解锁、导出成绩。
   名单里的姓名、班级等都是外来内容，进页面前一律经过 API.esc 转义。 */
(function () {
  'use strict';

  var esc = API.esc;
  var t = AuthUI.t;
  var users = [];
  var lastCredentials = [];

  function el(id) { return document.getElementById(id); }

  /* ---------- 名单导入 ---------- */

  var FORMULA_PREFIXES = '=+-@';

  function csvCell(value) {
    value = String(value == null ? '' : value);
    // 以 = + - @ 开头的单元格在 Excel 里会被当成公式，前面补一个单引号（字符码 39）
    if (value && FORMULA_PREFIXES.indexOf(value.charAt(0)) >= 0) value = String.fromCharCode(39) + value;
    var quote = String.fromCharCode(34);
    var needsQuotes = /[,\r\n]/.test(value) || value.indexOf(quote) >= 0;
    return needsQuotes ? quote + value.split(quote).join(quote + quote) + quote : value;
  }

  function downloadCredentials() {
    var lines = [t('credsHeader')].concat(lastCredentials.map(function (c) {
      return [c.student_no, c.name, c.class_name, c.password].map(csvCell).join(',');
    }));
    var blob = new Blob(['﻿' + lines.join('\r\n')], { type: 'text/csv;charset=utf-8' });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'lexica-initial-passwords.csv';
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(function () { URL.revokeObjectURL(a.href); }, 60000);
  }

  function showReport(res) {
    lastCredentials = res.credentials || [];
    var html = '<div><b>' + esc(t('importDone', { created: res.created, updated: res.updated, skipped: res.skipped })) + '</b></div>';
    if ((res.ignored_columns || []).length) {
      html += '<div>' + esc(t('importIgnored', { cols: res.ignored_columns.join('、') })) + '</div>';
    }
    if ((res.errors || []).length) {
      html += '<div>' + esc(t('importErrors')) + '</div><ul>' + res.errors.slice(0, 50).map(function (e) {
        return '<li>' + esc(t('importRow', { row: e.row, no: e.student_no || '-', reason: e.reason })) + '</li>';
      }).join('') + '</ul>';
    }
    if (lastCredentials.length) {
      html += '<div class="hint" style="margin-top:8px">' + esc(t('credsNote')) + '</div>' +
        '<div class="actions"><button class="btn green" id="btnCreds" type="button">' +
        esc(t('credsDownload', { n: lastCredentials.length })) + '</button></div>';
    }
    el('importReport').innerHTML = html;
    var button = el('btnCreds');
    if (button) button.onclick = downloadCredentials;
  }

  function doImport() {
    var file = el('rosterFile').files[0];
    if (!file) { API.toast(t('noFile')); return; }
    var fd = new FormData();
    fd.append('file', file);
    if (el('resetExisting').checked) fd.append('reset_existing', '1');
    var btn = el('btnImport');
    btn.disabled = true;
    btn.textContent = t('importing');
    API.upload('/api/admin/import', fd).then(function (res) {
      showReport(res);
      return loadUsers();
    }).catch(function (err) {
      API.toast(AuthUI.errorText(err));
    }).finally(function () {
      btn.disabled = false;
      btn.textContent = t('importButton');
    });
  }

  /* ---------- 账号列表 ---------- */

  function distinct(field) {
    var seen = {};
    users.forEach(function (u) { if (u[field]) seen[u[field]] = true; });
    return Object.keys(seen).sort();
  }

  function fillSelect(id, field) {
    var select = el(id);
    var keep = select.value;
    select.innerHTML = '<option value="">' + esc(t('allOption')) + '</option>' +
      distinct(field).map(function (v) { return '<option value="' + esc(v) + '">' + esc(v) + '</option>'; }).join('');
    if (keep && distinct(field).indexOf(keep) >= 0) select.value = keep;
  }

  function filtered() {
    var cls = el('fClass').value, college = el('fCollege').value, dept = el('fDept').value;
    var q = el('fSearch').value.trim().toLowerCase();
    return users.filter(function (u) {
      return (!cls || u.class_name === cls) && (!college || u.college === college) &&
        (!dept || u.department === dept) &&
        (!q || u.student_no.toLowerCase().indexOf(q) >= 0 || u.name.toLowerCase().indexOf(q) >= 0);
    });
  }

  function tagCell(u) {
    if (u.role === 'admin') return '';
    if (!(u.tags || []).length) return '<span class="hint">' + esc(t('noTags')) + '</span>';
    return u.tags.map(function (tag) { return '<span class="pill gray">' + esc(tag) + '</span>'; }).join(' ');
  }

  function status(u) {
    if (u.role === 'admin') return '<span class="pill good">' + esc(t('statusAdmin')) + '</span>';
    if (u.disabled) return '<span class="pill bad">' + esc(t('statusDisabled')) + '</span>';
    if (u.locked) return '<span class="pill bad">' + esc(t('statusLocked')) + '</span>';
    if (u.must_change) return '<span class="pill warn">' + esc(t('statusMustChange')) + '</span>';
    return '<span class="pill">' + esc(t('statusOk')) + '</span>';
  }

  function render() {
    var rows = filtered();
    el('usersCount').textContent = t('usersCount', { n: rows.length });
    var body = document.querySelector('#userTable tbody');
    if (!rows.length) {
      body.innerHTML = '<tr><td colspan="11" class="empty">' + esc(t('noUsers')) + '</td></tr>';
    } else {
      body.innerHTML = rows.map(function (u) {
        var actions = '<button class="btn sm ghost" data-act="reset" data-id="' + u.id + '">' + esc(t('reset')) + '</button>';
        if (u.locked) actions += '<button class="btn sm ghost" data-act="unlock" data-id="' + u.id + '">' + esc(t('unlock')) + '</button>';
        if (u.role !== 'admin') {
          actions += '<button class="btn sm ghost" data-act="tags" data-id="' + u.id + '">' + esc(t('editTags')) + '</button>';
          actions += '<button class="btn sm ' + (u.disabled ? 'green' : 'danger') + '" data-act="' +
            (u.disabled ? 'enable' : 'disable') + '" data-id="' + u.id + '">' + esc(t(u.disabled ? 'enable' : 'disable')) + '</button>';
        }
        return '<tr><td>' + esc(u.student_no) + '</td><td>' + esc(u.name) + '</td><td>' + esc(u.class_name) +
          '</td><td>' + esc(u.college) + '</td><td>' + esc(u.department) + '</td><td>' + tagCell(u) + '</td><td>' + status(u) +
          '</td><td class="num">' + u.games + '</td><td class="num">' + u.best + '</td><td>' +
          esc(u.last_login_at || t('never')) + '</td><td><div class="cell-actions">' + actions + '</div></td></tr>';
      }).join('');
    }
    updateExportLink();
  }

  function updateExportLink() {
    var params = [];
    [['class_name', 'fClass'], ['college', 'fCollege'], ['department', 'fDept']].forEach(function (pair) {
      var value = el(pair[1]).value;
      if (value) params.push(pair[0] + '=' + encodeURIComponent(value));
    });
    el('btnExport').href = API.path('/api/admin/export/scores.csv' + (params.length ? '?' + params.join('&') : ''));
  }

  function loadUsers() {
    return API.get('/api/admin/users').then(function (res) {
      users = res.users;
      fillSelect('fClass', 'class_name');
      fillSelect('fCollege', 'college');
      fillSelect('fDept', 'department');
      render();
    }).catch(function (err) {
      API.toast(AuthUI.errorText(err));
    });
  }

  function findUser(id) {
    return users.filter(function (u) { return String(u.id) === String(id); })[0];
  }

  function act(button) {
    var u = findUser(button.dataset.id);
    if (!u) return;
    var action = button.dataset.act;
    var url = '/api/admin/users/' + u.id + '/';
    var done;
    if (action === 'reset') {
      if (!window.confirm(t('confirmReset', { name: u.name }))) return;
      done = API.post(url + 'reset-password', {}).then(function (res) {
        var box = el('secretBox');
        box.hidden = false;
        box.innerHTML = esc(t('resetDone', { name: u.name, no: u.student_no })) + ' <code>' + esc(res.password) + '</code>';
        box.scrollIntoView({ block: 'nearest' });
      });
    } else if (action === 'tags') {
      var typed = window.prompt(t('tagsPrompt', { name: u.name }), (u.tags || []).join(', '));
      if (typed === null) return;
      done = API.post(url + 'tags', { tags: typed }).then(function () { API.toast(t('tagsSaved')); });
    } else if (action === 'unlock') {
      done = API.post(url + 'unlock', {});
    } else if (action === 'disable') {
      if (!window.confirm(t('confirmDisable', { name: u.name }))) return;
      done = API.post(url + 'disabled', { disabled: true });
    } else {
      done = API.post(url + 'disabled', { disabled: false });
    }
    button.disabled = true;
    done.then(loadUsers).catch(function (err) {
      API.toast(AuthUI.errorText(err));
      button.disabled = false;
    });
  }

  /* 批量：只作用于当前筛选出来的学生（管理员账号不受影响） */
  function bulkTags(mode) {
    var typed = el('bulkTags').value.trim();
    if (!typed) { API.toast(t('bulkNeedTags')); return; }
    var ids = filtered().filter(function (u) { return u.role !== 'admin'; }).map(function (u) { return u.id; });
    if (!ids.length) { API.toast(t('bulkNoUsers')); return; }
    var key = mode === 'add' ? 'bulkConfirmAdd' : 'bulkConfirmRemove';
    if (!window.confirm(t(key, { n: ids.length, tags: typed }))) return;
    var body = { user_ids: ids };
    body[mode === 'add' ? 'add' : 'remove'] = typed;
    API.post('/api/admin/users/tags', body).then(function (res) {
      API.toast(t('bulkDone', { n: res.changed }));
      return loadUsers();
    }).catch(function (err) { API.toast(AuthUI.errorText(err)); });
  }

  document.addEventListener('DOMContentLoaded', function () {
    el('btnImport').onclick = doImport;
    el('btnBulkAdd').onclick = function () { bulkTags('add'); };
    el('btnBulkRemove').onclick = function () { bulkTags('remove'); };
    ['fClass', 'fCollege', 'fDept'].forEach(function (id) { el(id).onchange = render; });
    el('fSearch').oninput = render;
    document.querySelector('#userTable tbody').addEventListener('click', function (event) {
      var button = event.target.closest('button[data-act]');
      if (button) act(button);
    });
    AuthUI.ready.then(function (info) {
      if (info.user && info.user.role === 'admin') loadUsers();
    });
  });
})();
