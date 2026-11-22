/* ============================================================
   module-progress.js —— 静态模块向总后台上报练习小结
   ------------------------------------------------------------
   化学、物理、每日话题、无线电执照这四个模块是纯前端的（数据在 localStorage），
   老师却要在总后台（/backends/）看到「谁练了多少」——所以它们把小结报给后端，
   后端存进 subject_records，老师在总后台就能看到。

   用法（页面里）：
     <meta name="wp-base" content="/word-puzzle">     后端接口前缀
     <meta name="wp-module" content="chemistry">      模块 id（server/modules.py 登记的那个）
     <script src="/shared/module-progress.js"></script>

   页面里上报：
     WPModule.setSummary(function () { return {score: 30, questions: 6}; });
     WPModule.reportNow();                  // 立刻报一次

   没登录就悄悄不报：这些模块不要求登录，报不上去也不该影响练习本身。
   ============================================================ */
(function (global) {
  'use strict';

  var COPY = {
    zh: {
      signedIn: '已登录：{name}',
      signIn: '登录后保存成绩',
      staff: '老师视图',
      done: '已保存'
    },
    en: {
      signedIn: 'Signed in: {name}',
      signIn: 'Sign in to save progress',
      staff: 'Staff view',
      done: 'Saved'
    }
  };

  function meta(name) {
    var node = document.querySelector('meta[name="' + name + '"]');
    return node ? String(node.content || '') : '';
  }

  var base = meta('wp-base').replace(/\/$/, '');
  var subject = meta('wp-module');
  var user = null;
  var summaryFn = null;
  var lastPayload = null;

  function lang() { return document.documentElement.lang.indexOf('en') === 0 ? 'en' : 'zh'; }
  function copy() { return COPY[lang()]; }

  function post(payload) {
    if (!base || !subject || !user) return Promise.resolve(false);
    var text = JSON.stringify({ subject: subject, kind: 'practice', payload: payload });
    return fetch(base + '/api/records', {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      body: text
    }).then(function (response) {
      return response.ok;
    }).catch(function () {
      return false;
    });
  }

  /* 页眉右上角的身份条：登录了显示是谁，没登录提示「登录后才保存成绩」 */
  function chip() {
    var host = document.getElementById('portalHeaderControls');
    if (!host) return;
    var old = document.getElementById('moduleIdentity');
    if (old) old.remove();
    var link = document.createElement('a');
    link.id = 'moduleIdentity';
    link.className = 'module-identity';
    var text = copy();
    if (user) {
      var staff = user.role === 'teacher' || user.role === 'admin';
      link.textContent = text.signedIn.replace('{name}', user.name || user.student_no || '') + (staff ? ' · ' + text.staff : '');
      link.href = staff ? '/backends/' : '/word-puzzle/stats.html';
    } else {
      link.textContent = text.signIn;
      link.href = '/word-puzzle/login.html';
    }
    host.insertBefore(link, host.firstChild);
  }

  function loadUser() {
    if (!base) return Promise.resolve(null);
    return fetch(base + '/api/auth/me', { credentials: 'same-origin' })
      .then(function (response) { return response.ok ? response.json() : null; })
      .then(function (body) {
        if (body && body.ok && body.user) user = body.user;
        return user;
      })
      .catch(function () { return null; });
  }

  global.WPModule = {
    /* 页面用它给出「这次练习的总结」；没设置就不上报。 */
    setSummary: function (fn) { summaryFn = fn; },
    /* 立刻报一次小结。 */
    reportNow: function () {
      if (!summaryFn) return Promise.resolve(false);
      var payload;
      try { payload = summaryFn(); } catch (e) { return Promise.resolve(false); }
      if (!payload) return Promise.resolve(false);
      lastPayload = payload;
      return post(payload);
    },
    /* 最近一次上报的内容（调试和测试用）。 */
    last: function () { return lastPayload; },
    user: function () { return user; }
  };

  function init() {
    chip();
    loadUser().then(function () {
      chip();
      if (summaryFn) global.WPModule.reportNow();
    });
    global.addEventListener('portal-lang-change', function () { chip(); });
    /* 离开页面时把还没报的小结补报一次（sendBeacon 在页面关闭时最可靠）。 */
    global.addEventListener('pagehide', function () {
      if (!summaryFn || !user || !base || !subject) return;
      var payload;
      try { payload = summaryFn(); } catch (e) { return; }
      if (!payload) return;
      var text = JSON.stringify({ subject: subject, kind: 'practice', payload: payload });
      try {
        if (global.navigator && navigator.sendBeacon) {
          navigator.sendBeacon(base + '/api/records', new Blob([text], { type: 'application/json' }));
          return;
        }
      } catch (e) { /* 浏览器不让用 beacon 就算了 */ }
      post(payload);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})(window);
