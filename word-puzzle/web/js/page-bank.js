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

  /* ---------------- 上传 ---------------- */

  function upload(file) {
    if (!file) return;
    var fd = new FormData();
    fd.append('file', file, file.name);
    var msg = document.getElementById('upMsg');
    msg.className = 'msg on info';
    msg.textContent = '正在上传 ' + file.name + '…';
    API.upload('/api/materials', fd).then(function (res) {
      var s = res.summary || {};
      var fmtName = { docx: 'Word', pdf: 'PDF', csv: 'CSV', tsv: 'TSV',
                      txt: 'TXT', json: 'JSON', md: 'Markdown' };
      msg.className = 'msg on ok';
      msg.textContent = '上传成功：' + res.material.name + ' · ' +
        s.word_count + ' 个词条 · ' + s.unit_count + ' 个单元' +
        (fmtName[res.material.fmt] ? '（' + fmtName[res.material.fmt] + '）' : '');
      if (s.units && s.units.length) {
        var preview = s.units.slice(0, 3).map(function (u) {
          return u.name + '(' + u.count + ')';
        }).join('、');
        msg.textContent += ' · ' + preview +
          (s.units.length > 3 ? ' 等' : '');
      }
      API.toast('上传成功');
      loadMaterials();
    }).catch(function (e) {
      msg.className = 'msg on err';
      msg.textContent = '上传失败：' + e.message;
    });
  }

  /* ---------------- 列表渲染 ---------------- */

  function renderMaterials() {
    var box = document.getElementById('matList');
    if (!materials.length) {
      box.innerHTML = '<div class="empty">还没有上传资料，点上面的「上传题库」开始</div>';
      return;
    }
    box.innerHTML = materials.map(function (m) {
      return '<div class="item">' +
        '  <div class="main"><b>' + esc(m.name) + '</b>' +
        '    <small>' + esc(m.filename) + ' · ' + m.word_count + ' 词 · ' +
        m.unit_count + ' 单元 · ' + esc(API.fmtTime(m.created_at)) + '</small></div>' +
        '  <div class="ops">' +
        '    <button class="btn sm" data-use="' + m.id + '">用它生成题库</button>' +
        '    <button class="btn sm danger" data-del="' + m.id + '">删除</button>' +
        '  </div></div>';
    }).join('');

    box.querySelectorAll('[data-use]').forEach(function (b) {
      b.onclick = function () {
        document.getElementById('sourceSel').value = 'material';
        onSourceChange();
        document.getElementById('matSel').value = b.dataset.use;
        API.toast('已选择该资料');
      };
    });
    box.querySelectorAll('[data-del]').forEach(function (b) {
      b.onclick = function () {
        if (!confirm('确定删除这份资料？')) return;
        API.del('/api/materials/' + b.dataset.del).then(loadMaterials)
          .catch(function (e) { API.toast(e.message); });
      };
    });
  }

  function renderBanks() {
    var box = document.getElementById('bankList');
    if (!banks.length) {
      box.innerHTML = '<div class="empty">还没有题库</div>';
      return;
    }
    box.innerHTML = banks.map(function (b) {
      return '<div class="item">' +
        '  <div class="main"><b>' + esc(b.title) + '</b>' +
        '    <small>' + b.word_count + ' 词 · ' + b.unit_count + ' 单元 · ' +
        esc(API.fmtTime(b.created_at)) + '</small></div>' +
        '  <div class="ops">' +
        '    <a class="btn sm" href="' + esc(API.path('/play.html?bank=' + b.id)) + '">开始游戏</a>' +
        '    <button class="btn sm ghost" data-offline="' + b.id + '">生成离线测试</button>' +
        '    <button class="btn sm danger" data-del="' + b.id + '">删除</button>' +
        '  </div></div>';
    }).join('');

    box.querySelectorAll('[data-offline]').forEach(function (b) {
      b.onclick = function () { makeOffline(parseInt(b.dataset.offline, 10)); };
    });
    box.querySelectorAll('[data-del]').forEach(function (b) {
      b.onclick = function () {
        if (!confirm('确定删除这个题库？')) return;
        API.del('/api/banks/' + b.dataset.del).then(loadBanks)
          .catch(function (e) { API.toast(e.message); });
      };
    });
  }

  function renderFiles() {
    var box = document.getElementById('fileList');
    if (!files.length) {
      box.innerHTML = '<div class="empty">还没有生成过</div>';
      return;
    }
    box.innerHTML = files.map(function (f) {
      return '<div class="item">' +
        '  <div class="main"><b>' + esc(f.name) + '</b>' +
        '    <small>' + f.size + ' 字节 · ' + esc(f.created_at) + '</small></div>' +
        '  <div class="ops">' +
        '    <button class="btn sm" data-download="' + esc(f.url) + '" data-name="' + esc(f.name) + '">下载</button>' +
        '    <a class="btn sm ghost" href="' + esc(API.path(f.url + '?inline=1')) + '" target="_blank" rel="noopener">打开</a>' +
        '  </div></div>';
    }).join('');

    box.querySelectorAll('[data-download]').forEach(function (b) {
      b.onclick = function () {
        API.download(b.dataset.download, b.dataset.name).catch(function () {
          API.toast('下载被浏览器拦截了；请点“打开”后用浏览器另存。', 6000);
        });
      };
    });
  }

  /* ---------------- 数据加载 ---------------- */

  function loadMaterials() {
    return API.get('/api/materials').then(function (res) {
      materials = res.materials || [];
      renderMaterials();
      var selBox = document.getElementById('matSel');
      var keep = selBox.value;
      selBox.innerHTML = materials.map(function (m) {
        return '<option value="' + m.id + '">' + esc(m.name) +
          '（' + m.word_count + ' 词）</option>';
      });
      if (keep) selBox.value = keep;
    }).catch(function (e) { API.toast(e.message); });
  }

  function loadBanks() {
    return API.get('/api/banks').then(function (res) {
      banks = res.banks || [];
      renderBanks();
    }).catch(function (e) { API.toast(e.message); });
  }

  function loadFiles() {
    return API.get('/api/offline').then(function (res) {
      files = res.files || [];
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
    return p;
  }

  function makeOffline(bankId) {
    API.toast('正在生成离线测试页…', 8000);
    return API.post('/api/banks/' + bankId + '/offline', {}).then(function (res) {
      API.toast('已生成：' + res.filename);
      API.download(res.url, res.filename).catch(function () {
        API.toast('下载被浏览器拦截了；请在离线文件列表点“打开”后另存。', 6000);
      });
      loadFiles();
      return res;
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
      box.textContent = '将使用上传的资料生成题库，层级名称可在下方自定义。';
      return;
    }
    if (!s.units) {
      box.textContent = '当前范围在内置词库里没有内容（小学 / 大学 / 自定义层级需要用自己的资料）。';
      return;
    }
    box.textContent = '当前范围：' + s.path + ' · ' +
      s.units + ' 个单元 · ' + s.words + ' 个词条';
  }

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
        API.toast('已生成题库：' + res.bank.title);
        loadBanks();
      }).catch(function (e) {
        API.toast(e.message);
      }).finally(function () { btn.disabled = false; });
    };

    document.getElementById('btnOffline').onclick = function () {
      var btn = this;
      btn.disabled = true;
      btn.textContent = '生成中…';
      API.post('/api/banks', payload()).then(function (res) {
        return makeOffline(res.bank.id);
      }).catch(function (e) {
        API.toast(e.message);
      }).finally(function () {
        btn.disabled = false;
        btn.textContent = '🧪 生成离线测试';
        loadBanks();
      });
    };

    loadMaterials();
    loadBanks();
    loadFiles();
  });
})();
