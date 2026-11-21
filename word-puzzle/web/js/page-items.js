/* ============================================================
   page-items.js —— 新题型的网站页面（spell.html 单词大比拼、order.html 排排坐 共用）
   从 /api/banks/{id} 取题库，题库分了几关就先选关；然后交给 spell-ui.js / order-ui.js。
   排排坐的录音交给 /api/recordings，服务器识别后给分；成绩交给 /api/scores（排排坐的分数由服务器重新算）。
   ============================================================ */
(function () {
  'use strict';

  var GAME = document.body.getAttribute('data-game');           /* spell | order */
  var PAGES = { match: '/play.html', spell: '/spell.html', order: '/order.html' };
  function t(key, params) { return WPI18N.t(key, params); }
  function $(id) { return document.getElementById(id); }
  function qs(name) {
    var m = new RegExp('[?&]' + name + '=([^&]*)').exec(location.search);
    return m ? decodeURIComponent(m[1]) : '';
  }
  function home() { return API.path('/') + '#type=' + GAME; }

  var bank = null, groups = [], failing = '', game = null;

  function fail(key, raw) {
    failing = raw ? '' : key;
    $('igMount').innerHTML = '<div class="card"><div class="empty">' + API.esc(raw || t(key)) + '</div></div>';
  }

  function heading() {
    if (!bank) return;
    document.title = t(GAME === 'spell' ? 'sp_docTitle' : 'or_docTitle', { title: bank.title });
    $('igTitle').textContent = bank.title;
    $('igSub').textContent = t(GAME === 'spell' ? 'sp_rules' : 'or_rules');
  }

  function token() {
    return 'p' + Date.now().toString(36) + Math.random().toString(36).slice(2, 10);
  }

  function upload(i, blob, mime, ms, playToken) {
    var fd = new FormData();
    fd.append('bank_id', String(bank.id));
    fd.append('item_ord', String(ordsOf(current)[i]));
    fd.append('play_token', playToken || '');
    fd.append('duration_ms', String(Math.round(ms || 0)));
    var ext = /mp4|aac|m4a/.test(mime) ? 'm4a' : /ogg/.test(mime) ? 'ogg' : 'webm';
    fd.append('file', blob, 'reading.' + ext);
    return API.upload('/api/recordings', fd).then(function (res) { return res.recording; });
  }

  var current = 0;
  function ordsOf(k) {
    var start = 0;
    for (var j = 0; j < k; j++) start += groups[j].items.length;
    return groups[k].items.map(function (_, i) { return start + i; });
  }

  function start(k) {
    current = k;
    var ords = ordsOf(k);
    var cfg = {
      items: groups[k].items, ords: ords, backHref: home(), playToken: token,
      audioUrl: function (i) { return API.path('/api/banks/' + bank.id + '/items/' + ords[i] + '/audio'); },
      save: function (report) { return WPAdapter.save(report, { bank_id: bank.id, title: bank.title }); }
    };
    if (GAME === 'order' && AuthUI.info().user) cfg.upload = upload;
    game = (GAME === 'spell' ? WPSpellUI : WPOrderUI).start($('igMount'), cfg);
  }

  function pickLevel() {
    $('igMount').innerHTML = '<div class="card"><h2>' + API.esc(t('ig_pickLevel')) + '</h2><div class="list">' +
      groups.map(function (g, k) {
        return '<div class="item"><div class="main"><b>' + API.esc(g.unit || t('ig_level', { n: k + 1 })) + '</b> <small>' +
          API.esc(t('ig_levelCount', { n: g.items.length })) + '</small></div><div class="ops"><button type="button" class="btn sm" data-level="' +
          k + '">' + API.esc(t('home_play')) + '</button></div></div>';
      }).join('') + '</div></div>';
    $('igMount').onclick = function (ev) {
      var b = ev.target.closest('[data-level]');
      if (b) { $('igMount').onclick = null; start(parseInt(b.getAttribute('data-level'), 10)); }
    };
  }

  WPI18N.onChange(function () {
    if (failing) fail(failing);
    heading();
    if (!game && groups.length > 1) pickLevel();
  });

  document.addEventListener('DOMContentLoaded', function () {
    $('igBack').href = home();
    var id = parseInt(qs('bank'), 10);
    if (!id) { fail('ig_noBank'); return; }
    AuthUI.ready.then(function () { return API.get('/api/banks/' + id); }).then(function (res) {
      bank = res.bank;
      if (bank.game_type !== GAME) { location.replace(API.path((PAGES[bank.game_type] || PAGES.match) + '?bank=' + id)); return; }
      groups = (res.groups || []).filter(function (g) { return g.items && g.items.length; });
      heading();
      if (!groups.length) { fail('ig_empty'); return; }
      var info = AuthUI.info();
      if (info.user) API.post('/api/recent', { bank_id: id }).catch(function () { });
      try { WPRecent.add(localStorage, WPRecent.userKey(info), id, Date.now()); } catch (e) { }
      if (groups.length > 1) pickLevel(); else start(0);
    }).catch(function (e) { fail('', e.message || t('ig_loadFail')); });
  });
})();
