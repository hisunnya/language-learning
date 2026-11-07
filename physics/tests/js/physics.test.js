// physics-core.js 与 physics.js 的行为测试：用 vm 在 node 里直接跑。
// 服务器上没有 node（见 AGENTS.md §4），由 tests/test_physics_js.py 在缺 node 时跳过。
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT = path.resolve(__dirname, '..', '..');
const DATA = JSON.parse(fs.readFileSync(path.join(ROOT, 'data', 'physics.json'), 'utf8'));
const CORE = fs.readFileSync(path.join(ROOT, 'js', 'physics-core.js'), 'utf8');
const UI = fs.readFileSync(path.join(ROOT, 'js', 'physics.js'), 'utf8');

function loadCore() {
  const window = {};
  vm.runInContext(CORE, vm.createContext({ window, Math, Number, String, Object, Array, isFinite }));
  return window.PhysicsCore;
}
const Core = loadCore();

// 固定种子，失败时可复现
function lcg(seed) {
  let s = seed >>> 0;
  return () => { s = (Math.imul(s, 1664525) + 1013904223) >>> 0; return s / 4294967296; };
}

// 独立重算：公式写在测试里，不用被测代码里的同一份
const SOLVE = {
  speed: (i) => i.s / i.t,
  density: (i) => i.m / i.V,
  ohm: (i) => i.U / i.R,
  work: (i) => i.F * i.s,
  velocity: (i) => i.v0 + i.a * i.t,
  newton: (i) => i.F / i.m,
  parallel: (i) => (i.r1 * i.r2) / (i.r1 + i.r2),
  kinetic: (i) => 0.5 * i.m * i.v * i.v,
  potential: (i) => i.m * 10 * i.h,
  gas: (i) => (i.n * 8.314 * i.T) / i.V / 1000,
  rc: (i) => i.R * i.C,
  shm: (i) => 2 * Math.PI * Math.sqrt(i.m / i.k),
  capacitor: (i) => 0.5 * i.C * i.V * i.V,
  photon: (i) => 1239.84 / i.lambda,
};

function assertChoices(q, label) {
  assert.strictEqual(q.choices.length, 4, `${label} 应有 4 个选项`);
  const keys = q.choices.map((c) => c.key);
  assert.strictEqual(new Set(keys).size, 4, `${label} 选项重复：${keys}`);
  assert.strictEqual(keys.filter((k) => k === q.answer).length, 1, `${label} 必须恰好一个正确答案`);
  q.choices.forEach((c) => assert.ok(c.zh && c.en, `${label} 选项缺少一种语言`));
}

// ---------- 公式题：数值对、选项合理 ----------
const seenFormulas = {};
for (const stage of Core.STAGES) {
  const rng = lcg(7);
  for (let i = 0; i < 3000; i++) {
    const q = Core.calcQuestion(stage, rng);
    seenFormulas[q.id] = true;
    assertChoices(q, `${stage}/${q.id}`);
    const expected = SOLVE[q.id](q.inputs);
    assert.ok(Math.abs(expected - q.value) < 1e-9, `${q.id} 数值不对：${expected} vs ${q.value}`);
    assert.ok(q.answer.startsWith(Core.fmt(expected) + ' '), `${q.id} 答案文字不对：${q.answer}`);
    assert.ok(q.explain.includes(Core.fmt(expected)), `${q.id} 解题步骤没有写出结果：${q.explain}`);
    q.choices.forEach((c) => assert.ok(parseFloat(c.key) > 0, `${q.id} 出现非正数选项：${c.key}`));
  }
}
Object.keys(SOLVE).forEach((id) => assert.ok(seenFormulas[id], `公式 ${id} 从未被抽到`));

