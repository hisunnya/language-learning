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

check('动词猎手计分和答案判断：第五次提交才答对也得零分', () => {
  eq(C.verbCheck('look after', 'Look After'), true);
  eq(C.verbCheck('', 'look after'), false);
  eq(C.verbPoints({ solved: true }), 10);
  eq(C.verbPoints({ solved: true, wrong: 2 }), 6);
  eq(C.verbPoints({ solved: true, wrong: 3 }), 4);
  eq(C.verbPoints({ solved: true, wrong: 4 }), 0);
  eq(C.verbPoints({ solved: true, wrong: 5 }), 0);
  eq(C.verbPoints({ solved: true, wrong: 9 }), 0);
  eq(C.verbPoints({ solved: false, wrong: 0 }), 0);
});

check('动词猎手：每题恰有一个正确答案和四个不重复的随机选项', () => {
  const items = 'abcdefghij'.split('').map((answer) => ({ answer }));
  const pool = 'abcdefghijxyzwv'.split('');
  const dealt = C.dealVerbChoices(items, pool, 12345);
  eq(dealt, C.dealVerbChoices(items, pool, 12345), '同种子可复现');
  eq(dealt.map((options) => options.length), Array(10).fill(5));
  items.forEach((item, i) => {
    const options = dealt[i];
    eq(new Set(options.map(C.key)).size, 5, '选项不得重复');
    eq(options.filter((word) => C.verbCheck(word, item.answer)).length, 1, '每题只有一个正确答案');
    if (options.filter((word) => !C.verbCheck(word, item.answer)).length !== 4) throw new Error('每题应有四个错误选项');
  });
  if (JSON.stringify(dealt) === JSON.stringify(C.dealVerbChoices(items, pool, 54321))) throw new Error('新种子应重新随机分配选项');
  let rejected = false;
  try { C.dealVerbChoices(items.slice(0, 1), ['a', 'b', 'c', 'd'], 1); } catch (e) { rejected = true; }
  if (!rejected) throw new Error('答案缺失或错误选项不足时应拒绝开始');
  rejected = false;
  try { C.dealVerbChoices(items, ['a', 'a', ...pool.slice(2)], 1); } catch (e) { rejected = true; }
  if (!rejected) throw new Error('重复选项应被拒绝');
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

check('拖动放片段：框里换位置、拖到框外退回、从上面拖到指定位置', () => {
  eq(C.placeAt([3, 1, 2], 2, 0, 2), [2, 3, 1], '把最后一个拖到最前面');
  eq(C.placeAt([3, 1, 2], 3, 2, 0), [1, 2, 3], '把第一个拖到最后');
  eq(C.placeAt([3, 1, 2], 1, null, 1), [3, 2], '拖到框外 = 退回');
  eq(C.placeAt([3, 1], 0, 1, null), [3, 0, 1], '从上面拖进来插到中间');
  eq(C.placeAt([3, 1], 0, 9, null), [3, 1, 0], '位置超出就放到最后');
  const orig = [3, 1, 2]; C.placeAt(orig, 2, 0, 2); eq(orig, [3, 1, 2], '不改原数组');
});

check('关名：按语言拼，单元分段时加 (i/n)，没有单元名叫第几关', () => {
  const tables = { zh: { ig_level: '第 {n} 关', ig_levelPart: '{unit}（{i}/{n}）' }, en: { ig_level: 'Level {n}', ig_levelPart: '{unit} ({i}/{n})' } };
  const tr = (lang) => (key, vars) => tables[lang][key].replace(/\{(\w+)\}/g, (m, k) => vars[k]);
  eq(C.levelName({ unit: 'Unit 3', part: 2, parts: 3 }, 1, tr('en')), 'Unit 3 (2/3)');
  eq(C.levelName({ unit: 'Unit 3', part: 2, parts: 3 }, 1, tr('zh')), 'Unit 3（2/3）');
  eq(C.levelName({ unit: 'Unit 3', part: 1, parts: 1 }, 0, tr('en')), 'Unit 3');
  eq(C.levelName({ unit: '', part: 2, parts: 2 }, 1, tr('en')), 'Level 2');
});

if (failures.length) { console.log(failures.join('\n')); process.exit(1); }
console.log('item-core 全部通过（' + passed + ' 项）');
