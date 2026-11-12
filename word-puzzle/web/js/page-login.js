/* page-login.js —— 学号 + 密码登录 */
(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    var form = document.getElementById('loginForm');
    var msg = document.getElementById('loginMsg');
    var btn = document.getElementById('btnLogin');

    AuthUI.ready.then(function (info) {
      if (!info.enabled) {
        form.hidden = true;
        API.msg(msg, AuthUI.t('notEnabled'), 'info');
      }
    });

    form.addEventListener('submit', function (event) {
      event.preventDefault();
      var studentNo = document.getElementById('studentNo').value.trim();
      var password = document.getElementById('password').value;
      if (!studentNo || !password) {
        API.msg(msg, AuthUI.t('err_missing'), 'err');
        return;
      }
      btn.disabled = true;
      btn.textContent = AuthUI.t('signingIn');
      API.post('/api/auth/login', { student_no: studentNo, password: password }).then(function (res) {
        // 还没改初始密码就先去改；否则回到刚才想去的页面
        if (res.user.must_change) AuthUI.go('change-password.html', true);
        else location.replace(AuthUI.queryNext());
      }).catch(function (err) {
        document.getElementById('password').value = '';
        API.msg(msg, AuthUI.errorText(err), 'err');
        btn.disabled = false;
        btn.textContent = AuthUI.t('signIn');
      });
    });
  });
})();
