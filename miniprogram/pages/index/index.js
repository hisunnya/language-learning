const bookData = require('../../data/grade9.js');
const bank = require('../../utils/bank.js');

Page({
  data: {
    stage: bookData.stage,
    grade: bookData.grade,
    note: bookData.note,
    bookTabs: [],
    bookIndex: 0,
    units: [],
    totalWords: 0,
    totalLevels: 0
  },

  onLoad: function () {
    var tabs = bookData.books.map(function (b) {
      return { key: b.key, name: b.name };
    });
    this.setData({ bookTabs: tabs });
    this.applyBook(0);
  },

  applyBook: function (index) {
    var book = bookData.books[index];
    if (!book) return;

    var units = book.units.map(function (u, i) {
      var levels = bank.buildLevels(book, i, bank.MAX_PAIRS);
      return {
        index: i,
        name: u.name,
        count: u.words.length,
        levels: levels.length
      };
    });

    var totalWords = units.reduce(function (sum, u) {
      return sum + u.count;
    }, 0);
    var totalLevels = bank.buildLevels(book, 'all', bank.MAX_PAIRS).length;

    this.setData({
      bookIndex: index,
      units: units,
      totalWords: totalWords,
      totalLevels: totalLevels
    });
  },

  onSwitchBook: function (event) {
    var index = Number(event.currentTarget.dataset.index);
    if (index === this.data.bookIndex) return;
    this.applyBook(index);
  },

  onStartAll: function () {
    this.gotoGame('all');
  },

  onStartUnit: function (event) {
    this.gotoGame(Number(event.currentTarget.dataset.index));
  },

  gotoGame: function (unit) {
    var bookIndex = this.data.bookIndex;
    wx.setStorageSync('wp_last_selection', { book: bookIndex, unit: unit });
    wx.navigateTo({
      url: '/pages/game/game?book=' + bookIndex + '&unit=' + unit
    });
  },

  onShowRules: function () {
    wx.showModal({
      title: '怎么玩',
      content:
        '英文和中文都可以先点，点第二张时配对。\n\n' +
        '每对 +100 分；连击每多一次 +20 分，最高 +100。\n' +
        '配错扣 20 分、扣 3 秒，连击清零。\n\n' +
        '每关 120 秒，过关后剩余时间每秒折算 10 分，' +
        '并按剩余时间给下一关加时，最多 150 秒。',
      showCancel: false,
      confirmText: '知道了'
    });
  }
});
