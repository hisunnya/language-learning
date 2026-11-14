/* ============================================================
   page-home.js —— 首页
   ============================================================ */
(function () {
  'use strict';

  var sel = null;
  var banks = [];
  var loaded = false;      /* 题库列表取回来之前，别把「加载中…」换成「还没有题库」 */

  function esc(s) { return API.esc(s); }
  function t(key, params) { return WPI18N.t(key, params); }

  function counts(b) {
    return t('home_counts', { words: b.word_count, units: b.unit_count, time: API.fmtTime(b.created_at) });
  }

  function defaultBank() {
    for (var i = 0; i < banks.length; i++) {
      var b = banks[i];
      if (b.source === 'seed' && b.level1 === '初中' && b.level2 === '九年级' &&
          b.level3 === '上册' && b.unit_mode === 'all') {
        return b;
      }
    }
    return banks.length ? banks[0] : null;
  }

  function renderDefault() {
    var box = document.getElementById('defaultList');
    var card = document.getElementById('defaultCard');
    var b = defaultBank();
    if (!b) { card.hidden = true; return; }
    card.hidden = false;
    box.innerHTML =
      '<div class="item">' +
      '  <div class="main"><b>' + esc(b.title) + '</b>' +
      '    <small>' + esc(counts(b)) + '</small></div>' +
      '  <div class="ops">' +
      '    <a class="btn sm" href="' + esc(API.path('/play.html?bank=' + b.id)) + '">' + esc(t('home_play')) + '</a>' +
      '    <button class="btn sm ghost" data-offline="' + b.id + '">' + esc(t('home_offline')) + '</button>' +
      '  </div></div>';

    var btn = box.querySelector('[data-offline]');
    if (btn) btn.onclick = function () { makeOffline(b.id, btn); };
  }

  function isStudentView() {
    return !AuthUI.isAdmin();
  }

  /* 标签只在启用了登录的站点（家庭版 / 班级版）才有意义；局域网版没有学生账号 */
  function tagsEnabled() {
    return !!(AuthUI.info() && AuthUI.info().enabled);
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
      var banks = groups[name].slice();
      /* 按单元顺序排（seq 是第几单元）；没有 seq 的老题库保持原来的先后 */
      if (banks.some(function (b) { return b.seq > 0; })) {
        banks = banks.map(function (b, i) { return { b: b, i: i }; }).sort(function (x, y) {
          var a = x.b.seq > 0 ? x.b.seq : 1e9, c = y.b.seq > 0 ? y.b.seq : 1e9;
          return a - c || x.i - y.i;
        }).map(function (x) { return x.b; });
      }
      return { name: name, banks: banks };
    });
  }

  function tagPills(b) {
    return (b.tags || []).map(function (tag) {
      return '<span class="pill gray">' + esc(tag) + '</span>';
    }).join(' ');
  }

  function bankItem(b, student) {
    var src = b.source === 'material' ? '<span class="pill gray">' + esc(t('home_srcMaterial')) + '</span>'
                                      : '<span class="pill">' + esc(t('home_srcSeed')) + '</span>';
    var meta = '<small>' + esc(counts(b)) + '</small>';
    var ops = '<a class="btn sm" href="' + esc(API.path('/play.html?bank=' + b.id)) + '">' + esc(t('home_play')) + '</a>';
    if (!student) {
      ops += (tagsEnabled() ? '<button class="btn sm ghost" data-meta="' + b.id + '">' + esc(t('home_meta')) + '</button>' : '') +
        '<button class="btn sm ghost" data-offline="' + b.id + '">' + esc(t('home_offline')) + '</button>' +
        '<button class="btn sm danger" data-del="' + b.id + '">' + esc(t('home_delete')) + '</button>';
    }
    return '<div class="item">' +
      '  <div class="main"><b>' + esc(b.title) + '</b>' + (student ? '' : ' ' + src) +
      (student || !tagsEnabled() ? '' : ' ' + (tagPills(b) || '<span class="pill warn">' + esc(t('home_noTags')) + '</span>')) +
      '    ' + meta + '</div>' +
      '  <div class="ops">' + ops + '</div></div>';
  }

  function renderBanks() {
    var box = document.getElementById('bankList');
    var student = isStudentView();
    if (!banks.length) {
      box.innerHTML = student
        ? '<div class="empty">' + esc(t('home_emptyStudent')) + '</div>'
        : '<div class="empty">' + esc(t('home_emptyTeacher')) + '</div>';
      return;
    }
    box.innerHTML = groupByCategory(banks).map(function (g) {
      var canRelease = !student && tagsEnabled() && g.name && g.banks.length > 1;
      var head = '<div class="sub" style="margin:14px 0 4px;display:flex;align-items:center;gap:10px"><b>' +
        esc(g.name || t(student ? 'home_catOther' : 'home_catNone')) + '</b>' +
        (canRelease ? '<button class="btn sm ghost" data-release="' + esc(g.name) + '">' + esc(t('rel_button')) + '</button>' : '') + '</div>';
      return head + g.banks.map(function (b) { return bankItem(b, student); }).join('');
    }).join('');

    box.querySelectorAll('[data-offline]').forEach(function (btn) {
      btn.onclick = function () { makeOffline(parseInt(btn.dataset.offline, 10), btn); };
    });
    box.querySelectorAll('[data-release]').forEach(function (btn) {
      btn.onclick = function () { editRelease(btn.getAttribute('data-release')); };
    });
    box.querySelectorAll('[data-meta]').forEach(function (btn) {
      btn.onclick = function () { editMeta(parseInt(btn.dataset.meta, 10)); };
    });
    box.querySelectorAll('[data-del]').forEach(function (btn) {
      btn.onclick = function () {
        var id = parseInt(btn.dataset.del, 10);
        if (!confirm(t('home_confirmDelete'))) return;
        API.del('/api/banks/' + id).then(loadBanks)
          .catch(function (e) { API.toast(e.message); });
      };
    });
  }

  /* 老师设置题库的分类和标签：学生标签里至少有一个和题库的相同，才看得到这个题库 */
  function editMeta(id) {
    var b = banks.filter(function (x) { return x.id === id; })[0];
    if (!b) return;
    var category = window.prompt(t('home_promptCategory'), b.category || '');
    if (category === null) return;
    var tags = window.prompt(t('home_promptTags'), (b.tags || []).join(', '));
    if (tags === null) return;
    API.post('/api/banks/' + id + '/meta', { category: category, tags: tags })
      .then(function () { API.toast(t('home_saved')); return loadBanks(); })
      .catch(function (e) { API.toast(e.message); });
  }

  /* 批量开放：对一本书（同一分类）的各个单元题库，一次给一批加上 / 去掉某个班级标签。
     预设（整本书 / 上半部分 / 下半部分 / 前 N 个）只是帮老师勾选，勾完还能手动调整。 */
  function editRelease(category) {
    var units = groupByCategory(banks).filter(function (g) { return g.name === category; })[0];
    if (!units) return;
    units = units.banks;
    var state = { tag: '', n: 3, ticked: {}, tags: [] };
    var back = document.createElement('div');
    back.className = 'modal-back';
    back.innerHTML = '<div class="modal" role="dialog" aria-modal="true"></div>';
    document.body.appendChild(back);
    var box = back.querySelector('.modal');

    function close() { window.removeEventListener('portal-lang-change', draw); back.remove(); }
    function hasTag(b) { var tag = state.tag.trim(); return !!tag && (b.tags || []).indexOf(tag) >= 0; }
    function tickedIds() { return units.filter(function (b) { return state.ticked[b.id]; }).map(function (b) { return b.id; }); }

    function draw() {
      var chips = state.tags.map(function (x) {
        return '<button class="chip" type="button" data-chip="' + esc(x.tag) + '" title="' + esc(t('rel_chipTitle', { n: x.students })) + '">' + esc(x.tag) + '</button>';
      }).join('');
      var PRESET_TEXT = { all: 'rel_all', firstHalf: 'rel_firstHalf', secondHalf: 'rel_secondHalf' };
      var presets = ['all', 'firstHalf', 'secondHalf'].map(function (k) {
        return '<button class="btn sm ghost" type="button" data-preset="' + k + '">' + esc(t(PRESET_TEXT[k])) + '</button>';
      }).join('') +
        '<span class="preset-n"><button class="btn sm ghost" type="button" data-preset="firstN">' + esc(t('rel_firstN')) + '</button>' +
        '<input type="number" min="0" max="' + units.length + '" value="' + esc(state.n) + '" data-n aria-label="N"></span>' +
        '<button class="btn sm ghost" type="button" data-preset="none">' + esc(t('rel_none')) + '</button>';
      var rows = units.map(function (b) {
        return '<label class="unit-row"><input type="checkbox" data-bank="' + b.id + '"' + (state.ticked[b.id] ? ' checked' : '') + '> <span>' +
          esc(b.level4 || b.title) + '</span> <small>' + esc(t('rel_words', { n: b.word_count })) + '</small>' +
          '<span class="pill good rel-open"' + (hasTag(b) ? '' : ' hidden') + '>' + esc(t('rel_isOpen')) + '</span></label>';
      }).join('');
      box.innerHTML = '<h2>' + esc(t('rel_title', { category: category })) + '</h2><p class="sub">' + esc(t('rel_hint')) + '</p>' +
        '<label class="rel-label">' + esc(t('rel_tagLabel')) + '<input type="text" data-tag maxlength="20" value="' + esc(state.tag) + '" placeholder="' + esc(t('rel_tagPlaceholder')) + '"></label>' +
        '<div class="chips">' + chips + '</div><div class="presets">' + presets + '</div>' +
        '<div class="unit-list">' + rows + '</div><p class="hint" data-summary></p>' +
        '<div class="actions modal-actions"><button class="btn gold" type="button" data-act="open">' + esc(t('rel_open')) + '</button>' +
        '<button class="btn" type="button" data-act="withdraw">' + esc(t('rel_withdraw')) + '</button>' +
        '<button class="btn ghost" type="button" data-act="cancel">' + esc(t('rel_cancel')) + '</button></div>';
      summary();
    }
    function summary() {
      var el = box.querySelector('[data-summary]');
      if (el) el.textContent = t('rel_summary', { n: tickedIds().length, total: units.length });
    }
    function refreshPills() {
      Array.prototype.forEach.call(box.querySelectorAll('.unit-row'), function (row, i) {
        row.querySelector('.rel-open').hidden = !hasTag(units[i]);
      });
    }
    function applyPreset(kind) {
      state.ticked = {};
      WPRelease.indexes(kind, units.length, state.n).forEach(function (i) { state.ticked[units[i].id] = true; });
      draw();
    }
    function run(act) {
      var tag = state.tag.trim();
      if (!tag) { API.toast(t('rel_noTag')); return; }
      var ids = tickedIds();
      if (!ids.length) { API.toast(t('rel_noneTicked')); return; }
      /* 真正会变的单元：开放 = 还没有这个标签的；收回 = 已经有的。提示按它算，不把本来就是这个状态的也算进去 */
      var changing = units.filter(function (b) { return state.ticked[b.id] && (act === 'open' ? !hasTag(b) : hasTag(b)); });
      if (!changing.length) { API.toast(t('rel_nothing')); return; }
      var body = { bank_ids: ids };
      body[act === 'open' ? 'add' : 'remove'] = tag;
      API.post('/api/banks/tags', body).then(function () {
        API.toast(t(act === 'open' ? 'rel_opened' : 'rel_withdrawn', { n: changing.length, tag: tag }));
        close();
        return loadBanks();
      }).catch(function (e) { API.toast(e.message); });
    }

    box.addEventListener('input', function (ev) {
      if (ev.target.matches('[data-tag]')) { state.tag = ev.target.value; refreshPills(); }
      else if (ev.target.matches('[data-n]')) state.n = ev.target.value;
    });
    box.addEventListener('change', function (ev) {
      var c = ev.target.closest('input[data-bank]');
      if (c) { state.ticked[c.getAttribute('data-bank')] = c.checked; summary(); }
    });
    box.addEventListener('click', function (ev) {
      var chip = ev.target.closest('[data-chip]');
      if (chip) { state.tag = chip.getAttribute('data-chip'); box.querySelector('[data-tag]').value = state.tag; refreshPills(); return; }
      var preset = ev.target.closest('[data-preset]');
      if (preset) { applyPreset(preset.getAttribute('data-preset')); return; }
      var btn = ev.target.closest('[data-act]');
      if (!btn) return;
      var act = btn.getAttribute('data-act');
      if (act === 'cancel') close(); else run(act);
    });
    back.addEventListener('click', function (ev) { if (ev.target === back) close(); });
    window.addEventListener('portal-lang-change', draw);
    draw();
    API.get('/api/admin/tags').then(function (res) {
      state.tags = (res.tags || []).filter(function (x) { return x.students > 0; });
      draw();
    }).catch(function () { });
  }

  function loadBanks() {
    return AuthUI.ready.then(function () { return API.get('/api/banks'); }).then(function (res) {
      banks = res.banks || [];
      loaded = true;
      renderBanks();
      renderDefault();
    }).catch(function (e) { API.toast(e.message); });
  }

  function makeOffline(bankId, button) {
    if (button) { button.disabled = true; button.textContent = t('home_synthesizing'); }
    API.toast(t('home_synthToast'), 600000);
    return API.post('/api/banks/' + bankId + '/offline', {}).then(function (res) {
      API.toast(t('home_generated', { name: res.filename }));
      API.download(res.url, res.filename).catch(function () {
        API.toast(t('home_downloadBlocked'), 6000);
      });
    }).catch(function (e) {
      API.toast(e.message, 12000);
    }).finally(function () {
      if (button) { button.disabled = false; button.textContent = t('home_offline'); }
    });
  }

  /* 切换语言：列表、统计提示是脚本画的，要重画（静态文字由页眉换） */
  WPI18N.onChange(function () {
    if (loaded) { renderBanks(); renderDefault(); }
    updateInfo();
  });

  document.addEventListener('DOMContentLoaded', function () {
    sel = new Selector('#levelBox', {
      onChange: function () { updateInfo(); }
    });

    /* 「每关词数」：交给后端分组时用 */
    var pairsInput = document.getElementById('pairsPerLevel');
    if (pairsInput) {
      pairsInput.oninput = function () { updateInfo(); };
    }

    API.get('/api/meta').then(function (meta) {
      var c = meta.curriculum || {};
      document.getElementById('curTotal').textContent = c.word_total || '—';
      document.getElementById('curUnits').textContent = c.unit_total || '—';
    }).catch(function () { });

    sel.init().then(function () { updateInfo(); }).catch(function (e) {
      API.toast(e.message);
    });

    loadBanks();

    document.getElementById('btnMake').onclick = function () {
      var s = sel.get();
      s.pairs_per_level = pairsPerLevel();
      var btn = this;
      btn.disabled = true;
      btn.textContent = t('home_making');
      API.post('/api/banks', s).then(function (res) {
        location.href = API.path('/play.html?bank=' + res.bank.id);
      }).catch(function (e) {
        API.toast(e.message);
        btn.disabled = false;
        btn.textContent = t('home_make');
      });
    };

    document.getElementById('btnUpload').onclick = function () {
      location.href = API.path('/bank.html');
    };

    document.getElementById('btnOffline').onclick = function () {
      var s = sel.get();
      s.pairs_per_level = pairsPerLevel();
      var btn = this;
      btn.disabled = true;
      btn.textContent = t('home_preparing');
      API.post('/api/banks', s).then(function (res) {
        btn.textContent = t('home_synthesizing');
        API.toast(t('home_synthToast'), 600000);
        return API.post('/api/banks/' + res.bank.id + '/offline', {});
      }).then(function (res) {
        API.toast(t('home_generatedBlocked', { name: res.filename }), 6000);
        return API.download(res.url, res.filename).catch(function () {
          API.toast(t('home_downloadBlocked'), 6000);
        });
      }).then(function () {
        btn.disabled = false;
        loadBanks();
      }).catch(function (e) {
        API.toast(e.message, 12000);
        btn.disabled = false;
        btn.textContent = t('home_offline');
      });
    };
  });

  /* 「每关词数」：默认 12，输错了也按默认值来 */
  function pairsPerLevel() {
    var input = document.getElementById('pairsPerLevel');
    var value = input ? parseInt(input.value, 10) : 12;
    if (!value || value < 4 || value > 40) return 12;
    return value;
  }

  function updateInfo() {
    if (!sel) return;
    var s = sel.summary();
    var box = document.getElementById('selInfo');
    if (!s.units) {
      box.textContent = t('home_noContent');
      return;
    }
    var per = pairsPerLevel();
    var levels = Math.ceil(s.words / per);
    box.textContent = t('home_range', { path: s.path, units: s.units, words: s.words, per: per, levels: levels });
  }
})();
