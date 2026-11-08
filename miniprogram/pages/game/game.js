const bookData = require('../../data/grade9.js');
const bank = require('../../utils/bank.js');
const core = require('../../utils/game-core.js');
const audio = require('../../utils/audio.js');
const i18n = require('../../utils/i18n.js');
const prefs = require('../../utils/prefs.js');

const TIME_PER_LEVEL = core.LEVEL_TIME;

Page({
  data: {
    lang: 'zh',
    theme: 'indigo',
    t: i18n.dict('zh'),
    audioOn: false,
    levelLine: '',
    overlayNextBonusText: '',
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
    this.gone = false;
    this.timers = [];
    var snap = prefs.snapshot();
    snap.audioOn = audio.enabled();
    this.setData(snap);
    prefs.applyChrome();
    var t = snap.t;

    var bookIndex = Number(query.book || 0);
    var unit = query.unit === 'all' ? 'all' : Number(query.unit || 0);
    var book = bookData.books[bookIndex];

    if (!book) {
      wx.showToast({ title: t.toastNoBank, icon: 'none' });
      return;
    }

    this.book = book;
    this.unit = unit;
    this.levels = bank.buildLevels(book, unit, bank.MAX_PAIRS);

    if (!this.levels.length) {
      wx.showToast({ title: t.toastNoWords, icon: 'none' });
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
    // 回到前台：用冻结时的剩余时间接着走，切走的这段不算
    if (this.game) this.game.resume();
    this.startTicker();
  },

  onHide: function () {
    // 切到别的应用：暂停计时，免得学生回去看一眼消息就被扣时间
    if (this.game) this.game.pause();
    this.stopTicker();
  },

  onUnload: function () {
    this.gone = true;
    this.stopTicker();
    (this.timers || []).forEach(function (id) { clearTimeout(id); });
    this.timers = [];
    audio.dispose();
  },

  /* 页面卸载后不能再 setData，所以所有延时都登记起来，卸载时一起取消 */
  later: function (fn, ms) {
    var self = this;
    var id = setTimeout(function () {
      if (self.gone) return;
      fn();
    }, ms);
    this.timers.push(id);
    return id;
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
        title: i18n.switchHint(this.data.lang, evt.side),
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
        overlayNextBonusText: i18n.format(this.data.t.clearNextValue, { n: evt.nextBonus }),
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
    var lang = this.data.lang;
    var levelName = i18n.localizeLevel(evt.levelName || '', lang);
    this.setData({
      cards: cards,
      levelName: levelName,
      levelLine: i18n.format(this.data.t.levelLine, {
        no: evt.level + 1,
        total: this.levels.length,
        name: levelName
      }),
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

    wx.setNavigationBarTitle({ title: levelName || this.data.t.navTitleGame });

    // 进关就自动下载这一关的发音；下载失败只是没有声音，游戏照常进行。
    // 本关的下载完成后，顺手把下一关的也预取好。
    var lv = this.game.state.lv;
    var next = this.levels[lv + 1];
    audio.preload(evt.cards.map(function (c) { return c.word; })).then(function () {
      if (next) audio.preload(next.words);
    });
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
    this.later(function () {
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

    this.later(function () {
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
    this.later(function () {
      self.setData({ fxText: text, fxShow: true });
      self.later(function () {
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
    var t = this.data.t;
    wx.showModal({
      title: t.restartTitle,
      content: t.restartBody,
      confirmText: t.restartConfirm,
      success: function (res) {
        if (!res.confirm) return;
        self.game.restart();
        self.setData({ overlay: '' });
        self.startTicker();
      }
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
