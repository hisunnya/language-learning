/* ============================================================
   page-stats.js —— 成绩记录
   ============================================================ */
(function () {
  'use strict';

  function esc(s) { return API.esc(s); }

  function fmtDur(sec) {
    sec = Math.max(0, Math.round(sec || 0));
    var m = Math.floor(sec / 60), s = sec % 60;
    return (m < 10 ? '0' : '') + m + ':' + (s < 10 ? '0' : '') + s;
  }

  function render(res) {
    var st = res.stats || {};
    document.getElementById('sCount').textContent = st.count || 0;
    document.getElementById('sBest').textContent = st.best || 0;
    document.getElementById('sAvg').textContent = st.avg || 0;
    document.getElementById('sTotal').textContent = st.total || 0;

    var byBank = st.by_bank || [];
    var tb1 = document.querySelector('#byBankTable tbody');
    tb1.innerHTML = byBank.length ? byBank.map(function (r) {
      return '<tr><td>' + esc(r.bank_title || '(未命名)') + '</td>' +
        '<td class="num">' + r.n + '</td>' +
        '<td class="num">' + r.best + '</td>' +
        '<td class="num">' + r.total + '</td></tr>';
    }).join('') : '<tr><td colspan="4" class="empty">还没有成绩</td></tr>';

    var scores = res.scores || [];
    var tb2 = document.querySelector('#scoreTable tbody');
    tb2.innerHTML = scores.length ? scores.map(function (r) {
      return '<tr>' +
        '<td>' + esc(API.fmtTime(r.created_at)) + '</td>' +
        '<td>' + esc(r.bank_title || '(未命名)') + '</td>' +
        '<td class="num">' + r.score + '</td>' +
        '<td>' + r.matched + ' / ' + r.total_pairs + '</td>' +
        '<td>' + r.wrong + '</td>' +
        '<td>x' + r.best_combo + '</td>' +
        '<td>' + fmtDur(r.duration) + '</td>' +
        '<td>' + r.level_count + '</td></tr>';
    }).join('') : '<tr><td colspan="8" class="empty">还没有成绩，去玩一局吧</td></tr>';
  }

  document.addEventListener('DOMContentLoaded', function () {
    API.get('/api/scores?limit=200').then(render).catch(function (e) {
      API.toast(e.message);
    });
  });
})();