// ---------- 量与单位 ----------
for (const stage of Core.STAGES) {
  const pool = Core.visibleQuantities(DATA, stage);
  for (const quantity of pool) {
    const q = Core.unitsQuestion(DATA, stage, quantity, lcg(3));
    assertChoices(q, `${stage}/${quantity.zh}`);
    const expected = stage === 'junior' ? quantity.unit : stage === 'high' ? quantity.zh : quantity.base;
    assert.strictEqual(q.answer, expected);
  }
  const rng = lcg(11);
  for (let i = 0; i < 500; i++) {
    const q = Core.unitsQuestion(DATA, stage, null, rng);
    assertChoices(q, `${stage}/随机`);
    if (stage === 'university') assert.ok(!/本身就是/.test(q.explain), '大学阶段不应随机出“A = A”');
  }
}
// 阶段是累加的：初中的量不会在高中消失
assert.ok(Core.visibleQuantities(DATA, 'high').length > Core.visibleQuantities(DATA, 'junior').length);

// ---------- 现象与概念：每道题都能被抽到，且答案在选项里 ----------
for (const stage of Core.STAGES) {
  const wanted = new Set(DATA.concepts.filter((c) => c.stage === stage).map((c) => c.zh));
  const seen = new Set();
  const rng = lcg(5);
  for (let i = 0; i < 2000; i++) {
    const q = Core.conceptQuestion(DATA, stage, rng);
    assertChoices(q, `${stage}/概念`);
    assert.ok(q.explainZh && q.explainEn);
    seen.add(q.zh);
  }
  assert.deepStrictEqual([...seen].sort(), [...wanted].sort());
}

// ---------- 数值填空 ----------
for (const stage of Core.STAGES) {
  const rng = lcg(21);
  for (let i = 0; i < 1000; i++) {
    const q = Core.numericQuestion(stage, rng);
    assert.strictEqual(q.type, 'numeric');
    const expected = SOLVE[q.id](q.inputs);
    assert.ok(Math.abs(expected - q.value) < 1e-9, `${q.id} 填空题数值不对`);
    assert.ok(Core.checkNumeric(q, Core.fmt(expected)), `${q.id} 标准答案必须被接受`);
    assert.ok(Core.checkNumeric(q, String(expected)), `${q.id} 未取整的答案必须被接受`);
    assert.ok(Core.checkNumeric(q, String(expected * 1.01)), `${q.id} 1% 的误差应被接受`);
    assert.ok(!Core.checkNumeric(q, String(expected * 1.05)), `${q.id} 5% 的误差不应被接受`);
    assert.ok(!Core.checkNumeric(q, String(expected * 2)), `${q.id} 两倍不应被接受`);
  }
}
assert.ok(Core.checkNumeric({ value: 6.28, tolerance: 0.015 }, ' 6,3 '), '逗号小数应被接受');
for (const bad of ['', 'abc', '1/2', '6.28 m', '--3', '1e', NaN, null]) {
  assert.ok(!Core.checkNumeric({ value: 6.28, tolerance: 0.015 }, bad), `不应接受：${bad}`);
}

// ---------- 找错：第一处错误的位置、四种情形都要出现 ----------
for (const stage of Core.STAGES) {
  const rng = lcg(33);
  const kinds = {};
  for (let i = 0; i < 1500; i++) {
    const q = Core.mistakeQuestion(stage, rng);
    kinds[q.kind] = true;
    assertChoices(q, `${stage}/找错`);
    const [l1, l2, l3] = q.visual.split('\n');
    assert.ok(l1.startsWith('① ') && l2.startsWith('② ') && l3.startsWith('③ '), '应有三步');
    const template = Core.CALC[stage].filter((t) => t.id === q.id)[0];
    const right = Core.fmt(SOLVE[q.id](q.inputs));
    const shown = l2.split(' = ').pop();
    const unit = l3.slice(l3.lastIndexOf(' ') + 1);
    const expectFirst = { none: '0', formula: '1', arithmetic: '2', unit: '3' }[q.kind];
    assert.strictEqual(q.answer, expectFirst, `${q.kind} 的答案位置不对`);
    assert.strictEqual(l1 === '① ' + template.lhs + ' = ' + template.formula, q.kind !== 'formula');
    assert.strictEqual(shown === right, q.kind !== 'arithmetic', `${q.id}/${q.kind}：第 ② 步的数 ${shown} vs ${right}`);
    assert.strictEqual(unit === template.unit, q.kind !== 'unit');
    assert.ok(q.explain.length > 0);
  }
  assert.deepStrictEqual(Object.keys(kinds).sort(), ['arithmetic', 'formula', 'none', 'unit'], `${stage} 四种情形都应出现`);
}

