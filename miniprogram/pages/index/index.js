const bookData = require('../../data/grade9.js');
const bank = require('../../utils/bank.js');
const i18n = require('../../utils/i18n.js');
const prefs = require('../../utils/prefs.js');

Page({
  data: {
    lang: 'zh',
    theme: 'indigo',
    themeName: '',
    t: i18n.dict('zh'),
    palettes: [],
    bookTabs: [],
    bookIndex: 0,
    units: [],
    summaryText: ''
  },

  onLoad: function () {
    this.bookIndex = 0;
    this.stats = null;
    this.applyPrefs();
    this.applyBook(0);
    this.ready = true;
  },

  onShow: function () {
    // 从游戏页返回时重新读一次偏好，保证两个页面的语言、配色一致
    if (this.ready) this.applyPrefs();
  },

  applyPrefs: function () {
    var snap = prefs.snapshot();
    this.setData(snap);
    prefs.applyChrome();
    wx.setNavigationBarTitle({ title: snap.t.navTitleIndex });
    this.renderTexts();
  },

  /* 语言一变，凡是 JS 里拼出来的文字（册名、统计、单元信息）都要重算 */
  renderTexts: function () {
    var lang = this.data.lang;
    var t = this.data.t;
    this.setData({
      bookTabs: bookData.books.map(function (b) {
        return { key: b.key, name: i18n.bookLabel(b, bookData.grade, lang) };
      })
    });
    if (!this.stats) return;
    this.setData({
      units: this.stats.units.map(function (u) {
        return {
          index: u.index,
          name: u.name,
          meta: i18n.format(t.unitMeta, { count: u.count, levels: u.levels })
        };
      }),
      summaryText: i18n.format(t.summary, {
        words: this.stats.totalWords,
        levels: this.stats.totalLevels
      })
    });
  },

  applyBook: function (index) {
    var book = bookData.books[index];
    if (!book) return;

    var units = book.units.map(function (u, i) {
      var levels = bank.buildLevels(book, i, bank.MAX_PAIRS);
      return { index: i, name: u.name, count: u.words.length, levels: levels.length };
    });
    var totalWords = units.reduce(function (sum, u) {
      return sum + u.count;
    }, 0);
    var totalLevels = bank.buildLevels(book, 'all', bank.MAX_PAIRS).length;

    this.bookIndex = index;
    this.stats = { units: units, totalWords: totalWords, totalLevels: totalLevels };
    this.setData({ bookIndex: index });
    this.renderTexts();
  },

  onToggleLang: function () {
    prefs.setLang(this.data.lang === 'zh' ? 'en' : 'zh');
    this.applyPrefs();
  },

  onPickTheme: function (event) {
    prefs.setTheme(event.currentTarget.dataset.key);
    this.applyPrefs();
  },

  onSwitchBook: function (event) {
    var index = Number(event.currentTarget.dataset.index);
    if (index === this.bookIndex) return;
    this.applyBook(index);
  },

  onStartAll: function () {
    this.gotoGame('all');
  },

  onStartUnit: function (event) {
    this.gotoGame(Number(event.currentTarget.dataset.index));
  },

  gotoGame: function (unit) {
    var bookIndex = this.bookIndex;
    wx.setStorageSync('wp_last_selection', { book: bookIndex, unit: unit });
    wx.navigateTo({
      url: '/pages/game/game?book=' + bookIndex + '&unit=' + unit
    });
  },

  onShowRules: function () {
    var t = this.data.t;
    wx.showModal({
      title: t.rulesTitle,
      content: t.rulesBody,
      showCancel: false,
      confirmText: t.gotIt
    });
  }
});
