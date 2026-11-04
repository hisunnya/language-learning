/* ============================================================
   selector.js —— 四级层级选择器（学段 / 年级 / 学期 / 单元）
   ------------------------------------------------------------
   每一级都有一个「自定义…」选项，填了就用自定义名覆盖显示名。
   第三级（学期）默认「整学年」；第四级（单元）支持
   全部单元 / 分单元 / 第 N 至第 M 单元。

   用法：
     var sel = new Selector('#levelBox', { onChange: fn });
     await sel.init();
     sel.get();       // 当前选择
     sel.summary();   // {path, units, words}
   ============================================================ */
(function (global) {
  'use strict';

  var CUSTOM = '自定义';
  var _seq = 0;

  var UNIT_MODE_NAMES = {
    'all': '全部单元',
    'per-unit': '分单元',
    'range': '第 N 至第 M 单元'
  };

  function Selector(mount, opts) {
    this.opts = opts || {};
    this.el = typeof mount === 'string' ? document.querySelector(mount) : mount;
    this.units = [];
    this.meta = null;
    this.id = 'sel' + (++_seq);
    this.render();
  }

  Selector.prototype.render = function () {
    var id = this.id;
    function box(n, label, ph) {
      return '<div class="field"><label><span class="n">' + n + '</span>' + label +
        '</label>' +
        '<select id="' + id + '-l' + n + '"></select>' +
        '<input type="text" class="custombox" id="' + id + '-c' + n +
        '" placeholder="' + ph + '">' +
        '<div class="hint" id="' + id + '-h' + n + '"></div></div>';
    }
    this.el.innerHTML =
      '<div class="row">' + box(1, '学段', '自定义学段名称') + box(2, '年级', '自定义年级名称') + '</div>' +
      '<div class="row" style="margin-top:12px">' + box(3, '学期', '自定义学期名称') + box(4, '单元', '自定义单元名称') + '</div>' +
      '<div class="row" id="' + id + '-range" style="margin-top:12px;display:none">' +
      '  <div class="field"><label>起始单元</label><select id="' + id + '-from"></select></div>' +
      '  <div class="field"><label>结束单元</label><select id="' + id + '-to"></select></div>' +
      '</div>';

    var self = this;
    this.l1 = document.getElementById(id + '-l1');
    this.l2 = document.getElementById(id + '-l2');
    this.l3 = document.getElementById(id + '-l3');
    this.l4 = document.getElementById(id + '-l4');
    this.cus = {
      level1: document.getElementById(id + '-c1'),
      level2: document.getElementById(id + '-c2'),
      level3: document.getElementById(id + '-c3'),
      level4: document.getElementById(id + '-c4')
    };
    this.hint = {
      level1: document.getElementById(id + '-h1'),
      level2: document.getElementById(id + '-h2'),
      level3: document.getElementById(id + '-h3'),
      level4: document.getElementById(id + '-h4')
    };
    this.from = document.getElementById(id + '-from');
    this.to = document.getElementById(id + '-to');
    this.rangeBox = document.getElementById(id + '-range');

    this.l1.onchange = function () { self.onL1(); };
    this.l2.onchange = function () { self.onL2(); };
    this.l3.onchange = function () { self.onL3(); };
    this.l4.onchange = function () { self.onL4(); };
    this.from.onchange = function () { self.notify(); };
    this.to.onchange = function () { self.notify(); };
    Object.keys(this.cus).forEach(function (k) {
      self.cus[k].oninput = function () { self.notify(); };
    });
  };

  Selector.prototype.fill = function (sel, items, keepValue, noCustom) {
    var old = keepValue ? sel.value : '';
    sel.innerHTML = '';
    items.forEach(function (it) {
      var o = document.createElement('option');
      o.value = it.key;
      o.textContent = it.name;
      sel.appendChild(o);
    });
    if (!noCustom) {
      var c = document.createElement('option');
      c.value = CUSTOM;
      c.textContent = CUSTOM + '…';
      sel.appendChild(c);
    }
    if (old) {
      for (var i = 0; i < sel.options.length; i++) {
        if (sel.options[i].value === old) { sel.selectedIndex = i; break; }
      }
    }
  };

  Selector.prototype.init = function () {
    var self = this;
    return API.get('/api/meta').then(function (meta) {
      self.meta = meta;
      self.fill(self.l1, meta.stages);
      var d = meta.default_selection || {};
      if (d.level1) self.l1.value = d.level1;
      return self.onL1();
    });
  };

  Selector.prototype.onL1 = function () {
    var self = this;
    var stage = this.l1.value;
    var grades = (self.meta.grades && self.meta.grades[stage]) || [];
    self.fill(self.l2, grades.map(function (g) { return { key: g, name: g }; }));
    /* 默认年级：meta.default_selection 里的那个（初中→九年级） */
    var d = (self.meta.default_selection || {});
    if (d.level2) {
      for (var i = 0; i < self.l2.options.length; i++) {
        if (self.l2.options[i].value === d.level2) {
          self.l2.selectedIndex = i;
          break;
        }
      }
    }
    return this.onL2();
  };

  Selector.prototype.onL2 = function () {
    var self = this;
    var q = 'level1=' + encodeURIComponent(this.l1.value) +
            '&level2=' + encodeURIComponent(this.l2.value);
    return API.get('/api/terms?' + q).then(function (res) {
      var opts = res.options || [];
      self.fill(self.l3, opts.map(function (o) {
        return { key: o.key, name: o.name + (o.available ? '' : '（无内置内容）') };
      }));
      var def = (self.meta && self.meta.default_term) || '整学年';
      for (var i = 0; i < self.l3.options.length; i++) {
        if (self.l3.options[i].value === def) { self.l3.selectedIndex = i; break; }
      }
      self.syncCustom();
      return self.onL3();
    });
  };

  Selector.prototype.onL3 = function () {
    var self = this;
    var q = 'level1=' + encodeURIComponent(this.l1.value) +
            '&level2=' + encodeURIComponent(this.l2.value) +
            '&level3=' + encodeURIComponent(this.l3.value);
    return API.get('/api/units?' + q).then(function (res) {
      self.units = res.units || [];
      var modes = (res.modes || []).map(function (m) {
        return { key: m.key, name: m.name };
      });
      self.fill(self.l4, modes);
      self.syncCustom();
      self.fillRange();
      self.notify();
    });
  };

  Selector.prototype.onL4 = function () {
    this.fillRange();
    this.syncCustom();
    this.notify();
  };

  Selector.prototype.fillRange = function () {
    var isRange = this.l4.value === 'range';
    this.rangeBox.style.display = isRange ? '' : 'none';
    if (!isRange) return;
    var opts = this.units.map(function (u) {
      return { key: String(u.index), name: '第 ' + u.index + ' 单元 · ' +
               u.name + '（' + u.count + ' 词）' };
    });
    this.fill(this.from, opts, true, true);
    this.fill(this.to, opts, true, true);
    if (this.from.options.length) {
      this.from.selectedIndex = 0;
      this.to.selectedIndex = this.to.options.length - 1;
    }
  };

  Selector.prototype.syncCustom = function () {
    var self = this;
    Object.keys(this.cus).forEach(function (k) {
      var sel = { level1: self.l1, level2: self.l2, level3: self.l3, level4: self.l4 }[k];
      self.cus[k].classList.toggle('on', sel.value === CUSTOM);
    });
  };

  Selector.prototype.notify = function () {
    this.syncCustom();
    if (this.opts.onChange) this.opts.onChange(this.get());
  };

  Selector.prototype.get = function () {
    var self = this;
    var mode = this.l4.value;
    var custom = {};
    ['level1', 'level2', 'level3', 'level4'].forEach(function (k) {
      custom[k] = self.cus[k].value.trim();
    });
    return {
      level1: this.l1.value,
      level2: this.l2.value,
      level3: this.l3.value,
      level4: this.l4.value,
      custom: custom,
      unit_mode: mode === CUSTOM ? 'all' : mode,
      unit_from: this.from.value ? parseInt(this.from.value, 10) : 1,
      unit_to: this.to.value ? parseInt(this.to.value, 10) : this.units.length
    };
  };

  Selector.prototype.summary = function () {
    var s = this.get();
    var names = [s.level1, s.level2, s.level3,
                 UNIT_MODE_NAMES[s.unit_mode] || s.level4];
    var keys = ['level1', 'level2', 'level3', 'level4'];
    for (var i = 0; i < 4; i++) {
      if (s.custom[keys[i]]) names[i] = s.custom[keys[i]];
    }
    var total = 0, count = 0;
    if (s.unit_mode === 'range') {
      for (var j = s.unit_from; j <= s.unit_to && j <= this.units.length; j++) {
        total += this.units[j - 1].count; count++;
      }
    } else {
      this.units.forEach(function (u) { total += u.count; count++; });
    }
    return {
      path: names.join(' - '),
      units: count,
      words: total,
      unit_mode: s.unit_mode,
      unit_mode_name: UNIT_MODE_NAMES[s.unit_mode] || ''
    };
  };

  global.Selector = Selector;
})(window);
