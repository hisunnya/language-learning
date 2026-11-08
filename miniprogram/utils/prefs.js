/* ============================================================
   prefs.js —— 语言和配色偏好
   ------------------------------------------------------------
   * 记在本机存储里（wp_lang / wp_theme），下次打开还是上次的选择；
   * 配色和网站版一致：靛蓝·雪白、墨绿·玄夜、琥珀·米白、绯红·藕白、鎏金·曜黑，
     每套的 CSS 变量写在 app.wxss 的 .theme-xxx 里；
   * 小程序的导航栏和页面底色不在 WXML 里，要用 wx.setNavigationBarColor /
     wx.setBackgroundColor 单独设，这里统一处理。
   ============================================================ */

var i18n = require('./i18n.js');

var LANG_KEY = 'wp_lang';
var THEME_KEY = 'wp_theme';
var DEFAULT_LANG = 'zh';
var DEFAULT_THEME = 'indigo';

/* main = 强调色（方块右上半），bg = 页面底色（方块左下半）；dark = 深色底，导航栏文字要反白 */
var PALETTES = [
  { key: 'indigo', zh: '靛蓝 · 雪白', en: 'Indigo · Snow', main: '#4f46e5', bg: '#f4f6fb', dark: false },
  { key: 'ink', zh: '墨绿 · 玄夜', en: 'Ink · Obsidian', main: '#34d399', bg: '#0c1210', dark: true },
  { key: 'amber', zh: '琥珀 · 米白', en: 'Amber · Cream', main: '#b45309', bg: '#fbf6ec', dark: false },
  { key: 'lotus', zh: '绯红 · 藕白', en: 'Crimson · Lotus', main: '#db2777', bg: '#fdf4f6', dark: false },
  { key: 'obsidian', zh: '鎏金 · 曜黑', en: 'Gilded · Obsidian', main: '#d4af37', bg: '#08080a', dark: true }
];

function read(key) {
  try {
    return wx.getStorageSync(key) || '';
  } catch (e) {
    return '';
  }
}

function write(key, value) {
  try {
    wx.setStorageSync(key, value);
  } catch (e) { /* 存储失败就只在本次生效 */ }
}

function paletteOf(key) {
  for (var i = 0; i < PALETTES.length; i++) {
    if (PALETTES[i].key === key) return PALETTES[i];
  }
  return PALETTES[0];
}

function getLang() {
  var saved = read(LANG_KEY);
  return saved === 'en' || saved === 'zh' ? saved : DEFAULT_LANG;
}

function getTheme() {
  var saved = read(THEME_KEY);
  return paletteOf(saved).key === saved ? saved : DEFAULT_THEME;
}

function setLang(lang) {
  var value = i18n.normalize(lang);
  write(LANG_KEY, value);
  return value;
}

function setTheme(key) {
  var value = paletteOf(key).key;
  write(THEME_KEY, value);
  return value;
}

/* 页面 setData 要用的全部数据 */
function snapshot() {
  var lang = getLang();
  var theme = getTheme();
  var current = paletteOf(theme);
  return {
    lang: lang,
    theme: theme,
    themeName: current[lang],
    t: i18n.dict(lang),
    palettes: PALETTES.map(function (p) {
      return {
        key: p.key,
        name: p[lang],
        on: p.key === theme,
        style: '--swatch-main:' + p.main + ';--swatch-bg:' + p.bg + ';'
      };
    })
  };
}

/* 导航栏、页面底色（页面根节点管不到的地方） */
function applyChrome() {
  var palette = paletteOf(getTheme());
  try {
    wx.setNavigationBarColor({
      frontColor: palette.dark ? '#ffffff' : '#000000',
      backgroundColor: palette.bg,
      fail: function () {}
    });
    wx.setBackgroundColor({
      backgroundColor: palette.bg,
      backgroundColorTop: palette.bg,
      backgroundColorBottom: palette.bg,
      fail: function () {}
    });
  } catch (e) { /* 低版本基础库没有这些接口，不影响使用 */ }
}

module.exports = {
  PALETTES: PALETTES,
  DEFAULT_LANG: DEFAULT_LANG,
  DEFAULT_THEME: DEFAULT_THEME,
  paletteOf: paletteOf,
  getLang: getLang,
  getTheme: getTheme,
  setLang: setLang,
  setTheme: setTheme,
  snapshot: snapshot,
  applyChrome: applyChrome
};
