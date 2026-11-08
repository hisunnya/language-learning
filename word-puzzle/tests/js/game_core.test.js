/* ============================================================
   game-core.test.js —— 纯运算层的行为测试
   ------------------------------------------------------------
   用法::

       node tests/js/game_core.test.js

   game-core.js 是一段 IIFE，挂在 ``window.WPGame`` 上；
   这里伪造一个 ``window`` 全局再加载它，因此不需要浏览器。
   ============================================================ */
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const CORE = path.join(__dirname, '..', '..', 'web', 'js', 'game-core.js');

/* ---------- 迷你断言 ---------- */

let passed = 0;
const failures = [];

function check(name, fn) {
  try {
    fn();
    passed++;
  } catch (err) {
    failures.push(name + '：' + err.message);
  }
}

function eq(actual, expected, note) {
  if (actual !== expected) {
    throw new Error(
      '期望 ' + JSON.stringify(expected) + '，实际 ' + JSON.stringify(actual) +
      (note ? '（' + note + '）' : '')
    );
  }
}

function ok(value, note) {
  if (!value) throw new Error('期望为真' + (note ? '（' + note + '）' : ''));
}

/* ---------- 加载 game-core.js ---------- */

/* 可控的时钟：核心用 Date.now() 算截止点，测试要能「快进」 */
const clock = { now: 1700000000000 };
class FakeDate extends Date {
  static now() { return clock.now; }
}

const sandbox = { console: console, Date: FakeDate };
sandbox.window = sandbox;
sandbox.globalThis = sandbox;
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(CORE, 'utf8'), sandbox, { filename: CORE });

const WPGame = sandbox.window.WPGame;
if (!WPGame || !WPGame.Game) throw new Error('game-core.js 没有导出 WPGame.Game');

/* ---------- 测试夹具 ---------- */

const WORDS = [
  { en: 'apple', cn: '苹果', ipa: 'ˈæpəl' },
  { en: 'banana', cn: '香蕉', ipa: 'bəˈnɑːnə' },
  { en: 'cherry', cn: '樱桃', ipa: 'ˈtʃeri' }
];

function newGame() {
  const events = [];
  const game = new WPGame.Game({
    levels: [{ name: '第 1 关', words: WORDS }],
    onEvent: (evt) => events.push(evt)
  });
  game.start(0);
  return { game: game, events: events };
}

/** 牌面按 id 与类型取，方便构造点击序列 */
function cards(game) {
  const out = { en: {}, cn: {} };
  game.cards.forEach((c) => { out[c.t][c.id] = c; });
  return out;
}

function typesOf(events, type) {
  return events.filter((e) => e.type === type);
}

/* ---------- 选卡：中文可以先点 ---------- */

check('中文先点也可以选中', () => {
  const { game, events } = newGame();
  const c = cards(game);
  game.pick(c.cn[0]);
  const select = typesOf(events, 'select');
  eq(select.length, 1, '应当产生一次 select 事件');
  eq(select[0].side, 'cn', 'side 应为 cn');
  eq(game.state.sel.card.t, 'cn', '选中的应是中文卡');
});

check('英文先点也可以选中', () => {
  const { game, events } = newGame();
  const c = cards(game);
  game.pick(c.en[0]);
  const select = typesOf(events, 'select');
  eq(select.length, 1);
  eq(select[0].side, 'en');
});

check('中文先点 + 英文后点 = 配对成功', () => {
  const { game, events } = newGame();
  const c = cards(game);
  game.pick(c.cn[0]);
  game.pick(c.en[0]);
  const matched = typesOf(events, 'match');
  eq(matched.length, 1, '应当配对成功');
  eq(matched[0].enCard.t, 'en', 'enCard 应是英文卡');
  eq(matched[0].cnCard.t, 'cn', 'cnCard 应是中文卡');
  eq(matched[0].word.en, 'apple');
  eq(game.state.matched, 1);
  eq(game.state.sel, null, '配对后应清空选中');
});

check('英文先点 + 中文后点 = 配对成功', () => {
  const { game, events } = newGame();
  const c = cards(game);
  game.pick(c.en[1]);
  game.pick(c.cn[1]);
  eq(typesOf(events, 'match').length, 1);
  eq(game.state.matched, 1);
});

