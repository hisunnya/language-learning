(function () {
  'use strict';

  var LANG_KEY = 'lg_lang';
  var THEME_KEY = 'lg_theme';
  var PALETTES = [
    { key: 'indigo', zh: '靛蓝 · 雪白', en: 'Indigo · Snow', main: '#4F46E5', bg: '#F4F6FB' },
    { key: 'ink', zh: '墨绿 · 玄夜', en: 'Ink · Obsidian', main: '#34D399', bg: '#0C1210' },
    { key: 'amber', zh: '琥珀 · 米白', en: 'Amber · Cream', main: '#B45309', bg: '#FBF6EC' },
    { key: 'lotus', zh: '绯红 · 藕白', en: 'Crimson · Lotus', main: '#DB2777', bg: '#FDF4F6' },
    { key: 'obsidian', zh: '鎏金 · 曜黑', en: 'Gilded · Obsidian', main: '#D4AF37', bg: '#08080A' },
  ];
  var controlHost = document.getElementById('portalHeaderControls');
  if (controlHost) {
    controlHost.innerHTML = '<button type="button" class="portal-lang-btn" id="portalLangBtn">' +
      '<span class="zh">中</span><span class="sep">/</span><span class="en">EN</span></button>' +
      '<div class="portal-theme-picker" role="group" aria-label="配色">' +
      PALETTES.map(function (p) {
        return '<button type="button" class="portal-theme-chip" data-theme-val="' + p.key + '"' +
          ' data-tooltip-zh="' + p.zh + '" data-tooltip-en="' + p.en + '"' +
          ' aria-label="' + p.zh + '" aria-pressed="false">' +
          '<span class="portal-swatch" style="--swatch-main:' + p.main + ';--swatch-bg:' + p.bg + '"></span>' +
          '</button>';
      }).join('') + '</div>';
  }
  var langBtn = document.getElementById('portalLangBtn');
  var chips = Array.prototype.slice.call(document.querySelectorAll('.portal-theme-chip'));

  function read(key, fallback) {
    try { return localStorage.getItem(key) || fallback; }
    catch (e) { return fallback; }
  }

  function write(key, value) {
    try { localStorage.setItem(key, value); }
    catch (e) { /* 浏览器隐私设置可能禁用本地存储 */ }
  }

  function applyLanguage(lang) {
    lang = lang === 'en' ? 'en' : 'zh';
    document.documentElement.lang = lang === 'en' ? 'en' : 'zh-CN';
    document.querySelectorAll('[data-module-zh][data-module-en]').forEach(function (el) {
      el.textContent = el.getAttribute(lang === 'en' ? 'data-module-en' : 'data-module-zh');
    });
    var picker = document.querySelector('.portal-theme-picker');
    if (picker) picker.setAttribute('aria-label', lang === 'en' ? 'Palettes' : '配色');
    chips.forEach(function (chip) {
      chip.setAttribute('aria-label', chip.getAttribute(lang === 'en' ? 'data-tooltip-en' : 'data-tooltip-zh'));
    });
    if (langBtn) {
      langBtn.classList.toggle('is-en', lang === 'en');
      langBtn.setAttribute('aria-label', lang === 'en' ? 'Switch to Chinese' : '切换到 English');
      langBtn.setAttribute('data-tooltip-zh', '切换到 English');
      langBtn.setAttribute('data-tooltip-en', 'Switch to 中文');
    }
    write(LANG_KEY, lang);
    /* 页面里由脚本动态画出来的内容（表格、列表、弹出的提示）监听这个事件重画；
       静态文字靠上面的 data-module-zh / data-module-en 就够了。 */
    window.dispatchEvent(new CustomEvent('portal-lang-change', { detail: { lang: lang } }));
  }

  function applyTheme(theme) {
    if (!PALETTES.some(function (p) { return p.key === theme; })) theme = 'indigo';
    document.documentElement.dataset.theme = theme;
    chips.forEach(function (chip) {
      chip.setAttribute('aria-pressed', String(chip.dataset.themeVal === theme));
    });
    write(THEME_KEY, theme);
    window.dispatchEvent(new CustomEvent('portal-theme-change', { detail: { theme: theme } }));
  }

  if (langBtn) {
    langBtn.addEventListener('click', function () {
      applyLanguage(document.documentElement.lang.indexOf('en') === 0 ? 'zh' : 'en');
    });
  }
  chips.forEach(function (chip) {
    chip.addEventListener('click', function () { applyTheme(chip.dataset.themeVal); });
  });

  applyLanguage(read(LANG_KEY, 'zh'));
  applyTheme(read(THEME_KEY, 'indigo'));
  window.PortalHeader = { applyLanguage: applyLanguage, applyTheme: applyTheme };
})();
