/* offline_theme.test.js —— 离线页的配色选择：五个小方块、记住选择、认不得的存值回到默认、提示随语言换 */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm');
const code = fs.readFileSync(path.join(__dirname, '..', '..', 'web', 'js', 'offline-theme.js'), 'utf8');
let passed = 0; const failures = [];
function check(name, ok, detail) { if (ok) passed++; else failures.push(name + (detail ? '：' + detail : '')); }

function makePage(saved, lang) {
  const store = saved === undefined ? {} : { lg_theme: saved };
  const root = { attrs: {}, setAttribute(k, v) { this.attrs[k] = v; } };
  let chips = [], box = { attrs: {}, setAttribute(k, v) { this.attrs[k] = v; } };
  const listeners = [];
  const host = { set innerHTML(html) {
      chips = (html.match(/data-theme-val="([a-z]+)"/g) || []).map((m) => {
        const key = /"([a-z]+)"/.exec(m)[1];
        const swatch = new RegExp('data-theme-val="' + key + '"[^>]*><span class="swatch" style="([^"]*)"').exec(html);
        return { key, style: swatch ? swatch[1] : '', pressed: 'false', title: '', attrs: {}, setAttribute(k, v) { this.attrs[k] = v; if (k === 'aria-pressed') this.pressed = v; }, getAttribute(k) { return k === 'data-theme-val' ? this.key : this.attrs[k]; } };
      });
    }, addEventListener: (t, f) => { host.handler = f; } };
  const sandbox = {
    document: { documentElement: root, querySelectorAll: (q) => (q === '.theme-chip' ? chips : []), querySelector: (q) => (q === '.theme-picker' ? box : null) },
    localStorage: { getItem: (k) => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = v; } },
    WPI18N: { lang: () => lang || 'zh', onChange: (f) => listeners.push(f) },
    Array, String,
  };
  sandbox.window = sandbox; vm.createContext(sandbox); vm.runInContext(code, sandbox);
  return { T: sandbox.WPTheme, root, chips: () => chips, host, store, box, listeners, setLang: (l) => { lang = l; listeners.forEach((f) => f()); },
    click: (key) => host.handler({ target: { closest: () => chips.filter((c) => c.key === key)[0] } }) };
}

let p = makePage();
p.T.init(p.host);
check('五套配色，五个小方块', p.chips().length === 5 && p.chips().map((c) => c.key).join() === 'indigo,ink,amber,lotus,obsidian');
check('没存过：默认靛蓝，当前这个标上 aria-pressed', p.root.attrs['data-theme'] === 'indigo' && p.chips().filter((c) => c.pressed === 'true').map((c) => c.key).join() === 'indigo');
check('每个方块带自己的两个颜色（主色和页面底色）', p.chips().every((c) => /--swatch-main:#[0-9A-F]{6}/.test(c.style) && /--swatch-bg:#[0-9A-F]{6}/.test(c.style)) && new Set(p.chips().map((c) => c.style)).size === 5);
p.click('obsidian');
check('点方块：换配色、存起来、只有它被标上', p.root.attrs['data-theme'] === 'obsidian' && p.store.lg_theme === 'obsidian' && p.chips().filter((c) => c.pressed === 'true').map((c) => c.key).join() === 'obsidian');
p = makePage('lotus'); p.T.init(p.host);
check('下次打开按上次的选择', p.root.attrs['data-theme'] === 'lotus' && p.chips().filter((c) => c.pressed === 'true')[0].key === 'lotus');
p = makePage('hacker<script>'); p.T.init(p.host);
check('存的值认不得：回到默认，也不会把它写进页面', p.root.attrs['data-theme'] === 'indigo' && p.store.lg_theme === 'indigo');
p = makePage('amber'); p.T.early();
check('early()：在页面画出来之前先把配色设好', p.root.attrs['data-theme'] === 'amber' && p.chips().length === 0);
p = makePage(undefined, 'zh'); p.T.init(p.host);
check('提示是中文配色名，组名「配色」', p.chips()[0].title === '靛蓝 · 雪白' && p.box.attrs['aria-label'] === '配色');
p.setLang('en');
check('切到英文：提示和组名跟着换', p.chips()[0].title === 'Indigo · Snow' && p.chips()[4].title === 'Gilded · Obsidian' && p.box.attrs['aria-label'] === 'Palettes');
p = makePage(); p.T.init(p.host);
const bad = { getItem: () => { throw new Error('denied'); }, setItem: () => { throw new Error('denied'); } };
let ok = true; try { const q = makePage(); q.T.init(q.host); q.click('ink'); } catch (e) { ok = false; }
check('正常点击不报错', ok);

if (failures.length) { console.error('失败 ' + failures.length + ' 项：\n  ' + failures.join('\n  ')); process.exit(1); }
console.log('离线页配色：' + passed + ' 项通过');
