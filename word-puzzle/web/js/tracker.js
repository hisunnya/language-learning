/* ============================================================
   tracker.js —— 访问记录上报（家庭版）
   页面打开时报一次 view，在前台期间每 15 秒报一次 ping（带累计前台秒数），离开时报 leave。
   同一个浏览器标签页里先后打开的页面共用一个会话号 sid（存在 sessionStorage），
   老师页面里的「一次访问」就是一个 sid。上报失败一律悄悄忽略，绝不影响页面本身。
   ============================================================ */
(function (global) {
  'use strict';

  var PING_MS = 15000, TICK_MS = 1000;
  var base = ((document.querySelector('meta[name="wp-base"]') || {}).content || '').replace(/\/$/, '');
  var endpoint = base + '/api/track';

  function rand() {
    var out = '', i;
    try {
      var buf = new Uint8Array(12);
      global.crypto.getRandomValues(buf);
      for (i = 0; i < buf.length; i++) out += ('0' + buf[i].toString(16)).slice(-2);
    } catch (e) {
      for (i = 0; i < 24; i++) out += Math.floor(Math.random() * 16).toString(16);
    }
    return out;
  }

  function sessionId() {
    try {
      var sid = sessionStorage.getItem('wp_sid');
      if (!sid) { sid = rand(); sessionStorage.setItem('wp_sid', sid); }
      return sid;
    } catch (e) { return rand(); }          /* 禁用了 sessionStorage：每个页面各算一次访问 */
  }

  /* 浏览器能告诉我们的设备信息，能拿多少拿多少；拿不到的字段就不放 */
  function clientInfo() {
    var n = global.navigator || {}, s = global.screen || {}, c = n.connection || {}, info = {};
    function put(key, value) { if (value !== undefined && value !== null && value !== '') info[key] = value; }
    put('screen', s.width && (s.width + 'x' + s.height));
    put('viewport', global.innerWidth && (global.innerWidth + 'x' + global.innerHeight));
    put('dpr', global.devicePixelRatio);
    try { put('tz', Intl.DateTimeFormat().resolvedOptions().timeZone); } catch (e) {}
    put('tz_offset', new Date().getTimezoneOffset());
    put('lang', n.language);
    put('langs', (n.languages || []).join(','));
    put('platform', n.platform);
    put('cores', n.hardwareConcurrency);
    put('memory', n.deviceMemory);
    put('touch', n.maxTouchPoints);
    put('connection', c.effectiveType);
    put('downlink', c.downlink);
    put('rtt', c.rtt);
    put('save_data', c.saveData);
    put('online', n.onLine);
    put('cookies', n.cookieEnabled);
    put('dnt', n.doNotTrack);
    try { put('color_scheme', global.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'); } catch (e) {}
    try { put('standalone', global.matchMedia('(display-mode: standalone)').matches); } catch (e) {}
    var uad = n.userAgentData;
    if (uad) {
      put('ua_mobile', uad.mobile);
      put('ua_platform', uad.platform);
      put('ua_brands', (uad.brands || []).map(function (b) { return b.brand + ' ' + b.version; }).join(', '));
    }
    return info;
  }

  var vid = rand(), sid = sessionId();
  var active = 0, last = Date.now(), sent = false, ended = false, timer = null, pinger = null;

  function visible() { return !document.visibilityState || document.visibilityState === 'visible'; }
  function tick() {
    var now = Date.now();
    if (visible()) active += Math.max(0, Math.min(now - last, 5000)) / 1000;      /* 一次最多算 5 秒：电脑睡眠后醒来不会一下加几小时 */
    last = now;
  }

  function send(body, beacon) {
    body.vid = vid;
    var text = JSON.stringify(body);
    try {
      if (beacon && global.navigator && navigator.sendBeacon && navigator.sendBeacon(endpoint, new Blob([text], { type: 'application/json' }))) return;
      global.fetch(endpoint, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: text, keepalive: true, credentials: 'same-origin' })
        .catch(function () {});
    } catch (e) {}
  }

  function report(event, beacon) {
    tick();
    if (event === 'view') {
      sent = true;
      send({ event: 'view', sid: sid, path: location.pathname, title: document.title, referrer: document.referrer, client: clientInfo() }, false);
      detail();
    } else if (sent) {
      send({ event: event, active: Math.round(active) }, beacon);
    }
  }

  /* 设备型号等「高精度」信息要异步取（Chrome 系），取到了再补报一次 */
  function detail() {
    var uad = global.navigator && navigator.userAgentData;
    if (!uad || !uad.getHighEntropyValues) return;
    try {
      uad.getHighEntropyValues(['model', 'platformVersion', 'architecture', 'bitness', 'fullVersionList']).then(function (v) {
        var info = { ua_model: v.model, ua_platform_version: v.platformVersion, ua_arch: v.architecture, ua_bitness: v.bitness };
        if (v.fullVersionList && v.fullVersionList.length) info.ua_full_version = v.fullVersionList.map(function (b) { return b.brand + ' ' + b.version; }).join(', ');
        send({ event: 'env', client: info }, false);
      }).catch(function () {});
    } catch (e) {}
  }

  function leave() {
    if (ended) return;
    ended = true;
    clearInterval(timer);
    clearInterval(pinger);
    report('leave', true);
  }

  report('view');
  timer = setInterval(tick, TICK_MS);
  pinger = setInterval(function () { if (visible()) report('ping'); }, PING_MS);
  document.addEventListener('visibilitychange', function () {
    if (!visible()) report('ping', true); else { last = Date.now(); ended = false; }
  });
  global.addEventListener('pagehide', leave);

  global.WPTrack = { vid: vid, sid: sid, active: function () { tick(); return Math.round(active); }, report: report, clientInfo: clientInfo, leave: leave };
})(window);
