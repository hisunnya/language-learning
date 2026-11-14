/* ============================================================
   i18n.js —— 词境页面的中英文切换
   ------------------------------------------------------------
   * 静态文字：标签上写 data-module-zh / data-module-en（页眉脚本 module-header.js 负责替换）；
     占位符和提示用 data-i18n-placeholder-zh/en、data-i18n-aria-zh/en（本文件负责）。
   * 脚本画出来的文字：WPI18N.t('key', {n: 3})，词条在 i18n-lexica.js 里，中英文必须是同一组键。
   * 切换语言时页眉会发出 portal-lang-change 事件，动态内容用 WPI18N.onChange 重画。
   * 离线单文件页没有页眉：这里自己负责读 / 存语言（lg_lang）并提供切换，默认跟随浏览器语言。
   ============================================================ */
(function (global) {
  'use strict';

  var LANG_KEY = 'lg_lang';
  var dict = { zh: {}, en: {} };
  var listeners = [];

  function normalize(value) {
    return String(value || '').toLowerCase().indexOf('en') === 0 ? 'en' : 'zh';
  }

  function lang() {
    return normalize(document.documentElement.getAttribute('lang'));
  }

  function add(zh, en) {
    var k;
    for (k in zh) if (Object.prototype.hasOwnProperty.call(zh, k)) dict.zh[k] = zh[k];
    for (k in en) if (Object.prototype.hasOwnProperty.call(en, k)) dict.en[k] = en[k];
  }

  /* t('key', {n: 3})：{n} 会被替换；没有英文词条时退回中文，再没有就原样返回键，页面不会空白 */
  function t(key, params) {
    var text = dict[lang()][key];
    if (text === undefined) text = dict.zh[key];
    if (text === undefined) return key;
    if (params) {
      text = text.replace(/\{(\w+)\}/g, function (m, name) {
        return params[name] === undefined ? m : String(params[name]);
      });
    }
    return text;
  }

  /* 静态属性：页眉脚本只换文字，占位符 / 提示由这里换 */
  function applyAttributes() {
    var l = lang();
    [['placeholder', 'placeholder'], ['aria', 'aria-label'], ['title', 'title']].forEach(function (pair) {
      var selector = '[data-i18n-' + pair[0] + '-zh]';
      Array.prototype.forEach.call(document.querySelectorAll(selector), function (el) {
        var value = el.getAttribute('data-i18n-' + pair[0] + '-' + l);
        if (value !== null) el.setAttribute(pair[1], value);
      });
    });
  }

  /* 没有页眉的页面（离线单文件页）：自己换 data-module-* 文字 */
  function applyText() {
    var l = lang();
    Array.prototype.forEach.call(document.querySelectorAll('[data-module-zh][data-module-en]'), function (el) {
      el.textContent = el.getAttribute('data-module-' + l);
    });
  }

  function emit() {
    listeners.forEach(function (fn) { try { fn(lang()); } catch (e) { /* 一处重画出错不影响其他处 */ } });
  }

  function onChange(fn) { listeners.push(fn); }

  /* 页眉切换语言时：换占位符，再通知各页面重画 */
  global.addEventListener('portal-lang-change', function () {
    applyAttributes();
    emit();
  });

  /* 离线页用：设置语言并保存。有页眉时由页眉负责，这里只在没有页眉时才直接改 */
  function setLang(value) {
    value = normalize(value);
    if (global.PortalHeader && global.PortalHeader.applyLanguage) {
      global.PortalHeader.applyLanguage(value);
      return;
    }
    document.documentElement.setAttribute('lang', value === 'en' ? 'en' : 'zh-CN');
    try { localStorage.setItem(LANG_KEY, value); } catch (e) { }
    applyText();
    applyAttributes();
    emit();
  }

  function initStandalone() {
    if (global.PortalHeader) return;           /* 有页眉：它已经设好了语言 */
    var saved = '';
    try { saved = localStorage.getItem(LANG_KEY) || ''; } catch (e) { }
    var value = saved || ((global.navigator && global.navigator.language) || 'zh');
    setLang(normalize(value));
  }

  document.addEventListener('DOMContentLoaded', function () {
    applyAttributes();
    initStandalone();
  });

  global.WPI18N = {
    lang: lang, t: t, add: add, onChange: onChange, setLang: setLang,
    applyAttributes: applyAttributes
  };
})(window);
