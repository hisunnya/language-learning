/* ============================================================
   page-home.js —— 首页
   ============================================================ */
(function () {
  'use strict';

  var sel = null;
  var banks = [];

  function esc(s) { return API.esc(s); }

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
      '    <small>' + b.word_count + ' 词 · ' + b.unit_count + ' 单元 · ' +
      esc(API.fmtTime(b.created_at)) + '</small></div>' +
      '  <div class="ops">' +
      '    <a class="btn sm" href="' + esc(API.path('/play.html?bank=' + b.id)) + '">开始游戏</a>' +
      '    <button class="btn sm ghost" data-offline="' + b.id + '">生成离线测试</button>' +
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
    return names.map(function (name) { return { name: name, banks: groups[name] }; });
  }

  function tagPills(b) {
    return (b.tags || []).map(function (t) {
      return '<span class="pill gray">' + esc(t) + '</span>';
    }).join(' ');
  }

  function bankItem(b, student) {
    var src = b.source === 'material' ? '<span class="pill gray">上传资料</span>'
                                      : '<span class="pill">内置词库</span>';
    var meta = '<small>' + b.word_count + ' 词 · ' + b.unit_count + ' 单元 · ' +
      esc(API.fmtTime(b.created_at)) + '</small>';
    var ops = '<a class="btn sm" href="' + esc(API.path('/play.html?bank=' + b.id)) + '">开始游戏</a>';
    if (!student) {
      ops += (tagsEnabled() ? '<button class="btn sm ghost" data-meta="' + b.id + '">分类和标签</button>' : '') +
        '<button class="btn sm ghost" data-offline="' + b.id + '">生成离线测试</button>' +
        '<button class="btn sm danger" data-del="' + b.id + '">删除</button>';
    }
    return '<div class="item">' +
      '  <div class="main"><b>' + esc(b.title) + '</b>' + (student ? '' : ' ' + src) +
      (student || !tagsEnabled() ? '' : ' ' + (tagPills(b) || '<span class="pill warn">未设标签：学生看不到</span>')) +
      '    ' + meta + '</div>' +
      '  <div class="ops">' + ops + '</div></div>';
  }

  function renderBanks() {
    var box = document.getElementById('bankList');
    var student = isStudentView();
    if (!banks.length) {
      box.innerHTML = student
        ? '<div class="empty">老师还没有给你开放题库，请联系老师。</div>'
        : '<div class="empty">还没有题库，先在上面生成一个吧</div>';
      return;
    }
    box.innerHTML = groupByCategory(banks).map(function (g) {
      var head = '<div class="sub" style="margin:14px 0 4px"><b>' +
        esc(g.name || (student ? '其他' : '未分类')) + '</b></div>';
      return head + g.banks.map(function (b) { return bankItem(b, student); }).join('');
    }).join('');

    box.querySelectorAll('[data-offline]').forEach(function (btn) {
      btn.onclick = function () { makeOffline(parseInt(btn.dataset.offline, 10), btn); };
    });
    box.querySelectorAll('[data-meta]').forEach(function (btn) {
      btn.onclick = function () { editMeta(parseInt(btn.dataset.meta, 10)); };
    });
    box.querySelectorAll('[data-del]').forEach(function (btn) {
      btn.onclick = function () {
        var id = parseInt(btn.dataset.del, 10);
        if (!confirm('确定删除这个题库？')) return;
        API.del('/api/banks/' + id).then(loadBanks)
          .catch(function (e) { API.toast(e.message); });
      };
    });
  }

  /* 老师设置题库的分类和标签：学生标签里至少有一个和题库的相同，才看得到这个题库 */
  function editMeta(id) {
    var b = banks.filter(function (x) { return x.id === id; })[0];
    if (!b) return;
    var category = window.prompt('分类（例如：教材同步、考试词汇；只用来整理，留空表示未分类）：', b.category || '');
    if (category === null) return;
    var tags = window.prompt('标签，用逗号隔开。学生标签里有一个相同就能看到这个题库；留空则学生看不到：',
      (b.tags || []).join(', '));
    if (tags === null) return;
    API.post('/api/banks/' + id + '/meta', { category: category, tags: tags })
      .then(function () { API.toast('已保存'); return loadBanks(); })
      .catch(function (e) { API.toast(e.message); });
  }

  function loadBanks() {
    return AuthUI.ready.then(function () { return API.get('/api/banks'); }).then(function (res) {
      banks = res.banks || [];
      renderBanks();
      renderDefault();
    }).catch(function (e) { API.toast(e.message); });
  }

  function makeOffline(bankId, button) {
    var originalText = button ? button.textContent : '';
    if (button) { button.disabled = true; button.textContent = '正在合成语音…'; }
    API.toast('正在合成离线语音，可能需要几分钟，请勿关闭此页。', 600000);
    return API.post('/api/banks/' + bankId + '/offline', {}).then(function (res) {
      API.toast('已生成：' + res.filename);
      API.download(res.url, res.filename).catch(function () {
        API.toast('浏览器未允许下载，请到题库工作台打开离线页后另存。', 6000);
      });
    }).catch(function (e) {
      API.toast(e.message, 12000);
    }).finally(function () {
      if (button) { button.disabled = false; button.textContent = originalText; }
    });
  }

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
      btn.textContent = '生成中…';
      API.post('/api/banks', s).then(function (res) {
        location.href = API.path('/play.html?bank=' + res.bank.id);
      }).catch(function (e) {
        API.toast(e.message);
        btn.disabled = false;
        btn.textContent = '生成题库并开始';
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
      btn.textContent = '正在准备语音…';
      API.post('/api/banks', s).then(function (res) {
        btn.textContent = '正在合成语音…';
        API.toast('正在合成离线语音，可能需要几分钟，请勿关闭此页。', 600000);
        return API.post('/api/banks/' + res.bank.id + '/offline', {});
      }).then(function (res) {
        API.toast('已生成：' + res.filename + '。若下载被拦截，可在题库工作台打开。', 6000);
        return API.download(res.url, res.filename).catch(function () {
          API.toast('浏览器未允许下载，请到题库工作台打开离线页后另存。', 6000);
        });
      }).then(function () {
        btn.disabled = false;
        loadBanks();
      }).catch(function (e) {
        API.toast(e.message, 12000);
        btn.disabled = false;
        btn.textContent = '生成离线测试';
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
      box.textContent = '当前范围在内置词库里没有内容（小学 / 大学 / 自定义层级目前只能用自己的资料）。' +
        '可以换个层级，或到「题库工作台」上传资料。';
      return;
    }
    var per = pairsPerLevel();
    var levels = Math.ceil(s.words / per);
    box.textContent = '当前范围：' + s.path + ' · ' +
      s.units + ' 个单元 · ' + s.words + ' 个词条 · ' +
      '每关最多 ' + per + ' 词（约 ' + levels + ' 关）';
  }
})();
