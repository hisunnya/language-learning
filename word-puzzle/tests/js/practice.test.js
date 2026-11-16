/* practice.test.js —— 读音练习：滑动判断、发音地址（网站版 / 离线版）、行的 HTML（转义、中文默认藏着）、显示 / 隐藏 */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm');
const code = fs.readFileSync(path.join(__dirname, '..', '..', 'web', 'js', 'practice-ui.js'), 'utf8');
const sandbox = { window: {}, Audio: function (u) { this.src = u; this.play = () => Promise.resolve(); this.pause = () => {}; this.addEventListener = () => {}; }, encodeURIComponent, String, Math, Object, Array, setTimeout, clearTimeout, fetch: undefined };
sandbox.window = sandbox; vm.createContext(sandbox); vm.runInContext(code, sandbox);
const P = sandbox.WPPractice;
let passed = 0; const failures = [];
function check(name, ok, detail) { if (ok) passed++; else failures.push(name + (detail ? '：' + detail : '')); }

// 滑动
check('向右滑够远 = 显示', P.swipe(120, 5) === 'reveal');
check('向左滑够远 = 隐藏', P.swipe(-120, -8) === 'hide');
check('滑得太短不算', P.swipe(30, 0) === null && P.swipe(-30, 0) === null && P.swipe(47, 0) === null);
check('正好够远算', P.swipe(P.SWIPE_MIN, 0) === 'reveal' && P.swipe(-P.SWIPE_MIN, 0) === 'hide');
check('竖着滚动（主要是竖向）不算', P.swipe(60, 120) === null && P.swipe(80, -200) === null);
check('斜着滑得太斜不算，稍斜还算', P.swipe(100, 70) === null && P.swipe(100, 40) === 'reveal');

// 键
check('音频键：小写、去首尾空格', P.audioKey('  Work on sth. ') === 'work on sth.' && P.audioKey(null) === '');

// 发音地址
let pl = P.createPlayer({ audio: { apple: 'data:audio/mpeg;base64,AAA' } });
check('离线版：用内嵌的语音，按小写词找', pl.url('Apple') === 'data:audio/mpeg;base64,AAA' && pl.url('banana') === '');
let errors = [];
pl = P.createPlayer({ audio: {}, onError: (w) => errors.push(w) });
check('离线版没有这个词的语音：播不了并报告', pl.play('banana') === false && errors.join() === 'banana');
pl = P.createPlayer({ base: '/word-puzzle/api/audio/' });
check('网站版：地址是后端的 /api/audio/ + 编码后的词', pl.url('turn one’s attention to sth. / sb.') === '/word-puzzle/api/audio/' + encodeURIComponent('turn one’s attention to sth. / sb.'));
check('网站版能播', pl.play('apple') === true);

