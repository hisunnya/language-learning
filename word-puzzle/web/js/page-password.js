/* page-password.js —— 修改密码（首次登录必须改；之后也可以主动改） */
(function () {
  'use strict';

  /* 和服务端 password_problem 同一套规则，先在本地提示，省得来回一趟 */
  function problem(oldPw, newPw, studentNo) {
    if (newPw.length < 8) return 'pwTooShort';
    if (newPw === oldPw) return 'pwSame';
    if (studentNo && newPw.toLowerCase().indexOf(studentNo.toLowerCase()) >= 0) return 'pwHasNumber';
    var kinds = (/[a-z]/.test(newPw) ? 1 : 0) + (/[A-Z]/.test(newPw) ? 1 : 0) +
      (/[0-9]/.test(newPw) ? 1 : 0) + (/[^A-Za-z0-9]/.test(newPw) ? 1 : 0);
    return kinds < 2 ? 'pwNeedMix' : '';
  }

  document.addEventListener('DOMContentLoaded', function () {
    var form = document.getElementById('changeForm');
    var msg = document.getElementById('changeMsg');
    var btn = document.getElementById('btnChange');
    var student = '';

    AuthUI.ready.then(function (info) {
      if (info.user) {
        student = info.user.student_no;
        // 已经改过密码的人是主动来改的，给他一个退路；首次登录的人没有退路
        document.getElementById('cancelLink').hidden = !!info.user.must_change;
      }
    });

    form.addEventListener('submit', function (event) {
      event.preventDefault();
      var oldPw = document.getElementById('oldPassword').value;
      var newPw = document.getElementById('newPassword').value;
      var again = document.getElementById('newPassword2').value;
      var key = problem(oldPw, newPw, student);
      if (!key && newPw !== again) key = 'pwMismatch';
      if (key) {
        API.msg(msg, AuthUI.t(key), 'err');
        return;
      }
      btn.disabled = true;
      btn.textContent = AuthUI.t('saving');
      API.post('/api/auth/change-password', { old_password: oldPw, new_password: newPw }).then(function () {
        API.msg(msg, AuthUI.t('passwordChanged'), 'ok');
        setTimeout(function () { location.replace(AuthUI.queryNext()); }, 700);
      }).catch(function (err) {
        API.msg(msg, AuthUI.errorText(err), 'err');
        btn.disabled = false;
        btn.textContent = AuthUI.t('savePassword');
      });
    });
  });
})();
