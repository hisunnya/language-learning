/* ============================================================
   auth-ui.js —— 学生版的登录态在页面里的体现
   ------------------------------------------------------------
   * 问一次 /api/auth/me，没登录就跳到登录页，还没改初始密码就跳到改密码页；
   * 顶部加「当前用户 + 退出」，管理员多一个「账号管理」入口；
   * 家庭版（没有登录功能）什么都不做，页面和以前完全一样；
   * 页面用 <body data-auth="..."> 声明自己的要求：
       public = 不需要登录（登录页）   change = 允许还没改密码（改密码页）
       admin  = 只给管理员            （不写）= 普通已登录用户
   ============================================================ */
(function (global) {
  'use strict';

  var BASE = ((document.querySelector('meta[name="wp-base"]') || {}).content || '').replace(/\/$/, '');

  var TEXT = {
    zh: {
      signOut: '退出',
      changePassword: '修改密码',
      adminLink: '账号管理',
      visitsLink: '访问记录',
      tenantsLink: '老师与分配',
      leaderboardLink: '积分榜',
      teacherSignIn: '教师登录',
      signingIn: '登录中…',
      signIn: '登录',
      saving: '保存中…',
      savePassword: '保存新密码',
      notEnabled: '这个站点没有启用登录功能，直接回首页使用即可。',
      err_invalid_credentials: '学号或密码不对（连续错 5 次会临时锁定 15 分钟）',
      err_rate_limited: '尝试太频繁了，请稍后再试',
      err_missing: '请输入学号和密码',
      err_wrong_old_password: '旧密码不对',
      err_weak_password: '新密码不符合要求：至少 8 位，字母、数字、符号至少用两种，不能包含学号',
      err_forbidden: '没有权限做这件事',
      err_network: '网络不通，请稍后再试',
      err_bad_role: '角色不对',
      err_deleted: '这个账号已被删除，请联系管理员恢复',
      err_not_primary: '这个学生由别的老师负责，只有他或超级管理员能重置密码、停用、解锁；你可以看成绩、打自己的标签',
      err_no_request: '这条申请已经处理过了，或者不存在',
      err_generic: '出错了，请稍后再试',
      pwTooShort: '新密码至少 8 位',
      pwNeedMix: '新密码请至少混合使用两种字符（字母、数字、符号）',
      pwMismatch: '两次输入的新密码不一致',
      pwSame: '新密码不能和旧密码一样',
      pwHasNumber: '新密码不能包含学号',
      passwordChanged: '密码已更新，正在跳转…',
      noFile: '请先选择名单文件',
      importing: '导入中…',
      importButton: '导入名单',
      importDone: '新建 {created} 个，更新 {updated} 个，跳过 {skipped} 个',
      importIgnored: '这些列不会被保存：{cols}',
      importErrors: '有问题的行：',
      importRow: '第 {row} 行 {no}：{reason}',
      credsNote: '初始密码只会显示这一次，请现在下载清单；关闭或刷新页面后任何人都查不到。',
      credsDownload: '下载初始密码清单（{n} 人）',
      credsHeader: '学号,姓名,班级,初始密码',
      statusAdmin: '管理员',
      statusTeacher: '老师',
      importShared: '其中 {n} 个学号已属于其他老师，现在由你们共享（不改对方那边的资料）',
      importRequested: '其中 {n} 个学号已属于其他老师，没有挂到你名下：已向对方提交共享申请，对方（或超级管理员）批准后才会出现在你的列表里',
      reqApprove: '同意共享',
      reqReject: '拒绝',
      reqIn: '{requester}（{no}{group}）想共享学生 {sno} {name} {cls}',
      reqInGroup: '，{group}',
      reqOut: '学号 {sno}',
      reqPending: '等待批准',
      reqApproved: '已批准',
      reqRejected: '已拒绝',
      reqConfirmApprove: '同意把 {name}（{sno}）也共享给 {requester}？对方能看到他的成绩和访问记录、给他打标签，但不能重置密码。',
      reqConfirmReject: '拒绝 {requester} 的共享申请？',
      reqDone: '已处理',
      managedBy: '由 {name} 负责',
      deleteUser: '删除',
      confirmDeleteOne: '删除「{name}」？只属于你的学生会被删除（管理员能恢复）；也属于别的老师的，只从你名下移走。',
      confirmBulkDelete: '删除下面列表里的 {n} 个学生？只属于你的会被删除（管理员能恢复）；也属于别的老师的，只从你名下移走。',
      deleteDone: '已删除 {deleted} 个；{unlinked} 个也属于别的老师，只从你名下移走',
      statusMustChange: '待改密码',
      statusLocked: '已锁定',
      statusDisabled: '已停用',
      statusOk: '正常',
      reset: '重置密码',
      disable: '停用',
      enable: '启用',
      unlock: '解锁',
      confirmReset: '确定重置「{name}」的密码吗？对方所有设备都会被退出登录。',
      confirmDisable: '确定停用「{name}」吗？对方会立刻被退出登录。',
      resetDone: '「{name}」（{no}）的新初始密码：',
      noUsers: '没有符合条件的账号',
      allOption: '全部',
      usersCount: '共 {n} 个账号',
      never: '从未登录',
      err_bad_tags: '标签不合法：每个标签最多 20 个字，最多 10 个，用逗号隔开',
      tagsColumn: '标签',
      editTags: '标签',
      noTags: '—',
      tagsPrompt: '给「{name}」设置标签，用逗号隔开（留空表示清空）：',
      tagsSaved: '标签已保存',
      bulkNeedTags: '请先填写标签，用逗号隔开',
      bulkNoUsers: '当前列表里没有可以修改的学生',
      bulkConfirmAdd: '给当前列表里的 {n} 个学生加上标签「{tags}」吗？',
      bulkConfirmRemove: '从当前列表里的 {n} 个学生身上去掉标签「{tags}」吗？',
      bulkDone: '已修改 {n} 个学生'
    },
    en: {
      signOut: 'Sign out',
      changePassword: 'Change password',
      adminLink: 'Accounts',
      visitsLink: 'Visits',
      tenantsLink: 'Teachers',
      leaderboardLink: 'Leaderboard',
      teacherSignIn: 'Teacher sign-in',
      signingIn: 'Signing in…',
      signIn: 'Sign in',
      saving: 'Saving…',
      savePassword: 'Save new password',
      notEnabled: 'Sign-in is not enabled on this site. Just go to the home page.',
      err_invalid_credentials: 'Wrong student number or password (5 wrong tries in a row lock the account for 15 minutes)',
      err_rate_limited: 'Too many attempts. Please try again later.',
      err_missing: 'Please enter your student number and password',
      err_wrong_old_password: 'The current password is wrong',
      err_weak_password: 'The new password is not acceptable: at least 8 characters, mix at least two kinds (letters, digits, symbols), and do not include your student number',
      err_forbidden: 'You are not allowed to do that',
      err_network: 'Network problem, please try again later',
      err_bad_role: 'Invalid role',
      err_deleted: 'This account has been deleted; ask the administrator to restore it',
      err_not_primary: 'This student is looked after by another teacher; only that teacher or the super administrator can reset the password, disable or unlock. You can see the scores and use your own tags',
      err_no_request: 'This request was already handled, or does not exist',
      err_generic: 'Something went wrong, please try again later',
      pwTooShort: 'The new password needs at least 8 characters',
      pwNeedMix: 'Mix at least two kinds of characters (letters, digits, symbols)',
      pwMismatch: 'The two new passwords do not match',
      pwSame: 'The new password must differ from the old one',
      pwHasNumber: 'The new password must not contain your student number',
      passwordChanged: 'Password updated, redirecting…',
      noFile: 'Please choose the roster file first',
      importing: 'Importing…',
      importButton: 'Import roster',
      importDone: 'Created {created}, updated {updated}, skipped {skipped}',
      importIgnored: 'These columns are not stored: {cols}',
      importErrors: 'Rows with problems:',
      importRow: 'Row {row} {no}: {reason}',
      credsNote: 'Initial passwords are shown only once. Download the list now; after you close or refresh this page nobody can look them up.',
      credsDownload: 'Download initial passwords ({n})',
      credsHeader: 'Student no.,Name,Class,Initial password',
      statusAdmin: 'Admin',
      statusTeacher: 'Teacher',
      importShared: '{n} of these numbers already belong to another teacher and are now shared with you (their details are left unchanged)',
      importRequested: '{n} of these numbers already belong to another teacher and were NOT added to your list: a share request was sent, and they appear only after that teacher (or the super administrator) approves',
      reqApprove: 'Approve',
      reqReject: 'Reject',
      reqIn: '{requester} ({no}{group}) wants to share student {sno} {name} {cls}',
      reqInGroup: ', {group}',
      reqOut: 'Student no. {sno}',
      reqPending: 'Waiting for approval',
      reqApproved: 'Approved',
      reqRejected: 'Rejected',
      reqConfirmApprove: 'Also share {name} ({sno}) with {requester}? They will see the scores and visits and can tag the student, but cannot reset the password.',
      reqConfirmReject: 'Reject the share request from {requester}?',
      reqDone: 'Done',
      managedBy: 'Looked after by {name}',
      deleteUser: 'Delete',
      confirmDeleteOne: 'Delete “{name}”? A student who is only yours is deleted (the administrator can restore it); one who also belongs to another teacher is only removed from your list.',
      confirmBulkDelete: 'Delete the {n} students in the list below? Students who are only yours are deleted (the administrator can restore them); those who also belong to another teacher are only removed from your list.',
      deleteDone: '{deleted} deleted; {unlinked} also belong to another teacher and were only removed from your list',
      statusMustChange: 'Must change password',
      statusLocked: 'Locked',
      statusDisabled: 'Disabled',
      statusOk: 'Active',
      reset: 'Reset password',
      disable: 'Disable',
      enable: 'Enable',
      unlock: 'Unlock',
      confirmReset: 'Reset the password of “{name}”? They will be signed out everywhere.',
      confirmDisable: 'Disable “{name}”? They will be signed out immediately.',
      resetDone: 'New initial password for “{name}” ({no}):',
      noUsers: 'No matching accounts',
      allOption: 'All',
      usersCount: '{n} accounts',
      never: 'Never signed in',
      err_bad_tags: 'Invalid tags: at most 20 characters each and 10 tags, separated by commas',
      tagsColumn: 'Tags',
      editTags: 'Tags',
      noTags: '—',
      tagsPrompt: 'Tags for "{name}", separated by commas (leave empty to clear):',
      tagsSaved: 'Tags saved',
      bulkNeedTags: 'Enter the tags first, separated by commas',
      bulkNoUsers: 'There are no students in the current list to change',
      bulkConfirmAdd: 'Add the tags "{tags}" to the {n} students in the current list?',
      bulkConfirmRemove: 'Remove the tags "{tags}" from the {n} students in the current list?',
      bulkDone: 'Changed {n} students'
    }
  };

  function lang() {
    return document.documentElement.lang.indexOf('en') === 0 ? 'en' : 'zh';
  }

  function t(key, vars) {
    var text = (TEXT[lang()] || TEXT.zh)[key];
    if (text === undefined) text = TEXT.zh[key] === undefined ? key : TEXT.zh[key];
    return String(text).replace(/\{(\w+)\}/g, function (all, name) {
      return vars && vars[name] !== undefined ? vars[name] : all;
    });
  }

  /* 服务端错误按 code 翻译成当前语言；没有对应项就退回服务端给的中文原文 */
  function errorText(err) {
    var code = err && err.code;
    if (code && TEXT.zh['err_' + code] !== undefined) return t('err_' + code);
    if (err && err.network) return t('err_network');
    return (err && err.message) || t('err_generic');
  }

  /* 登录后跳回哪里：只允许本站（wp-base 下）的路径，防止被人做成钓鱼跳转 */
  function safeNext(value) {
    value = String(value || '');
    var home = BASE + '/';
    if (value.indexOf(home) === 0 && /^[A-Za-z0-9_\-.\/?=&%]*$/.test(value) &&
        value.indexOf('..') < 0 && value.indexOf('//') < 0) return value;
    return home;
  }

  function here() { return location.pathname + location.search; }
  function queryNext() {
    var m = /[?&]next=([^&]*)/.exec(location.search);
    return safeNext(m ? decodeURIComponent(m[1]) : '');
  }
  function go(page, withNext) {
    location.replace(BASE + '/' + page + (withNext ? '?next=' + encodeURIComponent(here()) : ''));
  }

  var info = { enabled: false, user: null, guest: false };

  /* 角色：记在 <html> 的 class 和 sessionStorage 里。换页面时 <head> 里的脚本据此在页面画出来之前就设好，
     不会先闪一下教师版。服务器的答复回来后再校正一次。 */
  var ROLE_KEY = 'wp_role';
  var TEACHER_KEY = 'wp_teacher';       /* 登录着的老师（不是家庭版里没登录的访客）：首页直接跳去题库工作台 */
  function workbench() { return BASE + '/bank.html#banks'; }
  function setTeacher(on) {
    try { if (on) sessionStorage.setItem(TEACHER_KEY, '1'); else sessionStorage.removeItem(TEACHER_KEY); } catch (e) { }
  }
  /* 超级管理员（admin）和老师（teacher）在页面上都是「老师视图」：管理功能都在，只是老师只看得到自己名下的数据（服务端保证） */
  function isStaffRole(role) { return role === 'admin' || role === 'teacher'; }

  function setRole(role) {            /* role: 'admin' | 'teacher' | 'student' | '' (未知，清掉) */
    if (isStaffRole(role)) role = 'admin';
    var h = document.documentElement;
    h.classList.remove('role-pending', 'role-student', 'role-admin');
    if (role) h.classList.add(role === 'admin' ? 'role-admin' : 'role-student');
    try {
      if (role) sessionStorage.setItem(ROLE_KEY, role === 'admin' ? 'admin' : 'student');
      else sessionStorage.removeItem(ROLE_KEY);
    } catch (e) { }
    if (role !== 'admin') setTeacher(false);
  }

  function decorate(user) {
    document.body.classList.add('role-' + user.role);
    var controls = document.getElementById('portalHeaderControls');
    if (controls && !document.getElementById('userChip')) {
      var chip = document.createElement('div');
      chip.className = 'user-chip';
      chip.id = 'userChip';
      var name = document.createElement('a');
      name.className = 'user-name';
      name.href = BASE + '/change-password.html?next=' + encodeURIComponent(here());
      name.textContent = user.name;
      name.title = user.student_no + ' · ' + t('changePassword');
      var out = document.createElement('button');
      out.type = 'button';
      out.className = 'user-out';
      out.setAttribute('data-module-zh', TEXT.zh.signOut);
      out.setAttribute('data-module-en', TEXT.en.signOut);
      out.textContent = t('signOut');
      out.addEventListener('click', function () {
        out.disabled = true;
        API.post('/api/auth/logout', {}).catch(function () {}).then(function () { setRole(''); go(info.guest ? '' : 'login.html', false); });
      });
      chip.appendChild(name);
      chip.appendChild(out);
      controls.parentNode.insertBefore(chip, controls);
    }
    /* 学生只看得到选题库和玩：题库管理、生成离线页等带 admin-only 的东西都不显示。
       服务端本来就会拒绝，这里是不让他们看到用不了的入口。 */
    addLeaderboardLink();
    if (isStaffRole(user.role)) { hideHomeLink(); addNavLinks(user.role === 'admin'); }
  }

  /* 积分榜：登录的人都看得到（学生看本班，老师看自己的班）；排在「成绩记录」后面 */
  function addLeaderboardLink() {
    var nav = document.querySelector('.portal-nav');
    if (!nav || document.getElementById('leaderboardNavLink')) return;
    var link = document.createElement('a');
    link.id = 'leaderboardNavLink';
    link.href = BASE + '/leaderboard.html';
    link.setAttribute('data-module-zh', TEXT.zh.leaderboardLink);
    link.setAttribute('data-module-en', TEXT.en.leaderboardLink);
    link.textContent = t('leaderboardLink');
    nav.appendChild(link);
  }

  /* 老师登录后没有「首页」：题库工作台就是首页（首页和它的内容重复） */
  function hideHomeLink() {
    Array.prototype.forEach.call(document.querySelectorAll('.portal-nav a'), function (a) {
      if (a.getAttribute('href') === BASE + '/' && a.parentNode) a.parentNode.removeChild(a);
    });
  }

  /* 登录后去哪：默认回首页；老师的首页是题库工作台 */
  function landing(user) {
    var next = queryNext();
    return user && isStaffRole(user.role) && next === BASE + '/' ? workbench() : next;
  }

  /* 老师才用得到的两个入口：账号管理、访问记录 */
  function addNavLinks(isSuper) {
    var nav = document.querySelector('.portal-nav');
    if (nav && !document.getElementById('adminNavLink')) {
      var link = document.createElement('a');
      link.id = 'adminNavLink';
      link.href = BASE + '/admin.html';
      link.setAttribute('data-module-zh', TEXT.zh.adminLink);
      link.setAttribute('data-module-en', TEXT.en.adminLink);
      link.textContent = t('adminLink');
      if (location.pathname.slice(-10) === 'admin.html') link.className = 'active';     /* 只有账号管理页自己才高亮（题库工作台也是 data-auth=admin，不能按它判断） */
      nav.appendChild(link);
    }
    if (nav && !document.getElementById('visitsNavLink')) {
      var visits = document.createElement('a');
      visits.id = 'visitsNavLink';
      visits.href = BASE + '/visits.html';
      visits.setAttribute('data-module-zh', TEXT.zh.visitsLink);
      visits.setAttribute('data-module-en', TEXT.en.visitsLink);
      visits.textContent = t('visitsLink');
      if (document.body.getAttribute('data-auth') === 'visits') visits.className = 'active';
      nav.appendChild(visits);
    }
    if (nav && isSuper && !document.getElementById('tenantsNavLink')) {
      var tenants = document.createElement('a');
      tenants.id = 'tenantsNavLink';
      tenants.href = BASE + '/tenants.html';
      tenants.setAttribute('data-module-zh', TEXT.zh.tenantsLink);
      tenants.setAttribute('data-module-en', TEXT.en.tenantsLink);
      tenants.textContent = t('tenantsLink');
      if (document.body.getAttribute('data-auth') === 'super') tenants.className = 'active';
      nav.appendChild(tenants);
    }
  }

  /* 家庭版里还没登录的人：所有菜单都显示，右上角给一个「教师登录」；点到管理功能时才会被要求登录 */
  function decorateGuest() {
    addNavLinks();
    var controls = document.getElementById('portalHeaderControls');
    if (controls && !document.getElementById('teacherSignIn')) {
      var link = document.createElement('a');
      link.id = 'teacherSignIn';
      link.className = 'user-name';
      link.href = BASE + '/login.html?next=' + encodeURIComponent(here());
      link.setAttribute('data-module-zh', TEXT.zh.teacherSignIn);
      link.setAttribute('data-module-en', TEXT.en.teacherSignIn);
      link.textContent = t('teacherSignIn');
      var chip = document.createElement('div');
      chip.className = 'user-chip';
      chip.appendChild(link);
      controls.parentNode.insertBefore(chip, controls);
    }
  }

  var ready = API.get('/api/auth/me').then(function (res) {
    var mode = document.body.getAttribute('data-auth') || '';
    info = { enabled: !!res.auth_enabled, user: res.user || null, guest: !!res.guest_mode };
    if (!info.enabled) {
      setRole('admin');                       /* 家庭版没有账号，等同老师 */
      if (mode === 'admin' || mode === 'visits' || mode === 'super' || mode === 'change') go('', false);
      return info;
    }
    if (!info.user && info.guest) {                /* 家庭版：不登录也能用，管理页才要登录 */
      if (mode === 'admin' || mode === 'visits' || mode === 'super' || mode === 'change') { setRole(''); go('login.html', true); return info; }
      if (mode === 'public') document.documentElement.classList.remove('role-pending');
      else { setRole('admin'); setTeacher(false); decorateGuest(); }
      return info;
    }
    if (!info.user) {
      setRole('');
      if (mode === 'public') document.documentElement.classList.remove('role-pending');
      else go('login.html', true);            /* 马上要跳走：页面保持不显示，免得先闪出内容 */
      return info;
    }
    setRole(info.user.role);
    if (isStaffRole(info.user.role)) setTeacher(true);
    if (info.user.must_change && mode !== 'change') { go('change-password.html', true); return info; }
    if (mode === 'public' && !info.user.must_change) { location.replace(landing(info.user)); return info; }
    if (isStaffRole(info.user.role) && document.body.getAttribute('data-page') === 'home') { location.replace(workbench()); return info; }
    if ((mode === 'admin' || mode === 'visits') && !isStaffRole(info.user.role)) { go('', false); return info; }
    if (mode === 'super' && info.user.role !== 'admin') { go(isStaffRole(info.user.role) ? 'bank.html#banks' : '', false); return info; }
    decorate(info.user);
    return info;
  }).catch(function () {
    setRole('student');                       /* 问不到服务器：按学生视图显示，总比一直空白、或露出教师控件好 */
    return info;
  });

  global.AuthUI = {
    ready: ready,
    t: t,
    errorText: errorText,
    safeNext: safeNext,
    queryNext: queryNext,
    landing: landing,
    go: go,
    info: function () { return info; },
    /* 家庭版没有账号，等同管理员（行为不变） */
    isAdmin: function () { return !info.enabled || (info.guest && !info.user) || !!(info.user && isStaffRole(info.user.role)); },
    /* 超级管理员（能加老师、共享 / 分配、恢复删除）；家庭版没有账号体系时也算 */
    isSuper: function () { return !info.enabled || !!(info.user && info.user.role === 'admin'); },
    TEXT: TEXT
  };
})(window);
