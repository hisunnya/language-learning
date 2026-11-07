/* ============================================================
   game-core.js —— 纯运算层（移植自 word-puzzle/web/js/game-core.js）
   ------------------------------------------------------------
   只负责「关卡 / 计分 / 计时 / 连击」这些计算，不碰 DOM、不碰存储、
   不碰网络，也不碰任何小程序 API。界面层自己订阅 onEvent 来画。
   相比网站版唯一的新增是 wrongLog：记录每次配错的英文词与选错的中文，
   导出成绩时可以直接统计「错词榜」。
   ============================================================ */

var LEVEL_TIME = 120;
var LEVEL_BONUS_MAX = 30;
var LEVEL_LIMIT_MAX = LEVEL_TIME + LEVEL_BONUS_MAX;
var PAIR_SCORE = 100;
var COMBO_STEP = 20;
var COMBO_CAP = 5;
var MISS_TIME = 3;
var MISS_SCORE = 20;
var TIME_BONUS = 10;

function Game(opts) {
  opts = opts || {};
  this.levels = opts.levels || [];
  this.levelTime = opts.levelTime || LEVEL_TIME;
  this.onEvent = opts.onEvent || function () {};
  this.state = {
    lv: 0,
    score: 0,
    matched: 0,
    total_pairs: 0,
    sel: null,
    combo: 0,
    best: 0,
    wrong: 0,
    timeLeft: this.levelTime,
    limit: this.levelTime,
    deadline: 0,
    playing: false,
    startedAt: 0,
    levelStartScore: 0,
    levelStartAt: 0,
    levelStats: [],
    wrongLog: []
  };
}

