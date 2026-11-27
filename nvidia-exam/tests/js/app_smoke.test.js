/* ============================================================
   app_smoke.test.js —— 页面逻辑的冒烟测试
   ------------------------------------------------------------
   用法::

       node tests/js/app_smoke.test.js

   app.js 是一段 IIFE，只通过 DOM 说话。这里用一个够用的假 DOM
   把 index.html 里那些元素造出来，然后真的点一遍：
   换考试科目 → 组卷 → 作答 → 交卷 → 看题库 → 看指南 → 看统计。

   目的是抓运行时报错（拼错的字段、没定义的函数），不是检查像素。
   ============================================================ */
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const BASE = path.join(__dirname, '..', '..');

/* ---------- 迷你断言 ---------- */

let passed = 0;
const failures = [];

function check(name, fn) {
  try {
    fn();
    passed++;
  } catch (err) {
    failures.push(name + '：' + (err && err.message ? err.message : err));
  }
}

function eq(actual, expected, note) {
  if (actual !== expected) {
    throw new Error(
      '期望 ' + JSON.stringify(expected) + '，实际 ' + JSON.stringify(actual) +
      (note ? '（' + note + '）' : '')
    );
  }
}

function ok(cond, note) {
  if (!cond) throw new Error('条件不成立' + (note ? '（' + note + '）' : ''));
}

/* ---------- 假 DOM ---------- */

function makeClassList() {
  const set = new Set();
  return {
    add: (c) => set.add(c),
    remove: (c) => set.delete(c),
    contains: (c) => set.has(c),
    toggle: (c, force) => {
      const on = force === undefined ? !set.has(c) : !!force;
      if (on) set.add(c); else set.delete(c);
      return on;
    }
  };
}

function makeElement(tag, doc) {
  const el = {
    tagName: String(tag).toUpperCase(),
    children: [],
    attributes: {},
    dataset: {},
    style: {},
    textContent: '',
    value: '',
    checked: false,
    disabled: false,
    className: '',
    _listeners: {},
    classList: null,
    ownerDocument: doc,
    addEventListener(type, fn) {
      (this._listeners[type] = this._listeners[type] || []).push(fn);
    },
    removeEventListener() {},
    dispatch(type) {
      (this._listeners[type] || []).forEach((fn) => fn({ target: this }));
    },
    appendChild(child) {
      this.children.push(child);
      return child;
    },
    setAttribute(k, v) { this.attributes[k] = String(v); },
    getAttribute(k) { return this.attributes[k] === undefined ? null : this.attributes[k]; },
    insertAdjacentHTML(pos, html) { this.innerHTML += html; },
    querySelectorAll(selector) {
      const out = [];
      const walk = (node) => {
        node.children.forEach((child) => {
          if (selector === 'input:checked') {
            if (child.tagName === 'INPUT' && child.checked) out.push(child);
          } else if (selector === 'input') {
            if (child.tagName === 'INPUT') out.push(child);
          } else if (selector === '*') {
            out.push(child);
          }
          walk(child);
        });
      };
      walk(this);
      return out;
    },
    querySelector(selector) {
      const all = this.querySelectorAll(selector);
      return all.length ? all[0] : null;
    }
  };
  el.classList = makeClassList();
  // innerHTML 赋值会清掉子元素（浏览器就是这么干的）
  let html = '';
  Object.defineProperty(el, 'innerHTML', {
    get() { return html; },
    set(value) { html = String(value); el.children.length = 0; }
  });
  return el;
}

function makeDocument() {
  const registry = new Map();
  const doc = {
    documentElement: makeElement('html', null),
    body: makeElement('body', null),
    createElement(tag) { return makeElement(tag, doc); },
    getElementById(id) {
      if (!registry.has(id)) {
        const el = makeElement('div', doc);
        el.id = id;
        registry.set(id, el);
      }
      return registry.get(id);
    },
    querySelectorAll(selector) {
      if (selector === '.nav-btn') {
        if (!doc._nav) {
          doc._nav = ['exam', 'practice', 'browse', 'guides', 'stats'].map((view) => {
            const btn = makeElement('button', doc);
            btn.dataset.view = view;
            return btn;
          });
        }
        return doc._nav;
      }
      return [];
    },
    addEventListener(type, fn) { (this._listeners = this._listeners || {})[type] = fn; },
    dispatch(type) { (this._listeners || {})[type] && this._listeners[type]({}); }
  };
  doc._registry = registry;
  return doc;
}

