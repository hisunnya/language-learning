/* hub/shared/wechat.js：只在微信里生效；字号回调；下载提示（只在声明了 data-wx-download 的页面，可关闭，记住） */
const fs = require('fs');
const path = require('path');
const SRC = fs.readFileSync(path.join(__dirname, '..', '..', '..', 'hub', 'shared', 'wechat.js'), 'utf8');

let passed = 0; const failed = [];
function check(name, fn) { try { fn(); passed++; } catch (e) { failed.push(name + '：' + e.message); } }
function eq(a, b, m) { if (a !== b) throw new Error((m || '') + ' 期望 ' + JSON.stringify(b) + ' 实际 ' + JSON.stringify(a)); }
function ok(c, m) { if (!c) throw new Error(m || '应为真'); }

function el(tag) {
  const e = { tag, style: {}, children: [], attrs: {}, listeners: {}, textContent: '', parentNode: null,
    setAttribute(k, v) { this.attrs[k] = v; }, getAttribute(k) { return k in this.attrs ? this.attrs[k] : null; },
    hasAttribute(k) { return k in this.attrs; },
    appendChild(c) { c.parentNode = this; this.children.push(c); return c; },
    insertBefore(c, ref) { c.parentNode = this; this.children.unshift(c); return c; },
    removeChild(c) { this.children = this.children.filter((x) => x !== c); c.parentNode = null; },
    addEventListener(t, f) { (this.listeners[t] = this.listeners[t] || []).push(f); },
    click() { (this.listeners.click || []).forEach((f) => f()); } };
  return e;
}

function env(opts) {
  const body = el('body');
  if (opts.download) body.attrs['data-wx-download'] = '1';
  const html = el('html'); html.className = ''; html.attrs.lang = opts.lang || 'zh-CN';
  const docListeners = {};
  const doc = { documentElement: html, body, createElement: el, getElementById: (id) => (body.children.find((c) => c.id === id) || null),
    addEventListener(t, f) { (docListeners[t] = docListeners[t] || []).push(f); } };
  const store = opts.store || {};
  const winListeners = {};
  const calls = [];
  const win = { document: doc, navigator: { userAgent: opts.ua }, sessionStorage: { getItem: (k) => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = v; } },
    addEventListener(t, f) { (winListeners[t] = winListeners[t] || []).push(f); } };
  if (opts.bridge) win.WeixinJSBridge = { invoke: (n, a) => calls.push(['invoke', n, a.fontSize]), on: (n) => calls.push(['on', n]) };
  new Function('window', 'return (function (global) {' + SRC.slice(SRC.indexOf("'use strict';") + 13, SRC.lastIndexOf('})(typeof')) + '})(window)')(win);
  return { win, doc, html, body, calls, docListeners, winListeners, store };
}
const WX = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 MicroMessenger/8.0.47 NetType/WIFI Language/zh_CN';
const SAFARI = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Version/17.0 Mobile/15E148 Safari/604.1';

check('不是微信：什么都不做', () => {
  const e = env({ ua: SAFARI, download: true, bridge: true });
  eq(e.html.className, '');
  eq(e.body.children.length, 0, '不显示提示');
  eq(e.calls.length, 0);
  eq(e.win.WPWeChat.start(e.win), false);
});

check('微信：加 is-wechat，并让微信别放大字号', () => {
  const e = env({ ua: WX, bridge: true });
  ok(/is-wechat/.test(e.html.className));
  eq(JSON.stringify(e.calls[0]), JSON.stringify(['invoke', 'setFontSizeCallback', 0]));
  ok(e.calls.some((c) => c[0] === 'on' && c[1] === 'menu:setfont'), '用户在微信里改字号时也要再关掉');
});

check('微信桥还没准备好：等 WeixinJSBridgeReady 再调', () => {
  const e = env({ ua: WX, bridge: false });
  eq(e.calls.length, 0);
  ok(e.docListeners.WeixinJSBridgeReady && e.docListeners.WeixinJSBridgeReady.length === 1);
  e.win.WeixinJSBridge = { invoke: (n, a) => e.calls.push(['invoke', n, a.fontSize]), on: () => {} };
  e.docListeners.WeixinJSBridgeReady[0]();
  eq(e.calls[0][1], 'setFontSizeCallback');
});

check('微信 + 声明了下载的页面：顶部有提示，中文', () => {
  const e = env({ ua: WX, download: true });
  const tip = e.doc.getElementById('wxDownloadTip');
  ok(tip, '应有提示');
  ok(/在浏览器打开|默认浏览器打开/.test(tip.children[0].textContent));
  eq(e.body.children[0], tip, '放在最上面');
});

check('没声明下载的页面（学生玩游戏的页面）：不打扰', () => {
  const e = env({ ua: WX, download: false });
  eq(e.doc.getElementById('wxDownloadTip'), null);
});

check('英文界面显示英文，切换语言时跟着变', () => {
  const e = env({ ua: WX, download: true, lang: 'en' });
  const tip = e.doc.getElementById('wxDownloadTip');
  ok(/Open in browser/.test(tip.children[0].textContent));
  eq(tip.children[1].textContent, 'Got it');
  e.html.attrs.lang = 'zh-CN';
  e.winListeners['portal-lang-change'][0]();
  ok(/默认浏览器打开/.test(tip.children[0].textContent));
  eq(tip.children[1].textContent, '知道了');
});

check('点「知道了」：提示消失，本次会话不再出现', () => {
  const e = env({ ua: WX, download: true });
  const tip = e.doc.getElementById('wxDownloadTip');
  tip.children[1].click();
  eq(e.doc.getElementById('wxDownloadTip'), null);
  eq(e.store.wx_download_tip_closed, '1');
  const again = env({ ua: WX, download: true, store: e.store });
  eq(again.doc.getElementById('wxDownloadTip'), null, '同一会话里换页面也不再出现');
});

console.log('wechat.js：通过 ' + passed + ' 项');
if (failed.length) { console.log('失败 ' + failed.length + ' 项：\n  - ' + failed.join('\n  - ')); process.exit(1); }