Game.prototype = {
  start: function (index) {
    var st = this.state;
    st.lv = Math.max(0, Math.min(index | 0, this.levels.length - 1));
    this.buildBoard();
  },

  buildBoard: function () {
    var st = this.state;
    var level = this.levels[st.lv];
    var pairs = (level && level.words) ? level.words : [];
    st.total_pairs = pairs.length;
    st.matched = 0;
    st.sel = null;
    st.combo = 0;
    st.wrong = 0;
    st.timeLeft = st.limit;
    st.playing = true;
    st.startedAt = Date.now();
    st.levelStartAt = Date.now();
    st.levelStartScore = st.score;
    st.deadline = Date.now() + st.limit * 1000;

    var cards = [];
    pairs.forEach(function (w, i) {
      cards.push({ t: 'en', id: i, word: w });
      cards.push({ t: 'cn', id: i, word: w });
    });
    this.cards = shuffle(cards);
    this.emit({
      type: 'board',
      level: st.lv,
      cards: this.cards,
      total: st.total_pairs,
      levelName: (level && level.name) || ''
    });
    return this.cards;
  },

  pick: function (card) {
    var st = this.state;
    if (!st.playing || !card) return null;
    var level = this.levels[st.lv];
    if (!level || !level.words[card.id]) return null;

    if (st.sel) {
      var prev = st.sel.card;
      var sameCard = prev.t === card.t && prev.id === card.id;

      if (sameCard) {
        this.emit({ type: 'repeat', word: card.word, card: card });
        return null;
      }

      if (prev.t === card.t) {
        st.sel = { id: card.id, card: card };
        this.emit({
          type: 'switch',
          word: card.word,
          card: card,
          prevCard: prev,
          prevSide: prev.t,
          side: card.t
        });
        return null;
      }

      var enCard = prev.t === 'en' ? prev : card;
      var cnCard = prev.t === 'cn' ? prev : card;

      if (st.sel.id === card.id) {
        var gain = PAIR_SCORE + Math.min(st.combo, COMBO_CAP) * COMBO_STEP;
        st.combo++;
        if (st.combo > st.best) st.best = st.combo;
        st.score += gain;
        st.matched++;
        this.emit({
          type: 'match',
          word: card.word,
          gain: gain,
          combo: st.combo,
          enCard: enCard,
          cnCard: cnCard
        });
        st.sel = null;
        if (st.matched >= st.total_pairs) this.levelClear();
        return { type: 'match', gain: gain };
      }

      /* 配错：记下「哪个英文词被配上了哪个中文」，导出时做错词榜 */
      st.combo = 0;
      st.wrong++;
      st.score = Math.max(0, st.score - MISS_SCORE);
      st.deadline -= MISS_TIME * 1000;
      st.timeLeft = Math.max(0, (st.deadline - Date.now()) / 1000);
      st.wrongLog.push({
        en: enCard.word.en,
        cn: cnCard.word.cn,
        level: st.lv,
        levelName: (level && level.name) || ''
      });
      this.emit({
        type: 'miss',
        timeLeft: st.timeLeft,
        enCard: enCard,
        cnCard: cnCard
      });
      st.sel = null;
      return { type: 'miss' };
    }

    st.sel = { id: card.id, card: card };
    this.emit({ type: 'select', word: card.word, card: card, side: card.t });
    return null;
  },

  tick: function () {
    var st = this.state;
    if (!st.playing) return null;
    st.timeLeft = (st.deadline - Date.now()) / 1000;
    if (st.timeLeft <= 0) {
      st.timeLeft = 0;
      this.timeUp();
      return { type: 'timeUp' };
    }
    return { type: 'tick', timeLeft: st.timeLeft };
  },

  levelClear: function () {
    var st = this.state;
    if (!st.playing) return;
    st.playing = false;
    var bonus = Math.floor(st.timeLeft) * TIME_BONUS;
    st.score += bonus;
    var nextBonus = Math.min(LEVEL_BONUS_MAX, Math.floor(st.timeLeft / 2));
    var nextLimit = Math.min(st.limit + nextBonus, LEVEL_LIMIT_MAX);
    this.recordLevel();
    this.emit({
      type: 'levelClear',
      score: st.score,
      bonus: bonus,
      best: st.best,
      nextBonus: nextBonus,
      nextLimit: nextLimit,
      hasNext: st.lv < this.levels.length - 1,
      stats: st.levelStats[st.levelStats.length - 1]
    });
  },

  timeUp: function () {
    var st = this.state;
    if (!st.playing) return;
    st.playing = false;
    this.recordLevel();
    this.emit({
      type: 'timeUp',
      score: st.score,
      stats: st.levelStats[st.levelStats.length - 1],
      hasNext: st.lv < this.levels.length - 1
    });
  },

  next: function () {
    var st = this.state;
    if (st.lv >= this.levels.length - 1) return false;
    st.lv++;
    var nextBonus = Math.min(LEVEL_BONUS_MAX, Math.floor(st.timeLeft / 2));
    st.limit = Math.min(st.limit + nextBonus, LEVEL_LIMIT_MAX);
    this.buildBoard();
    return true;
  },

  replay: function () {
    this.buildBoard();
  },

  restart: function () {
    var st = this.state;
    st.lv = 0;
    st.score = 0;
    st.best = 0;
    st.levelStats = [];
    st.wrongLog = [];
    st.limit = this.levelTime;
    this.buildBoard();
  },

  recordLevel: function () {
    var st = this.state;
    st.levelStats.push({
      level: st.lv,
      name: (this.levels[st.lv] && this.levels[st.lv].name) || ('第' + (st.lv + 1) + '关'),
      score: st.score - (st.levelStartScore || 0),
      matched: st.matched,
      total: st.total_pairs,
      wrong: st.wrong,
      bestCombo: st.best,
      duration: Math.round((Date.now() - st.levelStartAt) / 1000)
    });
  },

  report: function () {
    var st = this.state;
    var detail = st.levelStats.slice();
    if (!detail.length) {
      detail.push({
        level: st.lv,
        name: (this.levels[st.lv] && this.levels[st.lv].name) || ('第' + (st.lv + 1) + '关'),
        score: st.score,
        matched: st.matched,
        total: st.total_pairs,
        wrong: st.wrong,
        bestCombo: st.best,
        duration: Math.round((Date.now() - st.levelStartAt) / 1000)
      });
    }
    return {
      score: st.score,
      matched: st.matched,
      total_pairs: st.total_pairs,
      wrong: st.wrong,
      best_combo: st.best,
      duration: Math.round((Date.now() - st.startedAt) / 1000),
      level_count: detail.length,
      detail: detail,
      wrong_log: st.wrongLog.slice()
    };
  },

  emit: function (evt) {
    try {
      this.onEvent(evt);
    } catch (e) {
      /* 界面异常不影响计分 */
    }
  }
};

function shuffle(a) {
  for (var i = a.length - 1; i > 0; i--) {
    var j = Math.floor(Math.random() * (i + 1));
    var t = a[i];
    a[i] = a[j];
    a[j] = t;
  }
  return a;
}

module.exports = {
  Game: Game,
  shuffle: shuffle,
  LEVEL_TIME: LEVEL_TIME,
  LEVEL_BONUS_MAX: LEVEL_BONUS_MAX,
  LEVEL_LIMIT_MAX: LEVEL_LIMIT_MAX,
  PAIR_SCORE: PAIR_SCORE,
  COMBO_STEP: COMBO_STEP,
  COMBO_CAP: COMBO_CAP,
  MISS_TIME: MISS_TIME,
  MISS_SCORE: MISS_SCORE,
  TIME_BONUS: TIME_BONUS
};