/* ---------- 连点同一侧要提示，且不算错 ---------- */

check('连点两个中文 = 换选中，不算错', () => {
  const { game, events } = newGame();
  const c = cards(game);
  game.pick(c.cn[0]);
  game.pick(c.cn[1]);
  const sw = typesOf(events, 'switch');
  eq(sw.length, 1, '应当产生一次 switch 事件');
  eq(sw[0].prevSide, 'cn');
  eq(sw[0].side, 'cn');
  eq(typesOf(events, 'miss').length, 0, '换选中不算配错');
  eq(game.state.wrong, 0, '错误次数不应增加');
  eq(game.state.sel.card.id, 1, '选中应切到第二张');
});

check('连点两个英文 = 换选中，不算错', () => {
  const { game, events } = newGame();
  const c = cards(game);
  game.pick(c.en[0]);
  game.pick(c.en[2]);
  const sw = typesOf(events, 'switch');
  eq(sw.length, 1);
  eq(sw[0].prevSide, 'en');
  eq(typesOf(events, 'miss').length, 0);
  eq(game.state.wrong, 0);
});

check('换选中之后可以继续正确配对', () => {
  const { game, events } = newGame();
  const c = cards(game);
  game.pick(c.cn[0]);
  game.pick(c.cn[1]);      /* 换成第 2 张中文 */
  game.pick(c.en[1]);      /* 用英文配第 2 个词 */
  eq(typesOf(events, 'match').length, 1, '换选中后仍应能配对');
  eq(game.state.matched, 1);
});

/* ---------- 再点同一张卡：重新朗读，保持选中 ---------- */

check('再点同一张卡 = repeat，保持选中且不算错', () => {
  const { game, events } = newGame();
  const c = cards(game);
  game.pick(c.cn[0]);
  game.pick(c.cn[0]);
  const rep = typesOf(events, 'repeat');
  eq(rep.length, 1, '应当产生一次 repeat 事件');
  eq(typesOf(events, 'miss').length, 0);
  eq(game.state.wrong, 0);
  eq(game.state.sel.card.id, 0, '选中应保持不变');
});

/* ---------- 配错仍然扣分扣时间 ---------- */

check('中文先点 + 配错英文 = miss，扣分扣时间', () => {
  const { game, events } = newGame();
  const c = cards(game);
  const before = game.state.timeLeft;
  game.pick(c.cn[0]);
  game.pick(c.en[2]);
  const miss = typesOf(events, 'miss');
  eq(miss.length, 1, '应当产生一次 miss');
  eq(game.state.wrong, 1);
  eq(game.state.score, 0, '分数不应增加');
  ok(game.state.timeLeft <= before - 3 + 0.01, '时间应被扣掉约 3 秒');
  eq(game.state.sel, null, '配错后应清空选中');
});

/* ---------- 全部配完即过关 ---------- */

check('三种词全部配对后过关', () => {
  const { game, events } = newGame();
  const c = cards(game);
  /* 全部用「中文先点」的顺序配对 */
  [0, 1, 2].forEach((id) => {
    game.pick(c.cn[id]);
    game.pick(c.en[id]);
  });
  eq(game.state.matched, 3);
  eq(typesOf(events, 'levelClear').length, 1, '应当过关');
  eq(game.state.playing, false);
});

/* ---------- 重玩不能刷分 ---------- */

/** 配对第 0..n-1 个词（中文先点） */
function match(game, n) {
  const c = cards(game);
  for (let id = 0; id < n; id++) { game.pick(c.cn[id]); game.pick(c.en[id]); }
}

check('重玩本关会收回这一关里拿到的分', () => {
  const { game } = newGame();
  match(game, 2);
  eq(game.state.score, 100 + 120, '先配对两个词');
  game.replay();
  eq(game.state.score, 0, '重玩后这一关的分应清零');
  eq(game.state.matched, 0);
});

check('多次「拿分、重玩」不会累积分数', () => {
  const { game } = newGame();
  for (let i = 0; i < 5; i++) { match(game, 2); game.replay(); }
  eq(game.state.score, 0);
});