// ---------- 配对 ----------
for (const stage of Core.STAGES) {
  const rng = lcg(44);
  const pool = Core.visibleQuantities(DATA, stage);
  for (let i = 0; i < 500; i++) {
    const q = Core.matchQuestion(DATA, stage, rng);
    assert.strictEqual(q.pairs.length, 4);
    assert.strictEqual(new Set(q.pairs.map((p) => p.left.zh)).size, 4, '左列重复');
    assert.strictEqual(new Set(q.pairs.map((p) => p.right.zh)).size, 4, '右列重复');
    q.pairs.forEach((p) => {
      assert.ok(p.left.zh && p.left.en && p.right.zh && p.right.en);
      const hit = pool.some((x) => stage === 'junior' ? x.zh === p.left.zh && x.unit === p.right.zh
        : stage === 'high' ? x.symbol === p.left.zh && x.zh === p.right.zh
          : x.unit === p.left.zh && x.base === p.right.zh);
      assert.ok(hit, `配对不符合数据：${p.left.zh} ↔ ${p.right.zh}`);
    });
  }
}

// ---------- 排序：顺序、方向、相邻至少 3 倍 ----------
for (const stage of Core.STAGES) {
  const rng = lcg(55);
  const dirs = {};
  for (let i = 0; i < 800; i++) {
    const q = Core.orderQuestion(DATA, stage, rng);
    assert.strictEqual(q.items.length, 4);
    const asc = q.zh.includes('由小到大');
    dirs[asc] = true;
    const v = q.items.map((it) => it.value);
    for (let k = 1; k < 4; k++) {
      const ratio = asc ? v[k] / v[k - 1] : v[k - 1] / v[k];
      assert.ok(ratio >= 3, `${q.zh}：相邻两项只差 ${ratio} 倍`);
    }
    assert.strictEqual(new Set(q.items.map((it) => it.key)).size, 4);
  }
  assert.strictEqual(Object.keys(dirs).length, 2, '两个方向都应出现');
}
assert.strictEqual(Core.fmtMagnitude(0.00007), '7×10⁻⁵');
assert.strictEqual(Core.fmtMagnitude(6400000), '6.4×10⁶');
assert.strictEqual(Core.fmtMagnitude(1.4), '1.4');

// ---------- 界面：极简 DOM 桩 ----------
// 桩要尽量像真浏览器：children 是没有 forEach 的 HTMLCollection，禁用的按钮不响应点击。
function collection(list) {
  const c = { length: list.length, item: (i) => list[i] };
  list.forEach((el, i) => { c[i] = el; });
  c[Symbol.iterator] = () => list[Symbol.iterator]();
  return c;
}
class El {
  constructor(tag) {
    this.tag = tag; this._kids = []; this.attrs = {}; this.listeners = {};
    this.dataset = {}; this.disabled = false; this.textContent = ''; this.value = ''; this._cls = new Set();
    this.classList = {
      add: (c) => this._cls.add(c),
      remove: (c) => this._cls.delete(c),
      contains: (c) => this._cls.has(c),
      toggle: (c, on) => { (on === undefined ? !this._cls.has(c) : on) ? this._cls.add(c) : this._cls.delete(c); },
    };
  }
  get children() { return collection(this._kids); }
  set className(v) { this._cls = new Set(String(v).split(/\s+/).filter(Boolean)); }
  get className() { return Array.from(this._cls).join(' '); }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  addEventListener(type, fn) { (this.listeners[type] = this.listeners[type] || []).push(fn); }
  appendChild(c) { this._kids.push(c); return c; }
  append(...cs) { cs.forEach((c) => this._kids.push(c)); }
  replaceChildren() { this._kids = []; }
  click() { if (this.disabled) return; (this.listeners.click || []).forEach((fn) => fn()); }
  key(name) { (this.listeners.keydown || []).forEach((fn) => fn({ key: name })); }
}
const kids = (el) => Array.from(el.children);

// 递归找后代：从答题区里按类名取按钮
function descendants(el, out = []) {
  el._kids.forEach((c) => { out.push(c); descendants(c, out); });
  return out;
}
const byClass = (root, cls) => descendants(root).filter((e) => e.classList.contains(cls));

