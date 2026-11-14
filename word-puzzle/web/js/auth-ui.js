/* ============================================================
   auth-ui.js —— 家庭版 / 班级版的登录态在页面里的体现
   ------------------------------------------------------------
   * 问一次 /api/auth/me，没登录就跳到登录页，还没改初始密码就跳到改密码页；
   * 顶部加「当前用户 + 退出」，管理员多一个「账号管理」入口；
   * 局域网版（没有登录功能）什么都不做，页面和以前完全一样；
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

  var info = { enabled: false, user: null };

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
        API.post('/api/auth/logout', {}).catch(function () {}).then(function () { go('login.html', false); });
      });
      chip.appendChild(name);
      chip.appendChild(out);
      controls.parentNode.insertBefore(chip, controls);
    }
    /* 学生只看得到选题库和玩：题库管理、生成离线页等带 admin-only 的东西都不显示。
       服务端本来就会拒绝，这里是不让他们看到用不了的入口。 */
    if (user.role !== 'admin') document.body.classList.add('role-student');
    var nav = document.querySelector('.portal-nav');
    if (nav && user.role === 'admin' && !document.getElementById('adminNavLink')) {
      var link = document.createElement('a');
      link.id = 'adminNavLink';
      link.href = BASE + '/admin.html';
      link.setAttribute('data-module-zh', TEXT.zh.adminLink);
      link.setAttribute('data-module-en', TEXT.en.adminLink);
      link.textContent = t('adminLink');
      if (document.body.getAttribute('data-auth') === 'admin') link.className = 'active';
      nav.appendChild(link);
    }
  }

  var ready = API.get('/api/auth/me').then(function (res) {
    var mode = document.body.getAttribute('data-auth') || '';
    info = { enabled: !!res.auth_enabled, user: res.user || null };
    if (!info.enabled) {
      if (mode === 'admin' || mode === 'change') go('', false);
      return info;
    }
    if (!info.user) {
      if (mode !== 'public') go('login.html', true);
      return info;
    }
    if (info.user.must_change && mode !== 'change') { go('change-password.html', true); return info; }
    if (mode === 'public' && !info.user.must_change) { location.replace(queryNext()); return info; }
    if (mode === 'admin' && info.user.role !== 'admin') { go('', false); return info; }
    decorate(info.user);
    return info;
  }).catch(function () { return info; });

  global.AuthUI = {
    ready: ready,
    t: t,
    errorText: errorText,
    safeNext: safeNext,
    queryNext: queryNext,
    go: go,
    info: function () { return info; },
    /* 局域网版没有账号，等同管理员（行为不变） */
    isAdmin: function () { return !info.enabled || (info.user && info.user.role === 'admin'); },
    TEXT: TEXT
  };
})(window);
