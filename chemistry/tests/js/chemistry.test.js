// chemistry.js 与 chemistry-core.js 的行为测试：用 vm + 极简 DOM 桩在 node 里直接跑。
// 服务器上没有 node（见 AGENTS.md §4），由 tests/test_chemistry_js.py 在缺 node 时跳过。
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT = path.resolve(__dirname, '..', '..');
const DATA = JSON.parse(fs.readFileSync(path.join(ROOT, 'data', 'chemistry.json'), 'utf8'));
const CORE_SRC = fs.readFileSync(path.join(ROOT, 'js', 'chemistry-core.js'), 'utf8');
const UI_SRC = fs.readFileSync(path.join(ROOT, 'js', 'chemistry.js'), 'utf8');

function loadCore() {
  const window = {};
  vm.runInContext(CORE_SRC, vm.createContext({ window, Math, Number, String, Object, Array, isFinite, Error }));
  return window.ChemistryCore;
}
const Core = loadCore();

function lcg(seed) {
  let s = seed >>> 0;
  return () => { s = (Math.imul(s, 1664525) + 1013904223) >>> 0; return s / 4294967296; };
}

const MASS = Object.fromEntries(DATA.elements.map((e) => [e.symbol, e.mass]));
const FORMULA = Object.fromEntries(DATA.formulas.map((f) => [f.formula, f]));
const weigh = (atoms, table) => Object.keys(atoms).reduce((s, k) => s + atoms[k] * table[k], 0);

// 对象来自 vm 沙箱，原型和主上下文不同，deepStrictEqual 会误报；按 JSON 比较
const canon = (v) => JSON.stringify(v, (k, x) => (x && typeof x === 'object' && !Array.isArray(x)
  ? Object.fromEntries(Object.keys(x).sort().map((key) => [key, x[key]])) : x));
const eq = (a, b, msg) => assert.strictEqual(canon(a), canon(b), msg);

function assertChoices(q, label) {
  assert.strictEqual(q.choices.length, 4, `${label} 应有 4 个选项`);
  const keys = q.choices.map((c) => c.key);
  assert.strictEqual(new Set(keys).size, 4, `${label} 选项重复：${keys}`);
  assert.strictEqual(keys.filter((k) => k === q.answer).length, 1, `${label} 必须恰好一个正确答案`);
  q.choices.forEach((c) => assert.ok(c.zh && c.en, `${label} 选项缺少一种语言`));
}

// ---------- 化学式解析器 ----------
eq(Core.parseFormula('Fe2O3'), { Fe: 2, O: 3 });
eq(Core.parseFormula('C6H12O6'), { C: 6, H: 12, O: 6 });
eq(Core.parseFormula('Ca(OH)2'), { Ca: 1, O: 2, H: 2 });
eq(Core.parseFormula('Al2(SO4)3'), { Al: 2, S: 3, O: 12 });
assert.throws(() => Core.parseFormula('xyz'));

// ---------- 题库本身：每个方程式的标准答案必须真的配平 ----------
DATA.balancedReactions.forEach((entry) => {
  const reaction = Core.parseReaction(entry);
  eq(Core.unbalanced(reaction, reaction.coefficients), [], `${entry.prompt} 的答案没有配平`);
});

// ---------- 数值填空 ----------
const kinds = {};
for (const stage of Core.STAGES) {
  const rng = lcg(9);
  for (let i = 0; i < 1500; i++) {
    const q = Core.numericQuestion(DATA, stage, rng);
    kinds[q.id] = true;
    assert.strictEqual(q.type, 'numeric');
    assert.ok(q.zh && q.en && q.explain && q.answerText);
    // 独立重算
    let expected;
    if (q.id === 'relative-mass') expected = weigh(FORMULA[q.zh.match(/（(.*?)）/)[1].replace(/[₀-₉]/g, (c) => '₀₁₂₃₄₅₆₇₈₉'.indexOf(c))].atoms, Core.INT_MASS);
    else if (q.id === 'molar-mass') expected = weigh(FORMULA[q.zh.match(/（(.*?)）/)[1].replace(/[₀-₉]/g, (c) => '₀₁₂₃₄₅₆₇₈₉'.indexOf(c))].atoms, MASS);
    if (expected !== undefined) assert.ok(Math.abs(expected - q.value) < 1e-9, `${q.id} 数值不对`);
    assert.ok(Core.checkNumeric(q, String(q.value)), `${q.id} 精确答案必须被接受`);
    assert.ok(Core.checkNumeric(q, Core.fmt(q.value)), `${q.id} 四位有效数字的答案必须被接受`);
    assert.ok(!Core.checkNumeric(q, String(q.value * 1.05)), `${q.id} 5% 的误差不应被接受`);
    assert.ok(!Core.checkNumeric(q, String(q.value * 2)), `${q.id} 两倍不应被接受`);
  }
}
['relative-mass', 'mass-from-moles', 'moles-from-mass', 'molar-mass', 'concentration', 'ph'].forEach((id) =>
  assert.ok(kinds[id], `数值题 ${id} 从未被抽到`));