check('重玩只收回本关的分，之前通关的分保留', () => {
  const events = [];
  const game = new WPGame.Game({
    levels: [{ name: 'A', words: WORDS }, { name: 'B', words: WORDS }],
    onEvent: (e) => events.push(e)
  });
  game.start(0);
  match(game, 3);                      /* 通关第 1 关 */
  const afterFirst = game.state.score;
  ok(afterFirst > 0);
  game.next();
  match(game, 2);
  game.replay();
  eq(game.state.score, afterFirst, '应回到第 2 关开始时的分数');
});

check('时间到后重玩同样收回分数', () => {
  const { game } = newGame();
  match(game, 2);
  clock.now += 200 * 1000;
  game.tick();
  eq(game.state.playing, false, '应当已经超时');
  game.replay();
  eq(game.state.score, 0);
});

/* ---------- 时长覆盖整局 ---------- */

check('duration 覆盖所有关卡，不是只算最后一关', () => {
  const game = new WPGame.Game({
    levels: [{ name: 'A', words: WORDS }, { name: 'B', words: WORDS }], onEvent: () => {}
  });
  game.start(0);
  clock.now += 40 * 1000;
  match(game, 3);
  game.next();
  clock.now += 25 * 1000;
  eq(game.report().duration, 65, '第 1 关 40 秒 + 第 2 关 25 秒');
});

check('重玩一关不会让 duration 归零', () => {
  const { game } = newGame();
  clock.now += 30 * 1000;
  game.replay();
  clock.now += 10 * 1000;
  eq(game.report().duration, 40);
});

check('从头开始后 duration 重新计', () => {
  const { game } = newGame();
  clock.now += 50 * 1000;
  game.restart();
  clock.now += 5 * 1000;
  eq(game.report().duration, 5);
});

/* ---------- 暂停：切到后台不扣时间 ---------- */

check('暂停期间剩余时间冻结，恢复后接着走', () => {
  const { game } = newGame();
  clock.now += 20 * 1000;
  game.tick();
  const left = game.state.timeLeft;
  ok(Math.abs(left - 100) < 0.01, '用掉 20 秒应剩 100 秒');
  ok(game.pause(), '应当暂停成功');
  clock.now += 90 * 1000;              /* 玩家切走 90 秒 */
  eq(game.tick(), null, '暂停时 tick 不应推进');
  ok(game.resume(), '应当恢复成功');
  clock.now += 10 * 1000;
  game.tick();
  ok(Math.abs(game.state.timeLeft - 90) < 0.01, '恢复后只扣实际玩的 10 秒，实际 ' + game.state.timeLeft);
  eq(game.state.playing, true, '不应因为切走而超时');
});

check('暂停时点牌无效', () => {
  const { game, events } = newGame();
  const c = cards(game);
  game.pause();
  eq(game.pick(c.cn[0]), null);
  eq(typesOf(events, 'select').length, 0);
  eq(game.state.sel, null);
  game.resume();
  game.pick(c.cn[0]);
  eq(typesOf(events, 'select').length, 1, '恢复后可以点牌');
});

check('没在玩的时候暂停无效，重复暂停 / 恢复无副作用', () => {
  const { game } = newGame();
  ok(game.pause());
  eq(game.pause(), false, '重复暂停');
  ok(game.resume());
  eq(game.resume(), false, '重复恢复');
  const done = newGame().game;
  match(done, 3);                      /* 已过关 */
  eq(done.pause(), false, '已过关不能暂停');
});

check('每次配错都会记进 wrong_log', () => {
  const { game } = newGame();
  const c = cards(game);
  game.pick(c.cn[0]); game.pick(c.en[1]);
  const log = game.report().wrong_log;
  eq(log.length, 1);
  eq(log[0].en, 'banana');
  eq(log[0].cn, '苹果');
});

/* ---------- 输出 ---------- */

console.log('game-core.js：通过 ' + passed + ' 项');
if (failures.length) {
  console.error('失败 ' + failures.length + ' 项：');
  failures.forEach((f) => console.error('  - ' + f));
  process.exit(1);
}