function makeStorage() {
  const data = new Map();
  return {
    getItem: (k) => (data.has(k) ? data.get(k) : null),
    setItem: (k, v) => { data.set(k, String(v)); },
    removeItem: (k) => { data.delete(k); },
    get length() { return data.size; },
    _dump: () => Object.fromEntries(data)
  };
}

/* ---------- 装载页面 ---------- */

const document = makeDocument();
const storage = makeStorage();
const timers = [];

const sandbox = {
  console,
  Math,
  Date,
  JSON,
  Object,
  Array,
  String,
  Number,
  Boolean,
  RegExp,
  Error,
  parseInt,
  parseFloat,
  isNaN,
  document,
  localStorage: storage,
  navigator: { language: 'zh-CN' },
  setInterval: (fn, ms) => {
    const id = { fn, ms, cancelled: false };
    timers.push(id);
    return id;
  },
  clearInterval: (id) => { if (id) id.cancelled = true; },
  setTimeout: (fn) => { fn(); return 0; },
  clearTimeout: () => {},
  CustomEvent: function (type, init) { this.type = type; this.detail = init && init.detail; },
  Event: function (type) { this.type = type; },
  dispatchEvent: () => true
};
sandbox.window = sandbox;
sandbox.globalThis = sandbox;
vm.createContext(sandbox);

function load(file) {
  const code = fs.readFileSync(path.join(BASE, file), 'utf8');
  vm.runInContext(code, sandbox, { filename: file });
}

load('data/bank.js');
load('data/guides.js');
load('js/store.js');
load('js/app.js');

/* 页面自己的 DOMContentLoaded 回调 */
document.dispatch('DOMContentLoaded');

const $ = (id) => document.getElementById(id);
const BANK = sandbox.window.NVIDIA_BANK;
const GUIDES = sandbox.window.NVIDIA_GUIDES;
const navButton = (view) =>
  document.querySelectorAll('.nav-btn').filter((b) => b.dataset.view === view)[0];

/* ---------- 用例 ---------- */

check('题库里有 8 项认证，每一项都有题目和知识域', () => {
  eq(BANK.exams.length, 8, '认证数量');
  BANK.exams.forEach((exam) => {
    ok(exam.questions.length > 0, exam.code + ' 没有题目');
    ok(exam.domains.length > 0, exam.code + ' 没有知识域');
    eq(exam.domains.reduce((acc, d) => acc + d.weight, 0), 100, exam.code + ' 的权重合计');
  });
});

check('考试科目下拉框列出了 8 项认证', () => {
  const picker = $('examPicker');
  eq((picker.innerHTML.match(/<option/g) || []).length, 8, '下拉框选项数');
  eq(picker.value, BANK.exams[0].id, '默认选中的科目');
});

check('规则卡片用的是当前科目的官方信息', () => {
  const html = $('examRuleCards').innerHTML;
  const exam = BANK.exams[0];
  ok(html.indexOf(String(exam.official.questions)) >= 0, '没有官方题量');
  ok(html.indexOf(String(exam.official.durationMin)) >= 0, '没有考试时长');
});

check('知识域下拉框跟着科目走', () => {
  eq($('examDomain').children.length, BANK.exams[0].domains.length + 1, '第一个科目的知识域');
});

check('切到另一项考试后，标题、规则卡片和知识域都跟着换', () => {
  const picker = $('examPicker');
  picker.value = 'ncp-ousd';
  picker.dispatch('change');
  const exam = BANK.exams.filter((e) => e.id === 'ncp-ousd')[0];
  ok(exam, '找不到 NCP-OUSD');
  eq($('examDomain').children.length, exam.domains.length + 1, '知识域数量');
  ok($('bankNote').textContent.indexOf('NCP-OUSD') >= 0, '页眉没有显示科目代码');
  ok($('examRuleCards').innerHTML.indexOf(String(exam.official.durationMin)) >= 0, '规则卡片没更新');
});

