/* ============================================================
   page-practice.js —— 读音练习（网站版）
   从 /api/banks/{id} 取题库，交给 practice-ui.js；老师多一个「下载离线版」（语音内嵌的单个 HTML）。
   ============================================================ */
(function () {
  'use strict';

  function t(key, params) { return WPI18N.t(key, params); }
  function $(id) { return document.getElementById(id); }
  function qs(name) {
    var m = new RegExp('[?&]' + name + '=([^&]*)').exec(location.search);
    return m ? decodeURIComponent(m[1]) : '';
  }

  var view = null, bank = null, groups = [], failing = '';

  function say(text, kind) {
    var el = $('pracMsg');
    el.className = 'msg on ' + (kind || 'info');
    el.textContent = text;
  }

  function fail(key, raw) {
    failing = raw ? '' : key;
    $('pracMount').innerHTML = '<div class="empty">' + API.esc(raw || t(key)) + '</div>';
    $('pracToggle').hidden = true;
    $('pracOffline').hidden = true;
    $('pracGame').hidden = true;
  }

  function updateToggle() {
    if (view) $('pracToggle').textContent = t(view.allRevealed() ? 'prac_hideAll' : 'prac_showAll');
  }

  WPI18N.onChange(function () {
    if (failing) $('pracMount').innerHTML = '<div class="empty">' + API.esc(t(failing)) + '</div>';
    if (bank) {
      document.title = t('prac_title', { title: bank.title });
      $('pracTitle').textContent = t('prac_heading', { title: bank.title });
    }
    updateToggle();
  });

  function recordOpen(id) {
    var info = AuthUI.info();
    if (info.user) API.post('/api/recent', { bank_id: id }).catch(function () { });     /* 和玩游戏一样记进「最近玩过」 */
    try { WPRecent.add(localStorage, WPRecent.userKey(info), id, Date.now()); } catch (e) { }
  }

  function makeOffline(btn) {
    btn.disabled = true;
    say(t('prac_synth'), 'info');
    API.post('/api/banks/' + bank.id + '/offline', { kind: 'practice' }).then(function (res) {
      say(t('prac_generated', { name: res.filename }), 'ok');
      return API.download(res.url, res.filename).catch(function () { say(t('prac_dlBlocked'), 'err'); });
    }).catch(function (e) { say(e.message, 'err'); }).finally(function () { btn.disabled = false; });
  }

  document.addEventListener('DOMContentLoaded', function () {
    var id = qs('bank');
    if (!id) { fail('prac_noBank'); return; }
    AuthUI.ready.then(function () {
      var teacher = !!(AuthUI.info().user && AuthUI.info().user.role === 'admin');
      $('pracBack').href = API.path(teacher ? '/bank.html#banks' : '/');
      return API.get('/api/banks/' + encodeURIComponent(id));
    }).then(function (res) {
      bank = res.bank;
      if (bank.game_type === 'spell' || bank.game_type === 'order') {      /* 读音练习只有中英配对的题库有；新题型直接去玩 */
        location.replace(API.path('/' + bank.game_type + '.html?bank=' + bank.id));
        return;
      }
      groups = (res.groups || []).map(function (g) { return { unit: g.unit, words: g.words }; });
      if (!groups.length) { fail('prac_empty'); return; }
      document.title = t('prac_title', { title: bank.title });
      $('pracTitle').textContent = t('prac_heading', { title: bank.title });
      $('pracSub').textContent = [bank.level1, bank.level2, bank.level3, bank.level4].filter(Boolean).join(' · ');
      $('pracGame').href = API.path('/play.html?bank=' + bank.id);
      var player = WPPractice.createPlayer({ base: API.path('/api/audio/'), onError: function () { API.toast(t('prac_audioFail')); } });
      view = WPPractice.init({ mount: $('pracMount'), groups: groups, player: player });
      var flat = [];
      groups.forEach(function (g) { g.words.forEach(function (w) { flat.push(w.en); }); });
      player.prefetch(flat, 30);
      $('pracToggle').onclick = function () { view.revealAll(!view.allRevealed()); updateToggle(); };
      $('pracMount').addEventListener('click', updateToggle);
      $('pracMount').addEventListener('pointerup', function () { setTimeout(updateToggle, 0); });
      $('pracOffline').onclick = function () { makeOffline(this); };
      updateToggle();
      recordOpen(bank.id);
    }).catch(function (e) { fail('', e.message); });
  });
})();
