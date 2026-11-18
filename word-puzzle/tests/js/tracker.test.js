/* tracker.test.js —— 页面上报：view / ping / leave、前台秒数、会话号、失败不影响页面 */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm');
const code = fs.readFileSync(path.join(__dirname, '..', '..', 'web', 'js', 'tracker.js'), 'utf8');
let passed = 0; const failures = [];
function check(name, ok, detail) { if (ok) passed++; else failures.push(name + (detail ? '：' + detail : '')); }

function makePage(opts) {
  opts = opts || {};
  const sent = [], beacons = [], listeners = {}, docListeners = {}, intervals = [];
  let clock = 1000000, visibility = 'visible';
  const store = Object.assign({}, opts.session || {});
  const RealDate = Date;
  const FakeDate = function () { return new RealDate(clock); };
  FakeDate.now = () => clock;
  const sandbox = {
    Date: FakeDate, Intl, JSON, Math, Promise, Uint8Array, Blob: class { constructor(parts) { this.text = parts.join(''); } },
    sessionStorage: opts.noStorage ? { getItem() { throw new Error('denied'); }, setItem() { throw new Error('denied'); } }
      : { getItem: (k) => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = String(v); } },
    document: {
      querySelector: () => ({ content: '/word-puzzle' }), title: '首页', referrer: 'https://x/', get visibilityState() { return visibility; },
      addEventListener: (n, f) => { docListeners[n] = f; },
    },
    location: { pathname: '/word-puzzle/stats.html', search: '?bank=7' },
    navigator: { language: 'zh-CN', languages: ['zh-CN', 'en'], platform: 'iPhone', hardwareConcurrency: 6, maxTouchPoints: 5, onLine: true, cookieEnabled: true,
      connection: { effectiveType: '4g', downlink: 10, rtt: 50 },
      sendBeacon: opts.noBeacon ? undefined : (url, blob) => { beacons.push({ url, body: JSON.parse(blob.text) }); return true; },
      userAgentData: opts.uad ? { mobile: true, platform: 'Android', brands: [{ brand: 'Chrome', version: '120' }], getHighEntropyValues: () => Promise.resolve({ model: 'Pixel 8', platformVersion: '14' }) } : undefined },
    screen: { width: 390, height: 844 }, innerWidth: 390, innerHeight: 700, devicePixelRatio: 3,
    matchMedia: () => ({ matches: false }),
    crypto: { getRandomValues: (a) => { for (let i = 0; i < a.length; i++) a[i] = (i * 37 + sent.length * 11 + 5) & 255; return a; } },
    fetch: (url, init) => { sent.push({ url, body: JSON.parse(init.body), init }); return opts.failFetch ? Promise.reject(new Error('net')) : Promise.resolve({}); },
    setInterval: (f, ms) => { intervals.push({ f, ms }); return intervals.length; }, clearInterval: () => {},
    addEventListener: (n, f) => { listeners[n] = f; },
  };
  sandbox.window = sandbox;
  vm.createContext(sandbox);
  vm.runInContext(code, sandbox);
  const advance = (sec) => { for (let i = 0; i < sec; i++) { clock += 1000; intervals[0].f(); if (i % 15 === 14) intervals[1].f(); } };
  return { sent, beacons, store, advance, win: sandbox, intervals, docListeners, listeners,
    hide: () => { visibility = 'hidden'; docListeners.visibilitychange(); }, show: () => { visibility = 'visible'; docListeners.visibilitychange(); },
    tick: (sec) => { clock += sec * 1000; } };
}

(async () => {
  let p = makePage();
  check('打开页面就报一次 view，发到 /word-puzzle/api/track', p.sent.length === 1 && p.sent[0].url === '/word-puzzle/api/track' && p.sent[0].body.event === 'view');
  const v = p.sent[0].body;
  check('view 带页面路径、标题、来源、会话号和页面号', v.path === '/word-puzzle/stats.html' && v.title === '首页' && v.referrer === 'https://x/' && /^[0-9a-f]{24}$/.test(v.vid) && /^[0-9a-f]{24}$/.test(v.sid));
  check('view 带设备信息：屏幕、核数、网络、语言', v.client.screen === '390x844' && v.client.cores === 6 && v.client.connection === '4g' && v.client.lang === 'zh-CN' && v.client.dpr === 3 && v.client.touch === 5);
  check('同一标签页的会话号存进 sessionStorage', p.store.wp_sid === v.sid);
  const q = makePage({ session: { wp_sid: 'abcdef0123456789' } });
  check('再打开一个页面沿用同一个会话号，页面号不同', q.sent[0].body.sid === 'abcdef0123456789');

  p.advance(30);
  const pings = p.sent.filter((x) => x.body.event === 'ping');
  check('前台每 15 秒报一次 ping，带累计前台秒数', pings.length === 2 && pings[0].body.active === 15 && pings[1].body.active === 30, JSON.stringify(pings.map((x) => x.body)));
  check('ping 的页面号和 view 一致', pings.every((x) => x.body.vid === v.vid));

  p = makePage(); p.advance(10); p.hide(); p.tick(600); p.show(); p.advance(5);
  check('切到后台的 10 分钟不算停留', p.win.WPTrack.active() === 15, String(p.win.WPTrack.active()));
  check('切到后台时用 sendBeacon 报一次（页面可能随后被系统回收）', p.beacons.length === 1 && p.beacons[0].body.event === 'ping' && p.beacons[0].body.active === 10);

  p = makePage(); p.tick(3 * 3600);
  check('电脑睡眠后醒来，一次最多只加 5 秒', p.win.WPTrack.active() <= 5, String(p.win.WPTrack.active()));

  p = makePage(); p.advance(20); p.listeners.pagehide(); p.listeners.pagehide();
  check('离开时用 sendBeacon 报 leave（只报一次）', p.beacons.filter((b) => b.body.event === 'leave').length === 1 && p.beacons.at(-1).body.active === 20);

  p = makePage({ noBeacon: true }); p.advance(3); p.listeners.pagehide();
  check('没有 sendBeacon 时用 keepalive 的 fetch', p.sent.at(-1).body.event === 'leave' && p.sent.at(-1).init.keepalive === true);

  p = makePage({ failFetch: true }); p.advance(15);
  check('网络失败不抛异常、页面照常', p.sent.length === 2);

  p = makePage({ noStorage: true });
  check('禁用 sessionStorage 也能上报', p.sent.length === 1 && /^[0-9a-f]{24}$/.test(p.sent[0].body.sid));

  p = makePage({ uad: true }); await Promise.resolve(); await Promise.resolve();
  const env = p.sent.filter((x) => x.body.event === 'env');
  check('取得到详细型号时补报一次 env', env.length === 1 && env[0].body.client.ua_model === 'Pixel 8' && env[0].body.vid === p.sent[0].body.vid);
  check('view 里带页面地址的查询串（服务器据此记下用的是哪个题库）', p.sent[0].body.search === '?bank=7');
  check('view 里带 Client Hints 的品牌和平台', p.sent[0].body.client.ua_platform === 'Android' && /Chrome 120/.test(p.sent[0].body.client.ua_brands));

  p = makePage(); p.hide();
  check('后台时不发 ping 心跳（定时器触发也不发）', (() => { const n = p.sent.length; p.intervals[1].f(); return p.sent.length === n; })());

  console.log(failures.length ? 'FAIL\n' + failures.join('\n') : 'tracker: ' + passed + ' checks passed');
  process.exit(failures.length ? 1 : 0);
})();
