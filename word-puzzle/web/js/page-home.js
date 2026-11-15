/* ============================================================
   page-home.js —— 首页：选一个题库开始玩
   ------------------------------------------------------------
   首页只做「选题库、玩」。新建、分类、标签、批量开放、删除、离线测试都在「题库工作台」
   （老师才看得到入口）。学生只看得到老师开放给自己的题库。
   ============================================================ */
(function () {
  'use strict';

  var banks = [];
  var loaded = false;      /* 题库列表取回来之前，别把「加载中…」换成「还没有题库」 */

  function esc(s) { return API.esc(s); }
  function t(key, params) { return WPI18N.t(key, params); }

  function counts(b) {
    return t('home_counts', { words: b.word_count, units: b.unit_count, time: API.fmtTime(b.created_at) });
  }

  function isStudentView() {
    return !AuthUI.isAdmin();
  }

  /* 按分类分组：分类按名字排，没分类的放最后 */
  function groupByCategory(list) {
    var groups = {}, names = [];
    list.forEach(function (b) {
      var name = b.category || '';
      if (!groups[name]) { groups[name] = []; names.push(name); }
      groups[name].push(b);
    });
    names.sort(function (a, b) {
      if (!a) return 1;
      if (!b) return -1;
      return a < b ? -1 : a > b ? 1 : 0;
    });
    return names.map(function (name) {
      var list = groups[name].slice();
      /* 按单元顺序排（seq 是第几单元）；没有 seq 的老题库保持原来的先后 */
      if (list.some(function (b) { return b.seq > 0; })) {
        list = list.map(function (b, i) { return { b: b, i: i }; }).sort(function (x, y) {
          var a = x.b.seq > 0 ? x.b.seq : 1e9, c = y.b.seq > 0 ? y.b.seq : 1e9;
          return a - c || x.i - y.i;
        }).map(function (x) { return x.b; });
      }
      return { name: name, banks: list };
    });
  }

  function bankItem(b) {
    return '<div class="item">' +
      '  <div class="main"><b>' + esc(b.title) + '</b> <small>' + esc(counts(b)) + '</small></div>' +
      '  <div class="ops"><a class="btn sm" href="' + esc(API.path('/play.html?bank=' + b.id)) + '">' + esc(t('home_play')) + '</a></div></div>';
  }

  function renderBanks() {
    var box = document.getElementById('bankList');
    var student = isStudentView();
    if (!banks.length) {
      box.innerHTML = '<div class="empty">' + esc(t(student ? 'home_emptyStudent' : 'home_emptyTeacher')) + '</div>';
      return;
    }
    box.innerHTML = groupByCategory(banks).map(function (g) {
      var head = '<div class="sub" style="margin:14px 0 4px"><b>' + esc(g.name || t(student ? 'home_catOther' : 'home_catNone')) + '</b></div>';
      return head + g.banks.map(bankItem).join('');
    }).join('');
  }

  function loadBanks() {
    return AuthUI.ready.then(function () { return API.get('/api/banks'); }).then(function (res) {
      banks = res.banks || [];
      loaded = true;
      renderBanks();
    }).catch(function (e) { API.toast(e.message); });
  }

  /* 切换语言：列表是脚本画的，要重画（静态文字由页眉换） */
  WPI18N.onChange(function () { if (loaded) renderBanks(); });

  document.addEventListener('DOMContentLoaded', function () {
    API.get('/api/meta').then(function (meta) {
      var c = meta.curriculum || {};
      document.getElementById('curTotal').textContent = c.word_total || '—';
      document.getElementById('curUnits').textContent = c.unit_total || '—';
    }).catch(function () { });
    loadBanks();
  });
})();
