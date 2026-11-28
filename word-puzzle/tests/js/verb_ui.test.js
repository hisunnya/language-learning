/* verb-ui.js 的单局导航、补做、计分和限时行为测试。 */
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const WEB = path.join(__dirname, '..', '..', 'web', 'js');
const ITEMS = [
  { answer: 'run', before: 'We', after: 'every day.', cn: '每天跑步', text: 'We run every day.' },
  { answer: 'walk', before: 'They', after: 'to school.', cn: '他们步行上学', text: 'They walk to school.' }
];
const POOL = ['run', 'walk', 'jump', 'eat', 'drive', 'sleep', 'read', 'work'];

function makeWorld(items = ITEMS, ords = items.map((_, i) => i)) {
  const listeners = {};
  const reports = [], progress = [];
  const timers = new Map();
  let now = 1000000, timerId = 0, onLangChange;
  class Clock extends Date {
    static now() { return now; }
  }
  const mount = {
    _html: '',
    elements: {},
    choices: [],
    set innerHTML(html) {
      this._html = html;
      this.elements = {};
      this.choices = [];
      if (html.includes('id="vhTimer"')) this.elements['#vhTimer'] = { textContent: '' };
      for (const match of html.matchAll(/<button\b([^>]*)>/g)) {
        const attrs = match[1];
        const id = (attrs.match(/\bid="([^"]+)"/) || [])[1];
        const choice = (attrs.match(/\bdata-choice="(\d+)"/) || [])[1];
        const isSlot = /\bdata-slot="true"/.test(attrs);
        const button = makeButton({
          choice,
          disabled: /\sdisabled(?:\s|$)/.test(attrs),
          rect: isSlot ? { left: 100, right: 140, top: 100, bottom: 130 } : undefined
        });
        if (id) this.elements['#' + id] = button;
        if (choice != null) this.choices.push(button);
        if (isSlot) this.elements['[data-slot]'] = button;
      }
    },
    get innerHTML() { return this._html; },
    querySelector(selector) { return this.elements[selector] || null; },
    querySelectorAll(selector) { return selector === '[data-choice]' ? this.choices : []; }
  };
  function makeButton(opts = {}) {
    const handlers = {};
    return {
      disabled: !!opts.disabled,
      style: {},
      classList: { add() { } },
      getAttribute(name) { return name === 'data-choice' ? opts.choice : null; },
      addEventListener(name, fn) { handlers[name] = fn; },
      fire(name, event) { if (handlers[name]) handlers[name](event); },
      getBoundingClientRect() { return opts.rect || { left: 0, right: 60, top: 0, bottom: 30, width: 60 }; },
      cloneNode() { return makeButton(opts); },
      remove() { }
    };
  }
  const document = {
    body: { appendChild() { } },
    addEventListener(name, fn) { listeners[name] = fn; },
    removeEventListener(name) { delete listeners[name]; }
  };
  const window = {
    WPI18N: {
      t(key, vars = {}) {
        return key + JSON.stringify(vars);
      },
      onChange(fn) { onLangChange = fn; }
    }
  };
  const sandbox = {
    window, document, Date: Clock, Promise, setTimeout, console,
    setInterval(fn) { timers.set(++timerId, fn); return timerId; },
    clearInterval(id) { timers.delete(id); }
  };
  vm.createContext(sandbox);
  vm.runInContext(fs.readFileSync(path.join(WEB, 'item-core.js'), 'utf8'), sandbox);
  vm.runInContext(fs.readFileSync(path.join(WEB, 'verb-ui.js'), 'utf8'), sandbox);
  const game = window.WPVerbUI.start(mount, {
    items, ords, choices: POOL, levelCount: 2,
    save(report) { reports.push(report); },
    progress(report) { progress.push(report); return Promise.resolve(true); }
  });
  return {
    window, mount, listeners, game, reports, progress, timers,
    advance(ms, tick = true) {
      now += ms;
      if (tick) Array.from(timers.values()).forEach((fn) => fn());
    },
    changeLanguage() { onLangChange(); },
    click(selector) {
      const button = mount.querySelector(selector);
      if (!button) throw new Error('找不到按钮 ' + selector);
      if (button.disabled) throw new Error('按钮当前不可用 ' + selector);
      button.onclick({});
    },
    chooseAnswer(answer = game.items[game.i].answer) {
      const index = game.choicesByItem[game.i].findIndex((word) => word.toLowerCase() === answer.toLowerCase());
      if (index < 0) throw new Error('当前题没有正确选项 ' + answer);
      mount.choices[index].onclick({});
    },
    chooseWrong() {
      const answer = game.items[game.i].answer.toLowerCase();
      const index = game.choicesByItem[game.i].findIndex((word) => word.toLowerCase() !== answer);
      mount.choices[index].onclick({});
    }
  };
}

