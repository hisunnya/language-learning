// 小程序工具层与页面逻辑的行为测试（node，缺 node 时由 tests/test_miniprogram.py 跳过）
'use strict';
const assert = require('assert');
const path = require('path');
const { createEnv } = require('./harness.js');

const ROOT = path.resolve(__dirname, '..', '..');
const results = [];
async function test(name, fn) {
  const env = createEnv();
  try { await fn(env); results.push(['ok', name]); }
  catch (e) { results.push(['fail', name, e]); }
  finally { env.restore(); }
}
const req = (rel) => require(path.join(ROOT, rel));
const tick = () => new Promise((r) => process.nextTick(r));
async function settle() { for (let i = 0; i < 6; i++) await tick(); }

(async () => {
  /* ---------- i18n ---------- */
  await test('两种语言的键完全一致，没有空字符串', () => {
    const { STRINGS } = req('utils/i18n.js');
    assert.deepStrictEqual(Object.keys(STRINGS.zh).sort(), Object.keys(STRINGS.en).sort());
    Object.keys(STRINGS.zh).forEach((k) => {
      assert.ok(STRINGS.zh[k] && STRINGS.en[k], k + ' 为空');
      // 模板里的占位符两种语言必须一致
      const ph = (s) => (s.match(/\{\w+\}/g) || []).sort().join();
      assert.strictEqual(ph(STRINGS.zh[k]), ph(STRINGS.en[k]), k + ' 的占位符不一致');
    });
  });

  await test('关卡名里的中文后缀在英文界面里被替换，单元名保持原样', () => {
    const { localizeLevel } = req('utils/i18n.js');
    assert.strictEqual(localizeLevel('Unit 3（2/3） · 含复习', 'zh'), 'Unit 3（2/3） · 含复习');
    assert.strictEqual(localizeLevel('Unit 3（2/3） · 含复习', 'en'), 'Unit 3 (2/3) · incl. review');
    assert.strictEqual(localizeLevel('Unit 9（补充）', 'en'), 'Unit 9 (extra)');
    assert.strictEqual(localizeLevel('Unit 9（补充2）', 'en'), 'Unit 9 (extra 2)');
    assert.strictEqual(localizeLevel('Unit 1', 'en'), 'Unit 1');
    assert.ok(!/[一-龥]/.test(localizeLevel('Unit 9（3/4） · 含复习', 'en')), '英文界面里不该残留汉字');
  });

  await test('连点同一侧的提示说的是「刚选的那一侧」（不能说反）', () => {
    const { switchHint } = req('utils/i18n.js');
    assert.ok(switchHint('zh', 'cn').includes('中文'), '新点的是中文卡，应说刚选的是中文');
    assert.ok(switchHint('zh', 'en').includes('英文'));
    assert.ok(/Chinese/.test(switchHint('en', 'cn')));
    assert.ok(/English/.test(switchHint('en', 'en')));
  });

  await test('format 填充占位符，缺的占位符原样保留', () => {
    const { format } = req('utils/i18n.js');
    assert.strictEqual(format('{a}-{b}', { a: 1, b: 'x' }), '1-x');
    assert.strictEqual(format('{a}-{b}', { a: 1 }), '1-{b}');
  });

  await test('册名：英文界面用「年级 · Vol.」', () => {
    const { bookLabel } = req('utils/i18n.js');
    assert.strictEqual(bookLabel({ name: '九年级上册', term: '上册' }, '九年级', 'zh'), '九年级上册');
    assert.strictEqual(bookLabel({ name: '九年级下册', term: '下册' }, '九年级', 'en'), 'Grade 9 · Vol. 2');
  });

  /* ---------- prefs ---------- */
  await test('语言和配色偏好会被记住，非法值回到默认', (env) => {
    const prefs = req('utils/prefs.js');
    assert.strictEqual(prefs.getLang(), 'zh');
    assert.strictEqual(prefs.getTheme(), 'indigo');
    prefs.setLang('en'); prefs.setTheme('lotus');
    assert.strictEqual(env.store.wp_lang, 'en');
    assert.strictEqual(env.store.wp_theme, 'lotus');
    env.store.wp_theme = 'no-such-theme'; env.store.wp_lang = 'fr';
    assert.strictEqual(prefs.getTheme(), 'indigo');
    assert.strictEqual(prefs.getLang(), 'zh');
  });

  await test('snapshot：当前配色被标记，方块带自己的两种颜色，名称随语言变', (env) => {
    const prefs = req('utils/prefs.js');
    prefs.setTheme('amber'); prefs.setLang('en');
    const snap = prefs.snapshot();
    assert.strictEqual(snap.palettes.length, 5);
    assert.deepStrictEqual(snap.palettes.filter((p) => p.on).map((p) => p.key), ['amber']);
    assert.strictEqual(snap.themeName, 'Amber · Cream');
    snap.palettes.forEach((p) => assert.ok(/--swatch-main:#[0-9a-f]{6};--swatch-bg:#[0-9a-f]{6};/.test(p.style), p.style));
    assert.strictEqual(new Set(snap.palettes.map((p) => p.style)).size, 5, '每个方块的颜色组合都不同');
  });

  await test('applyChrome：深色配色用白色导航栏文字，浅色用黑色', (env) => {
    const prefs = req('utils/prefs.js');
    prefs.setTheme('obsidian'); prefs.applyChrome();
    prefs.setTheme('lotus'); prefs.applyChrome();
    assert.strictEqual(env.calls.navColor[0].frontColor, '#ffffff');
    assert.strictEqual(env.calls.navColor[1].frontColor, '#000000');
    assert.strictEqual(env.calls.bgColor[0].backgroundColor, '#08080a');
  });

  await test('没有 wx.setNavigationBarColor 的低版本也不会报错', (env) => {
    const prefs = req('utils/prefs.js');
    delete env.wx.setNavigationBarColor; delete env.wx.setBackgroundColor;
    prefs.applyChrome();
  });

  /* ---------- audio：声音永远不能影响游戏 ---------- */
  await test('没配置时静默：不下载、不播放、不报错', async () => {
    const audio = req('utils/audio.js'); audio._reset();
    assert.strictEqual(audio.enabled(), false);
    audio.play('apple');
    assert.strictEqual(await audio.preload([{ en: 'apple' }]), 0);
  });

  await test('下载失败：preload 不抛异常、返回成功数，play 不抛异常', async (env) => {
    const audio = req('utils/audio.js'); audio._reset(() => env.clock.now);
    audio.configure({ download: () => Promise.reject(new Error('offline')) });
    assert.strictEqual(audio.enabled(), true);
    assert.strictEqual(await audio.preload([{ en: 'a' }, { en: 'b' }]), 0);
    audio.play('a');
    await settle();
  });

  await test('同步抛异常的下载器也不会拖垮游戏', async (env) => {
    const audio = req('utils/audio.js'); audio._reset(() => env.clock.now);
    audio.configure({ download: () => { throw new Error('boom'); } });
    assert.strictEqual(await audio.preload([{ en: 'a' }]), 0);
  });

  await test('同一个词同时只下载一次；成功后走缓存', async (env) => {
    const audio = req('utils/audio.js'); audio._reset(() => env.clock.now);
    let n = 0;
    audio.configure({ download: () => { n++; return Promise.resolve('/tmp/a.mp3'); } });
    const [x, y] = await Promise.all([audio.preload([{ en: 'a' }, { en: 'a' }]), audio.preload([{ en: 'a' }])]);
    assert.strictEqual(n, 1);
    assert.strictEqual(x, 1); assert.strictEqual(y, 1);
    await audio.preload([{ en: 'a' }]);
    assert.strictEqual(n, 1, '已缓存的词不再下载');
  });

  await test('失败的词冷却期内不重试，冷却后会再试，成功后恢复', async (env) => {
    const audio = req('utils/audio.js'); audio._reset(() => env.clock.now);
    let n = 0; let ok = false;
    audio.configure({ download: () => { n++; return ok ? Promise.resolve('/tmp/a.mp3') : Promise.reject(new Error('x')); } });
    await audio.preload([{ en: 'a' }]);
    await audio.preload([{ en: 'a' }]);
    assert.strictEqual(n, 1, '冷却期内不重试');
    env.clock.now += audio.RETRY_AFTER_MS + 1;
    ok = true;
    assert.strictEqual(await audio.preload([{ en: 'a' }]), 1);
    assert.strictEqual(n, 2);
  });

  await test('点得太快只播最后一个词', async (env) => {
    const audio = req('utils/audio.js'); audio._reset(() => env.clock.now);
    const played = [];
    env.wx.createInnerAudioContext = () => ({ stop() {}, play() {}, destroy() {}, onError() {},
      set src(v) { played.push(v); } });
    const resolvers = {};
    audio.configure({ download: (w) => new Promise((r) => { resolvers[w] = () => r('/tmp/' + w + '.mp3'); }) });
    audio.play('first'); audio.play('second');
    resolvers.first(); resolvers.second();
    await settle();
    assert.deepStrictEqual(played, ['/tmp/second.mp3']);
  });

  await test('云开发模式用 wx.cloud.downloadFile 和 fileID', async (env) => {
    const audio = req('utils/audio.js'); audio._reset(() => env.clock.now);
    const ids = [];
    env.wx.cloud = { downloadFile: (o) => { ids.push(o.fileID); o.success({ statusCode: 200, tempFilePath: '/tmp/x.mp3' }); } };
    audio.configure({ cloudPrefix: 'cloud://env/audio' });
    assert.strictEqual(await audio.preload([{ en: 'ice cream' }]), 1);
    assert.deepStrictEqual(ids, ['cloud://env/audio/ice%20cream.mp3']);
  });

  await test('云存储文件不存在（statusCode 不是 200）算失败，不当成功', async (env) => {
    const audio = req('utils/audio.js'); audio._reset(() => env.clock.now);
    env.wx.cloud = { downloadFile: (o) => o.success({ statusCode: 404, tempFilePath: '' }) };
    audio.configure({ cloudPrefix: 'cloud://env/audio/' });
    assert.strictEqual(await audio.preload([{ en: 'apple' }]), 0);
  });

  /* ---------- 游戏页 ---------- */
  // setup(audio)：页面加载后、onLoad 之前，对「页面真正用的那个 audio 模块」做配置
  function startGame(env, lang, unit, setup) {
    if (lang) env.store.wp_lang = lang;
    const page = env.loadPage('pages/game/game.js');
    if (setup) setup(req('utils/audio.js'));
    page.onLoad({ book: '0', unit: String(unit === undefined ? 0 : unit) });
    return page;
  }
  const cardOf = (page, t, id) => ({ currentTarget: { dataset: { t, id } } });

  await test('英文界面：关卡信息、按钮文字都是英文，关卡名里没有汉字', (env) => {
    const page = startGame(env, 'en');
    assert.strictEqual(page.data.lang, 'en');
    assert.ok(/^Level 1\/\d+ · /.test(page.data.levelLine), page.data.levelLine);
    assert.ok(!/[一-龥]/.test(page.data.levelLine), page.data.levelLine);
    assert.strictEqual(page.data.t.btnReplay, 'Replay level');
    assert.ok(!/[一-龥]/.test(env.calls.title.slice(-1)[0]), '导航栏标题也要是英文');
  });

  await test('配色：页面带 theme 类，导航栏和底色同步设置', (env) => {
    env.store.wp_theme = 'ink';
    const page = startGame(env, 'zh');
    assert.strictEqual(page.data.theme, 'ink');
    assert.strictEqual(env.calls.navColor.slice(-1)[0].backgroundColor, '#0c1210');
  });

  await test('没配置语音时不显示 🔊；配置后显示', (env) => {
    assert.strictEqual(startGame(env).data.audioOn, false);
    const page = startGame(env, 'zh', 0, (audio) => audio.configure({ download: () => Promise.resolve('/x') }));
    assert.strictEqual(page.data.audioOn, true);
    req('utils/audio.js')._reset();
  });

  await test('语音全部下载失败，整局照样能玩到过关', async (env) => {
    let asked = 0;
    const page = startGame(env, 'zh', 0, (audio) => {
      audio._reset(() => env.clock.now);
      audio.configure({ download: () => { asked++; return Promise.reject(new Error('offline')); } });
    });
    const words = page.levels[0].words;
    for (let i = 0; i < words.length; i++) {
      page.onTapCard(cardOf(page, 'cn', i));
      page.onTapCard(cardOf(page, 'en', i));
    }
    await settle();
    assert.strictEqual(page.data.overlay, 'clear', '语音失败不应影响过关');
    assert.ok(page.data.score > 0);
    assert.ok(asked > 0, '页面确实尝试过下载（否则这条测试没有意义）');
    req('utils/audio.js')._reset();
  });

  await test('连点两张中文卡：提示说「刚选的是中文」', (env) => {
    const page = startGame(env, 'zh');
    page.onTapCard(cardOf(page, 'cn', 0));
    page.onTapCard(cardOf(page, 'cn', 1));
    assert.ok(env.calls.toast.slice(-1)[0].includes('刚选的是中文'), env.calls.toast.join('|'));
  });

  await test('切到后台暂停计时，回来接着走，不扣切走的时间', (env) => {
    const page = startGame(env, 'zh');
    page.onShow();
    env.advance(20000);
    const before = page.game.state.timeLeft;
    page.onHide();
    env.advance(90000);
    assert.strictEqual(page.game.state.paused, true);
    page.onShow();
    env.advance(5000);
    const left = page.game.state.timeLeft;
    assert.ok(Math.abs(left - (before - 5)) < 0.5, '剩余 ' + left + '，应约为 ' + (before - 5));
    assert.strictEqual(page.data.overlay, '', '不应因为切走而超时');
  });

  await test('页面卸载后，没跑完的动画定时器不会再 setData', (env) => {
    const page = startGame(env, 'zh');
    page.onShow();
    page.onTapCard(cardOf(page, 'cn', 0));
    page.onTapCard(cardOf(page, 'en', 0));    /* 配对成功，会登记 460ms 的收牌定时器 */
    const updatesBefore = page.setUpdates.length;
    page.onUnload();
    env.advance(5000);
    assert.strictEqual(page.setUpdates.length, updatesBefore, '卸载后不应再有 setData');
    assert.strictEqual(env.timers.length, 0, '卸载后不应残留定时器');
  });

  await test('重玩本关会收回本关已得的分（页面层）', (env) => {
    const page = startGame(env, 'zh');
    page.onTapCard(cardOf(page, 'cn', 0));
    page.onTapCard(cardOf(page, 'en', 0));
    assert.ok(page.game.state.score > 0);
    page.onReplay();
    assert.strictEqual(page.game.state.score, 0);
  });

  /* ---------- 首页 ---------- */
  await test('首页：切换语言和配色会保存，并重算册名与统计文字', (env) => {
    const page = env.loadPage('pages/index/index.js');
    page.onLoad();
    assert.strictEqual(page.data.bookTabs[0].name, '九年级上册');
    assert.ok(/共 \d+ 词/.test(page.data.summaryText));
    page.onToggleLang();
    assert.strictEqual(env.store.wp_lang, 'en');
    assert.strictEqual(page.data.bookTabs[0].name, 'Grade 9 · Vol. 1');
    assert.ok(/\d+ words · about \d+ levels/.test(page.data.summaryText), page.data.summaryText);
    assert.ok(/words · \d+ levels/.test(page.data.units[0].meta));
    page.onPickTheme({ currentTarget: { dataset: { key: 'lotus' } } });
    assert.strictEqual(env.store.wp_theme, 'lotus');
    assert.deepStrictEqual(page.data.palettes.filter((p) => p.on).map((p) => p.key), ['lotus']);
    assert.strictEqual(page.data.themeName, 'Crimson · Lotus');
    page.onToggleLang();
    assert.strictEqual(page.data.themeName, '绯红 · 藕白');
  });

  await test('首页：切册后单元和统计更新，开始游戏带上正确的册和单元', (env) => {
    const page = env.loadPage('pages/index/index.js');
    page.onLoad();
    const first = page.data.summaryText;
    page.onSwitchBook({ currentTarget: { dataset: { index: 1 } } });
    assert.notStrictEqual(page.data.summaryText, first);
    page.onStartUnit({ currentTarget: { dataset: { index: 2 } } });
    assert.strictEqual(env.calls.navigate.pop(), '/pages/game/game?book=1&unit=2');
  });

  const failed = results.filter((r) => r[0] === 'fail');
  results.forEach((r) => { if (r[0] === 'fail') console.error('  ✗ ' + r[1] + '\n    ' + (r[2].stack || r[2]).split('\n').slice(0, 4).join('\n    ')); });
  console.log('小程序行为测试：通过 ' + (results.length - failed.length) + ' / ' + results.length + ' 项');
  process.exit(failed.length ? 1 : 0);
})();
