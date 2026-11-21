/* ============================================================
   page-stats.js —— 成绩记录
   ------------------------------------------------------------
   一行 = 一个学生 × 一套题（班级 / 学号 / 姓名 / 次数 / 完成 / 最高 / 最低 / 平均 / 平均用时 / 最近一次）。
   点一行展开，看每一次的具体情况（明细按需向服务器要，要过一次就记住）。
   学生只会看到自己的行（服务端保证），所以班级 / 学号 / 姓名三列对学生是隐藏的。
   ============================================================ */
(function () {
  'use strict';

  function esc(s) { return API.esc(s); }
  function t(key, params) { return WPI18N.t(key, params); }

  var data = null;                 /* /api/scores/summary 的结果 */
  var open = {};                   /* 展开着的行：key -> true */
  var playsCache = {};             /* key -> 明细列表，或 'loading' / 'error' */
  var filter = { cls: '', bank: '', q: '' };

  function fmtDur(sec) {
    sec = Math.max(0, Math.round(sec || 0));
    var m = Math.floor(sec / 60), s = sec % 60;
    return (m < 10 ? '0' : '') + m + ':' + (s < 10 ? '0' : '') + s;
  }

  /* 一行的身份：有账号用 user_id，没有（家庭版）用设备号；题库用编号，没有编号用名字 */
  function keyOf(r) {
    return (r.user_id != null ? 'u' + r.user_id : 'd' + r.device) + '|' + (r.bank_id != null ? 'b' + r.bank_id : 't' + r.bank_title);
  }
  /* 公开版 /words/：没有账号，只看这台设备的成绩（设备号是玩游戏时浏览器里生成的那个） */
  function deviceQuery() {
    if (!AuthUI.info().public) return '';
    var id = '';
    try { id = localStorage.getItem('wp_device_id') || ''; } catch (e) { }
    return 'device=' + encodeURIComponent(id);
  }
  function playsUrl(r) {
    if (AuthUI.info().public) {
      return '/api/scores/plays?' + deviceQuery() + (r.bank_id != null ? '&bank_id=' + r.bank_id : '&bank_title=' + encodeURIComponent(r.bank_title));
    }
    return '/api/scores/plays?' + (r.user_id != null ? 'user_id=' + r.user_id : 'device=' + encodeURIComponent(r.device)) +
      (r.bank_id != null ? '&bank_id=' + r.bank_id : '&bank_title=' + encodeURIComponent(r.bank_title));
  }

  function visibleRows() {
    var q = filter.q.trim().toLowerCase();
    return (data ? data.rows : []).filter(function (r) {
      return (!filter.cls || r.class_name === filter.cls) &&
        (!filter.bank || String(r.bank_id) === filter.bank) &&
        (!q || r.student_no.toLowerCase().indexOf(q) >= 0 || r.name.toLowerCase().indexOf(q) >= 0);
    });
  }

  function renderCards(rows) {
    var plays = 0, total = 0, best = 0;
    rows.forEach(function (r) { plays += r.plays; total += r.total; if (r.best > best) best = r.best; });
    document.getElementById('sCount').textContent = plays;
    document.getElementById('sBest').textContent = best;
    document.getElementById('sAvg').textContent = plays ? Math.round(total / plays * 10) / 10 : 0;
    document.getElementById('sTotal').textContent = total;
  }

  /* 排排坐：这一次交的朗读录音，点开就能听（学生听自己的，老师听自己名下学生的） */
  function recordingsRow(p) {
    if (!p.recordings || !p.recordings.length) return '';
    return '<tr class="rec-row"><td colspan="8"><div class="rec-list"><b>' + esc(t('stats_recordings')) + '</b>' +
      p.recordings.map(function (r) {
        var note = !r.valid ? t('stats_recInvalid') : r.status === 'done' ? t('stats_recBonus', { n: r.bonus, p: Math.round(r.accuracy * 100) })
          : r.status === 'pending' ? t('stats_recPending') : t('stats_recNoBonus');
        return '<span class="rec-item">' + esc(t('stats_recSentence', { n: r.item_ord + 1 })) +
          ' <audio controls preload="none" src="' + esc(API.path('/api/recordings/' + r.id + '/audio')) + '"></audio> ' +
          '<small title="' + esc(r.transcript || '') + '">' + esc(note) + (r.transcript ? ' · “' + esc(r.transcript) + '”' : '') + '</small></span>';
      }).join('') + '</div></td></tr>';
  }

  function detailHtml(key) {
    var d = playsCache[key];
    if (d === 'loading' || d === undefined) return '<div class="empty">' + esc(t('stats_detailLoading')) + '</div>';
    if (d === 'error') return '<div class="empty">' + esc(t('stats_detailFail')) + '</div>';
    return '<table class="detail-table"><thead><tr>' +
      ['stats_dTime', 'stats_dScore', 'stats_dMatched', 'stats_dWrong', 'stats_dCombo', 'stats_dDuration', 'stats_dLevels', 'stats_dDone']
        .map(function (k) { return '<th>' + esc(t(k)) + '</th>'; }).join('') + '</tr></thead><tbody>' +
      d.map(function (p) {
        return '<tr><td>' + esc(API.fmtTime(p.created_at)) + '</td><td>' + p.score + '</td>' +
          '<td>' + esc(t('stats_pair', { a: p.matched, b: p.total_pairs })) + '</td><td>' + p.wrong + '</td><td>x' + p.best_combo + '</td>' +
          '<td>' + fmtDur(p.duration) + '</td>' +
          '<td>' + esc(p.levels_total != null ? t('stats_levelsOf', { n: p.level_count, total: p.levels_total }) : String(p.level_count)) + '</td>' +
          '<td><span class="pill ' + (p.completed ? 'done' : 'notdone') + '">' + esc(t(p.completed ? 'stats_done' : 'stats_notDone')) + '</span></td></tr>' +
          recordingsRow(p);
      }).join('') + '</tbody></table>';
  }

  function render() {
    var rows = visibleRows();
    renderCards(rows);
    var body = document.querySelector('#sumTable tbody');
    var mine = !AuthUI.isAdmin();
    var who = {}, banks = {};
    rows.forEach(function (r) { who[r.user_id != null ? 'u' + r.user_id : 'd' + r.device] = 1; banks[r.bank_id != null ? 'b' + r.bank_id : 't' + r.bank_title] = 1; });
    document.getElementById('sumCount').textContent = rows.length
      ? [t('stats_count', { n: rows.length })].concat(mine ? [] : [t('stats_sumStudents', { n: Object.keys(who).length })], [t('stats_sumBanks', { n: Object.keys(banks).length })]).join(' · ')
      : '';
    if (!rows.length) {
      body.innerHTML = '<tr><td colspan="12" class="empty">' + esc(t(mine ? 'stats_noRowsMine' : 'stats_noRows')) + '</td></tr>';
      updateExport();
      return;
    }
    body.innerHTML = rows.map(function (r) {
      var key = keyOf(r), isOpen = !!open[key];
      return '<tr class="sum-row" tabindex="0" role="button" aria-expanded="' + isOpen + '" data-key="' + esc(key) + '" title="' +
        esc(t(isOpen ? 'stats_collapse' : 'stats_expand')) + '">' +
        '<td><span class="caret">▸</span></td>' +
        '<td class="admin-only">' + esc(r.class_name) + '</td><td class="admin-only">' + esc(r.student_no) + '</td><td class="admin-only">' + esc(r.name) + '</td>' +
        '<td class="bank">' + (r.game_type && r.game_type !== 'match' ? '<span class="pill type">' + esc(t('type_' + r.game_type)) + '</span> ' : '') +
        esc(r.bank_title || t('stats_unnamed')) + '</td>' +
        '<td class="num">' + r.plays + '</td><td class="num">' + r.completed + '</td>' +
        '<td class="num">' + r.best + '</td><td class="num">' + r.worst + '</td><td class="num">' + r.avg_score + '</td>' +
        '<td>' + fmtDur(r.avg_duration) + '</td><td>' + esc(API.fmtTime(r.last_at)) + '</td></tr>' +
        (isOpen ? '<tr class="detail-row"><td colspan="12">' + detailHtml(key) + '</td></tr>' : '');
    }).join('');
    updateExport();
  }

  function fillFilters() {
    var cls = document.getElementById('fClass'), bank = document.getElementById('fBank');
    if (!cls || !bank) return;
    cls.innerHTML = '<option value="">' + esc(t('stats_allClasses')) + '</option>' +
      data.classes.map(function (c) { return '<option value="' + esc(c) + '">' + esc(c) + '</option>'; }).join('');
    bank.innerHTML = '<option value="">' + esc(t('stats_allBanks')) + '</option>' +
      data.banks.map(function (b) { return '<option value="' + b.id + '">' + esc(b.title) + '</option>'; }).join('');
    cls.value = filter.cls; bank.value = filter.bank;
  }

  function updateExport() {
    var link = document.getElementById('btnExport');
    if (!link) return;
    var params = [];
    if (filter.cls) params.push('class_name=' + encodeURIComponent(filter.cls));
    if (filter.bank) params.push('bank_id=' + encodeURIComponent(filter.bank));
    if (filter.q.trim()) params.push('q=' + encodeURIComponent(filter.q.trim()));
    link.href = API.path('/api/admin/export/score-summary.csv' + (params.length ? '?' + params.join('&') : ''));
  }

  function toggle(key) {
    var row = data.rows.filter(function (r) { return keyOf(r) === key; })[0];
    if (!row) return;
    if (open[key]) { delete open[key]; render(); return; }
    open[key] = true;
    if (!Array.isArray(playsCache[key])) {
      playsCache[key] = 'loading';
      API.get(playsUrl(row)).then(function (res) { playsCache[key] = res.plays || []; })
        .catch(function () { playsCache[key] = 'error'; })
        .then(render);
    }
    render();
  }

  WPI18N.onChange(function () { if (data) { fillFilters(); render(); } });

  document.addEventListener('DOMContentLoaded', function () {
    var body = document.querySelector('#sumTable tbody');
    body.addEventListener('click', function (ev) {
      var row = ev.target.closest('.sum-row');
      if (row) toggle(row.getAttribute('data-key'));
    });
    body.addEventListener('keydown', function (ev) {
      if (ev.key !== 'Enter' && ev.key !== ' ') return;
      var row = ev.target.closest('.sum-row');
      if (row) { ev.preventDefault(); toggle(row.getAttribute('data-key')); }
    });
    var cls = document.getElementById('fClass'), bank = document.getElementById('fBank'), q = document.getElementById('fSearch');
    if (cls) cls.onchange = function () { filter.cls = cls.value; render(); };
    if (bank) bank.onchange = function () { filter.bank = bank.value; render(); };
    if (q) q.oninput = function () { filter.q = q.value; render(); };

    AuthUI.ready.then(function () { var d = deviceQuery(); return API.get('/api/scores/summary' + (d ? '?' + d : '')); }).then(function (res) {
      data = res;
      fillFilters();
      render();
    }).catch(function (e) { API.toast(e.message); });
  });
})();