let passed = 0;
const failures = [];
async function check(name, fn) { try { await fn(); passed++; } catch (e) { failures.push(name + '：' + e.message); } }
function ok(condition, message) { if (!condition) throw new Error(message); }

(async () => {
  await check('中英文题干同框纵向排列，不显示语言标签', async () => {
    const world = makeWorld();
    const html = world.mount.innerHTML;
    ok((html.match(/class="verb-bilingual"/g) || []).length === 1, '题干只有一个公共容器');
    ok(html.includes('class="verb-phrase" lang="en"') && html.includes('class="verb-cn" lang="zh-CN"'),
      '两种题干保留语言属性');
    ok(html.indexOf('class="verb-phrase"') < html.indexOf('class="verb-cn"'), '英文在上、中文在下');
    ok(!html.includes('verb-prompt') && !html.includes('verb-lang') &&
      !html.includes('vh_enLabel') && !html.includes('vh_cnLabel'), '不再分框或显示语言标签');
  });

  await check('单局题目随机排序，原始序号保留，每题五个选项', async () => {
    const world = makeWorld(ITEMS, [12, 19]);
    const { game } = world;
    ok(game.items.length === 2 && game.ords.length === 2, '两组题目作为同一局传入');
    ok(game.order.slice().sort((a, b) => a - b).join(',') === '0,1', '题序是全部题目的排列');
    game.choicesByItem.forEach((choices, i) => {
      ok(choices.length === 5, '每题恰有五个选项');
      ok(choices.filter((choice) => choice === game.items[i].answer).length === 1, '正确选项只出现一次');
    });
    ok(game.ords.slice().sort((a, b) => a - b).join(',') === '12,19', '乱序后仍保留成绩需要的原题序号');
    ok(!world.mount.querySelector('#vhSubmit') && !world.mount.querySelector('#vhListen'),
      '不再提供单题提交或朗读按钮');
    ok(!world.mount.querySelector('#vhFinish'), '首轮作答不显示提前交卷按钮');
  });

  await check('拖放后点下一题判分；第五次尝试才答对得零分，无单题提交和朗读', async () => {
    const world = makeWorld(ITEMS, [42, 43]);
    let report;
    world.game.cfg.save = (value) => { report = value; };
    const firstAnswer = world.game.items[0].answer;
    const firstOrd = world.game.ords[0];
    const wrongIndex = world.game.choicesByItem[0].findIndex((word) => word !== firstAnswer);
    const word = world.mount.choices[wrongIndex];
    word.fire('pointerdown', { button: 0, pointerId: 7, clientX: 10, clientY: 10 });
    world.listeners.pointermove({ pointerId: 7, clientX: 30, clientY: 30, preventDefault() { } });
    world.listeners.pointerup({ pointerId: 7, clientX: 120, clientY: 115 });
    ok(world.game.states[0].selected === wrongIndex, '拖到答案框后保留所选单词');
    ok(!world.mount.querySelector('#vhListen'), '答对前没有朗读按钮');
    await new Promise((resolve) => setTimeout(resolve, 0));

    for (let attempt = 0; attempt < 4; attempt++) {
      world.chooseWrong();
      world.click('#vhNext');
    }
    ok(world.game.states[0].wrong === 4 && world.game.total() === 0, '四次错误后，第五次提交正确仍为零分');
    world.chooseAnswer();
    world.click('#vhNext');
    ok(world.game.states[0].solved && world.game.total() === 0,
      '第五次提交答对仍为零分（' + JSON.stringify(world.game.states[0]) + '; score=' + world.game.total() + ')');
    world.click('#vhPrev');
    ok(!world.mount.querySelector('#vhListen') && !world.mount.querySelector('#vhSubmit'),
      '返回答对的题目也没有朗读或单题提交按钮');
    world.click('#vhNext');
    world.click('#vhSkip');
    world.click('#vhFinishNow');
    ok(report && report.score === 0 && report.matched === 1 && report.wrong === 4, '手动交卷保存整局成绩');
    ok(report.level_count === 1 && report.detail[0].i === 0 && report.detail[0].ord === firstOrd,
      '整套只结算一轮，保留本局题号和原题序号');
    ok(report.rule_version === 4 && Array.isArray(report.combo_events), '整局报告必须带轮次元数据');
    ok(world.progress.length > 0 && world.progress[0].detail[0].ord === firstOrd, '作答时同步原题号快照');
  });

  await check('空题提示可返回补做，也可以直接交卷', async () => {
    const world = makeWorld(ITEMS, [30, 31]);
    let report;
    world.game.cfg.save = (value) => { report = value; };
    world.click('#vhSkip');
    ok(world.game.i === 1 && world.game.states[0].skipped, '跳过后自动前进并标记题目');
    world.click('#vhSkip');
    ok(world.mount.querySelector('#vhReview'), '最后一题跳过后提示补答');
    world.click('#vhReview');
    ok(world.game.i === 0, '自动定位第一道空题');
    ok(world.mount.querySelector('#vhFinish'), '进入补答后显示交卷按钮');
    world.chooseAnswer();
    world.click('#vhFinish');
    ok(world.game.i === 0 && world.game.states[0].solved, '补答处交卷先判当前选择，无需走到末题');
    ok(world.mount.querySelector('#vhReview'), '仍有空题时再次确认');
    world.click('#vhFinishNow');
    ok(report.score === 10 && report.matched === 1 && report.total_pairs === 2, '跳过题得零分且成绩按整局统计');
  });

  await check('下一题自动提交，答错留在原题，全部答对自动交卷', async () => {
    const world = makeWorld();
    world.chooseWrong();
    world.click('#vhNext');
    ok(world.game.i === 0 && world.game.states[0].wrong === 1, '错误提交扣分且不前进');
    world.chooseAnswer();
    world.click('#vhNext');
    ok(world.game.i === 1 && world.game.states[0].solved, '答对自动提交并进入下一题');
    world.click('#vhPrev');
    ok(world.mount.choices.every((button) => button.disabled), '返回后已答对的题目不可修改');
    ok(!world.mount.querySelector('#vhFinish'), '首轮返回已答对题目仍不显示交卷');
    world.click('#vhNext');
    world.chooseAnswer();
    world.click('#vhNext');
    ok(world.game.done && world.reports.length === 1, '最后一题自动交卷且只保存一次');
    ok(world.reports[0].score === 22 && world.reports[0].matched === 2, '18分作答加20%完成速度奖取整');
    ok(world.timers.size === 0, '交卷后停止倒计时');
  });

  await check('下一题允许空题跳过，最后提交答对后可补答空题', async () => {
    const world = makeWorld();
    world.click('#vhNext');
    ok(world.game.i === 1 && world.game.states[0].skipped, '未选择时下一题直接跳过');
    world.chooseAnswer();
    world.click('#vhNext');
    ok(!world.game.done && world.mount.querySelector('#vhReview'), '最后一题正确，前面有空题时不直接交卷');
    world.click('#vhReview');
    world.chooseAnswer();
    world.click('#vhFinish');
    ok(world.game.done && world.reports[0].score === 25, '补答全部正确自动交卷，含二连1分和速度奖');
  });

  await check('补答时交卷判错仍可重试，交卷按钮不因选择答案而消失', async () => {
    const world = makeWorld();
    world.click('#vhNext');
    world.click('#vhNext');
    world.click('#vhReview');
    world.chooseWrong();
    world.click('#vhFinish');
    ok(world.game.i === 0 && world.game.states[0].wrong === 1 && !world.game.finishPrompt,
      '交卷判错扣分且留在本题，不进入确认页');
    ok(world.mount.querySelector('#vhFinish') && !world.mount.querySelector('#vhFinish').disabled,
      '补答交卷保持可用');
    world.chooseAnswer();
    world.click('#vhFinish');
    ok(world.game.finishPrompt && world.game.total() === 8, '改对后当前题计分并提示其他空题');
    world.click('#vhReview');
    ok(world.game.i === 1 && world.mount.querySelector('#vhFinish'), '再次补答定位下一道空题');
    world.click('#vhFinish');
    world.click('#vhFinishNow');
    ok(world.reports[0].score === 8, '补答处可放弃剩余空题交卷');
    world.click('#vhAgain');
    ok(!world.game.reviewing && !world.mount.querySelector('#vhFinish'),
      '补答后重新开始不保留补答交卷按钮');
  });

  await check('倒计时从开始计算，导航、切换语言和补答提示均不暂停或重置', async () => {
    const world = makeWorld();
    ok(world.mount.innerHTML.includes('0:24'), '两题时限为12×2秒');
    world.advance(1000);
    ok(world.mount.querySelector('#vhTimer').textContent.includes('0:23'), '更新剩余秒数');
    world.click('#vhNext');
    world.click('#vhNext');
    world.advance(22000);
    world.changeLanguage();
    ok(!world.game.done && world.mount.innerHTML.includes('0:01'), '补答提示和语言重绘仍只剩一秒');
    world.advance(1000);
    ok(world.game.done && world.reports.length === 1, '第24秒立即交卷');
    ok(world.reports[0].score === 0 && world.reports[0].duration === 24, '白卷零分，耗时24秒');
    ok(world.mount.innerHTML.includes('vh_timeout'), '明确显示超时交卷提示');
    world.advance(2000);
    ok(world.reports.length === 1, '超时只保存一次');
  });

  await check('超时只计已经答对的题，未提交的正确选择不计分', async () => {
    const world = makeWorld();
    world.chooseAnswer();
    world.click('#vhNext');
    world.chooseAnswer();
    world.advance(120000);
    ok(world.reports[0].score === 10 && world.reports[0].matched === 1, '未提交的正确答案零分');
    ok(world.reports[0].detail[1].skipped && !world.reports[0].detail[1].solved, '未提交题按未答处理');
    world.game.submit();
    ok(world.reports.length === 1 && !world.game.states[1].solved, '交卷后提交不改变成绩');
  });

  await check('零分成绩页使用中性标题，只高亮原填空位置的正确答案并转义题干', async () => {
    const world = makeWorld([
      { before: 'run with', answer: 'run', after: 'run again', cn: '重复动词', text: 'run with run run again' },
      { before: '<b>They</b>', answer: 'walk', after: '& "learn"', cn: '特殊字符', text: '<b>They</b> walk & "learn"' }
    ]);
    world.advance(120000);
    ok(world.reports[0].score === 0, '零分交卷');
    const html = world.mount.innerHTML;
    ok(html.includes('<h2>vh_resultsTitle') && !html.includes('ig_doneTitle'), '零分也使用成绩标题');
    ok((html.match(/<mark class="ig-key">/g) || []).length === 2, '每题只高亮正确填空词');
    ok(html.includes('run with <mark class="ig-key">run</mark> run again'), '不误高亮题干中重复的相同单词');
    ok(html.includes('&lt;b&gt;They&lt;/b&gt; <mark class="ig-key">walk</mark> &amp; &quot;learn&quot;') &&
      !html.includes('<b>They</b>'), '高亮之外的题干仍然安全转义');
    world.changeLanguage();
    ok(world.mount.innerHTML.includes('<h2>vh_resultsTitle') &&
      (world.mount.innerHTML.match(/<mark class="ig-key">/g) || []).length === 2, '切换语言后保留标题和答案高亮');
  });

  await check('后台计时器延迟也不能在截止后提交，再玩一次独立计时', async () => {
    const world = makeWorld();
    world.chooseAnswer();
    world.advance(125000, false);
    world.click('#vhNext');
    ok(world.game.done && world.reports[0].score === 0, '截止后点击先交卷，不接受迟到答案');
    ok(world.reports[0].duration === 24, '延迟回调的用时也不超出本轮时限');
    world.click('#vhAgain');
    ok(!world.game.done && world.timers.size === 1 && world.mount.innerHTML.includes('0:24'), '重玩建立唯一的新倒计时');
    ok(!world.mount.querySelector('#vhFinish'), '重玩恢复首轮流程，不保留补答交卷按钮');
    world.advance(23999);
    ok(!world.game.done, '新局24秒前仍可作答');
    world.advance(1);
    ok(world.game.done && world.reports.length === 2, '新局到时独立保存');
  });

  await check('拖动中超时会清理拖动监听且不填入答案', async () => {
    const world = makeWorld();
    const button = world.mount.choices[0];
    button.fire('pointerdown', { button: 0, pointerId: 7, clientX: 10, clientY: 10 });
    world.listeners.pointermove({ pointerId: 7, clientX: 30, clientY: 30, preventDefault() { } });
    world.advance(120000);
    ok(world.game.done && world.game.states[0].selected == null, '超时不把拖动中的答案算作选择');
    ok(!world.listeners.pointermove && !world.listeners.pointerup && !world.listeners.pointercancel, '拖动监听全部移除');
    ok(world.reports.length === 1 && world.timers.size === 0, '保存一次并停止计时');
  });

  if (failures.length) { console.log(failures.join('\n')); process.exit(1); }
  console.log('verb-ui 全部通过（' + passed + ' 项）');
})();