// 题干里的数字要和标准答案一致（独立算一遍）
(() => {
  const rng = lcg(1);
  for (let i = 0; i < 400; i++) {
    const q = Core.numericQuestion(DATA, 'university', rng);
    if (q.id === 'concentration') {
      const [, n, v] = q.zh.match(/把 ([\d.]+) mol 溶质配成 ([\d.]+) L/);
      assert.ok(Math.abs(Number(n) / Number(v) - q.value) < 1e-9);
    }
    if (q.id === 'ph') {
      const item = DATA.phQuestions.filter((p) => q.zh.includes(p.zh))[0];
      const p = -Math.log10(item.molarity);
      assert.strictEqual(q.value, item.kind === 'acid' ? Math.round(p) : 14 - Math.round(p));
    }
  }
  const high = lcg(2);
  for (let i = 0; i < 400; i++) {
    const q = Core.numericQuestion(DATA, 'high', high);
    if (q.id === 'mass-from-moles') {
      const n = Number(q.zh.match(/^([\d.]+) mol/)[1]);
      const molar = DATA.formulas.slice(0, 11).map((f) => weigh(f.atoms, Core.INT_MASS));
      assert.ok(molar.some((m) => Math.abs(q.value / n - m) < 1e-9), `质量 ÷ 物质的量 应等于某个化学式的摩尔质量：${q.value} / ${n}`);
    }
    if (q.id === 'moles-from-mass') {
      const grams = Number(q.zh.match(/^([\d.]+) g/)[1]);
      const molar = DATA.formulas.slice(0, 11).map((f) => weigh(f.atoms, Core.INT_MASS));
      assert.ok(molar.some((m) => Math.abs(grams / q.value - m) < 1e-9), `质量 ÷ 物质的量 应等于某个化学式的摩尔质量：${grams} / ${q.value}`);
    }
  }
})();
for (const bad of ['', 'abc', '18 g', '--1', null]) assert.ok(!Core.checkNumeric({ value: 18, tolerance: 0.005 }, bad));

// ---------- 配对 ----------
for (const stage of Core.STAGES) {
  const rng = lcg(3);
  for (let i = 0; i < 500; i++) {
    const q = Core.matchQuestion(DATA, stage, rng);
    assert.strictEqual(q.pairs.length, 4);
    assert.strictEqual(new Set(q.pairs.map((p) => p.left.zh)).size, 4);
    assert.strictEqual(new Set(q.pairs.map((p) => p.right.zh)).size, 4);
    q.pairs.forEach((p) => {
      let ok;
      if (stage === 'junior') ok = DATA.elements.some((e) => e.zh === p.left.zh && e.symbol === p.right.zh);
      else if (stage === 'high') ok = DATA.formulas.some((f) => f.zh === p.left.zh && Core.sub(f.formula) === p.right.zh);
      else ok = DATA.formulas.some((f) => Core.sub(f.formula) === p.left.zh && weigh(f.atoms, MASS).toFixed(2) + ' g/mol' === p.right.zh);
      assert.ok(ok, `配对不符合数据：${p.left.zh} ↔ ${p.right.zh}`);
    });
  }
}

// ---------- 排序 ----------
for (const stage of Core.STAGES) {
  const rng = lcg(4);
  const dirs = {};
  for (let i = 0; i < 600; i++) {
    const q = Core.orderQuestion(DATA, stage, rng);
    assert.strictEqual(q.items.length, 4);
    const asc = q.zh.includes('由小到大');
    dirs[asc] = true;
    const v = q.items.map((it) => it.value);
    for (let k = 1; k < 4; k++) assert.ok(asc ? v[k] > v[k - 1] : v[k] < v[k - 1], `${q.zh} 顺序不对：${v}`);
    const gap = { junior: 2, high: 1.2, university: 8 }[stage];
    for (let k = 1; k < 4; k++) assert.ok(Math.abs(v[k] - v[k - 1]) >= gap - 1e-9, `${stage} 相邻两项太接近：${v}`);
    assert.strictEqual(new Set(q.items.map((it) => it.key)).size, 4);
  }
  assert.strictEqual(Object.keys(dirs).length, 2, '两个方向都应出现');
}

