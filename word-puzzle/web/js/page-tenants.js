/* ============================================================
   page-tenants.js —— 老师与分配（只有超级管理员能进）
   ------------------------------------------------------------
   四个标签页（#teachers #assign #deleted #audit）：
     老师 —— 列表（名下多少学生、题库、词表）、添加老师（初始密码只显示一次）、重置密码、停用、删除；
     共享与分配 —— 勾选题库或学生，选一位老师，共享 / 转给 / 取消共享；
     已删除 —— 老师和超管删掉的学生、题库、词表，一键恢复；
     操作记录 —— 审计日志（加老师、共享、转移、删除、恢复、导入名单时的自动共享）。
   ============================================================ */
(function () {
  'use strict';

  var TABS = ['teachers', 'assign', 'deleted', 'audit'];
  var SUFFIX = { teachers: 'Teachers', assign: 'Assign', deleted: 'Deleted', audit: 'Audit' };
  var teachers = [], banks = [], students = [], picked = {};
  var current = 'teachers';

  function esc(s) { return API.esc(s); }
  function t(key, params) { return WPI18N.t(key, params); }
  function $(id) { return document.getElementById(id); }
  function when(sec) { return sec ? API.fmtTime(sec * 1000) : ''; }

  /* ---------------- 标签页 ---------------- */

  function tabFromHash() {
    var name = (location.hash || '').replace('#', '');
    return TABS.indexOf(name) >= 0 ? name : 'teachers';
  }

  function showTab(name) {
    current = name;
    TABS.forEach(function (n) {
      var on = n === name;
      $('tab' + SUFFIX[n]).classList.toggle('active', on);
      $('tab' + SUFFIX[n]).setAttribute('aria-selected', String(on));
      $('tab' + SUFFIX[n]).tabIndex = on ? 0 : -1;
      $('panel' + SUFFIX[n]).hidden = !on;
    });
    try { history.replaceState(null, '', '#' + name); } catch (e) { }
    if (name === 'assign') loadAssign();
    if (name === 'deleted') loadDeleted();
    if (name === 'audit') loadAudit();
  }

  /* ---------------- 老师 ---------------- */

  function renderTeachers() {
    var body = document.querySelector('#teacherTable tbody');
    if (!teachers.length) { body.innerHTML = '<tr><td colspan="10" class="empty">' + esc(t('ten_noTeachers')) + '</td></tr>'; return; }
    body.innerHTML = teachers.map(function (u) {
      var role = u.role === 'admin' ? '<span class="pill good">' + esc(t('ten_roleSuper')) + '</span>'
                                    : '<span class="pill">' + esc(t('ten_roleTeacher')) + '</span>';
      if (u.disabled) role += ' <span class="pill bad">' + esc(t('ten_disabled')) + '</span>';
      var ops = '';
      if (u.role === 'teacher') {
        ops = '<button class="btn sm ghost" data-act="group" data-id="' + u.id + '">' + esc(t('ten_setGroup')) + '</button>' +
              '<button class="btn sm ghost" data-act="reset" data-id="' + u.id + '">' + esc(t('ten_reset')) + '</button>' +
              '<button class="btn sm ' + (u.disabled ? 'green' : 'ghost') + '" data-act="' + (u.disabled ? 'enable' : 'disable') + '" data-id="' + u.id + '">' +
              esc(t(u.disabled ? 'ten_enable' : 'ten_disable')) + '</button>' +
              '<button class="btn sm danger" data-act="delete" data-id="' + u.id + '">' + esc(t('ten_delete')) + '</button>';
      }
      return '<tr><td>' + esc(u.name) + '</td><td>' + esc(u.student_no) + '</td><td>' + role + '</td>' +
        '<td>' + esc(u.teacher_group || t('ten_noGroup')) + '</td>' +
        '<td class="num">' + u.students + '</td><td class="num">' + u.own_banks + '</td><td class="num">' + u.shared_banks + '</td>' +
        '<td class="num">' + u.materials + '</td><td>' + esc(u.last_login_at || t('ten_never')) + '</td>' +
        '<td><div class="cell-actions">' + ops + '</div></td></tr>';
    }).join('');
  }

  function loadTeachers() {
    return API.get('/api/admin/teachers').then(function (res) {
      teachers = res.teachers || [];
      renderTeachers();
      fillTeacherSelect();
    }).catch(function (e) { API.toast(e.message); });
  }

  function addTeacher() {
    var body = { student_no: $('newNo').value.trim(), name: $('newName').value.trim(), password: $('newPw').value };
    var msg = $('teacherMsg'), box = $('teacherSecret');
    if (!body.student_no || !body.name) { msg.className = 'msg on err'; msg.textContent = t('ten_needNoName'); return; }
    $('btnAddTeacher').disabled = true;
    API.post('/api/admin/teachers', body).then(function (res) {
      msg.className = 'msg';
      box.hidden = false;
      box.innerHTML = esc(t('ten_added', { name: res.teacher.name, no: res.teacher.student_no })) + ' <code>' + esc(res.password) + '</code>';
      $('newNo').value = $('newName').value = $('newPw').value = '';
      return loadTeachers();
    }).catch(function (e) {
      msg.className = 'msg on err';
      msg.textContent = AuthUI.errorText(e);
    }).finally(function () { $('btnAddTeacher').disabled = false; });
  }

  function teacherAction(btn) {
    var u = teachers.filter(function (x) { return String(x.id) === btn.dataset.id; })[0];
    if (!u) return;
    var act = btn.dataset.act, done;
    if (act === 'group') {
      var typed = window.prompt(t('ten_groupPrompt', { name: u.name }), u.teacher_group || '');
      if (typed === null) return;
      btn.disabled = true;
      API.post('/api/admin/teachers/' + u.id + '/group', { group: typed }).then(function () {
        API.toast(t('ten_groupSaved'));
        return loadTeachers();
      }).catch(function (e) { API.toast(AuthUI.errorText(e)); btn.disabled = false; });
      return;
    }
    if (act === 'reset') {
      if (!confirm(t('ten_confirmReset', { name: u.name }))) return;
      done = API.post('/api/admin/users/' + u.id + '/reset-password', {}).then(function (res) {
        var box = $('teacherSecret');
        box.hidden = false;
        box.innerHTML = esc(t('ten_resetDone', { name: u.name })) + ' <code>' + esc(res.password) + '</code>';
      });
    } else if (act === 'disable' || act === 'enable') {
      if (act === 'disable' && !confirm(t('ten_confirmDisable', { name: u.name }))) return;
      done = API.post('/api/admin/users/' + u.id + '/disabled', { disabled: act === 'disable' });
    } else {
      if (!confirm(t('ten_confirmDelete', { name: u.name }))) return;
      done = API.post('/api/admin/teachers/' + u.id + '/delete', {});
    }
    btn.disabled = true;
    done.then(loadTeachers).catch(function (e) { API.toast(AuthUI.errorText(e)); btn.disabled = false; });
  }

  /* ---------------- 共享与分配 ---------------- */

  function kind() {
    var r = document.querySelector('input[name="assignKind"]:checked');
    return r ? r.value : 'bank';
  }

  function fillTeacherSelect() {
    var box = $('assignTeacher'), keep = box.value;
    box.innerHTML = teachers.filter(function (u) { return !u.disabled; }).map(function (u) {
      return '<option value="' + u.id + '">' + esc(u.name + ' (' + u.student_no + ')') + '</option>';
    }).join('');
    if (keep) box.value = keep;
  }

  function items() {
    var q = $('assignQ').value.trim().toLowerCase();
    var list = kind() === 'bank'
      ? banks.map(function (b) { return { id: b.id, label: b.title, meta: b.category || '', owner: b.owner_name || '' }; })
      : students.map(function (u) {
          return { id: u.id, label: u.name + ' · ' + u.student_no, meta: u.class_name || '',
                   owner: (u.teachers || []).map(function (x) { return x.name; }).join('、') };
        });
    return list.filter(function (x) { return !q || (x.label + ' ' + x.meta + ' ' + x.owner).toLowerCase().indexOf(q) >= 0; });
  }

  function renderAssign() {
    var shown = items();
    $('assignList').innerHTML = shown.length ? shown.map(function (x) {
      var key = kind() + ':' + x.id;
      return '<label class="pick-row"><input type="checkbox" data-key="' + esc(key) + '"' + (picked[key] ? ' checked' : '') + '> ' +
        '<span>' + esc(x.label) + '</span><small>' + esc([x.meta, x.owner].filter(Boolean).join(' · ')) + '</small></label>';
    }).join('') : '<div class="empty">' + esc(t('ten_nothing')) + '</div>';
    updateHint();
  }

  function pickedIds() {
    var prefix = kind() + ':';
    return Object.keys(picked).filter(function (k) { return picked[k] && k.indexOf(prefix) === 0; })
      .map(function (k) { return parseInt(k.slice(prefix.length), 10); });
  }

  function updateHint() {
    $('assignHint').textContent = t('ten_picked', { n: pickedIds().length });
  }

  function loadAssign() {
    var ownerName = {};
    teachers.forEach(function (u) { ownerName[u.id] = u.name; });
    return Promise.all([API.get('/api/banks'), API.get('/api/admin/users?role=student')]).then(function (res) {
      banks = (res[0].banks || []).map(function (b) {
        b.owner_name = b.owner_id ? (ownerName[b.owner_id] || '') : t('ten_builtIn');
        return b;
      });
      students = (res[1].users || []).filter(function (u) { return u.role === 'student'; });
      renderAssign();
    }).catch(function (e) { API.toast(e.message); });
  }

  function runAssign() {
    var ids = pickedIds(), teacher = parseInt($('assignTeacher').value, 10), mode = $('assignMode').value;
    if (!ids.length) { API.toast(t('ten_pickFirst')); return; }
    if (!teacher) { API.toast(t('ten_pickTeacher')); return; }
    var name = $('assignTeacher').selectedOptions[0].textContent;
    var CONFIRM = { share: 'ten_confirmAssign_share', move: 'ten_confirmAssign_move', unshare: 'ten_confirmAssign_unshare' };
    if (!confirm(t(CONFIRM[mode], { n: ids.length, teacher: name }))) return;
    $('btnAssign').disabled = true;
    API.post('/api/admin/assign', { kind: kind(), mode: mode, ids: ids, teacher_id: teacher }).then(function (res) {
      API.toast(t('ten_assigned', { n: res.changed }));
      picked = {};
      return Promise.all([loadAssign(), loadTeachers()]);
    }).catch(function (e) { API.toast(AuthUI.errorText(e)); }).finally(function () { $('btnAssign').disabled = false; });
  }

  /* ---------------- 已删除 ---------------- */

  function delRow(kindName, id, title, meta) {
    return '<div class="item"><div class="main"><b>' + esc(title) + '</b> <small>' + esc(meta) + '</small></div>' +
      '<div class="ops"><button class="btn sm green" data-restore="' + kindName + '" data-id="' + id + '">' + esc(t('ten_restore')) + '</button></div></div>';
  }

  function by(row) { return t('ten_deletedBy', { name: row.deleted_by_name || '-', time: when(row.deleted_at) }); }

  function loadDeleted() {
    return API.get('/api/admin/deleted').then(function (res) {
      var empty = '<div class="empty">' + esc(t('ten_noneDeleted')) + '</div>';
      $('delUsers').innerHTML = (res.users || []).map(function (u) {
        return delRow('user', u.id, u.name + ' · ' + u.student_no, [u.class_name, by(u)].filter(Boolean).join(' · '));
      }).join('') || empty;
      $('delBanks').innerHTML = (res.banks || []).map(function (b) {
        return delRow('bank', b.id, b.title, [b.owner_name ? t('ten_owner', { name: b.owner_name }) : t('ten_builtIn'), by(b)].join(' · '));
      }).join('') || empty;
      $('delMaterials').innerHTML = (res.materials || []).map(function (m) {
        return delRow('material', m.id, m.name, [t('ten_owner', { name: m.owner_name || '-' }), by(m)].join(' · '));
      }).join('') || empty;
    }).catch(function (e) { API.toast(e.message); });
  }

  /* ---------------- 操作记录 ---------------- */

  var ACTION_KEYS = {
    'teacher.create': 'ten_act_teacher_create', 'teacher.delete': 'ten_act_teacher_delete',
    'bank.share': 'ten_act_bank_share', 'bank.move': 'ten_act_bank_move', 'bank.unshare': 'ten_act_bank_unshare',
    'bank.delete': 'ten_act_bank_delete', 'bank.unshare_self': 'ten_act_bank_unshare_self', 'bank.restore': 'ten_act_bank_restore',
    'student.share': 'ten_act_student_share', 'student.move': 'ten_act_student_move', 'student.unshare': 'ten_act_student_unshare',
    'student.delete': 'ten_act_student_delete', 'student.unlink_self': 'ten_act_student_unlink_self',
    'student.auto_share': 'ten_act_student_auto_share', 'user.restore': 'ten_act_user_restore',
    'share.request': 'ten_act_share_request', 'share.approve': 'ten_act_share_approve', 'share.reject': 'ten_act_share_reject',
    'teacher.group': 'ten_act_teacher_group',
    'material.delete': 'ten_act_material_delete', 'material.restore': 'ten_act_material_restore'
  };

  function actionText(a) {
    return ACTION_KEYS[a] ? t(ACTION_KEYS[a]) : a;           /* 不认识的动作原样显示，不丢 */
  }

  function loadAudit() {
    return API.get('/api/admin/audit?limit=300').then(function (res) {
      var rows = res.audit || [];
      var body = document.querySelector('#auditTable tbody');
      body.innerHTML = rows.length ? rows.map(function (r) {
        var d = r.detail || {};
        var detail = [d.title, d.student_no, d.name, d.teacher, d.group].filter(Boolean).join(' · ');
        return '<tr><td>' + esc(when(r.ts)) + '</td><td>' + esc(r.actor_name || '-') + '</td><td>' + esc(actionText(r.action)) + '</td>' +
          '<td>' + esc((r.target_type || '') + (r.target_id ? ' #' + r.target_id : '')) + '</td><td>' + esc(detail) + '</td></tr>';
      }).join('') : '<tr><td colspan="5" class="empty">' + esc(t('ten_noAudit')) + '</td></tr>';
    }).catch(function (e) { API.toast(e.message); });
  }

  /* ---------------- 启动 ---------------- */

  WPI18N.onChange(function () {
    renderTeachers();
    if (current === 'assign') renderAssign();
    if (current === 'deleted') loadDeleted();
    if (current === 'audit') loadAudit();
  });

  document.addEventListener('DOMContentLoaded', function () {
    TABS.forEach(function (n) { $('tab' + SUFFIX[n]).addEventListener('click', function () { showTab(n); }); });
    $('btnAddTeacher').onclick = addTeacher;
    document.querySelector('#teacherTable tbody').addEventListener('click', function (ev) {
      var btn = ev.target.closest('button[data-act]');
      if (btn) teacherAction(btn);
    });
    Array.prototype.forEach.call(document.querySelectorAll('input[name="assignKind"]'), function (r) { r.onchange = renderAssign; });
    $('assignQ').oninput = renderAssign;
    $('assignList').addEventListener('change', function (ev) {
      var box = ev.target.closest('input[data-key]');
      if (box) { picked[box.getAttribute('data-key')] = box.checked; updateHint(); }
    });
    $('btnSelAll').onclick = function () { items().forEach(function (x) { picked[kind() + ':' + x.id] = true; }); renderAssign(); };
    $('btnSelNone').onclick = function () { picked = {}; renderAssign(); };
    $('btnAssign').onclick = runAssign;
    $('panelDeleted').addEventListener('click', function (ev) {
      var btn = ev.target.closest('button[data-restore]');
      if (!btn) return;
      btn.disabled = true;
      API.post('/api/admin/restore', { kind: btn.dataset.restore, id: parseInt(btn.dataset.id, 10) }).then(function () {
        API.toast(t('ten_restored'));
        return Promise.all([loadDeleted(), loadTeachers()]);
      }).catch(function (e) { API.toast(AuthUI.errorText(e)); btn.disabled = false; });
    });
    AuthUI.ready.then(function () {
      if (!AuthUI.isSuper()) return;
      return loadTeachers().then(function () { showTab(tabFromHash()); });
    });
  });

  /* 给行为测试用 */
  window.WPTenants = { actionText: actionText, ACTION_KEYS: ACTION_KEYS, tabFromHash: tabFromHash };
})();
