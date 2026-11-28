/* 单词大比拼：整套倒计时、超时结算与连击，使用可控时钟而不等真实时间。 */
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const WEB = path.join(__dirname, '../../web/js');

function world() {
  let now = 1000000, next = 0, nodes = {};
  const timers = new Map(), reports = [], progress = [];
  class Clock extends Date { static now() { return now; } }
  const mount = {
    set innerHTML(html) {
      this.html = html;
      nodes = {};
      for (const match of html.matchAll(/id="([^"]+)"/g)) {
        nodes[match[1]] = {
          value: '', textContent: '', classList: { add() {}, remove() {} },
          focus() {}, select() {}
        };
      }
    }
  };
  const window = { WPI18N: { t: key => key, onChange() {} } };
  const sandbox = { window, Date: Clock, console, Promise,
    document: { getElementById: id => nodes[id] },
    setInterval(fn) { timers.set(++next, fn); return next; },
    clearInterval(id) { timers.delete(id); }
  };
  vm.createContext(sandbox);
  for (const file of ['item-core.js', 'spell-ui.js']) {
    vm.runInContext(fs.readFileSync(path.join(WEB, file), 'utf8'), sandbox);
  }
  const items = ['run', 'walk', 'work'].map(answer => ({ answer, cn: answer, before: 'We', after: 'today.' }));
  const game = window.WPSpellUI.start(mount, {
    items, ords: [4, 5, 6], save: r => reports.push(r),
    progress: r => { progress.push(r); return Promise.resolve(true); }
  });
  return {
    game, reports, progress, timers,
    answer(value) { nodes.spInput.value = value || items[game.i].answer; game.check(); },
    advance(ms) { now += ms; for (const fn of [...timers.values()]) fn(); }
  };
}

{
  const w = world();
  assert.equal(w.game.round.limit, 60);
  w.advance(61000);
  assert.equal(w.reports.length, 1);
  assert.equal(w.reports[0].score, 0);
  assert.equal(w.reports[0].duration, 60);
  assert.equal(w.timers.size, 0);
  w.advance(50000);
  assert.equal(w.reports.length, 1);
}
{
  const w = world();
  w.answer();
  assert.equal(w.progress.length, 1, '正确作答立即保存快照，不等超时');
  assert.equal(w.progress[0].detail[0].ord, 4);
  assert.equal(w.progress[0].detail[0].solved, true);
  w.game.next();
  w.advance(60000);
  assert.equal(w.reports[0].score, 80);
  assert.equal(w.reports[0].matched, 1);
  assert.equal(w.reports[0].detail[0].ord, 4);
  assert.equal(w.reports[0].detail[1].solved, false);
}
{
  const w = world();
  for (let i = 0; i < 3; i++) { w.answer(); w.game.next(); }
  assert.equal(w.reports[0].score, 317);
  assert.equal(w.reports[0].best_combo, 3);
  assert.equal(w.reports[0].bonus_seconds, 2);
  assert.equal(w.reports[0].combo_bonus, 24);
  const settled = w.game.total();
  w.advance(10000);
  assert.equal(w.game.total(), settled);
}
{
  const w = world();
  w.game.hint();
  w.answer('incorrect');
  w.answer();
  w.game.giveUp();
  assert.equal(w.game.states[0].gaveUp, false, '已答对不能改成放弃');
  w.game.next();
  w.game.giveUp();
  w.game.next();
  w.game.giveUp();
  w.game.next();
  assert.equal(w.reports[0].score, 40);
  assert.equal(w.reports[0].combo_bonus, 0);
  assert.equal(w.reports[0].bonus_seconds, 0);
}
console.log('单词大比拼计时与结算：4 项通过');