// ---------- 找错 ----------
const seen = {};
for (const stage of Core.STAGES) {
  const rng = lcg(5);
  for (let i = 0; i < 1500; i++) {
    const q = Core.mistakeQuestion(DATA, stage, rng);
    assertChoices(q, `${stage}/找错`);
    assert.ok(q.explain.length > 0);
    if (stage === 'junior') {
      const valid = new Set(DATA.formulas.map((f) => Core.sub(f.formula)));
      DATA.wrongFormulas.forEach((w) => valid.add(Core.sub(w.right)));
      const wrongSet = new Set(DATA.wrongFormulas.map((w) => Core.sub(w.wrong)));
      q.choices.forEach((c) => assert.strictEqual(valid.has(c.key), c.key !== q.answer, `${c.key} 的对错判断不对`));
      assert.ok(wrongSet.has(q.answer));
      // 写错的化学式确实不是一个有效的、常见的化学式
      assert.ok(!DATA.formulas.some((f) => Core.sub(f.formula) === q.answer));
    } else if (stage === 'high') {
      // 独立数原子：答案描述必须与真实的不守恒元素一致
      const bad = Core.unbalanced(q.reaction, q.shown);
      eq(bad, q.unbalancedElements);
      const key = bad.length ? bad.join(',') : 'ok';
      assert.strictEqual(q.answer, key);
      seen[bad.length ? 'unbalanced' : 'balanced'] = true;
    } else {
      seen[q.kind] = true;
      const [l1, l2, l3] = q.visual.split('\n');
      assert.ok(l1.startsWith('① ') && l2.startsWith('② ') && l3.startsWith('③ '));
      const f = FORMULA[q.formula];
      const right = weigh(f.atoms, MASS).toFixed(2);
      const shown = l3.match(/= ([\d.]+) g\/mol/)[1];
      const expectFirst = { none: '0', composition: '1', mass: '2', sum: '3' }[q.kind];
      assert.strictEqual(q.answer, expectFirst);
      // 第 ① 步错：原子个数与化学式不符；第 ② 步错：原子量与周期表不符；第 ③ 步错：结果与求和不符
      const compWrong = Object.keys(f.atoms).some((s) => q.counts[s] !== f.atoms[s]);
      const massWrong = Object.keys(f.atoms).some((s) => q.masses[s] !== MASS[s]);
      assert.strictEqual(compWrong, q.kind === 'composition');
      assert.strictEqual(massWrong, q.kind === 'mass');
      assert.strictEqual(shown !== weigh(q.counts, q.masses).toFixed(2), q.kind === 'sum');
      if (q.kind === 'none' || q.kind === 'composition' || q.kind === 'mass') assert.ok(Math.abs(Number(shown) - weigh(q.counts, q.masses)) < 0.006);
      if (q.kind === 'none') assert.strictEqual(shown, right);
    }
  }
}
['unbalanced', 'balanced', 'none', 'composition', 'mass', 'sum'].forEach((k) => assert.ok(seen[k], `找错题情形 ${k} 从未出现`));

// ---------- 界面：极简 DOM 桩（尽量像真浏览器） ----------
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
      add: (c) => this._cls.add(c), remove: (c) => this._cls.delete(c), contains: (c) => this._cls.has(c),
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
  querySelector() { return this._inner || (this._inner = new El('span')); }
  click() { if (this.disabled) return; (this.listeners.click || []).forEach((fn) => fn()); }
  key(name) { (this.listeners.keydown || []).forEach((fn) => fn({ key: name })); }
}
const kids = (el) => Array.from(el.children);
function descendants(el, out = []) { el._kids.forEach((c) => { out.push(c); descendants(c, out); }); return out; }
const byClass = (root, cls) => descendants(root).filter((e) => e.classList.contains(cls));

