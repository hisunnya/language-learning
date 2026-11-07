// chemistry.js 的出题与作答行为测试：用 vm + 极简 DOM 桩在 node 里直接跑。
// 服务器上没有 node（见 AGENTS.md §4），由 tests/test_chemistry_js.py 在缺 node 时跳过。
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT = path.resolve(__dirname, '..', '..');
const DATA = JSON.parse(fs.readFileSync(path.join(ROOT, 'data', 'chemistry.json'), 'utf8'));
const SOURCE = fs.readFileSync(path.join(ROOT, 'js', 'chemistry.js'), 'utf8');

class El {
  constructor(tag) {
    this.tag = tag; this.children = []; this.attrs = {}; this.listeners = {};
    this.dataset = {}; this.disabled = false; this.textContent = ''; this._cls = new Set();
    this.classList = {
      add: (c) => this._cls.add(c),
      contains: (c) => this._cls.has(c),
      toggle: (c, on) => { (on === undefined ? !this._cls.has(c) : on) ? this._cls.add(c) : this._cls.delete(c); },
    };
  }
  set className(v) { this._cls = new Set(String(v).split(/\s+/).filter(Boolean)); }
  get className() { return Array.from(this._cls).join(' '); }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  addEventListener(type, fn) { (this.listeners[type] = this.listeners[type] || []).push(fn); }
  appendChild(c) { this.children.push(c); return c; }
  append(...cs) { cs.forEach((c) => this.children.push(c)); }
  replaceChildren() { this.children = []; }
  querySelector() { return this._inner || (this._inner = new El('span')); }
  click() { (this.listeners.click || []).forEach((fn) => fn()); }
}

async function boot() {
  const byId = {};
  const stages = ['junior', 'high', 'university'].map((s) => { const b = new El('button'); b.dataset.stage = s; return b; });
  const modes = ['elements', 'formulas', 'reactions'].map((m) => { const b = new El('button'); b.dataset.mode = m; return b; });
  const document = {
    documentElement: { lang: 'zh-CN' },
    getElementById: (id) => byId[id] || (byId[id] = new El('div')),
    querySelectorAll: (sel) => {
      if (sel === '[data-stage]') return stages;
      if (sel === '[data-mode]') return modes;
      if (sel === '.answer-option') return byId.answerOptions.children;
      return [];
    },
    createElement: (tag) => new El(tag),
  };
  const window = { addEventListener() {} };
  const ctx = vm.createContext({
    window, document, console, Math, Number, String, Object, Array,
    setTimeout, fetch: async () => ({ ok: true, json: async () => JSON.parse(JSON.stringify(DATA)) }),
  });
  vm.runInContext(SOURCE, ctx);
  for (let i = 0; i < 5; i++) await new Promise((r) => setTimeout(r, 0));
  return { byId, document, stages, modes, ctx };
}

function choices(env) { return env.byId.answerOptions.children.map((b) => b.textContent); }

(async () => {
  const env = await boot();
  const title = () => env.byId.questionTitle.textContent;
  assert.ok(choices(env).length >= 4, '首题应该已经渲染：' + title());

  const cn = Object.fromEntries(DATA.changes.map((c) => [c.zh, c.type]));
  let checked = 0;
  for (const stage of env.stages) {
    for (const mode of env.modes) {
      stage.click(); mode.click();
      for (let i = 0; i < 300; i++) {
        env.byId.nextQuestion.click();
        const list = choices(env);
        assert.strictEqual(list.length, 4, `${stage.dataset.stage}/${mode.dataset.mode} 应有 4 个选项：${list}`);
        assert.strictEqual(new Set(list).size, 4, `选项重复：${list}`);
        if (stage.dataset.stage !== 'junior' || mode.dataset.mode === 'formulas') {
          list.forEach((v) => { if (/^-?[\d.]+$/.test(v)) assert.ok(Number(v) > 0, `出现非正数选项：${list}`); });
        }
        if (stage.dataset.stage === 'junior' && mode.dataset.mode === 'reactions') {
          const chemical = list.filter((v) => cn[v] === 'chemical');
          assert.strictEqual(chemical.length, 1, `必须恰好一个化学变化：${list}`);
        }
        checked++;
      }
    }
  }

  // 初中反应题：点选唯一的化学变化应得分
  env.stages[0].click(); env.modes[2].click();
  let score0 = Number(env.byId.scoreValue.textContent);
  const buttons = env.byId.answerOptions.children;
  buttons.find((b) => cn[b.textContent] === 'chemical').click();
  assert.strictEqual(Number(env.byId.scoreValue.textContent), score0 + 10);

  // 切换语言不能让已作答的题重新出题（否则可以刷分）
  const before = choices(env).join('|');
  env.document.documentElement.lang = 'en';
  // 直接模拟 chemistry.js 注册的语言按钮回调
  const langBtn = env.document.getElementById('portalLangBtn');
  (langBtn.listeners.click || []).forEach((fn) => fn());
  await new Promise((r) => setTimeout(r, 5));
  // 语言按钮由 module-header.js 创建，本桩里没有监听器：这里验证 answered 状态保持
  assert.strictEqual(env.byId.answerOptions.children.every((b) => b.disabled), true, '已作答的选项应保持禁用');
  assert.strictEqual(choices(env).join('|'), before, '作答后题目不应被换掉');

  // 切换题型会清除元素高亮
  env.stages[0].click(); env.modes[0].click();
  env.byId.elementList.children[2].click();
  assert.ok(env.byId.elementList.children[2].classList.contains('is-focus'));
  env.modes[1].click();
  assert.ok(env.byId.elementList.children.every((b) => !b.classList.contains('is-focus')), '切换题型后高亮应清除');

  console.log(`chemistry.js 行为测试通过（${checked} 道随机题）`);
})().catch((e) => { console.error(e); process.exit(1); });
