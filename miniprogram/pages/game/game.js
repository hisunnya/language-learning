const bookData = require('../../data/grade9.js');
const bank = require('../../utils/bank.js');
const core = require('../../utils/game-core.js');
const audio = require('../../utils/audio.js');

const TIME_PER_LEVEL = core.LEVEL_TIME;

Page({
  data: {
    levelName: '',
    levelNo: 1,
    levelTotal: 1,
    score: 0,
    best: 0,
    timeLeft: TIME_PER_LEVEL,
    timePct: 100,
    timeWarn: false,
    matched: 0,
    total: 0,
    cards: [],
    overlay: '',
    overlayBonus: 0,
    overlayNextBonus: 0,
    overlayHasNext: false,
    overlayScore: 0,
    fxText: '',
    fxShow: false
  },

  onLoad: function (query) {
    var bookIndex = Number(query.book || 0);
    var unit = query.unit === 'all' ? 'all' : Number(query.unit || 0);
    var book = bookData.books[bookIndex];

    if (!book) {
      wx.showToast({ title: '题库未找到', icon: 'none' });
      return;
    }

    this.book = book;
    this.unit = unit;
    this.levels = bank.buildLevels(book, unit, bank.MAX_PAIRS);

    if (!this.levels.length) {
      wx.showToast({ title: '这个范围内没有单词', icon: 'none' });
      return;
    }

    var self = this;
    this.game = new core.Game({
      levels: this.levels,
      onEvent: function (evt) {
        self.onGameEvent(evt);
      }
    });

    this.setData({ levelTotal: this.levels.length });
    this.game.start(0);
  },

  onShow: function () {
    this.startTicker();
  },

  onHide: function () {
    this.stopTicker();
  },

  onUnload: function () {
    this.stopTicker();
    audio.dispose();
  },

  startTicker: function () {
    this.stopTicker();
    var self = this;
    this.timer = setInterval(function () {
      if (!self.game) return;
      self.game.tick();
    }, 200);
  },

  stopTicker: function () {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
  },

  onGameEvent: function (evt) {
    if (evt.type === 'board') {
      this.renderBoard(evt);
      return;
    }
    if (evt.type === 'select' || evt.type === 'repeat') {
      audio.play(evt.word && evt.word.en);
      this.markSelected(evt.card);
      return;
    }
    if (evt.type === 'switch') {
      audio.play(evt.word && evt.word.en);
      this.markSelected(evt.card);
      wx.showToast({
        title: evt.side === 'cn' ? '刚选的是英文，再点中文配对' : '刚选的是中文，再点英文配对',
        icon: 'none',
        duration: 900
      });
      return;
    }
    if (evt.type === 'match') {
      this.markMatched(evt);
      return;
    }
    if (evt.type === 'miss') {
      this.markMiss(evt);
      return;
    }
    if (evt.type === 'tick') {
      this.renderTime(evt.timeLeft);
      return;
    }
    if (evt.type === 'levelClear') {
      this.stopTicker();
      this.setData({
        overlay: 'clear',
        overlayScore: evt.score,
        overlayBonus: evt.bonus,
        overlayNextBonus: evt.nextBonus,
        overlayHasNext: evt.hasNext
      });
      return;
    }
    if (evt.type === 'timeUp') {
      this.stopTicker();
      this.setData({
        overlay: 'over',
        overlayScore: evt.score,
        overlayHasNext: evt.hasNext
      });
    }
  },

  renderBoard: function (evt) {
    var cards = evt.cards.map(function (c) {
      return {
        key: c.t + '-' + c.id,
        t: c.t,
        id: c.id,
        text: c.t === 'en' ? c.word.en : c.word.cn,
        ipa: c.t === 'en' ? c.word.ipa || '' : '',
        cls: 'card' + (c.t === 'en' ? ' card-en' : ' card-cn'),
        gone: false
      };
    });
    this._cards = cards;

    var st = this.game.state;
    this.setData({
      cards: cards,
      levelName: evt.levelName || '',
      levelNo: evt.level + 1,
      total: evt.total,
      matched: 0,
      score: st.score,
      best: st.best,
      timeLeft: Math.ceil(st.limit),
      timePct: 100,
      timeWarn: false,
      overlay: ''
    });

    wx.setNavigationBarTitle({ title: evt.levelName || '单词消消乐' });
    audio.preload(evt.cards.map(function (c) { return c.word; }));
  },

  renderTime: function (timeLeft) {
    var st = this.game.state;
    var pct = Math.max(0, Math.min(100, (timeLeft / st.limit) * 100));
    var secs = Math.ceil(Math.max(0, timeLeft));
    if (secs === this.data.timeLeft && Math.abs(pct - this.data.timePct) < 1) return;
    this.setData({
      timeLeft: secs,
      timePct: pct,
      timeWarn: timeLeft <= 10
    });
  },

  markSelected: function (card) {
    if (!card || !this._cards) return;
    var key = card.t + '-' + card.id;
    var cards = this._cards;
    for (var i = 0; i < cards.length; i++) {
      if (cards[i].key === key) {
        cards[i].cls = cards[i].cls.replace(' card-sel', '') + ' card-sel';
      } else if (!cards[i].gone) {
        cards[i].cls = cards[i].cls.replace(' card-sel', '');
      }
    }
    this.setData({ cards: cards });
  },

  markMatched: function (evt) {
    var enKey = 'en-' + evt.enCard.id;
    var cnKey = 'cn-' + evt.cnCard.id;
    var cards = this._cards;
    var self = this;

    for (var i = 0; i < cards.length; i++) {
      var c = cards[i];
      if (c.key === enKey || c.key === cnKey) {
        c.cls = c.cls.replace(' card-sel', '') + ' card-matched';
        c.gone = true;
      } else {
        c.cls = c.cls.replace(' card-sel', '');
      }
    }

    var st = this.game.state;
    this.setData({
      cards: cards,
      score: st.score,
      best: st.best,
      matched: st.matched
    });

    this.flashFx('+' + evt.gain + (evt.combo > 1 ? '  ×' + evt.combo : ''));
    setTimeout(function () {
      self.compactBoard();
    }, 460);
  },

  compactBoard: function () {
    var cards = this._cards;
    if (!cards) return;
    var visible = cards.filter(function (c) { return !c.gone; });
    this._cards = visible;
    this.setData({ cards: visible });
  },

  markMiss: function (evt) {
    var enKey = 'en-' + evt.enCard.id;
    var cnKey = 'cn-' + evt.cnCard.id;
    var cards = this._cards;
    var self = this;
    var touched = [];

    for (var i = 0; i < cards.length; i++) {
      var c = cards[i];
      c.cls = c.cls.replace(' card-sel', '');
      if (c.key === enKey || c.key === cnKey) {
        c.cls = c.cls + ' card-bad';
        touched.push(i);
      }
    }

    var st = this.game.state;
    this.setData({
      cards: cards,
      score: st.score,
      matched: st.matched
    });
    this.renderTime(evt.timeLeft);

    setTimeout(function () {
      var list = self._cards;
      if (!list) return;
      for (var j = 0; j < list.length; j++) {
        list[j].cls = list[j].cls.replace(' card-bad', '');
      }
      self.setData({ cards: list });
    }, 430);

    if (wx.vibrateShort) {
      wx.vibrateShort({ type: 'light', fail: function () {} });
    }
    return touched;
  },

  flashFx: function (text) {
    var self = this;
    this.setData({ fxShow: false });
    setTimeout(function () {
      self.setData({ fxText: text, fxShow: true });
      setTimeout(function () {
        self.setData({ fxShow: false });
      }, 800);
    }, 16);
  },

  onTapCard: function (event) {
    if (!this.game) return;
    if (this.data.overlay) return;
    var id = Number(event.currentTarget.dataset.id);
    var t = event.currentTarget.dataset.t;

    var cards = this._cards || [];
    var target = null;
    for (var i = 0; i < cards.length; i++) {
      if (cards[i].id === id && cards[i].t === t) {
        target = cards[i];
        break;
      }
    }
    if (!target || target.gone) return;

    var level = this.levels[this.game.state.lv];
    var word = level && level.words[id];
    if (!word) return;

    this.game.pick({ t: t, id: id, word: word });
  },

  onNextLevel: function () {
    if (!this.game) return;
    this.game.next();
    this.setData({ overlay: '' });
    this.startTicker();
  },

  onReplay: function () {
    if (!this.game) return;
    this.game.replay();
    this.setData({ overlay: '' });
    this.startTicker();
  },

  onRestartAll: function () {
    var self = this;
    wx.showModal({
      title: '从头开始',
      content: '分数会清零，从第一关重新来。确定吗？',
      confirmText: '重新开始',
      success: function (res) {
        if (!res.confirm) return;
        self.game.restart();
        self.setData({ overlay: '' });
        self.startTicker();
      }
    });
  },

  onShowRules: function () {
    var self = this;
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
  },

  onFinish: function () {
    var report = this.game ? this.game.report() : null;
    this.stopTicker();
    this.setData({ overlay: '' });
    if (report) {
      wx.setStorageSync('wp_last_report', report);
    }
    wx.navigateBack({
      fail: function () {
        wx.reLaunch({ url: '/pages/index/index' });
      }
    });
  }
});
