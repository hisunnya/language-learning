/* ============================================================
   game-core.js —— 纯运算层（移植自 word-puzzle/web/js/game-core.js）
   ------------------------------------------------------------
   只负责「关卡 / 计分 / 计时 / 连击」这些计算，不碰 DOM、不碰存储、
   不碰网络，也不碰任何小程序 API。界面层自己订阅 onEvent 来画。
   相比网站版唯一的新增是 wrongLog：记录每次配错的英文词与选错的中文，
   导出成绩时可以直接统计「错词榜」。
   ============================================================ */

var LEVEL_TIME = 60;
var LEVEL_BONUS_MAX = 0;
var LEVEL_LIMIT_MAX = LEVEL_TIME + LEVEL_BONUS_MAX;
var PAIR_SCORE = 20;
var COMBO_STEP = 2;
var COMBO_CAP = 7;
var MISS_TIME = 3;
var MISS_SCORE = 4;
var TIME_BONUS = 0.2;

function Game(opts) {
  opts = opts || {};
  this.levels = opts.levels || [];
  this.levelTime = opts.levelTime || LEVEL_TIME;
  this.onEvent = opts.onEvent || function () {};
  this.policy = {};
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
    paused: false,
    pausedLeft: 0,
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
    st.limit = this.policy.time_limit || Math.max(1, Math.round(this.levelTime * (this.policy.time_factor || 1)));
    st.pairStates = pairs.map(function (_, i) { return { ord: i, solved: false, wrong: 0 }; });
    st.comboEvents = [];
    st.secondsAdded = 0;
    st.comboBonus = 0;
    st.rawScore = 0;
    st.endedAt = 0;
    st.roundRecorded = false;
    st.best = 0;
    st.wrongLog = [];
    st.matched = 0;
    st.sel = null;
    st.combo = 0;
    st.wrong = 0;
    st.timeLeft = st.limit;
    st.playing = true;
    st.paused = false;
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
    if (!st.playing || st.paused || !card) return null;
    if (this.tick() && !st.playing) return null;
    var level = this.levels[st.lv];
    if (!level || !level.words[card.id]) return null;
    if (st.pairStates[card.id].solved) return null;

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
        var eligible = !st.pairStates[card.id].wrong;
        st.combo = eligible ? st.combo + 1 : 0;
        var extra = PAIR_SCORE * [0, 0, .1, .2, .4, .6, .8, 1][Math.min(7, st.combo)];
        var gain = PAIR_SCORE + extra;
        var seconds = st.combo < 2 ? 0 : st.combo < 5 ? 1 : 2;
        seconds = Math.max(0, Math.min(seconds, Math.min(10, Math.floor(st.limit * .2)) - st.secondsAdded));
        st.secondsAdded += seconds;
        st.deadline += seconds * 1000;
        st.comboBonus += extra;
        st.comboEvents.push({ ord: card.id, eligible: eligible });
        st.pairStates[card.id].solved = true;
        if (st.combo > st.best) st.best = st.combo;
        st.rawScore += gain;
        st.score = st.levelStartScore + Math.round(st.rawScore * (this.policy.score_factor == null ? 1 : this.policy.score_factor));
        st.matched++;
        this.emit({
          type: 'match',
          word: card.word,
          gain: gain,
          combo: st.combo,
          seconds: seconds,
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
      st.pairStates[enCard.id].wrong++;
      st.comboEvents.push({ ord: enCard.id, eligible: false, break: true });
      st.rawScore = Math.max(0, st.rawScore - MISS_SCORE);
      st.score = st.levelStartScore + Math.round(st.rawScore * (this.policy.score_factor == null ? 1 : this.policy.score_factor));
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
    if (!st.playing || st.paused) return null;
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
    st.timeLeft = Math.max(0, (st.deadline - Date.now()) / 1000);
    var bonus = st.rawScore * TIME_BONUS * Math.min(1, st.timeLeft / st.limit);
    st.score = st.levelStartScore + Math.round((st.rawScore + bonus) *
      (this.policy.score_factor == null ? 1 : this.policy.score_factor));
    st.endedAt = Date.now();
    var nextBonus = Math.min(LEVEL_BONUS_MAX, Math.floor(st.timeLeft / 2));
    var nextLimit = Math.min(st.limit + nextBonus, LEVEL_LIMIT_MAX);
    this.recordLevel();
    this.emit({
      type: 'levelClear',
      score: st.score,
      bonus: Math.round(bonus * (this.policy.score_factor == null ? 1 : this.policy.score_factor)),
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
    st.endedAt = Date.now();
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

  // 重玩当前关：这一关里已经拿到的分要收回，否则「拿几分、认输、重玩」可以无限刷分
  replay: function () {
    var st = this.state;
    st.score = st.levelStartScore || 0;
    this.buildBoard();
  },

  // 暂停计时：剩余时间冻结，期间不能点牌
  pause: function () {
    var st = this.state;
    if (!st.playing || st.paused) return false;
    st.paused = true;
    st.pausedLeft = Math.max(0, (st.deadline - Date.now()) / 1000);
    return true;
  },

  // 恢复计时：用冻结时的剩余时间重新算截止点
  resume: function () {
    var st = this.state;
    if (!st.paused) return false;
    st.paused = false;
    st.deadline = Date.now() + st.pausedLeft * 1000;
    return true;
  },

  restart: function () {
    var st = this.state;
    st.lv = 0;
    st.score = 0;
    st.best = 0;
    st.levelStats = [];
    st.wrongLog = [];
    st.startedAt = 0;
    st.limit = this.levelTime;
    this.buildBoard();
  },

  elapsed: function () {
    var st = this.state;
    if (!st.startedAt) return 0;
    return Math.min(st.limit + (st.secondsAdded || 0),
      Math.max(0, Math.round(((st.endedAt || Date.now()) - st.startedAt) / 1000)));
  },

  recordLevel: function () {
    var st = this.state;
    if (st.roundRecorded || !st.startedAt) return;
    st.roundRecorded = true;
    st.levelStats.push({
      level: st.lv,
      name: (this.levels[st.lv] && this.levels[st.lv].name) || ('第' + (st.lv + 1) + '关'),
      score: st.score - (st.levelStartScore || 0),
      matched: st.matched,
      total: st.total_pairs,
      wrong: st.wrong,
      bestCombo: st.best,
      duration: this.elapsed(),
      answers: st.pairStates.map(function (s) { return Object.assign({}, s); })
    });
  },

  report: function () {
    var st = this.state;
    var detail = st.roundRecorded ? st.levelStats.slice(-1) : [];
    if (!detail.length) {
      detail.push({
        level: st.lv,
        name: (this.levels[st.lv] && this.levels[st.lv].name) || ('第' + (st.lv + 1) + '关'),
        score: st.score - st.levelStartScore,
        matched: st.matched,
        total: st.total_pairs,
        wrong: st.wrong,
        bestCombo: st.best,
        duration: this.elapsed(),
        answers: (st.pairStates || []).map(function (s) { return Object.assign({}, s); })
      });
    }
    return {
      score: st.score - st.levelStartScore,
      level: st.lv,
      rule_version: 4,
      play_token: this.policy.play_token || '',
      combo_events: (st.comboEvents || []).slice(),
      initial_seconds: st.limit,
      time_left: st.timeLeft,
      bonus_seconds: st.secondsAdded || 0,
      combo_bonus: st.comboBonus || 0,
      matched: st.matched,
      total_pairs: st.total_pairs,
      wrong: st.wrong,
      best_combo: st.best,
      duration: this.elapsed(),
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
