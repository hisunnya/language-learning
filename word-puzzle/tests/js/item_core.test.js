/* item-core.js 的行为测试：node tests/js/item_core.test.js（由 tests/test_items.py 调用，没有 node 时跳过） */
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const sandbox = { window: {} };
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(path.join(__dirname, '..', '..', 'web', 'js', 'item-core.js'), 'utf8'), sandbox);
const C = sandbox.window.WPItemCore;

let passed = 0;
const failures = [];
function check(name, fn) { try { fn(); passed++; } catch (e) { failures.push(name + '：' + e.message); } }
function eq(a, b, msg) { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error((msg || '') + ' 期望 ' + JSON.stringify(b) + '，实际 ' + JSON.stringify(a)); }

check('拼写不分大小写、多余空格不算', () => {
  eq(C.spellCheck('Domestic', 'domestic'), 'right');
  eq(C.spellCheck('  DOMESTIC ', 'domestic'), 'right');
  eq(C.spellCheck('domestik', 'domestic'), 'close');
  eq(C.spellCheck('domestc', 'domestic'), 'close');
  eq(C.spellCheck('house', 'domestic'), 'wrong');
  eq(C.spellCheck('', 'domestic'), 'empty');
  eq(C.spellCheck('erradicat', 'eradicate'), 'close', '长词差两个字母也算差一点');
});

check('拼写计分：提示扣 3、拼错扣 2、拼对至少 1 分、看答案 0 分', () => {
  eq(C.spellPoints({ solved: true }), 10);
  eq(C.spellPoints({ solved: true, hints: 1, wrong: 1 }), 5);
  eq(C.spellPoints({ solved: true, hints: 2, wrong: 5 }), 1);
  eq(C.spellPoints({ gaveUp: true }), 0);
  eq(C.spellPoints({ solved: false }), 0);
});

check('提示：先字母个数，再首字母', () => {
  eq(C.spellHint('soar', 1), '_ _ _ _');
  eq(C.spellHint('soar', 2), 's _ _ _');
});

check('打乱：同一个种子同样的顺序，和原顺序不一样，是一个排列', () => {
  for (let n = 2; n <= 8; n++) {
    for (let seed = 1; seed < 40; seed++) {
      const a = C.shuffle(n, seed);
      eq(a, C.shuffle(n, seed));
      eq(a.slice().sort((x, y) => x - y), Array.from({ length: n }, (_, i) => i));
      if (a.every((v, i) => v === i)) throw new Error('没有打乱 n=' + n + ' seed=' + seed);
    }
  }
});

const F = [{ segs: [['To improve', 0]] }, { segs: [['your physical well-being,', 0]] }, { segs: [['you should ', 0], ['keep on', 1]] },
           { segs: [['exercising', 0]] }, { segs: [['every single day.', 0]] }];

check('排排坐：按文字判对错，指出第一个放错的位置', () => {
  eq(C.orderCheck(F, [0, 1, 2, 3, 4]), { ok: true, firstWrong: -1 });
  eq(C.orderCheck(F, [0, 2, 1, 3, 4]), { ok: false, firstWrong: 1 });
  eq(C.orderSentence(F, [0, 1, 2, 3, 4]), 'To improve your physical well-being, you should keep on exercising every single day.');
  const twins = [{ segs: [['the', 0]] }, { segs: [['cat', 0]] }, { segs: [['the', 0]] }];
  eq(C.orderCheck(twins, [2, 1, 0]).ok, true, '文字一样的两个片段换位置也算对');
});

check('排排坐计分：拼接 10、出错扣 2 最少 2；有效朗读 30；奖励另加', () => {
  eq(C.orderArrangePoints(0), 10);
  eq(C.orderArrangePoints(3), 4);
  eq(C.orderArrangePoints(9), 2);
  eq(C.orderPoints({ arranged: true, wrong: 1, recordingValid: true, bonus: 17 }), 8 + 30 + 17);
  eq(C.orderPoints({ arranged: true, wrong: 0 }), 10);
  eq(C.orderPoints({ arranged: false, recordingValid: true, bonus: 20 }), 0);
});

if (failures.length) { console.log(failures.join('\n')); process.exit(1); }
console.log('item-core 全部通过（' + passed + ' 项）');