// HTML
const groups = [{ unit: 'Unit 1', words: [{ en: 'sth. <b>', cn: '某物"&', ipa: '/x/' }, { en: 'apple', cn: '苹果', ipa: '' }] }, { unit: 'Unit 2', words: [{ en: 'pear', cn: '梨' }] }];
const html = P.listHtml(groups);
check('每个词一行，行号连续', (html.match(/class="prac-row"/g) || []).length === 3 && /data-i="2"/.test(html));
check('多个单元：有单元标题和词数；一个单元不显示标题', /<h3 class="prac-unit">Unit 1/.test(html) && !/prac-unit/.test(P.listHtml([groups[0]])));
check('英文和中文都做了转义', html.indexOf('<b>') < 0 && html.indexOf('&lt;b&gt;') > 0 && html.indexOf('某物&quot;&amp;') > 0);
const counts = P.listHtml([{ unit: 'A', words: [{ en: 'a', cn: 'b' }] }, { unit: 'B', words: [{ en: 'c', cn: 'd' }, { en: 'e', cn: 'f' }] }]);
check('只有一个词的单元用单数词条（1 word），多个词用复数词条', /A <small>prac_countOne</.test(counts) && /B <small>prac_count</.test(counts));
check('音标有才显示', /prac-ipa">\/x\//.test(html) && (html.match(/prac-ipa/g) || []).length === 1);
check('中文默认藏着：文字在 aria-hidden 里，按钮 aria-expanded=false', /class="prac-cn-text" aria-hidden="true"/.test(html) && /aria-expanded="false"/.test(html));
check('单词按钮和中文按钮都是 button（键盘能用）', (html.match(/<button type="button" class="prac-word"/g) || []).length === 3 && (html.match(/<button type="button" class="prac-cn"/g) || []).length === 3);

// 显示 / 隐藏
const row = { cls: new Set(), classList: { toggle(c, on) { on ? row.cls.add(c) : row.cls.delete(c); }, contains: (c) => row.cls.has(c) },
  attrs: {}, querySelector(sel) { return sel === '.prac-cn' ? cn : null; } };
const textEl = { attrs: {}, setAttribute(k, v) { this.attrs[k] = v; } };
const cn = { attrs: {}, setAttribute(k, v) { this.attrs[k] = v; }, querySelector: () => textEl };
P.setRevealed(row, true);
check('显示：加上 on，aria 同步', row.cls.has('on') && cn.attrs['aria-expanded'] === 'true' && textEl.attrs['aria-hidden'] === 'false');
P.setRevealed(row, false);
check('隐藏：去掉 on，aria 同步', !row.cls.has('on') && cn.attrs['aria-expanded'] === 'false' && textEl.attrs['aria-hidden'] === 'true');

// ---- init：点击、显示 / 隐藏、滑动、滑完之后不误触发发音（用最小的假 DOM 跑真实的 init）
function makeView(words) {
  const handlers = {};
  const rowsList = words.map((en, i) => {
    const textEl = { attrs: {}, setAttribute(k, v) { this.attrs[k] = v; } };
    const cnEl = { attrs: {}, setAttribute(k, v) { this.attrs[k] = v; }, querySelector: () => textEl };
    const row = { en, cls: new Set(), classList: { toggle(c, on) { on ? row.cls.delete(c) || row.cls.add(c) : row.cls.delete(c); }, contains: (c) => row.cls.has(c), add: (c) => row.cls.add(c), remove: (c) => row.cls.delete(c) },
      getAttribute: (k) => (k === 'data-en' ? en : String(i)), querySelector: (q) => (q === '.prac-cn' ? cnEl : null) };
    row.classList.toggle = (c, on) => { if (on) row.cls.add(c); else row.cls.delete(c); };
    return row;
  });
  const mount = { set innerHTML(v) { }, addEventListener: (type, fn) => { handlers[type] = fn; }, querySelectorAll: (q) => (q === '.prac-row' ? rowsList : q === '.prac-row.speaking' ? rowsList.filter((r) => r.cls.has('speaking')) : []) };
  const played = []; let clock = 1000;
  const player = { play: (en) => { played.push(en); return true; } };
  const view = sandbox.WPPractice.init({ mount, groups: [{ unit: 'U', words: words.map((en) => ({ en, cn: en + '释义' })) }], player, now: () => clock });
  const target = (row, act) => ({ closest: (q) => (q === '[data-act]' ? (act ? { getAttribute: () => act, closest: () => row } : null) : q === '.prac-row' ? row : null) });
  return { view, rowsList, played, handlers, target, tick: (ms) => { clock += ms; },
    click: (row, act) => handlers.click({ target: target(row, act) }),
    drag: (row, dx, dy) => { handlers.pointerdown({ target: target(row), clientX: 100, clientY: 100 }); handlers.pointerup({ clientX: 100 + dx, clientY: 100 + (dy || 0) }); } };
}
let v = makeView(['apple', 'banana']);
v.click(v.rowsList[0], 'play');
check('点单词：发音，读的是这一行的词，并标上正在读', v.played.join() === 'apple' && v.rowsList[0].cls.has('speaking') && !v.rowsList[1].cls.has('speaking'));
v.click(v.rowsList[1], 'play');
check('点另一个词：只有新的这个标「正在读」', v.played.join() === 'apple,banana' && !v.rowsList[0].cls.has('speaking') && v.rowsList[1].cls.has('speaking'));
check('一开始所有中文都藏着', !v.view.allRevealed() && v.rowsList.every((r) => !r.cls.has('on')));
v.click(v.rowsList[0], 'cn');
check('点中文：显示', v.rowsList[0].cls.has('on') && !v.rowsList[1].cls.has('on'));
v.click(v.rowsList[0], 'cn');
check('再点一次：藏起来', !v.rowsList[0].cls.has('on'));
v.view.revealAll(true);
check('全部显示 / 全部隐藏', v.view.allRevealed() && (v.view.revealAll(false), !v.view.allRevealed()));

v = makeView(['apple', 'banana']);
v.drag(v.rowsList[0], 120, 5);
check('向右滑：显示这一行的中文', v.rowsList[0].cls.has('on') && !v.rowsList[1].cls.has('on'));
v.click(v.rowsList[0], 'play');
check('刚滑完的那次点击不算「点单词」：不发音', v.played.length === 0);
v.tick(500);
v.click(v.rowsList[0], 'play');
check('过了一会儿再点才发音', v.played.join() === 'apple');
v.drag(v.rowsList[0], -120, 0);
check('向左滑：藏起来', !v.rowsList[0].cls.has('on'));
v.tick(500);
v.drag(v.rowsList[1], 20, 0);
check('滑得太短：什么都不变', !v.rowsList[1].cls.has('on'));
v.drag(v.rowsList[1], 40, 200);
check('主要是竖着滑（在滚动）：什么都不变，而且不挡住接下来的点击', !v.rowsList[1].cls.has('on'));
v.click(v.rowsList[1], 'play');
check('竖着滚动之后点单词照常发音', v.played.slice(-1)[0] === 'banana');
v.handlers.pointerdown({ target: v.target(null) }); v.handlers.pointerup({ clientX: 500, clientY: 100 });
check('手指不在任何一行上按下：不会出错也不会改变什么', !v.rowsList[0].cls.has('on'));
v.handlers.keydown({ target: v.target(v.rowsList[0]), key: 'ArrowRight', preventDefault() {} });
check('键盘 →：显示', v.rowsList[0].cls.has('on'));
v.handlers.keydown({ target: v.target(v.rowsList[0]), key: 'ArrowLeft', preventDefault() {} });
check('键盘 ←：隐藏', !v.rowsList[0].cls.has('on'));

if (failures.length) { console.error('失败 ' + failures.length + ' 项：\n  ' + failures.join('\n  ')); process.exit(1); }
console.log('读音练习：' + passed + ' 项通过');
