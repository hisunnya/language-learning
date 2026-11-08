/* 极简的小程序运行环境桩：能加载 Page({...})，提供 wx.* 和可控的时钟 / 定时器。
   没有微信开发者工具时，用它验证页面逻辑（不验证 WXML 渲染）。 */
'use strict';
const path = require('path');

function createEnv() {
  const store = {};
  const calls = { toast: [], modal: [], title: [], navColor: [], bgColor: [], vibrate: 0, navigate: [] };
  const clock = { now: 1700000000000 };
  const timers = [];
  let timerId = 0;

  const wxStub = {
    getStorageSync: (k) => (k in store ? store[k] : ''),
    setStorageSync: (k, v) => { store[k] = v; },
    showToast: (o) => calls.toast.push(o.title),
    showModal: (o) => calls.modal.push(o),
    setNavigationBarTitle: (o) => calls.title.push(o.title),
    setNavigationBarColor: (o) => calls.navColor.push(o),
    setBackgroundColor: (o) => calls.bgColor.push(o),
    vibrateShort: () => { calls.vibrate++; },
    navigateTo: (o) => calls.navigate.push(o.url),
    navigateBack: () => {},
    reLaunch: () => {},
    createInnerAudioContext: () => ({ stop() {}, play() {}, destroy() {}, onError() {} }),
    downloadFile: (o) => o.fail && o.fail(new Error('offline')),
  };

  class FakeDate extends Date { static now() { return clock.now; } }

  const fake = {
    setTimeout: (fn, ms) => { timers.push({ id: ++timerId, at: clock.now + (ms || 0), fn, every: 0 }); return timerId; },
    clearTimeout: (id) => { const i = timers.findIndex((t) => t.id === id); if (i >= 0) timers.splice(i, 1); },
    setInterval: (fn, ms) => { timers.push({ id: ++timerId, at: clock.now + ms, fn, every: ms }); return timerId; },
    clearInterval: (id) => fake.clearTimeout(id),
  };

  // 把时间往前推 ms，期间到点的定时器按顺序执行
  function advance(ms) {
    const end = clock.now + ms;
    for (;;) {
      timers.sort((a, b) => a.at - b.at);
      const next = timers.find((t) => t.at <= end);
      if (!next) break;
      clock.now = Math.max(clock.now, next.at);
      if (next.every) next.at += next.every; else timers.splice(timers.indexOf(next), 1);
      next.fn();
    }
    clock.now = end;
  }

  const g = global;
  const saved = {};
  const keys = ['wx', 'Page', 'App', 'Date', 'setTimeout', 'clearTimeout', 'setInterval', 'clearInterval'];
  keys.forEach((k) => { saved[k] = g[k]; });

  const pages = {};
  g.wx = wxStub;
  g.Date = FakeDate;
  g.setTimeout = fake.setTimeout; g.clearTimeout = fake.clearTimeout;
  g.setInterval = fake.setInterval; g.clearInterval = fake.clearInterval;

  function loadPage(rel) {
    const file = path.join(__dirname, '..', '..', rel);
    Object.keys(require.cache).filter((k) => k.startsWith(path.join(__dirname, '..', '..'))
      && !k.includes(path.join('tests', 'js'))).forEach((k) => delete require.cache[k]);
    let def = null;
    g.Page = (d) => { def = d; };
    require(file);
    const inst = Object.create(def);
    inst.data = JSON.parse(JSON.stringify(def.data));
    inst.setUpdates = [];
    inst.setData = function (d) { Object.assign(this.data, d); this.setUpdates.push(Object.keys(d)); };
    pages[rel] = inst;
    return inst;
  }

  function restore() {
    keys.forEach((k) => { if (saved[k] === undefined) delete g[k]; else g[k] = saved[k]; });
  }

  return { wx: wxStub, store, calls, clock, advance, loadPage, restore, timers };
}

module.exports = { createEnv };
