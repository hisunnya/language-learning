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
      var name = b.category || (AuthUI.info().public ? b.level1 : '') || '';     /* 公开版：没分类的按学段（初中 / 高中）分组 */
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

  /* 游戏类型：中英配对（原来的）、单词大比拼、排排坐。每个题库只属于一种 */
  var TYPES = ['match', 'spell', 'order'];
  var PAGES = { match: '/play.html', spell: '/spell.html', order: '/order.html' };
  function typeOf(b) { return TYPES.indexOf(b.game_type) >= 0 ? b.game_type : 'match'; }
  function typeFromHash() { var m = /type=(\w+)/.exec(location.hash); return m && TYPES.indexOf(m[1]) >= 0 ? m[1] : ''; }
  var chosen = typeFromHash();

  function itemCounts(b) {
    return t('home_itemCounts', { n: b.word_count, time: API.fmtTime(b.created_at) });
  }

  function bankItem(b, extra, withType) {
    var type = typeOf(b);
    var ops = type === 'match'
      ? '<a class="btn sm ghost" href="' + esc(API.path('/practice.html?bank=' + b.id)) + '">' + esc(t('bank_practice')) + '</a>' +
        '<a class="btn sm" href="' + esc(API.path('/play.html?bank=' + b.id)) + '">' + esc(t('home_play')) + '</a>'
      : '<a class="btn sm" href="' + esc(API.path(PAGES[type] + '?bank=' + b.id)) + '">' + esc(t('home_start')) + '</a>';
    return '<div class="item">' +
      '  <div class="main">' + (withType ? '<span class="pill type">' + esc(t('type_' + type)) + '</span> ' : '') +
      '<b>' + esc(b.title) + '</b> <small>' + esc(extra || (type === 'match' ? counts(b) : itemCounts(b))) + '</small></div>' +
      '  <div class="ops">' + ops + '</div></div>';
  }

  /* 先选玩法：登录的学生三种玩法都看得到（没开放题库的也显示，点进去提示「暂未开放」，先让他们知道有这些玩法）；
     公开版 /words/ 只有中英配对，就不显示选择。选过的记在地址的 #type= 里，从游戏返回时还是这一种 */
  function countOf(type) { return banks.filter(function (b) { return typeOf(b) === type; }).length; }
  function availableTypes() {
    if (AuthUI.info().public) return TYPES.filter(function (type) { return countOf(type) > 0; });
    return TYPES;
  }
  function renderTypes() {
    var box = document.getElementById('typeCards');
    var types = availableTypes();
    if (types.length <= 1) { box.hidden = true; chosen = types[0] || 'match'; return; }
    if (types.indexOf(chosen) < 0) chosen = '';
    box.hidden = false;
    box.innerHTML = types.map(function (type) {
      var n = countOf(type);
      return '<button type="button" class="type-card t-' + type + (type === chosen ? ' on' : '') + (n ? '' : ' empty') + '" data-type="' + type +
        '" aria-pressed="' + (type === chosen) + '">' +
        '<b>' + esc(t('type_' + type)) + '</b><small>' + esc(t('type_' + type + 'Desc')) + '</small>' +
        '<span class="tc-foot"><span class="pill gray">' + esc(n ? t('type_count', { n: n }) : t('type_soon')) + '</span>' +
        '<span class="tc-go">' + esc(t('type_go')) + '</span></span></button>';
    }).join('');
  }

  /* 每本书（分类）一个色块：带名字的书用主色标题条，「其他」用灰色标题条，一眼分得开 */
  function renderBanks() {
    var box = document.getElementById('bankList');
    var student = isStudentView();
    renderTypes();
    if (!chosen) { box.innerHTML = '<div class="empty">' + esc(t('type_pick')) + '</div>'; return; }
    var shown = banks.filter(function (b) { return typeOf(b) === chosen; });
    if (!shown.length) {
      var many = !document.getElementById('typeCards').hidden;
      box.innerHTML = '<div class="empty">' + esc(t(many ? 'type_none' : (student ? 'home_emptyStudent' : 'home_emptyTeacher'))) + '</div>';
      return;
    }
    box.innerHTML = groupByCategory(shown).map(function (g) {
      return '<section class="bank-group' + (g.name ? '' : ' other') + '">' +
        '<div class="bank-group-head"><b>' + esc(g.name || t(student ? 'home_catOther' : 'home_catNone')) + '</b>' +
        '<span class="pill gray">' + esc(t(g.banks.length === 1 ? 'home_groupCountOne' : 'home_groupCount', { n: g.banks.length })) + '</span></div>' +
        g.banks.map(function (b) { return bankItem(b); }).join('') + '</section>';
    }).join('');
  }

  /* 最近玩过：登录的账号取服务器上的记录（换设备也看得到）；没登录的访客、或者服务器取不到时，用这台设备上记的。
     都只显示现在还看得到的题库，最多 4 个 */
  var recent = [];
  function loadRecent() {
    var local = function () { return WPRecent.list(localStorage, WPRecent.userKey(AuthUI.info()), banks, 4); };
    if (!AuthUI.info().user) { recent = local(); return Promise.resolve(); }
    return API.get('/api/recent?limit=4').then(function (res) {
      recent = (res.recent || []).map(function (x) { return { bank: x.bank, t: x.last_at * 1000 }; });
    }).catch(function () { recent = local(); });
  }

  function renderRecent() {
    var card = document.getElementById('recentCard');
    var items = loaded ? recent : [];
    card.hidden = !items.length;
    var now = Date.now();
    document.getElementById('recentList').innerHTML = items.map(function (x) {
      var a = WPRecent.ago(x.t, now);
      return bankItem(x.bank, t('home_recentMeta', { ago: t(a.key, { n: a.n }), words: x.bank.word_count }), availableTypes().length > 1);
    }).join('');
  }

  function loadBanks() {
    return AuthUI.ready.then(function () { return API.get('/api/banks'); }).then(function (res) {
      banks = res.banks || [];
      loaded = true;
      renderBanks();
      return loadRecent().then(renderRecent);
    }).catch(function (e) { API.toast(e.message); });
  }

  /* 切换语言：列表是脚本画的，要重画（静态文字由页眉换） */
  WPI18N.onChange(function () { if (loaded) { renderBanks(); renderRecent(); } });

  document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('typeCards').addEventListener('click', function (ev) {
      var card = ev.target.closest('[data-type]');
      if (!card) return;
      chosen = card.getAttribute('data-type');
      history.replaceState(null, '', '#type=' + chosen);
      renderBanks();
    });
    API.get('/api/meta').then(function (meta) {
      var c = meta.curriculum || {};
      document.getElementById('curTotal').textContent = c.word_total || '—';
      document.getElementById('curUnits').textContent = c.unit_total || '—';
    }).catch(function () { });
    loadBanks();
  });
})();
