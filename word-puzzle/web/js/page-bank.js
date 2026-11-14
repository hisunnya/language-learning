/* ============================================================
   page-bank.js —— 题库工作台
   ============================================================ */
(function () {
  'use strict';

  var sel = null;
  var materials = [];
  var banks = [];
  var files = [];

  function esc(s) { return API.esc(s); }
  function t(key, params) { return WPI18N.t(key, params); }
  var loaded = { materials: false, banks: false, files: false };   /* 取回来之前别把「加载中」换成「没有」 */

  /* ---------------- 上传 ---------------- */

  function upload(file) {
    if (!file) return;
    var fd = new FormData();
    fd.append('file', file, file.name);
    var msg = document.getElementById('upMsg');
    msg.className = 'msg on info';
    msg.textContent = t('bank_uploading', { name: file.name });
    API.upload('/api/materials', fd).then(function (res) {
      var s = res.summary || {};
      var fmtName = { docx: 'Word', pdf: 'PDF', csv: 'CSV', tsv: 'TSV',
                      txt: 'TXT', json: 'JSON', md: 'Markdown' };
      msg.className = 'msg on ok';
      msg.textContent = t('bank_uploaded', {
        name: res.material.name, words: s.word_count, units: s.unit_count,
        fmt: fmtName[res.material.fmt] ? ' (' + fmtName[res.material.fmt] + ')' : ''
      });
      if (s.units && s.units.length) {
        var preview = s.units.slice(0, 3).map(function (u) {
          return u.name + '(' + u.count + ')';
        }).join(', ');
        msg.textContent += t('bank_uploadedMore', { preview: preview, more: s.units.length > 3 ? t('bank_etc') : '' });
      }
      API.toast(t('bank_uploadToast'));
      loadMaterials();
    }).catch(function (e) {
      msg.className = 'msg on err';
      msg.textContent = t('bank_uploadFailed', { error: e.message });
    });
  }

  /* ---------------- 列表渲染 ---------------- */

  function renderMaterials() {
    var box = document.getElementById('matList');
    if (!materials.length) {
      box.innerHTML = '<div class="empty">' + esc(t('bank_matEmpty')) + '</div>';
      return;
    }
    box.innerHTML = materials.map(function (m) {
      return '<div class="item">' +
        '  <div class="main"><b>' + esc(m.name) + '</b>' +
        '    <small>' + esc(t('bank_matCounts', { file: m.filename, words: m.word_count, units: m.unit_count,
                                              time: API.fmtTime(m.created_at) })) + '</small></div>' +
        '  <div class="ops">' +
        '    <button class="btn sm" data-use="' + m.id + '">' + esc(t('bank_useMat')) + '</button>' +
        '    <button class="btn sm danger" data-del="' + m.id + '">' + esc(t('bank_delete')) + '</button>' +
        '  </div></div>';
    }).join('');

    box.querySelectorAll('[data-use]').forEach(function (b) {
      b.onclick = function () {
        document.getElementById('sourceSel').value = 'material';
        onSourceChange();
        document.getElementById('matSel').value = b.dataset.use;
        API.toast(t('bank_matChosen'));
      };
    });
    box.querySelectorAll('[data-del]').forEach(function (b) {
      b.onclick = function () {
        if (!confirm(t('bank_confirmDelMat'))) return;
        API.del('/api/materials/' + b.dataset.del).then(loadMaterials)
          .catch(function (e) { API.toast(e.message); });
      };
    });
  }

  function renderBanks() {
    var box = document.getElementById('bankList');
    if (!banks.length) {
      box.innerHTML = '<div class="empty">' + esc(t('bank_bankEmpty')) + '</div>';
      return;
    }
    box.innerHTML = banks.map(function (b) {
      return '<div class="item">' +
        '  <div class="main"><b>' + esc(b.title) + '</b>' +
        '    <small>' + esc(t('bank_bankCounts', { words: b.word_count, units: b.unit_count,
                                               per: b.pairs_per_level ? t('bank_perLevel', { n: b.pairs_per_level }) : '',
                                               time: API.fmtTime(b.created_at) })) + '</small></div>' +
        '  <div class="ops">' +
        '    <a class="btn sm" href="' + esc(API.path('/play.html?bank=' + b.id)) + '">' + esc(t('bank_play')) + '</a>' +
        '    <button class="btn sm ghost" data-offline="' + b.id + '">' + esc(t('bank_offline')) + '</button>' +
        '    <button class="btn sm danger" data-del="' + b.id + '">' + esc(t('bank_delete')) + '</button>' +
        '  </div></div>';
    }).join('');

    box.querySelectorAll('[data-offline]').forEach(function (b) {
      b.onclick = function () { makeOffline(parseInt(b.dataset.offline, 10), b); };
    });
    box.querySelectorAll('[data-del]').forEach(function (b) {
      b.onclick = function () {
        if (!confirm(t('bank_confirmDelBank'))) return;
        API.del('/api/banks/' + b.dataset.del).then(loadBanks)
          .catch(function (e) { API.toast(e.message); });
      };
    });
  }

  function renderFiles() {
    var box = document.getElementById('fileList');
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
        API.download(b.dataset.download, b.dataset.name).catch(function () {
          API.toast(t('bank_dlBlocked'), 6000);
        });
      };
    });
  }

  /* ---------------- 数据加载 ---------------- */

  function loadMaterials() {
    return API.get('/api/materials').then(function (res) {
      materials = res.materials || [];
      loaded.materials = true;
      renderMaterials();
      var selBox = document.getElementById('matSel');
      var keep = selBox.value;
      selBox.innerHTML = materials.map(function (m) {
        return '<option value="' + m.id + '">' +
          esc(t('bank_matOption', { name: m.name, words: m.word_count })) + '</option>';
      });
      if (keep) selBox.value = keep;
    }).catch(function (e) { API.toast(e.message); });
  }

  function loadBanks() {
    return API.get('/api/banks').then(function (res) {
      banks = res.banks || [];
      loaded.banks = true;
      renderBanks();
    }).catch(function (e) { API.toast(e.message); });
  }

  function loadFiles() {
    return API.get('/api/offline').then(function (res) {
      files = res.files || [];
      loaded.files = true;
      renderFiles();
    }).catch(function () { });
  }

  /* ---------------- 生成 ---------------- */

  function payload() {
    var p = sel.get();
    p.source = document.getElementById('sourceSel').value;
    if (p.source === 'material') {
      p.material_id = parseInt(document.getElementById('matSel').value, 10) || 0;
    }
    p.pairs_per_level = pairsPerLevel();
    if (document.getElementById('splitNew').checked) p.split_units = true;     /* 一个单元一个题库 */
    return p;
  }

  /* 「每关词数」：默认 12，输错了也按默认值来 */
  function pairsPerLevel() {
    var input = document.getElementById('pairsPerLevel');
    var value = input ? parseInt(input.value, 10) : 12;
    if (!value || value < 4 || value > 40) return 12;
    return value;
  }

  function makeOffline(bankId, button) {
    if (button) { button.disabled = true; button.textContent = t('bank_synthesizing'); }
    API.toast(t('bank_synthToast'), 600000);
    return API.post('/api/banks/' + bankId + '/offline', {}).then(function (res) {
      API.toast(t('bank_generated', { name: res.filename }));
      API.download(res.url, res.filename).catch(function () {
        API.toast(t('bank_dlBlocked2'), 6000);
      });
      loadFiles();
      return res;
    }).catch(function (e) {
      API.toast(e.message, 12000);
      throw e;
    }).finally(function () {
      if (button) { button.disabled = false; button.textContent = t('bank_offline'); }
    });
  }

  function onSourceChange() {
    var isMat = document.getElementById('sourceSel').value === 'material';
    document.getElementById('matField').style.display = isMat ? '' : 'none';
    document.getElementById('levelBox').style.display = isMat ? 'none' : '';
    updateInfo();
  }

  function updateInfo() {
    if (!sel) return;
    var s = sel.summary();
    var box = document.getElementById('selInfo');
    if (document.getElementById('sourceSel').value === 'material') {
      box.textContent = t('bank_useMatInfo');
      return;
    }
    if (!s.units) {
      box.textContent = t('bank_noContent');
      return;
    }
    var per = pairsPerLevel();
    box.textContent = t('bank_range', { path: s.path, units: s.units, words: s.words, per: per,
                                        levels: Math.ceil(s.words / per) });
  }

  /* 切换语言：列表和说明是脚本画的，要重画（静态文字由页眉换） */
  WPI18N.onChange(function () {
    if (loaded.materials) {
      renderMaterials();
      var selBox = document.getElementById('matSel');
      Array.prototype.forEach.call(selBox.options, function (o, i) {
        var m = materials[i];
        if (m) o.textContent = t('bank_matOption', { name: m.name, words: m.word_count });
      });
    }
    if (loaded.banks) renderBanks();
    if (loaded.files) renderFiles();
    updateInfo();
  });

  /* ---------------- 启动 ---------------- */

  document.addEventListener('DOMContentLoaded', function () {
    sel = new Selector('#levelBox', { onChange: updateInfo });

    sel.init().then(function () {
      updateInfo();
    }).catch(function (e) { API.toast(e.message); });

    document.getElementById('sourceSel').onchange = onSourceChange;
    document.getElementById('matSel').onchange = updateInfo;

    document.getElementById('btnUpload').onclick = function () {
      document.getElementById('fileInput').click();
    };
    document.getElementById('fileInput').onchange = function () {
      var f = this.files && this.files[0];
      this.value = '';
      upload(f);
    };

    document.getElementById('btnMake').onclick = function () {
      var btn = this;
      btn.disabled = true;
      API.post('/api/banks', payload()).then(function (res) {
        API.toast(res.banks && res.banks.length > 1 ? t('bank_madeMany', { n: res.banks.length }) : t('bank_madeBank', { title: res.bank.title }));
        loadBanks();
      }).catch(function (e) {
        API.toast(e.message);
      }).finally(function () { btn.disabled = false; });
    };

    document.getElementById('btnOffline').onclick = function () {
      var btn = this;
      btn.disabled = true;
      btn.textContent = t('bank_making');
      API.post('/api/banks', payload()).then(function (res) {
        return makeOffline(res.bank.id);
      }).catch(function (e) {
        API.toast(e.message);
      }).finally(function () {
        btn.disabled = false;
        btn.textContent = t('bank_offlineBtn');
        loadBanks();
      });
    };

    loadBanks();
    // 资料和离线页只有管理员能用；学生的账号调这两个接口会被拒绝，所以不去调
    AuthUI.ready.then(function () {
      if (AuthUI.isAdmin()) { loadMaterials(); loadFiles(); }
    });
  });
})();
