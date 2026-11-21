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

  var state = { period: 'all', cls: '', game: 'all', data: null, picked: false };

  /* 奖牌：金 / 银 / 铜，拉丝金属质感（写死颜色，不跟配色走）：双圈圆盘 + 深色丝带 + 衬线数字。 */
  var MEDAL = {
    1: { a: '#FFF3C6', b: '#E9B94B', c: '#9A6D14', ink: '#5a3d00', ring: '#FFE9A0' },
    2: { a: '#FFFFFF', b: '#C9D2E0', c: '#7C889C', ink: '#3b4658', ring: '#F2F5FA' },
    3: { a: '#FFDFC4', b: '#D58F5B', c: '#8A4F26', ink: '#5a2c10', ring: '#F5C09C' }
  };

  function medal(rank) {
    var m = MEDAL[rank];
    var g = 'lbMedalG' + rank;
    return '<svg class="lb-medal" viewBox="0 0 56 68" aria-hidden="true" focusable="false">' +
      '<defs><linearGradient id="' + g + '" x1="0.15" y1="0" x2="0.85" y2="1">' +
      '<stop offset="0" stop-color="' + m.a + '"/><stop offset="0.5" stop-color="' + m.b + '"/><stop offset="1" stop-color="' + m.c + '"/></linearGradient></defs>' +
      '<path d="M15 0h10l5 24H20z" fill="#1b2354" stroke="' + m.b + '" stroke-width="1"/><path d="M41 0H31l-5 24h10z" fill="#232c66" stroke="' + m.b + '" stroke-width="1"/>' +
      '<circle cx="28" cy="43" r="20" fill="url(#' + g + ')" stroke="' + m.ring + '" stroke-width="1.6"/>' +
      '<circle cx="28" cy="43" r="15.5" fill="none" stroke="' + m.c + '" stroke-opacity="0.55" stroke-width="1.2"/>' +
      '<circle cx="28" cy="43" r="12.5" fill="none" stroke="#fff" stroke-opacity="0.35" stroke-width="0.8"/>' +
      '<text x="28" y="50.5" text-anchor="middle" font-size="21" font-weight="800" font-family="Songti SC,Noto Serif SC,STSong,Georgia,serif" fill="' + m.ink + '">' + rank + '</text>' +
      '</svg>';
  }

  function points(n) { return '<b>' + esc(n) + '</b><small>' + esc(t('lb_unit')) + '</small>'; }
  function meTag(e) { return e && e.me ? '<span class="lb-tag">' + esc(t('lb_me')) + '</span>' : ''; }
  /* 名字旁边的小徽章：在这个榜（总分或这一种玩法）上得过的最高一档 */
  function medals(e) {
    if (!e || !window.WPAwards) return '';
    return (e.badges || []).filter(function (b) { return b.game === state.game; }).map(function (b) { return WPAwards.mini(b); }).join('');
  }

  var showClass = false;        /* 老师看「全部学生」时才在名字旁边标班级；单个班的榜不用重复 */

  function slot(rank, e) {
    /* 位置（左 / 中 / 右）决定大小，名次决定颜色：并列第一的人两个都是金色，不会出现银色底配金牌 */
    var tier = e ? Math.min(e.rank, 3) : rank;
    var cls = 'lb-slot lb-pos-' + rank + ' lb-tier-' + tier + (e ? '' : ' lb-slot-empty') + (e && e.me ? ' is-me' : '');
    if (!e) {
      return '<div class="' + cls + '" data-rank="' + rank + '">' + medal(rank) + '<div class="lb-name">' + esc(t('lb_vacant')) + '</div></div>';
    }
    return '<div class="' + cls + '" data-rank="' + esc(e.rank) + '" aria-label="' + esc(t('lb_rankN', { n: e.rank })) + '">' + medal(e.rank) +
      '<div class="lb-name">' + esc(e.name) + medals(e) + meTag(e) + '</div>' +
      '<div class="lb-pts">' + points(e.points) + '</div>' +
      (showClass && e.class_name ? '<div class="lb-cls">' + esc(e.class_name) + '</div>' : '') + '</div>';
  }

  function title(d) {
    if (d.scope === 'overall') return d.title || t('lb_titleOverall');
    if (d.scope === 'staff') return d.class_name ? t('lb_title', { cls: d.class_name }) : t('lb_titleAll');
    return d.class_name ? t('lb_title', { cls: d.class_name }) : t('lb_titleMine');
  }

  function render() {
    var d = state.data;
    if (!d) return;
    showClass = d.scope !== 'class' && !d.class_name;
    $('lbTitle').textContent = title(d);
    $('lbSub').textContent = d.scope === 'overall' ? t('lb_subOverall', { n: d.class_count }) : t('lb_sub');
    $('lbSettings').hidden = !d.can_configure;
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
        '<span class="lb-who">' + esc(e.name) + medals(e) + meTag(e) + (showClass && e.class_name ? '<i>' + esc(e.class_name) + '</i>' : '') + '</span>' +
        '<span class="lb-score">' + points(e.points) + '</span></li>';
    }).join('');
    /* 我不在前十名：单独告诉我排第几 */
    var me = d.me, box = $('lbMe');
    var inTop = entries.some(function (e) { return e.me; });
    /* 学生：不在前十名时告诉他排第几；还没有积分就鼓励他玩一局；他的班没参加总榜就什么都不说 */
    var student = d.is_student && (d.scope === 'class' || (d.scope === 'overall' && d.my_class_in_board));
    if (student) {
      box.hidden = false;
      if (me && !inTop) box.textContent = t('lb_myRank', { rank: me.rank, n: me.points, total: d.total });
      else if (!me) box.textContent = t('lb_myNone');
      else box.hidden = true;
    } else {
      box.hidden = true;
    }
    renderClasses(d);
    Array.prototype.forEach.call(document.querySelectorAll('#lbGames [data-game]'), function (b) {
      var on = b.getAttribute('data-game') === state.game;
      b.classList.toggle('active', on);
      b.setAttribute('aria-pressed', String(on));
    });
    ['lbAll', 'lbWeek'].forEach(function (id) {
      var on = $(id).getAttribute('data-period') === state.period;
      $(id).classList.toggle('active', on);
      $(id).setAttribute('aria-pressed', String(on));
    });
  }

  function renderClasses(d) {
    var box = $('lbClassBox');
    if (d.is_student || d.scope === 'class') { box.hidden = true; return; }
    box.hidden = false;
    var select = $('lbClass');
    var html = '<option value="">' + esc(d.configured ? t('lb_overallOption', { n: d.class_count }) : t('lb_allClasses')) + '</option>' + (d.classes || []).map(function (c) {
      return '<option value="' + esc(c) + '">' + esc(c) + '</option>';
    }).join('');
    if (select.getAttribute('data-html') !== html) { select.innerHTML = html; select.setAttribute('data-html', html); }
    select.value = state.cls;
  }

  function load() {
    var url = '/api/leaderboard?period=' + state.period + '&game=' + state.game + (state.cls ? '&class_name=' + encodeURIComponent(state.cls) : '');
    return API.get(url).then(function (res) {
      /* 老师第一次进来：默认选第一个班（一个班一个榜），而不是把所有班混在一起 */
      if (res.scope === 'staff' && !res.configured && !state.picked && !state.cls && res.classes && res.classes.length) {
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
    Array.prototype.forEach.call(document.querySelectorAll('.lb-seg-btn[data-period]'), function (b) {
      b.addEventListener('click', function () {
        state.period = b.getAttribute('data-period');
        load();
      });
    });
    Array.prototype.forEach.call(document.querySelectorAll('#lbGames [data-game]'), function (b) {
      b.addEventListener('click', function () {
        state.game = b.getAttribute('data-game');
        load();
      });
    });
    $('lbClass').addEventListener('change', function () { state.cls = this.value; state.picked = true; load(); });
    AuthUI.ready.then(load);
  });

  window.WPLeaderboard = { medal: medal, slot: slot, title: title };
})();