check('模拟考试能组卷、作答、交卷，并按科目分开记分', () => {
  const exam = BANK.exams.filter((e) => e.id === 'ncp-ousd')[0];
  $('examLength').value = '10';
  $('examDomain').value = 'all';
  $('startExamBtn').dispatch('click');

  const opts = $('examOpts');
  ok(opts.children.length > 0, '没有渲染选项');
  ok($('examProgress').textContent.indexOf('/ 10') >= 0, '组卷题量不是 10：' + $('examProgress').textContent);

  // 每一题都选第一个选项，然后交卷
  for (let i = 0; i < 10; i++) {
    const inputs = opts.querySelectorAll('input');
    ok(inputs.length > 0, '第 ' + i + ' 题没有选项');
    inputs[0].checked = true;
    inputs[0].dispatch('change');
    $('examNextBtn').dispatch('click');
  }
  $('examSubmitBtn').dispatch('click');

  const state = sandbox.window.NXStore.getState();
  eq(state.history.length, 1, '考试历史条数');
  eq(state.history[0].exam, 'NCP-OUSD', '考试历史里没有科目代码');
  ok(Object.keys(state.answered).length > 0, '没有记录作答');
  ok(
    Object.keys(state.answered).every((k) => k.indexOf('ncp-ousd:') === 0),
    '作答记录的键没有带上科目：' + Object.keys(state.answered).slice(0, 3).join(',')
  );
  ok($('resultScore').innerHTML.indexOf('%') >= 0, '没有显示成绩');
});

check('交卷后可以逐题复盘，看到解析与来源', () => {
  $('resultReview').classList.add('hidden');
  $('resultReviewBtn').dispatch('click');
  const html = $('resultReview').innerHTML;
  ok(html.length > 0, '复盘是空的');
  ok(html.indexOf('rv-line src') >= 0, '复盘里没有来源链接');
});

check('题库浏览只列当前科目的题，并能按知识域筛选', () => {
  navButton('browse').dispatch('click');
  const all = $('browseList').innerHTML;
  ok(all.length > 0, '浏览列表是空的');

  const select = $('browseDomain');
  const domainId = BANK.exams.filter((e) => e.id === 'ncp-ousd')[0].domains[0].id;
  select.value = domainId;
  select.dispatch('change');
  ok($('browseList').innerHTML.length > 0, '按知识域筛选后空了');
});

check('指南视图列出当前科目的学习指南', () => {
  navButton('guides').dispatch('click');
  const html = $('guideList').innerHTML;
  ok(html.length > 0, '指南视图是空的');
  ok(html.indexOf('guide-item') >= 0, '没有指南条目');
  const entry = GUIDES.certs.filter((c) => c.code === 'NCP-OUSD')[0];
  ok(entry, '指南数据里没有 NCP-OUSD');
  eq((html.match(/guide-item/g) || []).length, entry.guides.length, '指南条目数');
  ok(html.indexOf('guides.lang') < 0, '指南的语言标签没翻译，页面上出现了键名本身');
});

check('统计页按科目统计，错题本里带科目代码', () => {
  navButton('stats').dispatch('click');
  ok($('statOverview').innerHTML.indexOf('stat-cell') >= 0, '统计概览是空的');
  const wrong = $('wrongList').innerHTML;
  if (wrong.indexOf('history-item') >= 0) {
    ok(wrong.indexOf('NCP-OUSD') >= 0, '错题本里没有科目代码');
  }
});

check('错题重练能取到题', () => {
  const ids = sandbox.window.NXStore.wrongIds();
  if (!ids.length) return;                     // 这轮全答对了，没有错题
  $('wrongPracticeBtn').dispatch('click');
  ok($('practiceRun').innerHTML !== undefined, '错题重练没有开始');
});

check('切回第一项考试后，题目与科目对得上', () => {
  const picker = $('examPicker');
  picker.value = BANK.exams[0].id;
  picker.dispatch('change');
  eq($('examDomain').children.length, BANK.exams[0].domains.length + 1, '知识域数量');
  $('examLength').value = '5';
  $('startExamBtn').dispatch('click');
  ok($('examProgress').textContent.indexOf('/ 5') >= 0, '组卷题量不是 5：' + $('examProgress').textContent);
});

check('语言切换后界面文案跟着变', () => {
  $('langBtn').dispatch('click');
  eq(document.documentElement.lang, 'en', 'html lang 没有变成 en');
  $('langBtn').dispatch('click');
  eq(document.documentElement.lang, 'zh-CN', 'html lang 没有变回 zh-CN');
});

/* ---------- 结果 ---------- */

timers.forEach((t) => { t.cancelled = true; });

if (failures.length) {
  console.error('失败 ' + failures.length + ' 项：');
  failures.forEach((f) => console.error('  ✗ ' + f));
  process.exit(1);
}
console.log('全部通过：' + passed + ' 项。');