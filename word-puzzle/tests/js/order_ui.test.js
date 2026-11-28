/* 排排坐：假时钟、假麦克风和极小 DOM，覆盖每句独立结算与异步评分。
   node tests/js/order_ui.test.js；既有 tests/test_items.py 会调用。 */
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const WEB = path.join(__dirname, '..', '..', 'web', 'js');
const ITEMS = [
  { cn: '一', answer: 'a b', fragments: [{ segs: [['a', 0]] }, { segs: [['b', 0]] }] },
  { cn: '二', answer: 'c d', fragments: [{ segs: [['c', 0]] }, { segs: [['d', 0]] }] }
];
const flush = async () => { for (let i = 0; i < 12; i++) await Promise.resolve(); };
const deferred = () => { let resolve, reject; const promise = new Promise((a, b) => { resolve = a; reject = b; }); return { promise, resolve, reject }; };
function ok(value, message) { if (!value) throw new Error(message); }
function makeWorld(mic = {}) {
  let now = 1000000, counter = 0, lang = 'zh', change;
  const timers = new Map(), elements = {}, stopped = [], audios = [], listeners = {};
  const mount = {
    _html: '',
    set innerHTML(v) { this._html = v; Object.keys(elements).forEach(k => delete elements[k]); },
    get innerHTML() { return this._html; },
    querySelectorAll() { return []; }
  };
  const document = {
    getElementById(id) {
      if (!mount._html.includes('id="' + id + '"')) return null;
      return elements[id] || (elements[id] = { style: {}, className: '', textContent: '', onclick: null });
    },
    addEventListener() {}, removeEventListener() {}, body: { appendChild() {} }
  };
  function schedule(fn, ms, repeat) { const id = ++counter; timers.set(id, { fn, at: now + ms, repeat }); return id; }
  function Stream() { this.getTracks = () => [{ stop() { stopped.push('track'); } }]; }
  function MediaRecorder() {
    if (mic.recorderThrows) throw new Error('device');
    this.state = 'inactive'; this.mimeType = 'audio/webm';
  }
  MediaRecorder.isTypeSupported = () => true;
  MediaRecorder.prototype.start = function () { this.state = 'recording'; };
  MediaRecorder.prototype.stop = function () {
    this.state = 'inactive';
    if (this.ondataavailable) this.ondataavailable({ data: { size: 5000 } });
    mic.pendingStop = () => { if (this.onstop) this.onstop(); };
  };
  function Audio(url) {
    this.url = url;
    this.play = () => mic.playReject ? Promise.reject(new Error('audio')) : Promise.resolve();
    this.pause = () => { if (this.onpause) this.onpause(); };
    audios.push(this);
  }
  const window = {
    navigator: { mediaDevices: { getUserMedia() {
      if (mic.permission) return mic.permission.promise;
      if (mic.deny) return Promise.reject(Object.assign(new Error('no'), { name: mic.deny }));
      return Promise.resolve(new Stream());
    } } },
    MediaRecorder, Audio,
    setInterval: (fn, ms) => schedule(fn, ms, ms),
    clearInterval: id => timers.delete(id),
    setTimeout: (fn, ms) => schedule(fn, ms, 0),
    clearTimeout: id => timers.delete(id),
    requestAnimationFrame: () => 0, cancelAnimationFrame() {},
    addEventListener: (name, fn) => { listeners[name] = fn; },
    confirm: () => true,
    Blob: function (parts, opts) { this.size = 5000; this.type = opts.type; },
    URL: { createObjectURL: () => 'blob:take', revokeObjectURL() {} },
    WPI18N: { t: (key, p) => lang + ':' + key + JSON.stringify(p || {}), onChange(fn) { change = fn; } }
  };
  class ClockDate extends Date { constructor(...args) { super(...(args.length ? args : [now])); } static now() { return now; } }
  const sandbox = { window, document, navigator: window.navigator, MediaRecorder, Audio, Blob: window.Blob,
    URL: window.URL, Date: ClockDate, Promise, console, setTimeout: window.setTimeout };
  vm.createContext(sandbox);
  ['item-core.js', 'order-ui.js'].forEach(file => vm.runInContext(fs.readFileSync(path.join(WEB, file), 'utf8'), sandbox));
  return {
    window, document, mount, mic, stopped, audios, timers, Stream,
    language() { lang = 'en'; change(); },
    hide() { listeners.pagehide(); },
    jump(ms) { now += ms; },
    click(id) { const el = document.getElementById(id); ok(el && el.onclick, '没有按钮 ' + id); el.onclick({}); },
    advance(ms) {
      const end = now + ms;
      while (true) {
        let next, id;
        for (const [k, timer] of timers) if (timer.at <= end && (!next || timer.at < next.at)) { next = timer; id = k; }
        if (!next) break;
        now = next.at;
        if (next.repeat) next.at += next.repeat; else timers.delete(id);
        next.fn();
      }
      now = end;
    }
  };
}
function start(w, cfg = {}) {
  return w.window.WPOrderUI.start(w.mount, Object.assign({ items: ITEMS, ords: [4, 9] }, cfg));
}
function arrange(w, game) { game.st().placed = [0, 1]; w.click('orCheck'); }
async function take(w, game) {
  w.click('orRecord'); await flush();
  w.advance(1500); w.click('orStop'); w.mic.pendingStop(); await flush();
  ok(game.st().take && !game.st().take.tooShort, '录音可提交');
}
let passed = 0;
const failures = [];
async function check(name, run) {
  try { await run(); passed++; } catch (e) { failures.push(name + '：' + e.stack); }
}
(async () => {
  await check('白卷三十秒零分，每句只保存一次，最后自动汇总', async () => {
    const w = makeWorld(), reports = [], game = start(w, { save: r => { reports.push(r); return true; } });
    w.advance(30000); await flush();
    ok(game.i === 1 && reports.length === 1 && reports[0].score === 0, '第一句三十秒交白卷');
    ok(reports[0].total_pairs === 1 && reports[0].detail[0].ord === 4, '独立单句报告');
    w.advance(30000); await flush();
    ok(game.done && reports.length === 2, '第二句自动汇总，不交累计成绩');
    game.finish(); game.next(); ok(reports.length === 2, '不重复保存');
  });
  await check('线上开始失败显式重试，策略到达前没有可玩倒计时', async () => {
    const w = makeWorld(), pending = deferred(); let calls = 0;
    const game = start(w, { begin() { calls++; return calls === 1 ? pending.promise : Promise.resolve({ play_token: 'retry', time_factor: .5 }); } });
    w.advance(60000); ok(!game.st().round && !w.document.getElementById('orCheck'), '等待策略时不可玩');
    pending.reject(new Error('offline')); await flush();
    ok(w.mount.innerHTML.includes('ig_beginFailed'), '不能伪装离线成功');
    w.click('orBeginRetry'); await flush();
    ok(game.st().round.limit === 15 && game.st().token === 'retry', '重试采用重复游玩计时');
  });
  await check('拼对冻结计时，权限等待也受一百二十秒约束，迟到授权立即关麦', async () => {
    const permission = deferred(), w = makeWorld({ permission }), reports = [], game = start(w, { save: r => reports.push(r) });
    w.advance(5000); arrange(w, game); const first = game.st(), remaining = first.round.left();
    w.click('orRecord'); w.advance(119900);
    ok(first.round.left() === remaining && game.i === 0, '录音阶段不消耗拼句时间');
    w.advance(100); await flush();
    ok(game.i === 1 && reports.length === 1 && reports[0].score > 0, '权限卡住也自动留下拼句分');
    permission.resolve(new w.Stream()); await flush();
    ok(w.stopped.length >= 1 && game.st().stage === 'idle', '迟到授权不污染下一句');
  });
  await check('录音开始、停止收尾、设备错误及三十秒上限', async () => {
    const w = makeWorld(), game = start(w); arrange(w, game);
    w.click('orRecord'); ok(game.st().stage === 'starting', '权限阶段'); game.next(); ok(game.i === 0, '不能中断麦克风');
    await flush(); w.advance(30000);
    ok(game.st().stage === 'stopping', '三十秒自动收尾');
    game.next(); ok(game.i === 0, '不能抢在收尾前换句');
    w.mic.pendingStop(); await flush();
    ok(game.st().take.ms === 30000 && w.stopped.length === 1, '音频不超过三十秒且关麦');
    const failed = makeWorld({ recorderThrows: true }), g = start(failed); arrange(failed, g);
    failed.click('orRecord'); await flush();
    ok(g.st().stage === 'micError' && failed.stopped.length === 1, '初始化失败也关麦');
    const denied = makeWorld({ deny: 'NotAllowedError' }), d = start(denied); arrange(denied, d);
    denied.click('orRecord'); await flush();
    ok(d.st().stage === 'denied' && denied.document.getElementById('orRetry'), '拒绝后可重试');
  });
  await check('上传等待显示不定进度，接受就有二十分，整数准确分零到三十五', async () => {
    const w = makeWorld(), upload = deferred(), result = deferred();
    const game = start(w, { upload: () => upload.promise, recording: () => result.promise });
    arrange(w, game); await take(w, game); const before = game.points(game.st());
    w.click('orSubmit'); await flush();
    ok(w.mount.innerHTML.includes('or-scoring-progress') && w.mount.innerHTML.includes('or_scoring'), '上传就显示评分进度');
    upload.resolve({ id: 8, valid: true, status: 'pending', bonus: 0 }); await flush();
    const pending = game.points(game.st());
    ok(pending > before && w.document.getElementById('orSkipWait'), '识别未完成也拿朗读分且可不等');
    w.advance(1500); await flush(); result.resolve({ id: 8, valid: true, status: 'done', bonus: 35, accuracy: 1 }); await flush();
    ok(game.st().rec.bonus === 35 && game.points(game.st()) > pending, '准确分计入');
    ok(w.mount.innerHTML.includes('or_sentenceScore') && w.mount.innerHTML.includes('orAutoNext'), '完成显示分数与自动下一句');
    w.advance(10000); await flush(); ok(game.i === 1, '十秒后自动换句');
  });
  await check('不等评分保存一次，迟到准确分更新旧句且不重画新句', async () => {
    const w = makeWorld(), reports = [], later = deferred();
    const game = start(w, { upload: () => Promise.resolve({ id: 5, valid: true, status: 'pending', bonus: 0 }),
      recording: () => later.promise, save: r => reports.push(r) });
    arrange(w, game); await take(w, game); w.click('orSubmit'); await flush();
    w.advance(1500); await flush(); w.click('orSkipWait'); await flush();
    const html = w.mount.innerHTML, first = game.states[0], old = game.points(first);
    ok(reports.length === 1 && reports[0].detail[0].recording_id === 5, '关联录音且只保存一次');
    later.resolve({ id: 5, valid: true, status: 'done', bonus: 35 }); await flush();
    ok(game.points(first) > old && reports.length === 1 && w.mount.innerHTML === html, '后台更新旧句不重交、不跳画面');
  });
  await check('音频回放暂停自动前进，结束暂停报错及播放失败均重新给足十秒', async () => {
    for (const event of ['onended', 'onpause', 'onerror', 'reject']) {
      const w = makeWorld(), game = start(w, { audioUrl: () => 'ref.mp3' }); arrange(w, game);
      const s = game.st(); game.acceptRecording(s, { valid: true, id: 2, status: 'done', bonus: 0 }, game.generation);
      game.play(0); const old = w.audios[w.audios.length - 1].onended;
      w.advance(15000); ok(game.i === 0, '回放时不自动换句');
      if (event === 'reject') { w.mic.playReject = true; game.play(0); await flush(); }
      else w.audios[w.audios.length - 1][event]();
      w.advance(9900); ok(game.i === 0, '回放后给足十秒');
      w.advance(100); await flush(); ok(game.i === 1, '恢复前进');
      old(); ok(!game.playing, '迟到回调不影响新句');
    }
  });
  await check('连续再播放忽略旧播放结束，自己的录音也暂停自动前进，末句进入汇总', async () => {
    const w = makeWorld(), game = start(w, { items: [ITEMS[0]], audioUrl: () => 'ref.mp3' });
    arrange(w, game); await take(w, game);
    game.acceptRecording(game.st(), { id: 1, valid: true, status: 'done', bonus: 35 }, game.generation);
    game.play(0); const old = w.audios[w.audios.length - 1].onended;
    w.click('orOwn'); old(); w.advance(15000); ok(!game.done && game.playing, '旧的结束事件不能覆盖新回放');
    w.audios[w.audios.length - 1].onended(); w.advance(10000);
    ok(game.done && w.mount.innerHTML.includes('ig-summary'), '最后一句自动汇总');
  });
  await check('语言切换不重启时钟或麦克风，重新开始取消旧异步任务和计时器', async () => {
    const w = makeWorld(), pending = deferred(), game = start(w, { upload: () => pending.promise });
    w.advance(4000); const deadline = game.st().round.deadline; w.language();
    ok(game.st().round.deadline === deadline && w.mount.innerHTML.includes('en:'), '切语言不加时间');
    arrange(w, game); w.click('orRecord'); await flush(); w.advance(1200);
    const recorder = game.recorder, watchdog = game.st().watchdog; w.language();
    ok(game.recorder === recorder && game.st().stage === 'recording' && game.st().watchdog === watchdog, '录音继续');
    w.click('orStop'); w.mic.pendingStop(); await flush(); w.click('orSubmit'); await flush();
    game.restart(); const html = w.mount.innerHTML;
    pending.resolve({ id: 99, valid: true, status: 'done', bonus: 35 }); await flush();
    ok(game.total() === 0 && w.mount.innerHTML === html && w.timers.size === 1, '旧上传不能污染重开局');
    w.hide(); ok(w.timers.size === 0, '离开页面清理定时器');
  });
  await check('下一句等待前句保存后才请求新策略并携带前局令牌', async () => {
    const w = makeWorld(), saved = deferred(), begins = [];
    const game = start(w, { begin: meta => { begins.push(meta); return Promise.resolve({ play_token: 'token' + begins.length }); },
      save: () => saved.promise });
    await flush(); arrange(w, game); w.click('orNext'); await flush();
    ok(begins.length === 1 && game.i === 0 && game.st().finalizing, '保存未完成留在当前句，不抢开下一局');
    saved.resolve(true); await flush();
    ok(begins.length === 2 && begins[1].previous_play_token === 'token1' && begins[1].ords[0] === 9, '服务端连续答题种子');
    game.restart(); await flush(); ok(!begins[2].previous_play_token, '重开不继承旧连击');
  });
  await check('错误扣六分最低六分，连击只奖励首次拼对，离线连续句继承连击', async () => {
    const w = makeWorld(), game = start(w);
    for (let i = 0; i < 7; i++) { game.st().placed = [1, 0]; w.click('orCheck'); }
    arrange(w, game);
    ok(game.st().round.combo === 0 && game.st().reward.combo === 0, '错过的句子不能续连击');
    ok(w.window.WPItemCore.orderArrangePoints(game.st().wrong) === 6, '错误扣分有下限');
    game.restart(); arrange(w, game);
    const events = game.st().round.events.length;
    game.render(); w.language();
    ok(game.st().round.events.length === events, '重画不能重复命中');
    game.next(); arrange(w, game);
    ok(game.st().reward.combo === 2 && game.st().reward.points === 3 && game.st().reward.seconds === 1, '第二句得到连击分与加秒');
    ok(w.mount.innerHTML.includes('reward-toast'), '显示连击奖励');
    game.restart(); ok(game.st().round.combo === 0, '重开归零');
  });
  await check('录音、浏览器收尾、待上传和上传卡住都被看门狗结束', async () => {
    for (const stage of ['recording', 'stopping', 'take', 'uploading']) {
      const w = makeWorld(), upload = deferred(), reports = [];
      const game = start(w, { items: [ITEMS[0]], upload: () => upload.promise, save: r => reports.push(r) });
      arrange(w, game); w.click('orRecord'); await flush();
      if (stage !== 'recording') { w.advance(1500); w.click('orStop'); }
      if (stage === 'take' || stage === 'uploading') { w.mic.pendingStop(); await flush(); }
      if (stage === 'uploading') { w.click('orSubmit'); await flush(); }
      w.advance(120000); await flush();
      ok(game.done && reports.length === 1 && reports[0].score > 0, stage + '没有卡死且保留拼句分');
      ok(w.stopped.length >= 1 && w.timers.size === 0, stage + '不留麦克风和计时器');
      if (stage === 'uploading') {
        upload.resolve({ id: 8, valid: true, status: 'done', bonus: 35 }); await flush();
        ok(reports.length === 1, '迟到上传不能重复结算');
      }
    }
  });
  await check('阶段接口顺序与零准确分；录音收尾延迟不算入音频时长', async () => {
    const w = makeWorld(), phase = deferred(), calls = [];
    const game = start(w, {
      phase: (token, value) => { calls.push(value); return value === 'recording' ? phase.promise : Promise.resolve(); },
      upload: () => { calls.push('upload'); return Promise.resolve({ id: 1, valid: true, status: 'done', bonus: 0 }); }
    });
    arrange(w, game); w.click('orRecord'); await flush(); w.advance(1500); w.click('orStop');
    w.advance(5000); w.mic.pendingStop(); await flush();
    ok(game.st().take.ms === 1500, '停止后浏览器交数据的延迟不是录音');
    w.click('orSubmit'); await flush(); ok(calls.join(',') === 'recording', '先等待服务器录音阶段');
    phase.resolve(); await flush();
    ok(calls.join(',') === 'recording,upload,scoring' && game.st().resolved, '上传后才进入评分阶段，零分也完成');
    w.advance(10000); await flush(); ok(game.i === 1, '零准确分照常进入下一句');
  });
  await check('超时报告冻结且迟到时钟的时长不超过策略限时', async () => {
    const w = makeWorld(), reports = [], game = start(w, { items: [ITEMS[0]], save: r => reports.push(r) });
    const first = game.st();
    w.jump(90000); game.tick(); await flush();
    ok(game.done && reports[0].duration === first.round.limit && reports[0].score === 0, '后台节流后仍按三十秒报告');
    const snapshot = JSON.stringify(reports[0]), elapsed = first.round.elapsed(), left = first.round.left();
    w.jump(600000);
    ok(first.round.elapsed() === elapsed && first.round.left() === left && JSON.stringify(reports[0]) === snapshot, '保存后冻结时间和报告');
  });
  await check('上传成功即取消交互看门狗，超过一百二十秒的识别仍更新已保存原句', async () => {
    const w = makeWorld(), reports = []; let complete = false, polls = 0;
    const game = start(w, { items: [ITEMS[0]], save: r => reports.push(r),
      upload: () => Promise.resolve({ id: 33, valid: true, status: 'pending', bonus: 0 }),
      recording: () => { polls++; return Promise.resolve({ id: 33, valid: true, status: complete ? 'done' : 'pending', bonus: complete ? 35 : 0 }); } });
    arrange(w, game); await take(w, game); w.click('orSubmit'); await flush();
    const state = game.st();
    ok(state.watchdog === null, '接受录音结束一百二十秒交互限时');
    for (let i = 0; i < 85; i++) { w.advance(1500); await flush(); }
    ok(game.i === 0 && !game.done && !state.resolved && polls >= 80, '识别超过原截止时间不会自动跳过');
    w.click('orSkipWait'); await flush();
    const before = game.total(), report = JSON.stringify(reports[0]);
    complete = true; w.advance(1500); await flush();
    ok(game.done && game.total() > before && state.rec.bonus === 35, '汇总仍收到迟到准确分');
    ok(reports.length === 1 && JSON.stringify(reports[0]) === report, '原报告稳定，由服务器补分而不再保存');
    ok(w.timers.size === 0, '终态不留轮询');
  });
  await check('状态请求卡住最多重试五次，明确重试后可恢复；轮询总时长有界', async () => {
    const w = makeWorld(), never = deferred(); let recover = false, requests = 0;
    const game = start(w, { recording: () => { requests++; return recover ?
      Promise.resolve({ id: 7, valid: true, status: 'done', bonus: 0 }) : never.promise; } });
    arrange(w, game); const state = game.st();
    game.acceptRecording(state, { id: 7, valid: true, status: 'pending', bonus: 0 }, game.generation);
    for (let i = 0; i < 5; i++) { w.advance(1500); await flush(); w.advance(10000); await flush(); }
    ok(state.pollStopped && requests === 5 && w.document.getElementById('orPollRetry'), '请求超时有界，给出显式重试');
    w.advance(120000); await flush(); ok(requests === 5, '不无限重试');
    recover = true; w.click('orPollRetry'); w.advance(1500); await flush();
    ok(state.resolved, '手动重试恢复评分');
    game.destroy(); ok(w.timers.size === 0, '清理请求超时器');
    const other = makeWorld(), g = start(other, { recording: () => Promise.resolve({ id: 1, valid: true, status: 'pending' }) });
    arrange(other, g); g.acceptRecording(g.st(), { id: 1, valid: true, status: 'pending' }, g.generation);
    other.jump(600001); g.acceptRecording(g.st(), g.st().rec, g.generation);
    ok(g.st().pollStopped && other.document.getElementById('orPollRetry'), '十分钟仍未终态时停止自动轮询');
    g.destroy(); ok(other.timers.size === 0, '轮询界限后可干净销毁');
  });
  await check('分数系数仅在全部分项合并后取整一次，朗读和准确分不参与速度奖', async () => {
    const w = makeWorld(), reports = [], game = start(w, { items: [ITEMS[0]], save: r => reports.push(r),
      begin: () => Promise.resolve({ play_token: 'fraction', score_factor: .37, combo_seed: 1, time_limit: 30 }) });
    await flush(); w.advance(16000); arrange(w, game);
    const state = game.st();
    ok(state.round.extra === 3 && state.round.left() === 15, '连击三分、加一秒后剩十五秒');
    game.acceptRecording(state, { id: 1, valid: true, status: 'pending', bonus: 0 }, game.generation);
    ok(game.points(state) === 21, '(30拼句 + 3连击 + 3.3速度 + 20朗读) × .37 = 20.831，取整21');
    game.acceptRecording(state, { id: 1, valid: true, status: 'done', bonus: 35 }, game.generation);
    ok(game.points(state) === 34, '准确奖35只加一次，不增加速度奖；91.3 × .37取整34');
    game.next(); await flush();
    ok(reports.length === 1 && reports[0].score === 34, '报告使用同一公式');
  });
  await check('后续句上传传关内下标而非题库序号，适配器再转换为正确题库题号', async () => {
    const w = makeWorld(), uploads = [], ords = [4, 9];
    const game = start(w, { ords,
      begin: meta => Promise.resolve({ play_token: 'ord-' + meta.ords[0] }),
      upload: (i, blob, mime, ms, token) => {
        uploads.push({ i, ord: ords[i], token });
        return Promise.resolve({ id: 4, valid: true, status: 'done', bonus: 0 });
      } });
    await flush(); arrange(w, game); game.next(); await flush();
    arrange(w, game); await take(w, game); w.click('orSubmit'); await flush();
    ok(uploads.length === 1 && uploads[0].i === 1 && uploads[0].ord === 9 &&
      uploads[0].token === 'ord-9', '第二句 i=1，经关卡映射到ord9，令牌也是第二句');
    game.destroy();
  });
  await check('错误断连击与答对快照先提交，答对检查点确认后才进入录音阶段', async () => {
    const w = makeWorld(), accepted = deferred(), calls = [], snapshots = [], saved = [];
    const game = start(w, { items: [ITEMS[0]],
      progress: report => {
        snapshots.push(report); calls.push('progress');
        return snapshots.length === 2 ? accepted.promise : Promise.resolve(true);
      },
      phase: (token, value) => { calls.push(value); return Promise.resolve(); },
      save: report => { saved.push(report); calls.push('save'); return true; }
    });
    w.advance(1000); game.st().placed = [1, 0]; w.click('orCheck'); await flush();
    ok(snapshots.length === 1 && snapshots[0].wrong === 1 && !snapshots[0].detail[0].arranged &&
      snapshots[0].combo_events[0].break, '错误快照包含wrong和断连击事件');
    w.advance(1000); arrange(w, game); await flush();
    ok(calls.join(',') === 'progress,progress' && snapshots[1].detail[0].arranged &&
      snapshots[1].matched === 1 && snapshots[1].time_left === 28, '答对时立即上报冻结前剩余时间，未抢先请求phase');
    accepted.resolve(true); await flush();
    ok(calls.join(',') === 'progress,progress,recording', '检查点成功后才进入录音阶段');
    game.st().skipped = true; game.next(); await flush();
    ok(calls.slice(-3).join(',') === 'progress,scoring,save' && snapshots[2].detail[0].skipped &&
      saved.length === 1, '跳过录音也先检查点再最终保存');
  });
  await check('超时直接结算白卷；拒绝的检查点有可见错误且不会产生未处理拒绝', async () => {
    const w = makeWorld(), snapshots = [], reports = [], game = start(w, { items: [ITEMS[0]],
      progress: report => { snapshots.push(report); return Promise.resolve(false); },
      save: report => { reports.push(report); return true; } });
    w.advance(30000); await flush();
    ok(game.done && snapshots.length === 0 && reports[0].matched === 0 && reports[0].time_left === 0 &&
      reports[0].detail[0].skipped, '超时不再发必定被拒的迟到快照，直接保存白卷');
    const failed = makeWorld(), phases = [], g = start(failed, {
      progress: () => Promise.reject(new Error('network')),
      phase: (token, value) => { phases.push(value); return Promise.resolve(); }
    });
    arrange(failed, g); await flush();
    ok(g.st().progressError && failed.mount.innerHTML.includes('ig_scoreNotSaved') &&
      phases.length === 0, '检查点失败可见，不假装已经进入服务器录音阶段');
    g.destroy();
    const old = makeWorld(), pending = deferred(), calls = [], previous = start(old, {
      progress: () => pending.promise,
      phase: () => { calls.push('phase'); return Promise.resolve(); }
    });
    arrange(old, previous); previous.restart(); pending.resolve(true); await flush();
    ok(!calls.length && previous.st().wrong === 0, '重开后旧检查点不能再启动旧录音阶段');
    previous.destroy();
  });
  await check('最终检查点失败仍尝试权威结算，保存成功后不误报成绩丢失', async () => {
    const w = makeWorld(), phases = [], reports = []; let checkpoints = 0;
    const game = start(w, { items: [ITEMS[0]],
      progress: () => Promise.resolve(++checkpoints === 1),
      phase: (token, value) => { phases.push(value); return Promise.resolve(); },
      save: report => { reports.push(report); return true; }
    });
    arrange(w, game); await flush();
    game.next(); await flush();
    ok(game.done && reports.length === 1 && phases.join(',') === 'recording,scoring', '检查点失败不阻止使用既有快照结算');
    ok(!game.states[0].progressError && game.states[0].saved, '最终保存成功才清除失败提示');
  });
  await check('跳过录音、拼句超时和录音看门狗都按检查点、评分阶段、最终保存的顺序结算', async () => {
    for (const mode of ['skip', 'arrangeTimeout', 'watchdog']) {
      const w = makeWorld(), calls = []; let serverPhase = 'arranging';
      const game = start(w, { items: [ITEMS[0]], upload: () => Promise.resolve({}),
        progress: () => { calls.push('progress'); return Promise.resolve(true); },
        phase: (token, value) => {
          ok(value !== serverPhase, '不能重复请求服务器已接受的阶段');
          serverPhase = value; calls.push(value); return Promise.resolve();
        },
        save: () => { calls.push('save'); ok(serverPhase === 'scoring', '服务端评分阶段才允许交成绩'); return true; }
      });
      if (mode === 'arrangeTimeout') w.advance(30000);
      else {
        arrange(w, game); await flush();
        if (mode === 'skip') w.click('orSkip');
        else { w.click('orRecord'); await flush(); w.advance(120000); }
      }
      await flush();
      ok(game.done && (mode === 'arrangeTimeout'
        ? calls.join(',') === 'scoring,save'
        : calls.slice(-3).join(',') === 'progress,scoring,save'), mode + '完成真实阶段序列');
      ok(calls.filter(v => v === 'scoring').length === 1 && game.states[0].saved, '只终结一次');
    }
  });
  await check('保存false留在原句原令牌，可重试且不重复已成功评分阶段，成功后才取下一句令牌', async () => {
    const w = makeWorld(), starts = [], calls = [], submissions = []; let saveCount = 0;
    const game = start(w, { upload: () => Promise.resolve({}),
      begin: meta => { starts.push(meta); return Promise.resolve({ play_token: 'same-' + starts.length }); },
      progress: report => { calls.push('progress'); return Promise.resolve(true); },
      phase: (token, value) => { calls.push(value); return Promise.resolve(true); },
      save: report => { submissions.push(report); calls.push('save'); return ++saveCount !== 1; }
    });
    await flush(); arrange(w, game); await flush(); w.click('orSkip'); await flush();
    const original = game.st();
    ok(game.i === 0 && !game.done && !original.saved && original.saveError && original.token === 'same-1' &&
      w.document.getElementById('orSaveRetry'), '保存失败显示当前句重试，不假成功');
    const deadline = original.round.deadline;
    game.restart(); await flush();
    ok(starts.length === 1 && game.st() === original && original.round.deadline === deadline, '失败后不能重开令牌');
    w.click('orSaveRetry'); await flush();
    ok(game.i === 1 && starts.length === 2 && original.saved &&
      starts[1].previous_play_token === 'same-1', '重试成功才继续，下一句用正确连击种子');
    ok(submissions.length === 2 && submissions.every(r => r.play_token === 'same-1') &&
      calls.filter(v => v === 'scoring').length === 1, '同令牌重试保存，不重发已接受的scoring');
    game.destroy();
  });
  await check('上传后的评分阶段不重复发送；评分阶段失败可重试且不会提前保存', async () => {
    const w = makeWorld(), calls = [];
    const game = start(w, { items: [ITEMS[0]],
      upload: () => Promise.resolve({ id: 1, valid: true, status: 'pending', bonus: 0 }),
      phase: (token, value) => { calls.push(value); return Promise.resolve(true); },
      save: () => { calls.push('save'); return true; }
    });
    arrange(w, game); await take(w, game); w.click('orSubmit'); await flush(); w.click('orSkipWait'); await flush();
    ok(game.done && calls.join(',') === 'recording,scoring,save', '上传成功后已经scoring，直接保存');
    const other = makeWorld(), reports = []; let attempts = 0;
    const g = start(other, { items: [ITEMS[0]],
      phase: (token, value) => Promise.resolve(value === 'scoring' ? ++attempts > 1 : true),
      save: report => { reports.push(report); return true; }
    });
    other.advance(30000); await flush();
    ok(!g.done && g.st().saveError && reports.length === 0 && attempts === 1, '服务器拒绝阶段后留在原句');
    other.click('orSaveRetry'); await flush();
    ok(g.done && reports.length === 1 && attempts === 2, '失败的阶段可以重试，成功后才保存');
  });
  if (failures.length) { console.error(failures.join('\n')); process.exit(1); }
  console.log('order-ui 全部通过（' + passed + ' 项）');
})();