async function boot() {
  const byId = {};
  const stages = ['junior', 'high', 'university'].map((s) => { const b = new El('button'); b.dataset.stage = s; return b; });
  const modeNames = ['elements', 'formulas', 'reactions', 'input', 'match', 'order', 'mistake'];
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
  const window = { addEventListener() {} };
  const ctx = vm.createContext({
    window, document, console, Math, Number, String, Object, Array, isFinite, Error,
    setTimeout, fetch: async () => ({ ok: true, json: async () => JSON.parse(JSON.stringify(DATA)) }),
  });
  vm.runInContext(CORE_SRC, ctx);
  vm.runInContext(UI_SRC, ctx);
  for (let i = 0; i < 5; i++) await new Promise((r) => setTimeout(r, 0));
  return { byId, document, stages, modes, modeNames, quiz: window.ChemQuiz };
}

(async () => {
  const env = await boot();
  const box = () => env.byId.answerOptions;
  const score = () => Number(env.byId.scoreValue.textContent);
  const feedback = () => env.byId.answerFeedback.textContent;
  const next = () => env.byId.nextQuestion.click();
  const mode = (name) => env.modes[env.modeNames.indexOf(name)].click();
  const texts = () => byClass(box(), 'answer-option').map((b) => b.textContent);
  assert.ok(texts().length >= 4, '首题应该已经渲染：' + env.byId.questionTitle.textContent);

  // ---- 原有的三种选择题 ----
  const cn = Object.fromEntries(DATA.changes.map((c) => [c.zh, c.type]));
  let checked = 0;
  for (const stage of env.stages) {
    for (const name of ['elements', 'formulas', 'reactions']) {
      stage.click(); mode(name);
      for (let i = 0; i < 300; i++) {
        next();
        const list = texts();
        assert.strictEqual(list.length, 4, `${stage.dataset.stage}/${name} 应有 4 个选项：${list}`);
        assert.strictEqual(new Set(list).size, 4, `选项重复：${list}`);
        if (stage.dataset.stage !== 'junior' || name === 'formulas') {
          list.forEach((v) => { if (/^-?[\d.]+$/.test(v)) assert.ok(Number(v) > 0, `出现非正数选项：${list}`); });
        }
        if (stage.dataset.stage === 'junior' && name === 'reactions') {
          assert.strictEqual(list.filter((v) => cn[v] === 'chemical').length, 1, `必须恰好一个化学变化：${list}`);
        }
        checked++;
      }
    }
  }
  env.stages[0].click(); mode('reactions');
  let before = score();
  byClass(box(), 'answer-option').find((b) => cn[b.textContent] === 'chemical').click();
  assert.strictEqual(score(), before + 10);

  // ---- 新题型：每个学段 × 每种题型，界面元素齐全 ----
  for (const stage of env.stages) {
    for (const name of ['input', 'match', 'order', 'mistake']) {
      stage.click(); mode(name);
      for (let i = 0; i < 60; i++) {
        next();
        const q = env.quiz.current();
        assert.ok(env.byId.questionTitle.textContent.length > 0);
        if (q.type === 'numeric') assert.strictEqual(byClass(box(), 'numeric-input').length, 1);
        else if (q.type === 'match') assert.strictEqual(byClass(box(), 'match-left').length, 4);
        else if (q.type === 'order') assert.strictEqual(byClass(box(), 'order-item').length, 4);
        else assert.strictEqual(byClass(box(), 'answer-option').length, 4);
        assert.strictEqual(env.byId.nextQuestion.disabled, true);
        assert.strictEqual(box().className.includes('is-'), name !== 'mistake');
        checked++;
      }
    }
  }
  // 旧题型之后 answer 区的样式要复位
  mode('elements');
  assert.strictEqual(box().className, 'answer-options');
  assert.ok(!env.byId.formulaStage.classList.contains('steps'));

  // ---- 找错（选择） ----
  for (const stage of env.stages) {
    stage.click(); mode('mistake'); next();
    let q = env.quiz.current(); before = score();
    byClass(box(), 'answer-option').filter((b) => b.dataset.key === q.answer)[0].click();
    assert.strictEqual(score(), before + 10);
    assert.ok(env.byId.answerExplain.textContent.length > 0, '答完要显示解释');
    assert.strictEqual(byClass(box(), 'correct').length, 1);
    next(); q = env.quiz.current(); before = score();
    byClass(box(), 'answer-option').filter((b) => b.dataset.key !== q.answer)[0].click();
    assert.strictEqual(score(), before);
    assert.strictEqual(String(env.byId.streakValue.textContent), '0');
  }

  // ---- 数值填空 ----
  for (const stage of env.stages) {
    stage.click(); mode('input'); next();
    let q = env.quiz.current(); before = score();
    const input = byClass(box(), 'numeric-input')[0], submit = byClass(box(), 'numeric-submit')[0];
    submit.click();
    assert.strictEqual(env.byId.nextQuestion.disabled, true, '空输入不应算作提交');
    input.value = Core.fmt(q.value); input.key('Enter');
    assert.strictEqual(score(), before + 10);
    assert.strictEqual(input.disabled, true);
    next(); q = env.quiz.current(); before = score();
    byClass(box(), 'numeric-input')[0].value = String(q.value * 3);
    byClass(box(), 'numeric-submit')[0].click();
    assert.strictEqual(score(), before);
    assert.ok(feedback().includes(q.answerText), '答错要告诉正确答案：' + feedback());
  }

  // ---- 配对 ----
  for (const stage of env.stages) {
    stage.click(); mode('match'); next();
    let q = env.quiz.current(); before = score();
    const pairUp = (key) => {
      byClass(box(), 'match-left').filter((b) => b.dataset.key === key)[0].click();
      byClass(box(), 'match-right').filter((b) => b.dataset.key === key && !b.disabled)[0].click();
    };
    q.pairs.forEach((p) => pairUp(p.key));
    assert.strictEqual(score(), before + 10);
    assert.strictEqual(byClass(box(), 'correct').length, 8);
    next(); q = env.quiz.current(); before = score();
    const [a, b] = q.pairs;
    byClass(box(), 'match-left').filter((x) => x.dataset.key === a.key)[0].click();
    byClass(box(), 'match-right').filter((x) => x.dataset.key === b.key)[0].click();
    assert.strictEqual(env.byId.nextQuestion.disabled, true, '配错一次不应结束');
    q.pairs.forEach((p) => pairUp(p.key));
    assert.strictEqual(score(), before, '配错过就不得分');
    assert.ok(feedback().includes('1'));
  }

  // ---- 排序 ----
  for (const stage of env.stages) {
    stage.click(); mode('order'); next();
    let q = env.quiz.current(); before = score();
    const clickItem = (key) => byClass(box(), 'order-item').filter((x) => x.dataset.key === key)[0].click();
    q.items.forEach((it) => clickItem(it.key));
    assert.strictEqual(score(), before + 10);
    next(); q = env.quiz.current(); before = score();
    clickItem(q.items[3].key);
    byClass(box(), 'order-placed')[0].click();
    assert.strictEqual(byClass(box(), 'order-placed').length, 0, '点已放入的应能撤回');
    q.items.slice().reverse().forEach((it) => clickItem(it.key));
    assert.strictEqual(score(), before);
    assert.ok(feedback().includes(q.items[0].zh), '答错要给出正确顺序');
  }

  // ---- 切换语言不能让已作答的题重新出题 ----
  stage0(); mode('reactions'); next();
  byClass(box(), 'answer-option')[0].click();
  const snapshot = texts().join('|');
  env.document.documentElement.lang = 'en';
  (env.document.getElementById('portalLangBtn').listeners.click || []).forEach((fn) => fn());
  await new Promise((r) => setTimeout(r, 5));
  assert.ok(byClass(box(), 'answer-option').every((b) => b.disabled), '已作答的选项应保持禁用');
  assert.strictEqual(texts().join('|'), snapshot, '作答后题目不应被换掉');
  env.document.documentElement.lang = 'zh-CN';
  mode('input'); next();
  byClass(box(), 'numeric-input')[0].value = '1'; byClass(box(), 'numeric-submit')[0].click();
  const q0 = env.quiz.current();
  env.document.documentElement.lang = 'en';
  (env.document.getElementById('portalLangBtn').listeners.click || []).forEach((fn) => fn());
  await new Promise((r) => setTimeout(r, 5));
  assert.strictEqual(env.quiz.current(), q0, '填空题作答后也不应换题');
  env.document.documentElement.lang = 'zh-CN';

  // ---- 切换题型会清除元素高亮 ----
  stage0(); mode('elements');
  env.byId.elementList.children[2].click();
  assert.ok(env.byId.elementList.children[2].classList.contains('is-focus'));
  mode('formulas');
  assert.ok(kids(env.byId.elementList).every((b) => !b.classList.contains('is-focus')), '切换题型后高亮应清除');

  function stage0() { env.stages[0].click(); }
  console.log(`chemistry 行为测试通过（${checked} 道界面题）`);
})().catch((e) => { console.error(e); process.exit(1); });
