/* recent.test.js —— 最近玩过的题库：记录、去重、上限、按账号分开、只显示还看得到的、「多久以前」 */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm');
const code = fs.readFileSync(path.join(__dirname, '..', '..', 'web', 'js', 'recent.js'), 'utf8');
const sandbox = { window: {}, JSON, parseInt, Math, Array, Object }; sandbox.window = sandbox;
vm.createContext(sandbox); vm.runInContext(code, sandbox);
const R = sandbox.WPRecent;
let passed = 0; const failures = [];
function check(name, ok, detail) { if (ok) passed++; else failures.push(name + (detail ? '：' + detail : '')); }
const store = (init) => { const m = Object.assign({}, init || {}); return { getItem: (k) => (k in m ? m[k] : null), setItem: (k, v) => { m[k] = String(v); }, raw: m }; };
const banks = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((id) => ({ id, title: 'b' + id, word_count: 10 * id }));

let s = store();
check('账号键：登录的用 u+编号，访客用 guest', R.userKey({ user: { id: 7 } }) === 'u7' && R.userKey({ user: null }) === 'guest' && R.userKey(null) === 'guest');
R.add(s, 'u1', 3, 1000); R.add(s, 'u1', 5, 2000); R.add(s, 'u1', 3, 3000);
let l = R.list(s, 'u1', banks, 4);
check('最近的在前，同一个题库只留最近一次', l.map((x) => x.bank.id).join() === '3,5' && l[0].t === 3000);
check('另一个账号看不到', R.list(s, 'u2', banks, 4).length === 0 && R.list(s, 'guest', banks, 4).length === 0);
for (let i = 1; i <= 10; i++) R.add(s, 'u1', i, 5000 + i);
check('每个账号最多记 ' + R.MAX + ' 个', JSON.parse(s.raw[R.KEY]).u1.length === R.MAX);
check('首页最多显示 limit 个', R.list(s, 'u1', banks, 4).length === 4 && R.list(s, 'u1', banks, 4)[0].bank.id === 10);
l = R.list(s, 'u1', banks.filter((b) => b.id !== 10 && b.id !== 9), 4);
check('现在看不到的题库（被收回标签）不显示，后面的顶上来', l.map((x) => x.bank.id).join() === '8,7,6,5');
R.add(s, 'u1', 'abc', 1); R.add(s, 'u1', 0, 1); R.add(s, 'u1', null, 1);
check('乱七八糟的编号不记', JSON.parse(s.raw[R.KEY]).u1.length === R.MAX);
check('存储里是乱码：当作没有，不报错', R.list(store({ wp_recent: '{{{' }), 'u1', banks, 4).length === 0 && R.list(store({ wp_recent: '[1,2]' }), 'u1', banks, 4).length === 0);
const full = { getItem: () => null, setItem: () => { throw new Error('quota'); } };
let threw = false; try { R.add(full, 'u1', 1, 1); } catch (e) { threw = true; }
check('存不了就悄悄不记，不影响游戏', !threw);

const now = 1_000_000_000;
const A = (sec) => R.ago(now - sec * 1000, now);
check('刚刚 / 分钟 / 小时 / 昨天 / 几天前',
  A(5).key === 'home_agoNow' && A(120).key === 'home_agoMin' && A(120).n === 2 && A(7200).key === 'home_agoHour' && A(7200).n === 2 &&
  A(90000).key === 'home_agoYesterday' && A(3 * 86400).key === 'home_agoDays' && A(3 * 86400).n === 3);
check('时间在「未来」（设备时钟被调过）按刚刚算', R.ago(now + 99999, now).key === 'home_agoNow');

if (failures.length) { console.error('失败 ' + failures.length + ' 项：\n  ' + failures.join('\n  ')); process.exit(1); }
console.log('最近玩过：' + passed + ' 项通过');
