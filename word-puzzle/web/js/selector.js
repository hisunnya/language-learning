/* ============================================================
  selector.js —— 四级层级选择器（学段 / 年级 / 册别 / 单元）
   ------------------------------------------------------------
   每一级都有一个「自定义…」选项，填了就用自定义名覆盖显示名。
  第三级（册别）默认「全年（上下册）」；第四级（单元）支持
   全部单元 / 分单元 / 第 N 至第 M 单元。

   用法：
     var sel = new Selector('#levelBox', { onChange: fn });
     await sel.init();
     sel.get();       // 当前选择
     sel.summary();   // {path, units, words}
   ============================================================ */
(function (global) {
  'use strict';

  /* 「自定义」既是下拉框里的值（和后端约定好的），也是显示文字；值不能翻译，显示文字用 t('sel_custom') */
  var CUSTOM = '自定义';
  var _seq = 0;

  function t(key, params) { return WPI18N.t(key, params); }

  var MODE_KEYS = { 'all': 'sel_mode_all', 'per-unit': 'sel_mode_perunit', 'range': 'sel_mode_range' };
  function modeName(key) { return MODE_KEYS[key] ? t(MODE_KEYS[key]) : ''; }

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
    /* 文字都带 data-k / data-ph，切换语言时由 refreshText() 统一换 */
    function box(n, labelKey, phKey) {
      return '<div class="field"><label><span class="n">' + n + '</span><span data-k="' + labelKey + '"></span>' +
        '</label>' +
        '<select id="' + id + '-l' + n + '"></select>' +
        '<input type="text" class="custombox" id="' + id + '-c' + n +
        '" data-ph="' + phKey + '">' +
        '<div class="hint" id="' + id + '-h' + n + '"></div></div>';
    }
    this.el.innerHTML =
      '<div class="row">' + box(1, 'sel_stage', 'sel_phStage') + box(2, 'sel_grade', 'sel_phGrade') + '</div>' +
      '<div class="row" style="margin-top:12px">' + box(3, 'sel_term', 'sel_phTerm') + box(4, 'sel_unit', 'sel_phUnit') + '</div>' +
      '<div class="row" id="' + id + '-range" style="margin-top:12px;display:none">' +
      '  <div class="field"><label data-k="sel_from"></label><select id="' + id + '-from"></select></div>' +
      '  <div class="field"><label data-k="sel_to"></label><select id="' + id + '-to"></select></div>' +
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
    this.refreshText();
    WPI18N.onChange(function () { self.refreshText(); });
  };

  /* 换语言：标签、占位符、「自定义…」「（无内置内容）」「全部单元」这些显示文字。
     下拉框里的值（后端认的）不变；学段 / 年级 / 册别的名字是教材数据，不翻译。 */
  Selector.prototype.refreshText = function () {
    var self = this;
    Array.prototype.forEach.call(this.el.querySelectorAll('[data-k]'), function (el) {
      el.textContent = t(el.getAttribute('data-k'));
    });
    Array.prototype.forEach.call(this.el.querySelectorAll('[data-ph]'), function (el) {
      el.setAttribute('placeholder', t(el.getAttribute('data-ph')));
    });
    [this.l1, this.l2, this.l3, this.l4].forEach(function (sel) {
      Array.prototype.forEach.call(sel.options, function (o) {
        if (o.value === CUSTOM) o.textContent = t('sel_custom') + '…';
        else if (o.getAttribute('data-base') !== null) {
          o.textContent = o.getAttribute('data-base') + (o.getAttribute('data-na') ? t('sel_unavailable') : '');
        }
      });
    });
    if (this.l4) {
      Array.prototype.forEach.call(this.l4.options, function (o) {
        if (MODE_KEYS[o.value]) o.textContent = modeName(o.value);
      });
    }
    if (this.units && this.units.length && this.l4.value === 'range') this.fillRange();
  };

  Selector.prototype.fill = function (sel, items, keepValue, noCustom) {
    var old = keepValue ? sel.value : '';
    sel.innerHTML = '';
    items.forEach(function (it) {
      var o = document.createElement('option');
      o.value = it.key;
      o.textContent = it.name;
      if (it.base !== undefined) {          /* 带「（无内置内容）」后缀的选项：记下原名，换语言时重新拼 */
        o.setAttribute('data-base', it.base);
        if (it.na) o.setAttribute('data-na', '1');
      }
      sel.appendChild(o);
    });
    if (!noCustom) {
      var c = document.createElement('option');
      c.value = CUSTOM;
      c.textContent = t('sel_custom') + '…';
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
        return { key: o.key, name: o.name + (o.available ? '' : t('sel_unavailable')),
                 base: o.name, na: !o.available };
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
        return { key: m.key, name: modeName(m.key) || m.name };
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
      return { key: String(u.index), name: t('sel_unitOption', { index: u.index, name: u.name, count: u.count }) };
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
    var labels = (this.meta && this.meta.term_labels) || {};
    var names = [s.level1, s.level2, labels[s.level3] || s.level3,
                 modeName(s.unit_mode) || s.level4];
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
      unit_mode_name: modeName(s.unit_mode)
    };
  };

  global.Selector = Selector;
})(window);