async function boot() {
  const byId = {};
  const stages = ['junior', 'high', 'university'].map((s) => { const b = new El('button'); b.dataset.stage = s; return b; });
  const modeNames = ['units', 'calc', 'input', 'match', 'order', 'mistake', 'concepts'];
  const modes = modeNames.map((m) => { const b = new El('button'); b.dataset.mode = m; return b; });
  const document = {
    documentElement: { lang: 'zh-CN' },
    getElementById: (id) => byId[id] || (byId[id] = new El('div')),
    querySelectorAll: (sel) => {
      if (sel === '[data-stage]') return stages;
      if (sel === '[data-mode]') return modes;
      if (sel === '.answer-option') return byClass(byId.answerOptions, 'answer-option');
      return [];
    },
    createElement: (tag) => new El(tag),
  };
  const window = {};
  const ctx = vm.createContext({
    window, document, console, Math, Number, String, Object, Array, isFinite, setTimeout,
    fetch: async () => ({ ok: true, json: async () => JSON.parse(JSON.stringify(DATA)) }),
  });
  vm.runInContext(CORE, ctx);
  vm.runInContext(UI, ctx);
  for (let i = 0; i < 5; i++) await new Promise((r) => setTimeout(r, 0));
  return { byId, document, stages, modes, modeNames, quiz: window.PhysicsQuiz };
}

