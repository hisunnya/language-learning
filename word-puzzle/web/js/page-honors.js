/* ============================================================
   page-honors.js —— 「成绩记录」页上的荣誉部分
   * 学生：我的荣誉（徽章墙 + 奖状列表，查看 / 下载 PNG / JPG），和「我的」页面是同一套（awards-ui.js）；
   * 老师、超管：名下学生的奖状（按班级筛选，每张都能查看、下载），以及用示例姓名的样张预览；
   * 公开版 /words/ 没有账号，什么都不显示。
   ============================================================ */
(function () {
  'use strict';

  function t(key, params) { return WPI18N.t(key, params); }
  function $(id) { return document.getElementById(id); }
  var mine = [], students = [], classes = [], samples = [], picked = '';

  function renderMine() {
    $('honorBadges').innerHTML = WPAwards.wall(mine);
    $('honorCerts').innerHTML = mine.length ? WPAwards.rows(mine) : '';
  }

  function renderStaff() {
    var select = $('awClass');
    select.innerHTML = '<option value="">' + API.esc(t('me_allClasses')) + '</option>' + classes.map(function (c) {
      return '<option value="' + API.esc(c) + '">' + API.esc(c) + '</option>';
    }).join('');
    select.value = picked;
    $('awCount').textContent = students.length ? t('me_staffCount', { n: students.length }) : '';
    $('staffAwards').innerHTML = WPAwards.rows(students, { who: true, empty: 'me_staffEmpty' });
    if (!$('awSamples').hidden) {
      $('awSampleBadges').innerHTML = WPAwards.wall(samples);
      $('awSampleCerts').innerHTML = WPAwards.rows(samples);
    }
  }

  function loadStaff() {
    return API.get('/api/admin/awards' + (picked ? '?class_name=' + encodeURIComponent(picked) : '')).then(function (res) {
      students = res.awards || [];
      classes = res.classes || [];
      renderStaff();
    }).catch(function (e) { $('staffAwards').innerHTML = '<div class="empty">' + API.esc(AuthUI.errorText(e)) + '</div>'; });
  }

  WPI18N.onChange(function () {
    if (!$('honorsCard').hidden) renderMine();
    if (!$('staffAwardsCard').hidden) { samples = WPAwards.samples(samples.length ? samples[0].teacher : ''); renderStaff(); }
  });

  document.addEventListener('DOMContentLoaded', function () {
    WPAwards.bind($('honorCerts'), function () { return mine; });
    WPAwards.bind($('staffAwards'), function () { return students; });
    WPAwards.bind($('awSampleCerts'), function () { return samples; });
    AuthUI.ready.then(function (info) {
      if (info.public || !info.user) return;
      if (AuthUI.isAdmin()) {
        $('staffAwardsCard').hidden = false;
        samples = WPAwards.samples(info.user.name);
        $('awSampleBtn').onclick = function () {
          var box = $('awSamples');
          box.hidden = !box.hidden;
          renderStaff();
        };
        $('awClass').onchange = function () { picked = this.value; loadStaff(); };
        return loadStaff();
      }
      $('honorsCard').hidden = false;
      return API.get('/api/awards').then(function (res) {
        mine = res.awards || [];
        renderMine();
        if (res.unseen) API.post('/api/awards/seen', {}).catch(function () { });
      });
    }).catch(function () { });
  });
})();
