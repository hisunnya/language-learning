/* bank_workbench.test.js —— 题库工作台：生成什么样的请求、什么时候不让生成、网址里的标签页
   用最小的假 DOM 跑真实的 page-bank.js */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm');
const code = fs.readFileSync(path.join(__dirname, '..', '..', 'web', 'js', 'page-bank.js'), 'utf8');
let passed = 0; const failures = [];
function check(name, ok, detail) { if (ok) passed++; else failures.push(name + (detail ? '：' + detail : '')); }

function makePage(opts) {
  opts = opts || {};
  const els = {};
  const el = (id) => (els[id] = els[id] || { id, value: '', checked: false, hidden: false, disabled: false, textContent: '', innerHTML: '', dataset: {}, classList: { toggle() {}, add() {}, remove() {} }, setAttribute() {}, addEventListener() {}, focus() {}, style: {} });
  const radios = { seed: { value: 'seed', checked: true }, upload: { value: 'upload', checked: false }, material: { value: 'material', checked: false } };
  let hash = opts.hash || '';
  const sandbox = {
    document: { getElementById: el, querySelector: (q) => (q.indexOf('source') >= 0 ? Object.values(radios).filter((r) => r.checked)[0] : null), querySelectorAll: () => [], addEventListener: (n, f) => { if (n === 'DOMContentLoaded') sandbox.__ready = f; } },
    location: { get hash() { return hash; }, set hash(v) { hash = v; } },
    history: { replaceState: () => {} }, confirm: () => true, window: null,
    API: { esc: (s) => String(s), get: () => Promise.resolve({ banks: [], materials: [], files: [], tags: [] }), post: () => Promise.resolve({}), del: () => Promise.resolve({}), toast() {}, path: (p) => p, fmtTime: () => '', templateLinks() {} },
    WPI18N: { t: (k) => k, onChange() {} },
    AuthUI: { info: () => ({ enabled: opts.accounts !== false }), isAdmin: () => true, ready: Promise.resolve() },
    BankPanels: { set() {}, tagPills: () => '', groupByCategory: () => [] },
    Selector: function () { this.init = () => Promise.resolve(); this.get = () => ({ level1: '初中', level2: '九年级', level3: 'all', level4: 'all', custom: {}, unit_mode: 'all', unit_from: 1, unit_to: 14 }); this.summary = () => ({ path: 'x', units: opts.seedUnits === undefined ? 14 : opts.seedUnits, words: 400 }); },
    FormData: function () { this.append = () => {}; },
    addEventListener() {}, Promise, RegExp, parseInt, String, JSON, Math, Object, Array, setTimeout,
  };
  sandbox.window = sandbox; sandbox.global = sandbox;
  vm.createContext(sandbox);
  vm.runInContext(code, sandbox);
  sandbox.__ready();
  return { els, el, radios, page: sandbox.WPBankWorkbench, setHash: (h) => { hash = h; } };
}
const choose = (p, which) => { Object.keys(p.radios).forEach((k) => { p.radios[k].checked = k === which; }); };

(async () => {
  // 网址里的标签页
  let p = makePage({ hash: '#new' });
  check('#new 直接打开「新建题库」', p.page.tabFromHash() === 'new');
  p.setHash('#offline?bank=3'); check('#offline 带参数也认', p.page.tabFromHash() === 'offline');
  p.setHash('#nonsense'); check('不认识的锚点回到「当前题库」', p.page.tabFromHash() === 'banks');
  p.setHash(''); check('没有锚点默认「当前题库」', p.page.tabFromHash() === 'banks');

  // 内置词库
  p = makePage();
  p.el('pairsPerLevel').value = '9';
  check('内置词库有内容就能生成', p.page.problem() === '');
  let body = p.page.buildPayload();
  check('内置词库：来源 seed，层级取自选择器，每关 9 词，不拆分', body.source === 'seed' && body.level1 === '初中' && body.pairs_per_level === 9 && !body.split_units && !('tags' in body) && !('category' in body));
  p.el('pairsPerLevel').value = '999'; check('每关词数超范围回到 9', p.page.buildPayload().pairs_per_level === 9);
  p.el('pairsPerLevel').value = 'abc'; check('每关词数乱写回到 9', p.page.buildPayload().pairs_per_level === 9);
  p.el('pairsPerLevel').value = '12'; check('老师想要 12 就是 12', p.page.buildPayload().pairs_per_level === 12);
  p = makePage({ seedUnits: 0 }); check('内置词库选了没有内容的范围：不让生成并说明', p.page.problem() === 'bank_noContent');

  // 上传 / 以前的词表：没选好之前不让生成，并说明缺什么
  p = makePage(); choose(p, 'upload');
  check('选了「上传新词表」但还没上传：提示先上传', p.page.problem() === 'bank_needUpload');
  choose(p, 'material'); check('选了「以前的词表」但没有可选的：提示', p.page.problem() === 'bank_needMaterial');

  // 开放给谁：分类和标签
  p = makePage(); p.el('newCategory').value = ' 测试书 '; p.el('newTags').value = '学前2601, 大学英语BI'; p.el('splitNew').checked = true;
  body = p.page.buildPayload();
  check('分类、标签、按单元拆分都带进请求', body.category === '测试书' && body.tags === '学前2601, 大学英语BI' && body.split_units === true);
  p = makePage({ accounts: false }); p.el('newTags').value = '班'; body = p.page.buildPayload();
  check('没有账号体系的站点不发标签（标签没有意义）', !('tags' in body));

  console.log(failures.length ? 'FAIL\n' + failures.join('\n') : '题库工作台行为：' + passed + ' 项通过');
  process.exit(failures.length ? 1 : 0);
})();
