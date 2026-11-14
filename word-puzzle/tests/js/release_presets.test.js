/* release_presets.test.js —— 批量开放的预设范围 */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm');
const win = {}; win.window = win; vm.createContext(win);
vm.runInContext(fs.readFileSync(path.join(__dirname, '..', '..', 'web', 'js', 'release-presets.js'), 'utf8'), win);
const { indexes } = win.WPRelease;
let passed = 0; const failures = [];
function check(name, actual, expected) {
  if (JSON.stringify(actual) === JSON.stringify(expected)) passed++;
  else failures.push(name + '：期望 ' + JSON.stringify(expected) + '，实际 ' + JSON.stringify(actual));
}
check('整本书', indexes('all', 6), [0, 1, 2, 3, 4, 5]);
check('上半部分（6 个单元）', indexes('firstHalf', 6), [0, 1, 2]);
check('下半部分（6 个单元）', indexes('secondHalf', 6), [3, 4, 5]);
check('奇数个单元：上半多一个', indexes('firstHalf', 5), [0, 1, 2]);
check('奇数个单元：下半少一个', indexes('secondHalf', 5), [3, 4]);
check('上半 + 下半正好不重不漏', indexes('firstHalf', 7).concat(indexes('secondHalf', 7)), indexes('all', 7));
check('只有 1 个单元：上半就是它，下半是空', [indexes('firstHalf', 1), indexes('secondHalf', 1)], [[0], []]);
check('前 N 个', indexes('firstN', 6, 2), [0, 1]);
check('N 是字符串也行（来自输入框）', indexes('firstN', 6, '4'), [0, 1, 2, 3]);
check('N 超出总数：收到总数', indexes('firstN', 6, 99), [0, 1, 2, 3, 4, 5]);
check('N 是 0、负数、空、乱写：什么都不选', [indexes('firstN', 6, 0), indexes('firstN', 6, -3), indexes('firstN', 6, ''), indexes('firstN', 6, 'abc')], [[], [], [], []]);
check('清空', indexes('none', 6), []);
check('不认识的预设：什么都不选', indexes('whatever', 6), []);
check('没有单元：全是空', [indexes('all', 0), indexes('firstHalf', 0), indexes('firstN', 0, 3)], [[], [], []]);
check('KINDS 列出全部预设', win.WPRelease.KINDS, ['all', 'firstHalf', 'secondHalf', 'firstN', 'none']);
if (failures.length) { console.error('失败 ' + failures.length + ' 项：\n  ' + failures.join('\n  ')); process.exit(1); }
console.log('批量开放预设行为测试：' + passed + ' 项全部通过');
