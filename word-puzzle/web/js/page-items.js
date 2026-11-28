/* ============================================================
   page-items.js —— 新题型网站页面共用
   从 /api/banks/{id} 取题库；动词猎手把整套题作为一局。
   翻译排排坐的录音交给 /api/recordings，服务器识别后给分；成绩交给 /api/scores（分数由服务器重新算）。
   ============================================================ */
(function () {
  'use strict';

  var GAME = document.body.getAttribute('data-game');           /* spell | order | verb */
  var PAGES = { match: '/play.html', spell: '/spell.html', order: '/order.html', verb: '/verb.html' };
  var I18N_PREFIX = { spell: 'sp', order: 'or', verb: 'vh' };
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
    document.title = t(I18N_PREFIX[GAME] + '_docTitle', { title: bank.title });
    $('igTitle').textContent = bank.title;
    $('igSub').textContent = GAME === 'verb'
      ? t('vh_startInfo', { n: groups.reduce(function (sum, group) { return sum + group.items.length; }, 0) })
      : t(I18N_PREFIX[GAME] + '_rules');
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

  var current = 0, verbItems = [], verbOrds = [], verbChoices = [];
  function ordsOf(k) {
    var start = 0;
    for (var j = 0; j < k; j++) start += groups[j].items.length;
    return groups[k].items.map(function (_, i) { return start + i; });
  }

  function start(k) {
    current = k;
    var ords = GAME === 'spell' ? verbOrds : ordsOf(k);
    var cfg = {
      items: GAME === 'spell' ? verbItems : groups[k].items, ords: ords, backHref: home(), playToken: token,
      begin: function (meta) { return WPAdapter.begin(meta, { bank_id: bank.id }); },
      progress: function (report) { return WPAdapter.progress(report); },
      phase: WPAdapter.phase,
      recording: WPAdapter.recording,
      save: function (report) { return WPAdapter.save(report, { bank_id: bank.id, title: bank.title }); }
    };
    if (GAME === 'verb') {
      cfg.items = verbItems;
      cfg.ords = verbOrds;
      cfg.choices = verbChoices;
      cfg.levelCount = groups.length;
      try {
        game = WPVerbUI.start($('igMount'), cfg);
      } catch (e) {
        if (e.message === 'verb_choices_invalid') fail('vh_dataError');
        else throw e;
      }
      return;
    }
    cfg.audioUrl = function (i) { return API.path('/api/banks/' + bank.id + '/items/' + ords[i] + '/audio'); };
    if (GAME === 'order' && AuthUI.info().user) cfg.upload = upload;
    var ui = GAME === 'spell' ? WPSpellUI : WPOrderUI;
    game = ui.start($('igMount'), cfg);
  }

  function pickVerb() {
    if (!verbItems.length) return;
    var button = $('igStart');
    if (!button) {
      $('igMount').innerHTML = '<div class="card"><button type="button" class="btn" id="igStart"></button></div>';
      button = $('igStart');
    }
    button.textContent = t('home_play');
    button.hidden = false;
    button.onclick = function () {
      button.hidden = true;
      start(0);
    };
  }

  function pickLevel() {
    $('igMount').innerHTML = '<div class="card"><h2>' + API.esc(t('ig_pickLevel')) + '</h2><div class="list">' +
      groups.map(function (g, k) {
        return '<div class="item"><div class="main"><b>' + API.esc(WPItemCore.levelName(g, k, t)) + '</b> <small>' +
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
    if (!game && (GAME === 'verb' || GAME === 'spell')) pickVerb();
    else if (!game && groups.length > 1) pickLevel();
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
      if (GAME === 'verb' || GAME === 'spell') {
        groups.forEach(function (group, level) {
          var groupOrds = ordsOf(level);
          group.items.forEach(function (item, i) {
            verbItems.push(item);
            verbOrds.push(groupOrds[i]);
          });
        });
        if (GAME === 'verb') verbChoices = (verbItems[0].choices || []).slice();
      }
      var info = AuthUI.info();
      if (info.user) API.post('/api/recent', { bank_id: id }).catch(function () { });
      try { WPRecent.add(localStorage, WPRecent.userKey(info), id, Date.now()); } catch (e) { }
      if (GAME === 'verb' || GAME === 'spell') pickVerb();
      else if (groups.length > 1) pickLevel();
      else start(0);
    }).catch(function (e) { fail('', e.message || t('ig_loadFail')); });
  });
})();
