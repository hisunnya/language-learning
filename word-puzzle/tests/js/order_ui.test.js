/* order-ui.js（排排坐）录音阶段的行为测试：node tests/js/order_ui.test.js（由 tests/test_items.py 调用，没有 node 时跳过）。
   用一个极小的假 DOM：mount.innerHTML 记下画出来的 HTML，getElementById 按 id 返回可以「点」的假元素；
   麦克风（getUserMedia / MediaRecorder）也是假的，可以让它成功、被拒绝、或者设备出错。 */
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const WEB = path.join(__dirname, '..', '..', 'web', 'js');

function makeWorld(mic) {
  const elements = {};
  const mount = {
    _html: '',
    set innerHTML(v) { this._html = v; for (const k of Object.keys(elements)) delete elements[k]; },
    get innerHTML() { return this._html; },
    querySelectorAll() { return []; }
  };
  const document = {
    getElementById(id) {
      if (!mount._html.includes('id="' + id + '"')) return null;
      return elements[id] || (elements[id] = { id, onclick: null, style: {}, className: '', textContent: '' });
    },
    addEventListener() { }, removeEventListener() { }, body: { appendChild() { } }
  };
  const stopped = [];
  function Stream() { this.tracks = [{ stop() { stopped.push('track'); } }]; }
  Stream.prototype.getTracks = function () { return this.tracks; };
  function MediaRecorder(stream) {
    if (mic.recorderThrows) throw Object.assign(new Error('bad type'), { name: 'NotSupportedError' });
    this.state = 'inactive'; this.mimeType = 'audio/webm';
  }
  MediaRecorder.isTypeSupported = () => true;
  MediaRecorder.prototype.start = function () { this.state = 'recording'; };
  MediaRecorder.prototype.stop = function () {
    this.state = 'inactive';
    this.ondataavailable({ data: { size: 5000 } });
    mic.pendingStop = () => this.onstop();          // 浏览器交出录音是异步的：测试决定什么时候
  };
  const window = {
    navigator: { mediaDevices: { getUserMedia() {
      if (mic.deny) return Promise.reject(Object.assign(new Error('no'), { name: mic.deny }));
      return Promise.resolve(new Stream());
    } } },
    MediaRecorder,
    setInterval() { return 1; }, clearInterval() { }, requestAnimationFrame() { return 1; }, cancelAnimationFrame() { },
    confirm() { return true; },
    Blob: function (parts, opts) { this.size = 5000; this.type = opts.type; },
    URL: { createObjectURL() { return 'blob:x'; }, revokeObjectURL() { } },
    Audio: function () { this.play = () => Promise.resolve(); this.pause = () => { }; }
  };
  const sandbox = { window, document, navigator: window.navigator, MediaRecorder, Blob: window.Blob, URL: window.URL,
                    Audio: window.Audio, Promise, Date, setTimeout, console };
  vm.createContext(sandbox);
  vm.runInContext(fs.readFileSync(path.join(WEB, 'item-core.js'), 'utf8'), sandbox);
  vm.runInContext(fs.readFileSync(path.join(WEB, 'order-ui.js'), 'utf8'), sandbox);
  return { window, document, mount, stopped, click: (id) => { const el = document.getElementById(id); if (!el) throw new Error('没有按钮 ' + id); el.onclick({}); } };
}

const ITEMS = [{ cn: '一', answer: 'a b', fragments: [{ text: 'a', segs: [['a', 0]] }, { text: 'b', segs: [['b', 0]] }] },
               { cn: '二', answer: 'c d', fragments: [{ text: 'c', segs: [['c', 0]] }, { text: 'd', segs: [['d', 0]] }] }];

function startArranged(world, cfg) {
  const game = world.window.WPOrderUI.start(world.mount, Object.assign({ items: ITEMS, ords: [0, 1] }, cfg || {}));
  game.states[0].placed = game.st().pool.slice().sort();
  game.states[0].arranged = true;
  game.render();
  return game;
}

const tick = () => new Promise((r) => setTimeout(r, 0));
let passed = 0;
const failures = [];
async function check(name, fn) { try { await fn(); passed++; } catch (e) { failures.push(name + '：' + e.message); } }
function ok(cond, msg) { if (!cond) throw new Error(msg); }

(async () => {
  await check('等麦克风、录音中、正在收尾时：没有「跳过」「下一句」，换句也被挡住', async () => {
    const mic = {};
    const w = makeWorld(mic);
    const game = startArranged(w, { upload: () => Promise.resolve({ valid: true }) });
    w.click('orRecord');
    ok(game.st().stage === 'starting', '先是 starting');
    ok(!w.mount.innerHTML.includes('id="orSkip"'), 'starting 时不能跳过');
    game.next();
    ok(game.i === 0, 'starting 时 next() 不换句');
    await tick();
    ok(game.st().stage === 'recording', '麦克风打开后是 recording');
    game.recorder.began -= 2000;                   // 假装已经录了 2 秒（太短的录音不让交）
    w.click('orStop');
    ok(game.st().stage === 'stopping', '点停止后先是 stopping');
    ok(w.mount.innerHTML.includes('or_stopping'), 'stopping 时显示「正在保存录音」');
    ok(!w.mount.innerHTML.includes('id="orSubmit"') && !w.mount.innerHTML.includes('id="orSkip"'), 'stopping 时没有提交 / 跳过');
    game.next();
    ok(game.i === 0, 'stopping 时 next() 不换句');
    mic.pendingStop();
    await tick();
    ok(game.st().stage === 'idle' && game.st().take, '收尾完成：有一段可以回放的录音');
    ok(w.mount.innerHTML.includes('id="orSubmit"'), '可以提交了');
    ok(w.stopped.length === 1, '麦克风关掉了');
  });

  await check('权限被拒绝 → denied（有「再试一次」）；设备出错 → micError', async () => {
    let w = makeWorld({ deny: 'NotAllowedError' });
    let game = startArranged(w, { upload: () => Promise.resolve({}) });
    w.click('orRecord');
    await tick(); await tick();
    ok(game.st().stage === 'denied', '拒绝权限是 denied，实际 ' + game.st().stage);
    ok(w.mount.innerHTML.includes('or_micDenied') && w.mount.innerHTML.includes('id="orRetry"'), '说明 + 再试一次');
    w = makeWorld({ deny: 'NotReadableError' });
    game = startArranged(w, { upload: () => Promise.resolve({}) });
    w.click('orRecord');
    await tick(); await tick();
    ok(game.st().stage === 'micError', '设备被占用是 micError，实际 ' + game.st().stage);
    ok(w.mount.innerHTML.includes('or_micFailed'), '提示可以再试');
  });

  await check('录音器起不来时把已经打开的麦克风关掉', async () => {
    const w = makeWorld({ recorderThrows: true });
    const game = startArranged(w, { upload: () => Promise.resolve({}) });
    w.click('orRecord');
    await tick(); await tick();
    ok(w.stopped.length === 1, '麦克风的轨道要停掉，否则手机上一直显示在录音');
    ok(game.st().stage === 'micError', '不是权限问题 → micError');
  });

  if (failures.length) { console.log(failures.join('\n')); process.exit(1); }
  console.log('order-ui 全部通过（' + passed + ' 项）');
})();
