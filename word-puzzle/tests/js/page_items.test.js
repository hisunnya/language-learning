/* page-items.js 的启动分发：验证动词猎手只需加载自己的 UI，也只显示一个开局按钮。 */
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const WEB = path.join(__dirname, '..', '..', 'web', 'js');
const nodes = {
  igMount: { innerHTML: '', onclick: null },
  igBack: { href: '' },
  igStart: { hidden: true, onclick: null },
  igTitle: { textContent: '' },
  igSub: { textContent: '' },
  curTotal: { textContent: '' },
  curUnits: { textContent: '' }
};
let domReady;
let startedWith;
let languageChange;
const groups = [
  { unit: 'Unit 3', part: 1, parts: 2, items: Array.from({ length: 5 }, (_, i) => ({ answer: 'run' + i, choices: ['run0', 'run1', 'run2', 'run3', 'run4', 'walk0', 'walk1', 'walk2', 'walk3', 'walk4', 'other1', 'other2', 'other3', 'other4'] })) },
  { unit: 'Unit 3', part: 2, parts: 2, items: Array.from({ length: 5 }, (_, i) => ({ answer: 'walk' + i, choices: ['run0', 'run1', 'run2', 'run3', 'run4', 'walk0', 'walk1', 'walk2', 'walk3', 'walk4', 'other1', 'other2', 'other3', 'other4'] })) }
];
const document = {
  body: { getAttribute: () => 'verb' },
  getElementById: (id) => nodes[id],
  addEventListener(name, callback) { if (name === 'DOMContentLoaded') domReady = callback; }
};
const sandbox = {
  document,
  location: { search: '?bank=20', pathname: '/verb.html' },
  history: { replaceState() {} },
  AuthUI: { ready: Promise.resolve(), info: () => ({ user: { role: 'student' } }) },
  API: {
    path: (url) => url,
    esc: (value) => String(value),
    get(url) {
      if (url === '/api/meta') return Promise.resolve({ curriculum: {} });
      if (url === '/api/recent?limit=4') return Promise.resolve({ recent: [] });
      return Promise.resolve({ bank: { id: 20, title: 'Unit 3', game_type: 'verb' }, groups });
    },
    post: () => Promise.resolve({})
  },
  WPI18N: {
    t: (key, params) => key === 'vh_startInfo' ? key + ':' + params.n : key,
    onChange(callback) { languageChange = callback; }
  },
  WPRecent: { add() {}, userKey: () => 'test' },
  WPItemCore: {
    levelName: () => 'Unit 3'
  },
  WPVerbUI: {
    start(mount, cfg) { startedWith = cfg; return {}; }
  },
  WPAdapter: { begin: () => Promise.resolve({}), phase() {}, recording() {} },
  console
};
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(path.join(WEB, 'page-items.js'), 'utf8'), sandbox);

(async () => {
  languageChange();
  if (!nodes.igStart.hidden) throw new Error('题库加载完成前不能显示开始按钮');
  domReady();
  await new Promise((resolve) => setTimeout(resolve, 0));
  const mount = nodes.igMount;
  if (mount.innerHTML || nodes.igStart.hidden || !nodes.igStart.onclick ||
      nodes.igSub.textContent !== 'vh_startInfo:10' || nodes.igBack.href !== '/#type=verb') {
    throw new Error('入口应复用标题卡片显示一份说明和开始按钮，不再生成第二张卡片');
  }
  languageChange();
  if (mount.innerHTML || nodes.igSub.textContent !== 'vh_startInfo:10') {
    throw new Error('切换语言后仍只显示一份说明，题目数保持正确');
  }
  nodes.igStart.onclick();
  if (!nodes.igStart.hidden) throw new Error('开始后应隐藏开始按钮');
  if (!startedWith || startedWith.levels || startedWith.items.length !== 10 ||
      startedWith.ords.join(',') !== '0,1,2,3,4,5,6,7,8,9' ||
      startedWith.levelCount !== 2 || startedWith.choices.length !== 14) {
    throw new Error('开始后应把两组十题展平为一局，并保留原始序号及完整选项词库');
  }
  if (startedWith.audioUrl) throw new Error('动词猎手不再提供朗读配置');
  const spellNodes = {};
  const html = fs.readFileSync(path.join(WEB, '..', 'spell.html'), 'utf8');
  for (const match of html.matchAll(/id="([^"]+)"/g)) spellNodes[match[1]] = {};
  if (spellNodes.igStart) throw new Error('夹具必须来自没有既有开始按钮的拼写页面');
  Object.defineProperty(spellNodes.igMount, 'innerHTML', {
    set(value) {
      this.html = value;
      if (value.includes('id="igStart"')) spellNodes.igStart = {};
    }
  });
  let spellReady, spellCfg;
  const spellSandbox = Object.assign({}, sandbox, {
    document: {
      body: { getAttribute: () => 'spell' },
      getElementById: id => spellNodes[id],
      addEventListener(name, callback) { if (name === 'DOMContentLoaded') spellReady = callback; }
    },
    WPI18N: { t: key => key, onChange() {} },
    API: Object.assign({}, sandbox.API, {
      get: () => Promise.resolve({ bank: { id: 21, title: '拼写', game_type: 'spell' }, groups })
    }),
    WPSpellUI: { start(mount, cfg) { spellCfg = cfg; return {}; } }
  });
  vm.createContext(spellSandbox);
  vm.runInContext(fs.readFileSync(path.join(WEB, 'page-items.js'), 'utf8'), spellSandbox);
  spellReady();
  await new Promise(resolve => setTimeout(resolve, 0));
  if (!spellNodes.igStart || !spellNodes.igStart.onclick) throw new Error('拼写页必须能开始整套游戏');
  spellNodes.igStart.onclick();
  if (spellCfg.items.length !== 10 || spellCfg.ords.join(',') !== '0,1,2,3,4,5,6,7,8,9') {
    throw new Error('拼写也必须合并全题，不分关');
  }
  console.log('page-items 动词猎手和拼写入口全部通过（2 项）');
})().catch((error) => { console.error(error); process.exit(1); });
