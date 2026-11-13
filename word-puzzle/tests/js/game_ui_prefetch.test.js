/* game_ui_prefetch.test.js —— 发音预取的行为测试
   选了关就在后台把这一关的发音取回来：并发有上限、不重复取、换关丢掉旧队列、
   失败不抛错、离线页（没有 audioBase）完全不动。 */
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const UI_FILE = path.join(__dirname, '..', '..', 'web', 'js', 'game-ui.js');
let passed = 0;
const failures = [];

function load(extra) {
  const calls = [], resolvers = [];
  const win = Object.assign({
    document: {},
    fetch(url) {
      calls.push(url);
      return new Promise((resolve, reject) => resolvers.push({ url, resolve, reject }));
    },
    Audio: function (src) { this.src = src; this.listeners = {}; this.addEventListener = (n, f) => { this.listeners[n] = f; }; },
    URL: { createObjectURL: (b) => 'blob:' + b.id },
  }, extra || {});
  win.window = win;
  vm.runInNewContext(fs.readFileSync(UI_FILE, 'utf8'), win, { filename: 'game-ui.js' });
  return { win, calls, resolvers, T: win.WPGameUI._test };
}

const ok = (id) => ({ ok: true, blob: () => Promise.resolve({ id }) });
const tick = () => new Promise((r) => setImmediate(r));
const words = (...ens) => ens.map((en) => ({ en }));

async function check(name, fn) {
  try { await fn(); passed++; } catch (e) { failures.push(name + '：' + e.message); }
}
function eq(a, b, note) {
  if (JSON.stringify(a) !== JSON.stringify(b)) {
    throw new Error('期望 ' + JSON.stringify(b) + '，实际 ' + JSON.stringify(a) + (note ? '（' + note + '）' : ''));
  }
}

(async () => {
  await check('没有 audioBase（离线页）时一个请求都不发', async () => {
    const { T, calls } = load();
    T.prefetch(words('apple', 'pear'));
    eq(calls.length, 0);
  });

  await check('并发最多 3 个，前一个完成才发下一个', async () => {
    const { T, calls, resolvers } = load();
    T.setBase('/api/audio/');
    T.prefetch(words('a', 'b', 'c', 'd', 'e'));
    eq(calls, ['/api/audio/a', '/api/audio/b', '/api/audio/c']);
    resolvers[0].resolve(ok(1));
    await tick();
    eq(calls.length, 4);
    eq(calls[3], '/api/audio/d');
  });

  await check('取回来的音频存进缓存，key 小写', async () => {
    const { T, resolvers } = load();
    T.setBase('/api/audio/');
    T.prefetch(words('Apple'));
    resolvers[0].resolve(ok(7));
    await tick();
    eq(T.cache.apple.src, 'blob:7');
  });

  await check('已缓存的词、正在取的词不重复取；单词里的空格会编码', async () => {
    const { T, calls, resolvers } = load();
    T.setBase('/api/audio/');
    T.prefetch(words('a', 'ice cream'));
    eq(calls[1], '/api/audio/ice%20cream');
    T.prefetch(words('a', 'b'));         /* a 正在取：只补 b */
    eq(calls.length, 3);
    eq(calls[2], '/api/audio/b');
    resolvers[0].resolve(ok(1)); await tick();
    T.prefetch(words('a'));              /* a 已缓存 */
    eq(calls.length, 3);
  });

  await check('换关：没开始的旧队列被丢掉，只取新选的', async () => {
    const { T, calls, resolvers } = load();
    T.setBase('/api/audio/');
    T.prefetch(words('a1', 'a2', 'a3', 'a4', 'a5'));    /* a1-a3 在取，a4 a5 排队 */
    T.prefetch(words('b1', 'b2'));
    resolvers[0].resolve(ok(1)); await tick();
    eq(calls.slice(3), ['/api/audio/b1']);
    eq(calls.includes('/api/audio/a4'), false);
  });

  await check('失败（HTTP 错误、网络错误）不抛错，不占着名额，也不进缓存', async () => {
    const { T, calls, resolvers } = load();
    T.setBase('/api/audio/');
    T.prefetch(words('a', 'b', 'c', 'd'));
    resolvers[0].resolve({ ok: false, status: 404 });
    resolvers[1].reject(new Error('net'));
    await tick();
    eq(calls.length, 4);
    eq(Object.keys(T.cache), []);
  });

  await check('等待期间用户已经点过（缓存里已有）就不覆盖', async () => {
    const { win, T, resolvers } = load();
    T.setBase('/api/audio/');
    T.prefetch(words('a'));
    const playing = new win.Audio('/api/audio/a');
    T.cache.a = playing;
    resolvers[0].resolve(ok(9));
    await tick();
    eq(T.cache.a === playing, true);
  });

  await check('浏览器没有 fetch 时安静跳过', async () => {
    const { T, win } = load({ fetch: undefined });
    T.setBase('/api/audio/');
    T.prefetch(words('a'));
    eq(Object.keys(T.cache), []);
  });

  if (failures.length) {
    console.error('失败 ' + failures.length + ' 项：\n  ' + failures.join('\n  '));
    process.exit(1);
  }
  console.log('发音预取行为测试：' + passed + ' 项全部通过');
})();
