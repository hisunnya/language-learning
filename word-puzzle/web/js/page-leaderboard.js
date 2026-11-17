/* ============================================================
   page-leaderboard.js —— 积分榜（奖牌榜）
   ------------------------------------------------------------
   学生只看得到自己班的（服务端按账号定班级）；老师可以选班或看全部。前三名金银铜，4–10 名一行一个。
   名字来自名单，是外来内容，进页面前一律经过 API.esc 转义。
   ============================================================ */
(function () {
  'use strict';

  function esc(s) { return API.esc(s); }
  function t(key, params) { return WPI18N.t(key, params); }
  function $(id) { return document.getElementById(id); }

  var state = { period: 'all', cls: '', data: null, picked: false };

  /* 奖牌：金 / 银 / 铜，写死颜色（不跟配色走）。第一名带皇冠。 */
  var MEDAL = {
    1: { a: '#FFE680', b: '#F2B200', c: '#B87A00', ribbon: '#D9362B' },
    2: { a: '#F7F9FC', b: '#C4CBD6', c: '#8892A3', ribbon: '#2F6FD0' },
    3: { a: '#F8C79B', b: '#D08850', c: '#8E5428', ribbon: '#2E9A63' }
  };

  function medal(rank) {
    var m = MEDAL[rank];
    var g = 'lbMedalG' + rank;
    var crown = rank === 1
      ? '<path d="M16 12l6 7 6-10 6 10 6-7-2 13H18z" fill="#F2B200" stroke="#B87A00" stroke-width="1.2" stroke-linejoin="round"/>'
      : '';
    return '<svg class="lb-medal" viewBox="0 0 56 66" aria-hidden="true" focusable="false">' +
      '<defs><linearGradient id="' + g + '" x1="0" y1="0" x2="1" y2="1">' +
      '<stop offset="0" stop-color="' + m.a + '"/><stop offset="0.55" stop-color="' + m.b + '"/><stop offset="1" stop-color="' + m.c + '"/></linearGradient></defs>' +
      '<path d="M14 0h12l6 22H20z" fill="' + m.ribbon + '"/><path d="M42 0H30l-6 22h12z" fill="' + m.ribbon + '" opacity="0.82"/>' +
      '<circle cx="28" cy="42" r="20" fill="url(#' + g + ')" stroke="' + m.c + '" stroke-width="2"/>' +
      '<circle cx="28" cy="42" r="14.5" fill="none" stroke="' + m.c + '" stroke-opacity="0.55" stroke-width="1.5"/>' +
      '<text x="28" y="49" text-anchor="middle" font-size="20" font-weight="800" font-family="Arial,Helvetica,sans-serif" fill="#fff" stroke="' + m.c + '" stroke-width="0.8">' + rank + '</text>' +
      crown + '</svg>';
  }

  function points(n) { return '<b>' + esc(n) + '</b><small>' + esc(t('lb_unit')) + '</small>'; }
  function meTag(e) { return e && e.me ? '<span class="lb-tag">' + esc(t('lb_me')) + '</span>' : ''; }

  var showClass = false;        /* 老师看「全部学生」时才在名字旁边标班级；单个班的榜不用重复 */

  function slot(rank, e) {
    var cls = 'lb-slot lb-slot-' + rank + (e ? '' : ' lb-slot-empty') + (e && e.me ? ' is-me' : '');
    if (!e) {
      return '<div class="' + cls + '">' + medal(rank) + '<div class="lb-name">' + esc(t('lb_vacant')) + '</div></div>';
    }
    return '<div class="' + cls + '" aria-label="' + esc(t('lb_rankN', { n: e.rank })) + '">' + medal(e.rank) +
      '<div class="lb-name">' + esc(e.name) + meTag(e) + '</div>' +
      '<div class="lb-pts">' + points(e.points) + '</div>' +
      (showClass && e.class_name ? '<div class="lb-cls">' + esc(e.class_name) + '</div>' : '') + '</div>';
  }

  function title(d) {
    if (d.scope === 'staff') return d.class_name ? t('lb_title', { cls: d.class_name }) : t('lb_titleAll');
    return d.class_name ? t('lb_title', { cls: d.class_name }) : t('lb_titleMine');
  }

  function render() {
    var d = state.data;
    if (!d) return;
    showClass = d.scope === 'staff' && !d.class_name;
    $('lbTitle').textContent = title(d);
    document.title = title(d) + ' · ' + t('lb_site');
    var entries = d.entries || [];
    var empty = $('lbEmpty');
    $('lbPodium').hidden = !entries.length;
    $('lbList').hidden = !entries.length;
    empty.hidden = !!entries.length;
    if (!entries.length) {
      empty.innerHTML = esc(t(d.period === 'week' ? 'lb_emptyWeek' : 'lb_empty')) + ' <a href="' + esc(API.path('/')) + '">' + esc(t('lb_play')) + '</a>';
    }
    /* 领奖台：左银（第 2 名）、中金（第 1 名）、右铜（第 3 名）。并列时名次相同，按座位顺序摆。 */
    $('lbPodium').innerHTML = slot(2, entries[1]) + slot(1, entries[0]) + slot(3, entries[2]);
    var top = entries[0] ? entries[0].points : 1;
    $('lbList').innerHTML = entries.slice(3).map(function (e) {
      var width = Math.max(4, Math.round(100 * e.points / (top || 1)));
      return '<li class="lb-row' + (e.me ? ' is-me' : '') + '"><span class="lb-bar" style="width:' + width + '%"></span>' +
        '<span class="lb-rank">' + esc(e.rank) + '</span>' +
        '<span class="lb-who">' + esc(e.name) + meTag(e) + (showClass && e.class_name ? '<i>' + esc(e.class_name) + '</i>' : '') + '</span>' +
        '<span class="lb-score">' + points(e.points) + '</span></li>';
    }).join('');
    /* 我不在前十名：单独告诉我排第几 */
    var me = d.me, box = $('lbMe');
    var inTop = entries.some(function (e) { return e.me; });
    if (d.scope === 'class') {
      box.hidden = false;
      if (me && !inTop) box.textContent = t('lb_myRank', { rank: me.rank, n: me.points, total: d.total });
      else if (!me) box.textContent = t('lb_myNone');
      else box.hidden = true;
    } else {
      box.hidden = true;
    }
    renderClasses(d);
    ['lbAll', 'lbWeek'].forEach(function (id) {
      var on = $(id).getAttribute('data-period') === state.period;
      $(id).classList.toggle('active', on);
      $(id).setAttribute('aria-pressed', String(on));
    });
  }

  function renderClasses(d) {
    var box = $('lbClassBox');
    if (d.scope !== 'staff') { box.hidden = true; return; }
    box.hidden = false;
    var select = $('lbClass');
    var html = '<option value="">' + esc(t('lb_allClasses')) + '</option>' + (d.classes || []).map(function (c) {
      return '<option value="' + esc(c) + '">' + esc(c) + '</option>';
    }).join('');
    if (select.getAttribute('data-html') !== html) { select.innerHTML = html; select.setAttribute('data-html', html); }
    select.value = state.cls;
  }

  function load() {
    var url = '/api/leaderboard?period=' + state.period + (state.cls ? '&class_name=' + encodeURIComponent(state.cls) : '');
    return API.get(url).then(function (res) {
      /* 老师第一次进来：默认选第一个班（一个班一个榜），而不是把所有班混在一起 */
      if (res.scope === 'staff' && !state.picked && !state.cls && res.classes && res.classes.length) {
        state.picked = true;
        state.cls = res.classes[0];
        return load();
      }
      state.picked = true;
      state.data = res;
      render();
    }).catch(function (err) {
      $('lbPodium').hidden = true;
      $('lbList').hidden = true;
      $('lbEmpty').hidden = false;
      $('lbEmpty').textContent = AuthUI.errorText ? AuthUI.errorText(err) : err.message;
    });
  }

  WPI18N.onChange(render);

  document.addEventListener('DOMContentLoaded', function () {
    Array.prototype.forEach.call(document.querySelectorAll('.lb-seg-btn'), function (b) {
      b.addEventListener('click', function () {
        state.period = b.getAttribute('data-period');
        load();
      });
    });
    $('lbClass').addEventListener('change', function () { state.cls = this.value; state.picked = true; load(); });
    AuthUI.ready.then(load);
  });

  window.WPLeaderboard = { medal: medal, slot: slot, title: title };
})();
