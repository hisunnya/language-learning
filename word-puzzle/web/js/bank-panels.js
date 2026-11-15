/* ============================================================
   bank-panels.js —— 题库的「分类 / 标签」面板和「批量开放」面板
   ------------------------------------------------------------
   题库工作台的「当前题库」标签页用它；改完调用 init 时给的 reload 刷新列表。
   分类 = 「书名」，只用来整理；标签 = 谁能看到（学生有一个相同的标签就能看到）。
   ============================================================ */
(function (global) {
  'use strict';

  var ctx = { banks: [], reload: function () { return Promise.resolve(); } };

  function esc(s) { return API.esc(s); }
  function t(key, params) { return WPI18N.t(key, params); }

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

  /* 标签的分隔符：逗号（中英文）、顿号、分号、换行 */
  var TAG_SEPARATORS = new RegExp('[,，、;；\\n]+');

  /* 老师设置题库的分类 / 标签，两件事分开、各有说明：
     分类 = 「书名」，只用来整理；标签 = 谁能看到（学生有一个相同的标签就能看到）。
     标签面板会按现在填的内容，实时算出有多少名学生能看到。 */
  function editField(kind, id) {
    var b = ctx.banks.filter(function (x) { return x.id === id; })[0];
    if (!b) return;
    var isTags = kind === 'tags';
    var state = { value: isTags ? (b.tags || []).join(', ') : (b.category || ''), allTags: [], students: null };
    var back = document.createElement('div');
    back.className = 'modal-back';
    back.innerHTML = '<div class="modal" role="dialog" aria-modal="true"></div>';
    document.body.appendChild(back);
    var box = back.querySelector('.modal');

    function close() { window.removeEventListener('portal-lang-change', draw); back.remove(); }
    function typed() {
      return isTags ? state.value.split(TAG_SEPARATORS).map(function (x) { return x.trim(); }).filter(Boolean) : [];
    }
    function categories() {
      var seen = {};
      ctx.banks.forEach(function (x) { if (x.category) seen[x.category] = true; });
      return Object.keys(seen).sort();
    }
    function previewText() {
      var tags = typed();
      if (!tags.length) return t('field_tagsNone');
      if (!state.students) return '';
      var n = state.students.filter(function (u) {
        return (u.tags || []).some(function (x) { return tags.indexOf(x) >= 0; });
      }).length;
      return t('field_tagsPreview', { n: n, total: state.students.length });
    }
    function refreshPreview() {
      var el = box.querySelector('[data-preview]');
      if (el) el.textContent = previewText();
    }
    function draw() {
      var chips;
      if (isTags) {
        chips = state.allTags.map(function (x) {
          return '<button class="chip" type="button" data-chip="' + esc(x.tag) + '">' + esc(x.tag) +
            (x.students ? ' <small>(' + esc(t('field_tagsCount', { n: x.students })) + ')</small>' : '') + '</button>';
        }).join('');
      } else {
        chips = categories().map(function (c) {
          return '<button class="chip" type="button" data-chip="' + esc(c) + '">' + esc(c) + '</button>';
        }).join('');
      }
      var K = isTags
        ? { title: 'field_tagsTitle', help: 'field_tagsHelp', label: 'field_tagsLabel', ph: 'field_tagsPlaceholder', existing: 'field_tagsExisting' }
        : { title: 'field_catTitle', help: 'field_catHelp', label: 'field_catLabel', ph: 'field_catPlaceholder', existing: 'field_catExisting' };
      box.innerHTML = '<h2>' + esc(t(K.title, { title: b.title })) + '</h2>' +
        '<p class="sub">' + esc(t(K.help)) + '</p>' +
        '<label class="rel-label">' + esc(t(K.label)) +
        '<input type="text" data-value maxlength="' + (isTags ? 120 : 20) + '" value="' + esc(state.value) + '" placeholder="' + esc(t(K.ph)) + '"></label>' +
        (chips ? '<p class="hint">' + esc(t(K.existing)) + '</p><div class="chips">' + chips + '</div>' : '') +
        (isTags ? '<p class="hint" data-preview>' + esc(previewText()) + '</p>' : '') +
        '<div class="actions modal-actions"><button class="btn gold" type="button" data-act="save">' + esc(t('field_save')) + '</button>' +
        '<button class="btn ghost" type="button" data-act="clear">' + esc(t('field_clear')) + '</button>' +
        '<button class="btn ghost" type="button" data-act="cancel">' + esc(t('field_cancel')) + '</button></div>';
    }

    box.addEventListener('input', function (ev) {
      if (!ev.target.matches('[data-value]')) return;
      state.value = ev.target.value;
      refreshPreview();
    });
    box.addEventListener('click', function (ev) {
      var chip = ev.target.closest('[data-chip]');
      if (chip) {
        var value = chip.getAttribute('data-chip');
        if (isTags) {
          var now = typed();
          if (now.indexOf(value) < 0) now.push(value);
          state.value = now.join(', ');
        } else {
          state.value = value;
        }
        box.querySelector('[data-value]').value = state.value;
        refreshPreview();
        return;
      }
      var btn = ev.target.closest('[data-act]');
      if (!btn) return;
      var act = btn.getAttribute('data-act');
      if (act === 'cancel') { close(); return; }
      if (act === 'clear') { state.value = ''; box.querySelector('[data-value]').value = ''; refreshPreview(); return; }
      btn.disabled = true;
      var body = {};
      body[isTags ? 'tags' : 'category'] = state.value;      /* 只提交这一项，另一项保持不变 */
      API.post('/api/banks/' + id + '/meta', body)
        .then(function () { API.toast(t('home_saved')); close(); return ctx.reload(); })
        .catch(function (e) { btn.disabled = false; API.toast(e.message); });
    });
    back.addEventListener('click', function (ev) { if (ev.target === back) close(); });
    window.addEventListener('portal-lang-change', draw);
    draw();
    if (isTags) {
      API.get('/api/admin/tags').then(function (res) { state.allTags = res.tags || []; draw(); }).catch(function () { });
      API.get('/api/admin/users').then(function (res) {
        state.students = (res.users || []).filter(function (u) { return u.role !== 'admin'; });
        refreshPreview();
      }).catch(function () { });
    }
  }

  /* 批量开放：对一本书（同一分类）的各个单元题库，一次给一批加上 / 去掉某个班级标签。
     预设（整本书 / 上半部分 / 下半部分 / 前 N 个）只是帮老师勾选，勾完还能手动调整。 */
  function editRelease(category) {
    var units = groupByCategory(ctx.banks).filter(function (g) { return g.name === category; })[0];
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
        return ctx.reload();
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


  global.BankPanels = {
    /* 每次题库列表刷新后调用：banks 是当前列表，reload 是改完之后要做的刷新 */
    set: function (banks, reload) { ctx.banks = banks || []; if (reload) ctx.reload = reload; },
    groupByCategory: groupByCategory,
    tagPills: tagPills,
    editField: editField,
    editRelease: editRelease
  };
})(window);
