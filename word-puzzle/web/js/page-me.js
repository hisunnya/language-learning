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

  function tierName(tier) { return t('me_tier_' + tier); }

  function renderProfile() {
    if (!user) return;
    $('meAvatar').textContent = (user.name || '?').slice(-2);
    $('meName').textContent = user.name || '';
    $('meMeta').textContent = [user.class_name, user.student_no].filter(Boolean).join(' · ');
  }

  function renderBadges() {
    var box = $('meBadges');
    if (!awards.length) { box.innerHTML = '<div class="empty">' + esc(t('me_noBadges')) + '</div>'; return; }
    var seen = {}, list = [];
    awards.forEach(function (a) {
      var k = a.game + '|' + a.days;
      if (!seen[k]) { seen[k] = { award: a, n: 0 }; list.push(seen[k]); }
      seen[k].n++;
    });
    list.sort(function (x, y) { return y.award.days - x.award.days; });
    box.innerHTML = list.map(function (x) {
      return '<div class="aw-cell">' + WPAwards.badge(x.award, 88) + '<b>' + esc(tierName(x.award.tier)) + (x.n > 1 ? ' ×' + x.n : '') + '</b>' +
        '<small>' + esc(WPAwards.gameName(x.award.game, WPI18N.lang()) + ' · ' + t('me_daysTop', { n: x.award.days })) + '</small></div>';
    }).join('');
  }

  function renderList() {
    var box = $('meCerts');
    if (!awards.length) { box.innerHTML = '<div class="empty">' + esc(t('me_noCerts')) + '</div>'; return; }
    box.innerHTML = awards.map(function (a, i) {
      return '<div class="item aw-row' + (a.seen ? '' : ' is-new') + '"><div class="aw-row-badge">' + WPAwards.badge(a, 46) + '</div>' +
        '<div class="main"><b>' + esc(t('me_certTitle', { tier: tierName(a.tier), game: WPAwards.gameName(a.game, WPI18N.lang()), n: a.days })) + '</b>' +
        (a.seen ? '' : ' <span class="pill good">' + esc(t('me_new')) + '</span>') +
        '<small>' + esc((a.board_label ? a.board_label + ' · ' : '') + a.start_day + ' — ' + a.end_day + ' · ' + a.serial) + '</small></div>' +
        '<div class="ops"><button type="button" class="btn sm" data-view="' + i + '">' + esc(t('me_view')) + '</button>' +
        '<button type="button" class="btn sm ghost" data-save="' + i + '" data-type="png">PNG</button>' +
        '<button type="button" class="btn sm ghost" data-save="' + i + '" data-type="jpeg">JPG</button></div></div>';
    }).join('');
  }

  function view(a) {
    var box = $('meModal');
    box.hidden = false;
    $('meModalImg').removeAttribute('src');
    $('meModalMsg').textContent = t('me_drawing');
    WPAwards.render(a).then(function (canvas) {
      $('meModalImg').src = canvas.toDataURL('image/png');
      $('meModalImg').alt = t('me_certTitle', { tier: tierName(a.tier), game: WPAwards.gameName(a.game, WPI18N.lang()), n: a.days });
      $('meModalMsg').textContent = t('me_longPress');
    });
    $('meModalPng').onclick = function () { WPAwards.save(a, 'png'); };
    $('meModalJpg').onclick = function () { WPAwards.save(a, 'jpeg'); };
  }

  function render() { renderProfile(); renderBadges(); renderList(); }

  WPI18N.onChange(render);

  document.addEventListener('DOMContentLoaded', function () {
    $('meCerts').addEventListener('click', function (ev) {
      var b = ev.target.closest('button');
      if (!b) return;
      if (b.hasAttribute('data-view')) view(awards[+b.getAttribute('data-view')]);
      if (b.hasAttribute('data-save')) {
        b.disabled = true;
        WPAwards.save(awards[+b.getAttribute('data-save')], b.getAttribute('data-type')).then(function () { b.disabled = false; });
      }
    });
    $('meModalClose').onclick = function () { $('meModal').hidden = true; };
    $('meModal').addEventListener('click', function (ev) { if (ev.target === $('meModal')) $('meModal').hidden = true; });
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
