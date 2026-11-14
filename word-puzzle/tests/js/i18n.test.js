/* i18n.test.js —— 中英文切换的行为测试
   取词、占位符、缺词时的退路；切换语言发出事件、重画；没有页眉的页面（离线单文件）自己读 / 存语言。 */
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const JS_DIR = path.join(__dirname, '..', '..', 'web', 'js');
let passed = 0;
const failures = [];
function check(name, fn) { try { fn(); passed++; } catch (e) { failures.push(name + '：' + e.message); } }
function eq(a, b, note) {
  if (JSON.stringify(a) !== JSON.stringify(b)) {
    throw new Error('期望 ' + JSON.stringify(b) + '，实际 ' + JSON.stringify(a) + (note ? '（' + note + '）' : ''));
  }
}

/* 一个够用的假页面：lang 属性、带 data-module-* 的元素、localStorage、事件 */
function makeWindow(opts) {
  opts = opts || {};
  const attrs = { lang: opts.htmlLang || 'zh-CN' };
  const elements = (opts.elements || []).map((e) => ({
    attrs: Object.assign({}, e), textContent: e.text || '',
    getAttribute(n) { return n in this.attrs ? this.attrs[n] : null; },
    setAttribute(n, v) { this.attrs[n] = v; },
  }));
  const store = Object.assign({}, opts.storage);
  const listeners = {}, domReady = [];
  const win = {
    navigator: { language: opts.navigator || 'zh-CN' },
    localStorage: { getItem: (k) => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = String(v); } },
    addEventListener(name, fn) { (listeners[name] = listeners[name] || []).push(fn); },
    dispatchEvent(ev) { (listeners[ev.type] || []).forEach((fn) => fn(ev)); },
    CustomEvent: function (type, init) { this.type = type; this.detail = init && init.detail; },
    document: {
      documentElement: { getAttribute: (n) => attrs[n], setAttribute: (n, v) => { attrs[n] = v; } },
      addEventListener(name, fn) { if (name === 'DOMContentLoaded') domReady.push(fn); },
      querySelectorAll(sel) {
        if (sel === '[data-module-zh][data-module-en]') {
          return elements.filter((e) => e.getAttribute('data-module-zh') !== null && e.getAttribute('data-module-en') !== null);
        }
        const m = /^\[data-i18n-(\w+)-zh\]$/.exec(sel);
        return m ? elements.filter((e) => e.getAttribute('data-i18n-' + m[1] + '-zh') !== null) : [];
      },
    },
  };
  win.window = win;
  if (opts.header) win.PortalHeader = opts.header;
  vm.createContext(win);
  vm.runInContext(fs.readFileSync(path.join(JS_DIR, 'i18n.js'), 'utf8'), win, { filename: 'i18n.js' });
  return { win, elements, store, attrs, ready() { domReady.forEach((fn) => fn()); } };
}

check('取词：按当前语言，{占位符}被替换，缺参数时原样保留', () => {
  const { win } = makeWindow();
  win.WPI18N.add({ hi: '你好 {name}，{n} 个' }, { hi: 'Hello {name}, {n}' });
  eq(win.WPI18N.t('hi', { name: '甲', n: 3 }), '你好 甲，3 个');
  eq(win.WPI18N.t('hi', { name: '甲' }), '你好 甲，{n} 个');
  win.document.documentElement.setAttribute('lang', 'en');
  eq(win.WPI18N.t('hi', { name: 'A', n: 3 }), 'Hello A, 3');
});

check('缺英文词条时退回中文，两边都没有就返回键，页面不会空白', () => {
  const { win } = makeWindow({ htmlLang: 'en' });
  win.WPI18N.add({ onlyZh: '只有中文' }, {});
  eq(win.WPI18N.t('onlyZh'), '只有中文');
  eq(win.WPI18N.t('nowhere'), 'nowhere');
});

check('0 和空字符串也是有效的参数值', () => {
  const { win } = makeWindow();
  win.WPI18N.add({ k: '{a}|{b}' }, { k: '{a}|{b}' });
  eq(win.WPI18N.t('k', { a: 0, b: '' }), '0|');
});

check('页眉发出 portal-lang-change：换占位符，再通知各页面重画', () => {
  const { win, elements } = makeWindow({ elements: [
    { 'data-i18n-placeholder-zh': '搜索', 'data-i18n-placeholder-en': 'Search', placeholder: '搜索' },
  ] });
  const seen = [];
  win.WPI18N.onChange((lang) => seen.push(lang));
  win.document.documentElement.setAttribute('lang', 'en');
  win.dispatchEvent(new win.CustomEvent('portal-lang-change', { detail: { lang: 'en' } }));
  eq(seen, ['en']);
  eq(elements[0].getAttribute('placeholder'), 'Search');
});

check('一个监听出错，不影响其他监听', () => {
  const { win } = makeWindow();
  let ran = false;
  win.WPI18N.onChange(() => { throw new Error('boom'); });
  win.WPI18N.onChange(() => { ran = true; });
  win.dispatchEvent(new win.CustomEvent('portal-lang-change'));
  eq(ran, true);
});

check('有页眉时 setLang 交给页眉，自己不动 lang 也不写存储', () => {
  const calls = [];
  const { win, attrs, store } = makeWindow({ header: { applyLanguage: (l) => calls.push(l) } });
  win.WPI18N.setLang('en');
  eq(calls, ['en']);
  eq(attrs.lang, 'zh-CN');
  eq(Object.keys(store), []);
});

check('没有页眉（离线页）：setLang 改 lang、存 lg_lang、换静态文字、通知重画', () => {
  const { win, elements, attrs, store } = makeWindow({ elements: [
    { 'data-module-zh': '开始', 'data-module-en': 'Start', text: '开始' },
  ] });
  let notified = '';
  win.WPI18N.onChange((l) => { notified = l; });
  win.WPI18N.setLang('en');
  eq(attrs.lang, 'en');
  eq(store.lg_lang, 'en');
  eq(elements[0].textContent, 'Start');
  eq(notified, 'en');
  win.WPI18N.setLang('zh');
  eq([attrs.lang, elements[0].textContent], ['zh-CN', '开始']);
});

check('离线页启动：先用保存的语言，没有就跟浏览器语言', () => {
  let page = makeWindow({ storage: { lg_lang: 'en' }, navigator: 'zh-CN',
    elements: [{ 'data-module-zh': '开始', 'data-module-en': 'Start', text: '开始' }] });
  page.ready();
  eq([page.attrs.lang, page.elements[0].textContent], ['en', 'Start']);
  page = makeWindow({ navigator: 'en-US' });
  page.ready();
  eq(page.attrs.lang, 'en');
  page = makeWindow({ navigator: 'fr-FR' });
  page.ready();
  eq(page.attrs.lang, 'zh-CN', '不认识的语言按中文');
});

check('有页眉的页面启动时，i18n.js 不去改语言', () => {
  const page = makeWindow({ header: { applyLanguage() {} }, storage: { lg_lang: 'en' } });
  page.ready();
  eq(page.attrs.lang, 'zh-CN');
});

if (failures.length) {
  console.error('失败 ' + failures.length + ' 项：\n  ' + failures.join('\n  '));
  process.exit(1);
}
console.log('中英文切换行为测试：' + passed + ' 项全部通过');
