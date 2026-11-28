/* ============================================================
   page-bank.js —— 题库工作台
   ------------------------------------------------------------
   三个标签页（网址 #banks #new #offline 可以收藏和直接打开）：
     当前题库 —— 看、分类、标签、批量开放、删除、玩；
     新建题库 —— 三步：Step 1 词表从哪来 → Step 2 定义题库 → Step 3 开放给谁（可以稍后再设）；
     离线测试 —— 把已有题库导出成单个 HTML 文件，只导出，不新建题库。
   「词表文件」是上传后保存的原始词表；「题库」是按单元和关卡切好、可以玩的内容。
   ============================================================ */
(function () {
  'use strict';

  var TABS = ['banks', 'new', 'offline'];
  var SUFFIX = { banks: 'Banks', 'new': 'New', offline: 'Offline' };
  var DEFAULT_LEVEL1 = '我的词表';      /* 上传的词表没写学段 / 年级 / 册别时存进去的默认名（是数据，不翻译） */
  var DEFAULT_LEVEL3 = '全部';
  var DEFAULT_LEVEL4 = '全部单元';

  var sel = null;
  var materials = [];
  var banks = [];
  var files = [];
  var allTags = [];
  var loaded = { materials: false, banks: false, files: false };   /* 取回来之前别把「加载中」换成「没有」 */
  var uploaded = null;           /* 刚上传的词表（Step 1 里「上传新词表」的结果） */
  var highlight = {};            /* 刚生成的题库编号：在「当前题库」里高亮 */
  var notice = null;             /* 「当前题库」顶部的提示：{ ids, category } */
  var current = 'banks';

  function esc(s) { return API.esc(s); }
  function t(key, params) { return WPI18N.t(key, params); }
  function $(id) { return document.getElementById(id); }
  function tagsEnabled() { return !!(AuthUI.info() && AuthUI.info().enabled); }

  /* ---------------- 标签页 ---------------- */

  function tabFromHash() {
    var name = (location.hash || '').replace('#', '').split(new RegExp('[?&]'))[0];
    return TABS.indexOf(name) >= 0 ? name : 'banks';
  }

  function showTab(name, setHash) {
    if (TABS.indexOf(name) < 0) name = 'banks';
    if (name !== 'banks' && current === 'banks') { notice = null; highlight = {}; }     /* 离开「当前题库」就不再显示刚生成的提示和高亮 */
    current = name;
    TABS.forEach(function (n) {
      var on = n === name;
      var tab = $('tab' + SUFFIX[n]), panel = $('panel' + SUFFIX[n]);
      tab.classList.toggle('active', on);
      tab.setAttribute('aria-selected', String(on));
      tab.tabIndex = on ? 0 : -1;
      panel.hidden = !on;
    });
    if (setHash !== false && location.hash !== '#' + name) {
      try { history.replaceState(null, '', '#' + name); } catch (e) { location.hash = '#' + name; }
    }
    if (name === 'banks' && loaded.banks) renderBanks();
    if (name === 'offline') { fillOfflineSelect(); loadFiles(); }
    if (name === 'new') updateInfo();
  }

  /* ---------------- 当前题库 ---------------- */

  function matchesFilter(b) {
    var q = $('bankFilter').value.trim().toLowerCase();
    if ($('onlyClosed').checked && tagsEnabled() && (b.tags || []).length) return false;
    if (!q) return true;
    var hay = [b.title, b.category || '', (b.tags || []).join(' ')].join(' ').toLowerCase();
    return hay.indexOf(q) >= 0;
  }

  function counts(b) {
    return t('bank_bankCounts', { words: b.word_count, units: b.unit_count,
                                  per: b.pairs_per_level ? t('bank_perLevel', { n: b.pairs_per_level }) : '',
                                  time: API.fmtTime(b.created_at) });
  }

  function bankItem(b) {
    var src = b.source === 'material' ? '<span class="pill gray">' + esc(t('home_srcMaterial')) + '</span>'
                                      : '<span class="pill">' + esc(t('home_srcSeed')) + '</span>';
    var tagPart = '';
    if (tagsEnabled()) {
      tagPart = ' ' + (BankPanels.tagPills(b) || '<span class="pill warn">' + esc(t('home_noTags')) + '</span>');
    }
    /* 老师看到的题库有三种来历：自己建的、别人共享给他的、所有老师共用的内置题库（超管什么都管，不标） */
    var rel = b.relation || 'owner';
    if (rel === 'shared') src += ' <span class="pill good">' + esc(t('bank_relShared')) + '</span>';
    var canEdit = rel === 'owner', canDelete = rel !== 'system';
    var type = ['spell', 'order', 'verb'].indexOf(b.game_type) >= 0 ? b.game_type : 'match';
    if (type !== 'match') src += ' <span class="pill type">' + esc(t('type_' + type)) + '</span>';
    var ops = type === 'match'
      ? '<a class="btn sm ghost" href="' + esc(API.path('/practice.html?bank=' + b.id)) + '">' + esc(t('bank_practice')) + '</a>' +
        '<a class="btn sm" href="' + esc(API.path('/play.html?bank=' + b.id)) + '">' + esc(t('bank_play')) + '</a>'
      : '<a class="btn sm" href="' + esc(API.path('/' + type + '.html?bank=' + b.id)) + '">' + esc(t('home_start')) + '</a>';
    if (tagsEnabled()) {
      ops += (canEdit ? '<button class="btn sm ghost" data-cat="' + b.id + '">' + esc(t('home_catBtn')) + '</button>' : '') +
             '<button class="btn sm ghost" data-tags="' + b.id + '">' + esc(t('home_tagsBtn')) + '</button>';
    }
    ops += '<button class="btn sm ghost" data-offline="' + b.id + '">' + esc(t('bank_toOffline')) + '</button>';
    if (canDelete) {
      ops += '<button class="btn sm danger" data-del="' + b.id + '" data-rel="' + rel + '">' +
             esc(t(rel === 'shared' ? 'bank_removeShared' : 'bank_delete')) + '</button>';
    }
    return '<div class="item' + (highlight[b.id] ? ' flash' : '') + '" data-bank-row="' + b.id + '">' +
      '  <div class="main"><b>' + esc(b.title) + '</b> ' + src + tagPart +
      '    <small>' + esc(type === 'match' ? counts(b) : t('home_itemCounts', { n: b.word_count, time: API.fmtTime(b.created_at) })) + '</small></div>' +
      '  <div class="ops">' + ops + '</div></div>';
  }

  function renderNotice() {
    var box = $('bankNotice');
    if (!notice) { box.className = 'msg info'; box.innerHTML = ''; return; }
    var made = notice.ids.length > 1 ? t('bank_madeMany', { n: notice.ids.length }) : t('bank_madeBank', { title: notice.title });
    var html = '<span>' + esc(made) + '</span>';
    if (tagsEnabled() && notice.noTags) {
      html += ' <span>' + esc(t('bank_noTagsNotice')) + '</span> ';
      if (notice.ids.length > 1 && notice.category) {
        html += '<button class="btn sm gold" type="button" data-notice-release="' + esc(notice.category) + '">' + esc(t('rel_button')) + '</button>';
      } else {
        html += '<button class="btn sm gold" type="button" data-notice-tags="' + notice.ids[0] + '">' + esc(t('home_tagsBtn')) + '</button>';
      }
    }
    box.className = 'msg on ok';
    box.innerHTML = html;
  }

  function renderBanks() {
    var box = $('bankList');
    var pill = $('bankCount');
    pill.hidden = !banks.length;
    pill.textContent = banks.length;
    renderNotice();
    if (!banks.length) {
      box.innerHTML = '<div class="empty">' + esc(t('bank_bankEmpty')) +
        '<br><button class="btn gold" type="button" data-go-new style="margin-top:10px">' + esc(t('bank_emptyCta')) + '</button></div>';
      return;
    }
    var shown = banks.filter(matchesFilter);
    if (!shown.length) { box.innerHTML = '<div class="empty">' + esc(t('bank_noMatch')) + '</div>'; return; }
    box.innerHTML = BankPanels.groupByCategory(shown).map(function (g) {
      var canRelease = tagsEnabled() && g.name && g.banks.length > 1;
      var head = '<div class="sub" style="margin:14px 0 4px;display:flex;align-items:center;gap:10px"><b>' +
        esc(g.name || t('home_catNone')) + '</b>' +
        (canRelease ? '<button class="btn sm ghost" data-release="' + esc(g.name) + '">' + esc(t('rel_button')) + '</button>' : '') + '</div>';
      return head + g.banks.map(bankItem).join('');
    }).join('');
  }

  function bindBankList() {
    var box = $('bankList');
    box.addEventListener('click', function (ev) {
      var el = ev.target.closest('button');
      if (!el) return;
      if (el.hasAttribute('data-go-new')) { showTab('new'); return; }
      if (el.dataset.cat) { BankPanels.editField('category', parseInt(el.dataset.cat, 10)); return; }
      if (el.dataset.tags) { BankPanels.editField('tags', parseInt(el.dataset.tags, 10)); return; }
      if (el.dataset.release) { BankPanels.editRelease(el.dataset.release); return; }
      if (el.dataset.offline) { goOffline(parseInt(el.dataset.offline, 10)); return; }
      if (el.dataset.del) {
        if (!confirm(t(el.dataset.rel === 'shared' ? 'bank_confirmRemoveShared' : 'bank_confirmDelBank'))) return;
        API.del('/api/banks/' + el.dataset.del).then(function (res) {
          API.toast(t(res.done === 'unshared' ? 'bank_removedShared' : 'bank_deletedSoft'));
          return loadBanks();
        }).catch(function (e) { API.toast(e.message); });
      }
    });
    $('bankNotice').addEventListener('click', function (ev) {
      var el = ev.target.closest('button');
      if (!el) return;
      if (el.dataset.noticeTags) BankPanels.editField('tags', parseInt(el.dataset.noticeTags, 10));
      if (el.dataset.noticeRelease) BankPanels.editRelease(el.dataset.noticeRelease);
    });
    $('bankFilter').addEventListener('input', renderBanks);
    $('onlyClosed').addEventListener('change', renderBanks);
  }

  /* ---------------- 离线测试 ---------------- */

  function fillOfflineSelect() {
    var box = $('offBank');
    var keep = box.value;
    box.innerHTML = banks.map(function (b) { return '<option value="' + b.id + '">' + esc(b.title) + '</option>'; }).join('');
    if (keep) box.value = keep;
    $('btnOfflineMake').disabled = !banks.length;
  }

  function goOffline(id) {
    fillOfflineSelect();
    $('offBank').value = String(id);
    showTab('offline');
  }

  function renderFiles() {
    var box = $('fileList');
    if (!files.length) {
      box.innerHTML = '<div class="empty">' + esc(t('bank_filesEmpty')) + '</div>';
      return;
    }
    box.innerHTML = files.map(function (f) {
      return '<div class="item">' +
        '  <div class="main"><b>' + esc(f.name) + '</b>' +
        '    <small>' + esc(t('bank_fileMeta', { size: f.size, time: f.created_at })) + '</small></div>' +
        '  <div class="ops">' +
        '    <button class="btn sm" data-download="' + esc(f.url) + '" data-name="' + esc(f.name) + '">' + esc(t('bank_download')) + '</button>' +
        '    <a class="btn sm ghost" href="' + esc(API.path(f.url + '?inline=1')) + '" target="_blank" rel="noopener">' + esc(t('bank_open')) + '</a>' +
        '  </div></div>';
    }).join('');
    box.querySelectorAll('[data-download]').forEach(function (b) {
      b.onclick = function () {
        API.download(b.dataset.download, b.dataset.name).catch(function () { API.toast(t('bank_dlBlocked'), 6000); });
      };
    });
  }

  function offlineKind() {
    var r = document.querySelector('input[name="offKind"]:checked');
    return r && r.value === 'practice' ? 'practice' : 'game';
  }

  function makeOffline(bankId, button) {
    if (button) { button.disabled = true; button.textContent = t('bank_synthesizing'); }
    API.toast(t('bank_synthToast'), 600000);
    return API.post('/api/banks/' + bankId + '/offline', { kind: offlineKind() }).then(function (res) {
      API.toast(t('bank_generated', { name: res.filename }));
      API.download(res.url, res.filename).catch(function () { API.toast(t('bank_dlBlocked2'), 6000); });
      loadFiles();
      return res;
    }).catch(function (e) {
      API.toast(e.message, 12000);
    }).finally(function () {
      if (button) { button.disabled = false; button.textContent = t('bank_offlineMake'); }
    });
  }

  /* ---------------- 新建题库：Step 1 词表从哪来 ---------------- */

  function source() {
    var r = document.querySelector('input[name="source"]:checked');
    return r ? r.value : 'seed';
  }

  function materialById(id) {
    return materials.filter(function (m) { return m.id === id; })[0] || null;
  }

  /* 当前选中的词表（上传的或以前传过的）；内置词库返回 null */
  function chosenMaterial() {
    if (source() === 'upload') return uploaded;
    if (source() === 'material') return materialById(parseInt($('matSel').value, 10));
    return null;
  }

  function onSourceChange() {
    var s = source();
    $('srcUpload').hidden = s !== 'upload';
    $('srcMaterial').hidden = s !== 'material';
    $('seedFields').hidden = s !== 'seed';
    $('materialFields').hidden = s === 'seed';
    var m = chosenMaterial();
    if (m && !$('bankTitle').value) $('bankTitle').value = m.name;
    updateInfo();
  }

  function renderMaterials() {
    var box = $('matList');
    if (!materials.length) { box.innerHTML = '<div class="empty">' + esc(t('bank_matEmpty')) + '</div>'; return; }
    box.innerHTML = materials.map(function (m) {
      return '<div class="item">' +
        '  <div class="main"><b>' + esc(m.name) + '</b>' +
        '    <small>' + esc(t('bank_matCounts', { file: m.filename, words: m.word_count, units: m.unit_count,
                                              time: API.fmtTime(m.created_at) })) + '</small></div>' +
        '  <div class="ops"><button class="btn sm danger" data-del="' + m.id + '">' + esc(t('bank_delete')) + '</button></div></div>';
    }).join('');
    box.querySelectorAll('[data-del]').forEach(function (b) {
      b.onclick = function () {
        if (!confirm(t('bank_confirmDelMat'))) return;
        API.del('/api/materials/' + b.dataset.del).then(loadMaterials).catch(function (e) { API.toast(e.message); });
      };
    });
  }

  function fillMaterialSelect() {
    var box = $('matSel');
    var keep = box.value;
    box.innerHTML = materials.map(function (m) {
      return '<option value="' + m.id + '">' + esc(t('bank_matOption', { name: m.name, words: m.word_count })) + '</option>';
    }).join('');
    if (keep) box.value = keep;
  }

  function upload(file, quick) {
    if (!file) return Promise.resolve(null);
    var fd = new FormData();
    fd.append('file', file, file.name);
    var msg = $('upMsg');
    msg.className = 'msg on info';
    msg.textContent = t('bank_uploading', { name: file.name });
    return API.upload('/api/materials', fd).then(function (res) {
      var s = res.summary || {};
      var fmtName = { docx: 'Word', pdf: 'PDF', csv: 'CSV', tsv: 'TSV', txt: 'TXT', json: 'JSON', md: 'Markdown' };
      uploaded = { id: res.material.id, name: res.material.name, word_count: s.word_count, unit_count: s.unit_count };
      msg.className = 'msg on ok';
      msg.textContent = t('bank_uploaded', {
        name: res.material.name, words: s.word_count, units: s.unit_count,
        fmt: fmtName[res.material.fmt] ? ' (' + fmtName[res.material.fmt] + ')' : ''
      });
      if (s.units && s.units.length) {
        var preview = s.units.slice(0, 3).map(function (u) { return u.name + '(' + u.count + ')'; }).join(', ');
        msg.textContent += t('bank_uploadedMore', { preview: preview, more: s.units.length > 3 ? t('bank_etc') : '' });
      }
      $('bankTitle').value = res.material.name;
      loadMaterials();
      updateInfo();
      return uploaded;
    }).catch(function (e) {
      msg.className = 'msg on err';
      msg.textContent = t('bank_uploadFailed', { error: e.message });
      return null;
    });
  }

  /* ---------------- 新建题库：Step 2 / Step 3 和生成 ---------------- */

  function pairsPerLevel() {
    var input = $('pairsPerLevel');
    var value = input ? parseInt(input.value, 10) : 9;
    if (!value || value < 4 || value > 40) return 9;
    return value;
  }

  /* 现在这些设置能不能生成；不能就返回原因（给「生成题库」旁边的提示用） */
  function problem() {
    var s = source();
    if (s === 'seed') {
      return sel && sel.summary().units ? '' : t('bank_noContent');
    }
    if (!chosenMaterial()) return t(s === 'upload' ? 'bank_needUpload' : 'bank_needMaterial');
    if (!$('bankTitle').value.trim()) return t('bank_needTitle');
    return '';
  }

  function updateInfo() {
    if (!sel) return;
    var per = pairsPerLevel(), split = $('splitNew').checked;
    var box = $('selInfo');
    var m = chosenMaterial();
    if (source() === 'seed') {
      var s = sel.summary();
      box.textContent = s.units ? t('bank_range', { path: s.path, units: s.units, words: s.words, per: per,
                                                    levels: Math.ceil(s.words / per) }) +
        (split ? t('bank_willMake', { n: s.units }) : '') : t('bank_noContent');
    } else if (m && m.word_count) {
      box.textContent = t('bank_matRange', { name: m.name, units: m.unit_count, words: m.word_count, per: per,
                                             levels: Math.ceil(m.word_count / per) }) +
        (split ? t('bank_willMake', { n: m.unit_count }) : '');
    } else {
      box.textContent = '';
    }
    var why = problem();
    $('btnMake').disabled = !!why;
    $('makeHint').textContent = why;
  }

  function buildPayload() {
    var p, m = chosenMaterial();
    if (source() === 'seed') {
      p = sel.get();
      p.source = 'seed';
    } else {
      p = {
        source: 'material', material_id: m.id, title: $('bankTitle').value.trim() || m.name,
        level1: $('lv1').value.trim() || DEFAULT_LEVEL1, level2: $('lv2').value.trim() || m.name,
        level3: $('lv3').value.trim() || DEFAULT_LEVEL3, level4: DEFAULT_LEVEL4, unit_mode: 'all'
      };
    }
    p.pairs_per_level = pairsPerLevel();
    if ($('splitNew').checked) p.split_units = true;
    var cat = $('newCategory').value.trim();
    if (cat) p.category = cat;
    var tags = $('newTags').value.trim();
    if (tags && tagsEnabled()) p.tags = tags;
    return p;
  }

  /* 生成成功之后：回到「当前题库」，高亮新题库，没设标签就提醒 */
  function afterMade(res, payload) {
    var made = res.banks && res.banks.length ? res.banks : [res.bank];
    highlight = {};
    made.forEach(function (b) { highlight[b.id] = true; });
    notice = { ids: made.map(function (b) { return b.id; }), title: made[0].title, category: made[0].category || '',
               noTags: !(payload.tags || '').trim() };
    return loadBanks().then(function () {
      showTab('banks');
      var row = document.querySelector('[data-bank-row="' + made[0].id + '"]');
      if (row && row.scrollIntoView) row.scrollIntoView({ block: 'center', behavior: 'smooth' });
    });
  }

  function make() {
    var why = problem();
    if (why) { $('makeHint').textContent = why; return; }
    var payload = buildPayload();
    var btn = $('btnMake'), msg = $('makeMsg');
    btn.disabled = true;
    msg.className = 'msg';
    API.post('/api/banks', payload).then(function (res) { return afterMade(res, payload); })
      .catch(function (e) {
        msg.className = 'msg on err';
        msg.textContent = e.message;
      }).finally(function () { updateInfo(); });
  }

  /* 快速上传并生成：上传后按默认设置直接生成（识别出的单元、每关 9 词、先不开放） */
  function quick(file) {
    upload(file, true).then(function (m) {
      if (!m) return;
      var payload = {
        source: 'material', material_id: m.id, title: m.name, level1: DEFAULT_LEVEL1, level2: m.name,
        level3: DEFAULT_LEVEL3, level4: DEFAULT_LEVEL4, unit_mode: 'all', pairs_per_level: pairsPerLevel(),
        split_units: m.unit_count > 1
      };
      return API.post('/api/banks', payload).then(function (res) { return afterMade(res, payload); })
        .catch(function (e) {
          var msg = $('upMsg');
          msg.className = 'msg on err';
          msg.textContent = e.message;
        });
    });
  }

  /* ---------------- 数据加载 ---------------- */

  function loadMaterials() {
    return API.get('/api/materials').then(function (res) {
      materials = res.materials || [];
      loaded.materials = true;
      renderMaterials();
      fillMaterialSelect();
      updateInfo();
    }).catch(function (e) { API.toast(e.message); });
  }

  function loadBanks() {
    return API.get('/api/banks').then(function (res) {
      banks = res.banks || [];
      loaded.banks = true;
      BankPanels.set(banks, loadBanks);
      renderBanks();
      if (current === 'offline') fillOfflineSelect();
    }).catch(function (e) { API.toast(e.message); });
  }

  function loadFiles() {
    return API.get('/api/offline').then(function (res) {
      files = res.files || [];
      loaded.files = true;
      renderFiles();
    }).catch(function () { });
  }

  function loadTags() {
    if (!tagsEnabled()) { $('tagsField').hidden = true; return; }
    API.get('/api/admin/tags').then(function (res) {
      allTags = res.tags || [];
      $('tagChips').innerHTML = allTags.map(function (x) {
        return '<button class="chip" type="button" data-chip="' + esc(x.tag) + '">' + esc(x.tag) + '</button>';
      }).join('');
    }).catch(function () { });
  }

  /* 切换语言：列表和说明是脚本画的，要重画（静态文字由页眉换） */
  WPI18N.onChange(function () {
    if (loaded.materials) { renderMaterials(); fillMaterialSelect(); }
    if (loaded.banks) renderBanks();
    if (loaded.files) renderFiles();
    updateInfo();
  });

  /* ---------------- 启动 ---------------- */

  document.addEventListener('DOMContentLoaded', function () {
    API.templateLinks();                       /* 模板下载链接 */
    TABS.forEach(function (n) {
      $('tab' + SUFFIX[n]).addEventListener('click', function () { showTab(n); });
    });
    $('bankTabs').addEventListener('keydown', function (ev) {
      if (ev.key !== 'ArrowRight' && ev.key !== 'ArrowLeft') return;
      var i = TABS.indexOf(current) + (ev.key === 'ArrowRight' ? 1 : -1);
      var next = TABS[(i + TABS.length) % TABS.length];
      showTab(next);
      $('tab' + SUFFIX[next]).focus();
    });
    window.addEventListener('hashchange', function () { var n = tabFromHash(); if (n !== current) showTab(n, false); });

    bindBankList();

    sel = new Selector('#levelBox', { onChange: updateInfo });
    sel.init().then(updateInfo).catch(function (e) { API.toast(e.message); });

    Array.prototype.forEach.call(document.querySelectorAll('input[name="source"]'), function (r) { r.onchange = onSourceChange; });
    $('matSel').onchange = function () { var m = chosenMaterial(); if (m) $('bankTitle').value = m.name; updateInfo(); };
    ['pairsPerLevel', 'splitNew', 'bankTitle'].forEach(function (id) {
      $(id).addEventListener(id === 'splitNew' ? 'change' : 'input', updateInfo);
    });
    $('btnPick').onclick = function () { $('fileInput').dataset.mode = 'pick'; $('fileInput').click(); };
    $('btnQuick').onclick = function () { $('fileInput').dataset.mode = 'quick'; $('fileInput').click(); };
    $('fileInput').onchange = function () {
      var f = this.files && this.files[0];
      var mode = this.dataset.mode;
      this.value = '';
      if (mode === 'quick') quick(f); else upload(f);
    };
    $('tagChips').addEventListener('click', function (ev) {
      var chip = ev.target.closest('[data-chip]');
      if (!chip) return;
      var cur = $('newTags').value.split(new RegExp('[,，、;；\\n]+')).map(function (x) { return x.trim(); }).filter(Boolean);
      if (cur.indexOf(chip.getAttribute('data-chip')) < 0) cur.push(chip.getAttribute('data-chip'));
      $('newTags').value = cur.join(', ');
    });
    $('btnMake').onclick = make;
    $('btnOfflineMake').onclick = function () {
      var id = parseInt($('offBank').value, 10);
      if (id) makeOffline(id, this);
    };

    loadBanks();
    // 词表文件、离线页和标签只有管理员能用；学生的账号调这些接口会被拒绝，所以不去调
    AuthUI.ready.then(function () {
      if (AuthUI.isAdmin()) { loadMaterials(); loadFiles(); loadTags(); }
      renderBanks();
    });
    showTab(tabFromHash(), false);
    onSourceChange();
  });

  /* 给行为测试用（tests/js/bank_workbench.test.js）；页面本身不用 */
  window.WPBankWorkbench = { buildPayload: buildPayload, problem: problem, tabFromHash: tabFromHash, source: source };
})();
