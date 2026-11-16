/* ============================================================
   offline-theme.js —— 离线单文件页的配色选择
   ------------------------------------------------------------
   和网站页眉里的一样：五套配色、小方块、斜着对半分（右上是主色，左下是页面底色）、
   提示里是中英文的配色名；选择记在浏览器里（localStorage 的 lg_theme，和网站同一个键），
   当前这套标上 aria-pressed。配色本身（html[data-theme=…] 里的变量）已经内嵌在页面的样式里。
   名字和颜色必须和 hub/shared/module-header.js 里的 PALETTES 一致（有测试对着）。
   ============================================================ */
(function (global) {
  'use strict';

  var KEY = 'lg_theme';
  var PALETTES = [
    { key: 'indigo', zh: '靛蓝 · 雪白', en: 'Indigo · Snow', main: '#4F46E5', bg: '#F4F6FB' },
    { key: 'ink', zh: '墨绿 · 玄夜', en: 'Ink · Obsidian', main: '#34D399', bg: '#0C1210' },
    { key: 'amber', zh: '琥珀 · 米白', en: 'Amber · Cream', main: '#B45309', bg: '#FBF6EC' },
    { key: 'lotus', zh: '绯红 · 藕白', en: 'Crimson · Lotus', main: '#DB2777', bg: '#FDF4F6' },
    { key: 'obsidian', zh: '鎏金 · 曜黑', en: 'Gilded · Obsidian', main: '#D4AF37', bg: '#08080A' }
  ];

  function known(key) { return PALETTES.some(function (p) { return p.key === key; }); }
  function saved() { try { return localStorage.getItem(KEY) || ''; } catch (e) { return ''; } }
  function lang() { return global.WPI18N && WPI18N.lang() === 'en' ? 'en' : 'zh'; }

  function apply(key) {
    if (!known(key)) key = 'indigo';
    document.documentElement.setAttribute('data-theme', key);
    try { localStorage.setItem(KEY, key); } catch (e) { }
    var chips = document.querySelectorAll('.theme-chip');
    Array.prototype.forEach.call(chips, function (chip) {
      chip.setAttribute('aria-pressed', String(chip.getAttribute('data-theme-val') === key));
    });
    return key;
  }

  /* 页面一打开就设好（在 <head> 里调用，免得先闪一下默认色） */
  function early() {
    var key = saved();
    document.documentElement.setAttribute('data-theme', known(key) ? key : 'indigo');
  }

  function names() {
    var l = lang();
    Array.prototype.forEach.call(document.querySelectorAll('.theme-chip'), function (chip) {
      var p = PALETTES.filter(function (x) { return x.key === chip.getAttribute('data-theme-val'); })[0];
      chip.title = p[l];
      chip.setAttribute('aria-label', p[l]);
    });
    var box = document.querySelector('.theme-picker');
    if (box) box.setAttribute('aria-label', l === 'en' ? 'Palettes' : '配色');
  }

  /* host：放选择器的元素 */
  function init(host) {
    host.innerHTML = '<div class="theme-picker" role="group">' + PALETTES.map(function (p) {
      return '<button type="button" class="theme-chip" data-theme-val="' + p.key + '" aria-pressed="false">' +
        '<span class="swatch" style="--swatch-main:' + p.main + ';--swatch-bg:' + p.bg + ';"></span></button>';
    }).join('') + '</div>';
    host.addEventListener('click', function (ev) {
      var chip = ev.target.closest('.theme-chip');
      if (chip) apply(chip.getAttribute('data-theme-val'));
    });
    names();
    if (global.WPI18N && WPI18N.onChange) WPI18N.onChange(names);
    apply(saved());
  }

  global.WPTheme = { KEY: KEY, PALETTES: PALETTES, apply: apply, early: early, init: init };
})(window);