(async () => {
  const env = await boot();
  const box = () => env.byId.answerOptions;
  const score = () => Number(env.byId.scoreValue.textContent);
  const feedback = () => env.byId.answerFeedback.textContent;
  const next = () => env.byId.nextQuestion.click();
  const mode = (name) => env.modes[env.modeNames.indexOf(name)].click();
  assert.ok(env.quiz.current(), '首题应该已经渲染：' + env.byId.questionTitle.textContent);

  // 每个学段 × 每种题型：都能出题且界面元素齐全
  let asked = 0;
  for (const stage of env.stages) {
    for (const name of env.modeNames) {
      stage.click(); mode(name);
      for (let i = 0; i < 60; i++) {
        next();
        const q = env.quiz.current();
        assert.ok(env.byId.questionTitle.textContent.length > 0);
        if (q.type === 'numeric') assert.strictEqual(byClass(box(), 'numeric-input').length, 1);
        else if (q.type === 'match') assert.strictEqual(byClass(box(), 'match-left').length, 4);
        else if (q.type === 'order') assert.strictEqual(byClass(box(), 'order-item').length, 4);
        else assert.strictEqual(byClass(box(), 'answer-option').length, 4);
        assert.strictEqual(env.byId.nextQuestion.disabled, true, '答题前「继续」应禁用');
        asked++;
      }
    }
  }

  // 选择题（含找错）：答对 +10，答错不加分、连击清零，且只有一个正确选项被标出
  for (const name of ['units', 'calc', 'mistake', 'concepts']) {
    env.stages[1].click(); mode(name);
    next();
    let q = env.quiz.current(), before = score();
    byClass(box(), 'answer-option').filter((b) => b.dataset.key === q.answer)[0].click();
    assert.strictEqual(score(), before + 10, `${name} 答对应 +10`);
    assert.ok(env.byId.answerExplain.textContent.length > 0, `${name} 答完要显示解释`);
    assert.strictEqual(byClass(box(), 'correct').length, 1);
    next(); q = env.quiz.current(); before = score();
    byClass(box(), 'answer-option').filter((b) => b.dataset.key !== q.answer)[0].click();
    assert.strictEqual(score(), before, `${name} 答错不加分`);
    assert.strictEqual(String(env.byId.streakValue.textContent), '0');
    assert.strictEqual(env.byId.nextQuestion.disabled, false);
  }

  // 数值填空：答对 / 答错 / 空输入不提交 / 回车提交
  for (const stage of env.stages) {
    stage.click(); mode('input');
    next();
    let q = env.quiz.current(), before = score();
    const input = byClass(box(), 'numeric-input')[0], submit = byClass(box(), 'numeric-submit')[0];
    submit.click();
    assert.strictEqual(env.byId.nextQuestion.disabled, true, '空输入不应算作提交');
    input.value = Core.fmt(q.value); input.key('Enter');
    assert.strictEqual(score(), before + 10, '回车应能提交，且答对 +10');
    assert.strictEqual(input.disabled, true);
    next(); q = env.quiz.current(); before = score();
    const wrong = byClass(box(), 'numeric-input')[0];
    wrong.value = String(q.value * 3);
    byClass(box(), 'numeric-submit')[0].click();
    assert.strictEqual(score(), before);
    assert.ok(feedback().includes(q.answerText), '答错要告诉正确答案');
  }

  // 配对：全对得分；中途配错一次则不得分，但仍能完成并看到解释
  for (const stage of env.stages) {
    stage.click(); mode('match');
    next();
    let q = env.quiz.current(), before = score();
    const pairUp = (key) => {
      byClass(box(), 'match-left').filter((b) => b.dataset.key === key)[0].click();
      byClass(box(), 'match-right').filter((b) => b.dataset.key === key && !b.disabled)[0].click();
    };
    q.pairs.forEach((p) => pairUp(p.key));
    assert.strictEqual(score(), before + 10, '全部配对正确应 +10');
    assert.strictEqual(byClass(box(), 'correct').length, 8);
    next(); q = env.quiz.current(); before = score();
    const [a, b] = q.pairs;
    byClass(box(), 'match-left').filter((x) => x.dataset.key === a.key)[0].click();
    byClass(box(), 'match-right').filter((x) => x.dataset.key === b.key)[0].click();
    assert.strictEqual(env.byId.nextQuestion.disabled, true, '配错一次不应结束');
    q.pairs.forEach((p) => pairUp(p.key));
    assert.strictEqual(score(), before, '配错过就不得分');
    assert.ok(feedback().includes('1'), '要说明配错了几次：' + feedback());
    assert.ok(env.byId.answerExplain.textContent.length > 0);
  }

  // 排序：按正确顺序点选得分；点错顺序不得分并给出正确顺序；点已放入的可以撤回
  for (const stage of env.stages) {
    stage.click(); mode('order');
    next();
    let q = env.quiz.current(), before = score();
    const clickItem = (key) => byClass(box(), 'order-item').filter((x) => x.dataset.key === key)[0].click();
    q.items.forEach((it) => clickItem(it.key));
    assert.strictEqual(score(), before + 10, '顺序正确应 +10');
    next(); q = env.quiz.current(); before = score();
    clickItem(q.items[3].key);
    assert.strictEqual(byClass(box(), 'order-placed').length, 1);
    byClass(box(), 'order-placed')[0].click();
    assert.strictEqual(byClass(box(), 'order-placed').length, 0, '点已放入的应能撤回');
    q.items.slice().reverse().forEach((it) => clickItem(it.key));
    assert.strictEqual(score(), before, '顺序错误不得分');
    assert.ok(feedback().includes(q.items[0].zh), '答错要给出正确顺序');
  }

  // 语言切换不能让已作答的题重新出题
  mode('input'); next();
  const num = byClass(box(), 'numeric-input')[0];
  num.value = '1'; byClass(box(), 'numeric-submit')[0].click();
  const snapshot = env.quiz.current();
  env.document.documentElement.lang = 'en';
  (env.document.getElementById('portalLangBtn').listeners.click || []).forEach((fn) => fn());
  await new Promise((r) => setTimeout(r, 5));
  assert.strictEqual(env.quiz.current(), snapshot, '作答后不应换题');
  env.document.documentElement.lang = 'zh-CN';

  // 点选物理量卡片 → 自动切到「量与单位」并聚焦该量
  env.stages[0].click(); mode('calc');
  env.byId.refList.children[3].click();
  assert.ok(env.byId.refList.children[3].classList.contains('is-focus'));
  assert.strictEqual(env.modes[0].attrs['aria-selected'], 'true');
  mode('concepts');
  assert.ok(kids(env.byId.refList).every((b) => !b.classList.contains('is-focus')), '切换题型后高亮应清除');

  console.log(`physics 行为测试通过（${asked} 道界面题）`);
})().catch((e) => { console.error(e); process.exit(1); });
