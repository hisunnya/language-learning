/* ============================================================
   core_parity.test.js —— 网站版与小程序版 game-core.js 必须行为一致
   ------------------------------------------------------------
   小程序里的 utils/game-core.js 是网站版 web/js/game-core.js 的移植（只改了
   导出方式），两份代码以后很容易各改各的。这里用同一个种子、同一串随机操作
   （点牌、走时间、暂停/恢复、重玩、下一关、从头开始）同时驱动两份，
   每一步比较返回值、状态和事件，任何一边的行为跑偏都会立刻失败。
   ============================================================ */
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const WEB = path.join(__dirname, '..', '..', 'web', 'js', 'game-core.js');
const MINI = path.join(__dirname, '..', '..', '..', 'miniprogram', 'utils', 'game-core.js');

function lcg(seed) {
  let s = seed >>> 0;
  return () => { s = (Math.imul(s, 1664525) + 1013904223) >>> 0; return s / 4294967296; };
}

function load(file, kind, rng, clock) {
  class FakeDate extends Date { static now() { return clock.now; } }
  const sandbox = { console, Date: FakeDate, Math: Object.assign(Object.create(Math), { random: rng }) };
  sandbox.window = sandbox;
  const mod = { exports: {} };
  sandbox.module = mod;
  sandbox.exports = mod.exports;
  vm.createContext(sandbox);
  vm.runInContext(fs.readFileSync(file, 'utf8'), sandbox, { filename: file });
  return kind === 'web' ? sandbox.window.WPGame : mod.exports;
}

const WORDS = Array.from({ length: 12 }, (_, i) => ({ en: 'w' + i, cn: '词' + i, ipa: '' }));
const LEVELS = [0, 1, 2].map((n) => ({ name: '关' + n, words: WORDS.slice(0, 6 + n * 3) }));

function makeSide(file, kind, seed) {
  const clock = { now: 1700000000000 };
  const core = load(file, kind, lcg(seed), clock);
  const events = [];
  const game = new core.Game({ levels: LEVELS, onEvent: (e) => events.push(e) });
  return { clock, game, events };
}

const SKIP = new Set(['gen']);
function snapshot(game) {
  const out = {};
  Object.keys(game.state).sort().forEach((k) => {
    if (SKIP.has(k)) return;
    const v = game.state[k];
    if (k === 'sel') out[k] = v ? [v.card.t, v.card.id] : null;
    else out[k] = JSON.parse(JSON.stringify(v));
  });
  out.cards = (game.cards || []).map((c) => c.t + c.id);
  return out;
}

function scalar(evt) {
  const out = { type: evt.type };
  Object.keys(evt).forEach((k) => {
    const v = evt[k];
    if (typeof v === 'number' || typeof v === 'string' || typeof v === 'boolean') out[k] = v;
  });
  return out;
}

function sameEvents(a, b, where) {
  if (a.length !== b.length) throw new Error(where + '：事件数量不同 ' + a.length + ' vs ' + b.length);
  a.forEach((evt, i) => {
    const x = scalar(evt), y = scalar(b[i]);
    // 只比较两边都有的标量字段（小程序版多带了 hasNext 这类界面用的字段）
    Object.keys(x).filter((k) => k in y).forEach((k) => {
      if (JSON.stringify(x[k]) !== JSON.stringify(y[k])) {
        throw new Error(where + '：第 ' + i + ' 个事件 ' + x.type + ' 的 ' + k + ' 不同：' + x[k] + ' vs ' + y[k]);
      }
    });
    if (x.type !== y.type) throw new Error(where + '：事件类型不同 ' + x.type + ' vs ' + y.type);
  });
}

let steps = 0;
for (const seed of [1, 2, 3, 4, 5, 6, 7, 8]) {
  const web = makeSide(WEB, 'web', seed);
  const mini = makeSide(MINI, 'mini', seed);
  const pickRng = lcg(seed * 977);
  web.game.start(0); mini.game.start(0);
  for (let i = 0; i < 1500; i++) {
    const roll = pickRng();
    let label, a, b;
    const cards = web.game.cards;
    if (roll < 0.62 && cards && cards.length) {
      // 多数时候认真配对，少数时候乱点
      const first = Math.floor(pickRng() * cards.length);
      let second = Math.floor(pickRng() * cards.length);
      if (pickRng() < 0.6) {
        second = cards.findIndex((c) => c.id === cards[first].id && c.t !== cards[first].t);
      }
      label = 'pick';
      const pickBoth = (side, idx) => { const c = side.game.cards[idx]; return side.game.pick(c); };
      a = [pickBoth(web, first), pickBoth(web, second)];
      b = [pickBoth(mini, first), pickBoth(mini, second)];
    } else if (roll < 0.75) {
      const dt = Math.floor(pickRng() * 40) * 1000;
      web.clock.now += dt; mini.clock.now += dt;
      label = 'tick'; a = web.game.tick(); b = mini.game.tick();
    } else if (roll < 0.82) {
      label = 'pause'; a = web.game.pause(); b = mini.game.pause();
    } else if (roll < 0.9) {
      label = 'resume'; a = web.game.resume(); b = mini.game.resume();
    } else if (roll < 0.94) {
      label = 'replay'; a = web.game.replay(); b = mini.game.replay();
    } else if (roll < 0.98) {
      label = 'next'; a = web.game.next(); b = mini.game.next();
    } else {
      label = 'restart'; a = web.game.restart(); b = mini.game.restart();
    }
    const where = 'seed ' + seed + ' 第 ' + i + ' 步 ' + label;
    if (JSON.stringify(a && a.type ? a.type : a) !== JSON.stringify(b && b.type ? b.type : b)) {
      throw new Error(where + '：返回值不同 ' + JSON.stringify(a) + ' vs ' + JSON.stringify(b));
    }
    const sa = JSON.stringify(snapshot(web.game)), sb = JSON.stringify(snapshot(mini.game));
    if (sa !== sb) throw new Error(where + '：状态不同\n  网站 ' + sa.slice(0, 400) + '\n  小程序 ' + sb.slice(0, 400));
    sameEvents(web.events, mini.events, where);
    const ra = JSON.stringify(web.game.report()), rb = JSON.stringify(mini.game.report());
    if (ra !== rb) throw new Error(where + '：report() 不同\n  网站 ' + ra.slice(0, 300) + '\n  小程序 ' + rb.slice(0, 300));
    steps++;
  }
}
console.log('网站版与小程序版 game-core.js 行为一致：通过 ' + steps + ' 步随机操作');
