/* ============================================================
   page-me.js —— 「我的」：个人信息、徽章、奖状（查看、下载 PNG / JPG）
   奖状由 awards-ui.js 在浏览器里画出来；微信里不能直接下载文件，所以「查看」会把奖状显示成图片，长按就能保存、转发。
   ============================================================ */
(function () {
  'use strict';

  function t(key, params) { return WPI18N.t(key, params); }
  function $(id) { return document.getElementById(id); }
  var esc = API.esc;
  var awards = [], user = null;

  function renderProfile() {
    if (!user) return;
    $('meAvatar').textContent = (user.name || '?').slice(-2);
    $('meName').textContent = user.name || '';
    $('meMeta').textContent = [user.class_name, user.student_no].filter(Boolean).join(' · ');
  }
  function renderBadges() { $('meBadges').innerHTML = WPAwards.wall(awards); }
  function renderList() { $('meCerts').innerHTML = WPAwards.rows(awards); }

  function render() { renderProfile(); renderBadges(); renderList(); }

  WPI18N.onChange(render);

  document.addEventListener('DOMContentLoaded', function () {
    WPAwards.bind($('meCerts'), function () { return awards; });
    AuthUI.ready.then(function (info) {
      user = info.user;
      $('mePassword').href = API.path('/change-password.html?next=' + encodeURIComponent(location.pathname));
      renderProfile();
      return API.get('/api/awards');
    }).then(function (res) {
      awards = res.awards || [];
      render();
      if (res.unseen) API.post('/api/awards/seen', {}).catch(function () { });
    }).catch(function (e) { $('meCerts').innerHTML = '<div class="empty">' + esc(AuthUI.errorText(e)) + '</div>'; });
  });
})();
