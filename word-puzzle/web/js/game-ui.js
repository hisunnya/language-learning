/* ============================================================
   game-ui.js —— 界面层
   ------------------------------------------------------------
   负责把 game-core 的状态画到 DOM 上：HUD、牌面、特效、结算面板。
   不做任何计分计算，也不直接读写后端（成绩由 adapter 负责）。
   ============================================================ */
(function (global) {
  'use strict';

  function $(id) { return document.getElementById(id); }
  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }
  function slugify(s) {
    return String(s).toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '');
  }
  function fmtTime(sec) {
    sec = Math.max(0, Math.ceil(sec));
    var m = Math.floor(sec / 60), s = sec % 60;
    return (m < 10 ? '0' : '') + m + ':' + (s < 10 ? '0' : '') + s;
  }

  /* ---------------- 音效（WebAudio 合成，无外部文件） ---------------- */
  var ac = null;
  function beep(freqs, dur, type, vol) {
    try {
      if (!ac) ac = new (window.AudioContext || window.webkitAudioContext)();
      if (ac.state === 'suspended') ac.resume();
      freqs.forEach(function (f, i) {
        var o = ac.createOscillator(), g = ac.createGain();
        var t0 = ac.currentTime + i * dur * 0.62;
        o.type = type || 'sine'; o.frequency.value = f;
        g.gain.setValueAtTime(0.0001, t0);
        g.gain.exponentialRampToValueAtTime(vol || 0.18, t0 + 0.012);
        g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
        o.connect(g); g.connect(ac.destination);
        o.start(t0); o.stop(t0 + dur + 0.02);
      });
    } catch (e) { /* 浏览器不支持就静音 */ }
  }
  var sfx = {
    right: function () { beep([784, 1046.5], 0.16, 'triangle', 0.16); },
    wrong: function () { beep([180, 120], 0.16, 'sawtooth', 0.09); },
    combo: function (n) { beep([880 + Math.min(n, 8) * 60, 1174 + Math.min(n, 8) * 80], 0.14, 'triangle', 0.15); },
    win: function () { beep([523, 659, 784, 1046], 0.22, 'triangle', 0.16); },
    lose: function () { beep([392, 330, 262], 0.24, 'sine', 0.14); },
    click: function () { beep([660], 0.07, 'sine', 0.07); }
  };

  /* ---------------- 朗读 ---------------- */
  var audioCache = {};
  var AUDIO = {};   /* 可选：slug -> data URI；没有就走浏览器 TTS */

  /* --- 美式女声优先 ---
     浏览器的 speechSynthesis 音色由操作系统决定，默认可能落到
     男声、英式（en-GB）甚至中文音色上。所以显式挑选：
     1) 语言必须是 en-US；
     2) 名字里带常见女声标识的优先（Female / Woman / Samantha / Zira ...）；
     3) 都找不到就退回任意 en-US 音色。
  */
  var FEMALE_HINTS = [
    'female', 'woman', 'samantha', 'zira', 'aria', 'jenny', 'victoria',
    'allison', 'ava', 'serena', 'fiona', 'moira', 'karen', 'tessa',
    'susan', 'zoe', 'catherine', 'carla', 'jessa', 'nicky', 'hazel',
    'sonia', 'libby', 'natasha', 'michelle', 'heera', 'linda', 'mary',
    'paulina', 'salli', 'shelley', 'kendra', 'joanna', 'sally', 'amy',
    'emma', 'nicole', 'kate', 'bella', 'claire', 'camila'
  ];

  var voicesCache = null;
  var serverAudio = {};   /* slug -> data URI（离线页内嵌的音频） */
  var serverAudioBase = '';  /* 非空则改用后端 /api/audio 渲染 */

  function loadVoices() {
    if (voicesCache && voicesCache.length) return voicesCache;
    try {
      voicesCache = (window.speechSynthesis &&
                     window.speechSynthesis.getVoices()) || [];
    } catch (e) {
      voicesCache = [];
    }
    return voicesCache;
  }

  /* Chrome / Edge 的音色是异步加载的，第一次 getVoices() 往往是空的。
     监听 voiceschanged，拿到之后重新缓存。 */
  function watchVoices() {
    try {
      if (!window.speechSynthesis ||
          window.speechSynthesis.addEventListener) {
        if (window.speechSynthesis) {
          window.speechSynthesis.addEventListener('voiceschanged', function () {
            voicesCache = null;      /* 强制下次重新读 */
            loadVoices();
          });
        }
      }
    } catch (e) { }
  }
  watchVoices();

  function isFemaleName(name) {
    var low = String(name || '').toLowerCase();
    for (var i = 0; i < FEMALE_HINTS.length; i++) {
      if (low.indexOf(FEMALE_HINTS[i]) >= 0) return true;
    }
    return false;
  }

  /** 挑一个 en-US 的女声音色。 */
  function pickVoice() {
    var all = loadVoices();
    if (!all.length) return null;
    var us = [], usFemale = [];
    for (var i = 0; i < all.length; i++) {
      var v = all[i];
      var lang = String(v.lang || '').replace('_', '-').toLowerCase();
      if (lang.indexOf('en-us') !== 0) continue;
      us.push(v);
      if (isFemaleName(v.name)) usFemale.push(v);
    }
    if (usFemale.length) {
      // 优先本地音色（不用联网），其次原始顺序
      for (var j = 0; j < usFemale.length; j++) {
        if (usFemale[j].localService) return usFemale[j];
      }
      return usFemale[0];
    }
    return us.length ? us[0] : null;
  }

  function fallbackSpeak(en) {
    try {
      if (window.speechSynthesis) {
        var u = new SpeechSynthesisUtterance(en);
        u.lang = 'en-US'; u.rate = 0.85;
        var v = pickVoice();
        if (v) { u.voice = v; u.lang = v.lang || 'en-US'; }
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(u);
        return true;
      }
    } catch (e) { }
    return false;
  }

  function speak(en, slug) {
    var key = slug || slugify(en);
    if (AUDIO[key]) {
      try {
        if (!audioCache[key]) {
          var a = new Audio(AUDIO[key]);
          a.preload = 'auto';
          a.addEventListener('error', function () {
            audioCache[key] = null; fallbackSpeak(en);
          });
          audioCache[key] = a;
        }
        var au = audioCache[key];
        if (au) {
          au.pause(); au.currentTime = 0;
          var pr = au.play();
          if (pr && pr.catch) pr.catch(function () { fallbackSpeak(en); });
          return true;
        }
      } catch (e) { }
    }
    /* 在线模式：优先用后端渲染的美式女声音频（espeak-ng en-us+f3），
       这样所有学生听到的都一样，也不受客户端音色影响。 */
    if (serverAudioBase) {
      try {
        if (!audioCache[key]) {
          var sa = new Audio(serverAudioBase + encodeURIComponent(en));
          sa.preload = 'auto';
          sa.addEventListener('error', function () {
            audioCache[key] = null; fallbackSpeak(en);
          });
          audioCache[key] = sa;
        }
        var sau = audioCache[key];
        if (sau) {
          sau.pause(); sau.currentTime = 0;
          var spr = sau.play();
          if (spr && spr.catch) spr.catch(function () { fallbackSpeak(en); });
          return true;
        }
      } catch (e) { }
    }
    return fallbackSpeak(en);
  }

  /* ---------------- 特效 ---------------- */
  var fx = null, toastTimer = null;

  function toast(msg) {
    var t = $('toast');
    if (!t) return;
    t.textContent = msg; t.classList.add('on');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { t.classList.remove('on'); }, 1600);
  }

  function burst(card) {
    if (!fx || !card) return;
    var r = card.getBoundingClientRect();
    var cx = r.left + r.width / 2, cy = r.top + r.height / 2;
    var emo = ['✨', '⭐', '🎉', '💫', '🌟', '🎈'];
    for (var i = 0; i < 14; i++) {
      var s = document.createElement('span');
      s.className = 'pt';
      s.textContent = emo[i % emo.length];
      var ang = (Math.PI * 2 / 14) * i + Math.random() * 0.5;
      var dist = 40 + Math.random() * 70;
      s.style.left = cx + 'px'; s.style.top = cy + 'px';
      s.style.setProperty('--dx', Math.cos(ang) * dist + 'px');
      s.style.setProperty('--dy', Math.sin(ang) * dist + 'px');
      s.style.setProperty('--rot', (Math.random() * 360 - 180) + 'deg');
      s.style.fontSize = (15 + Math.random() * 12) + 'px';
      fx.appendChild(s);
      (function (n) { setTimeout(function () { n.remove(); }, 760); })(s);
    }
  }

  function floatPlus(card, txt) {
    if (!fx || !card) return;
    var r = card.getBoundingClientRect();
    var s = document.createElement('div');
    s.className = 'plus'; s.textContent = txt;
    s.style.left = (r.left + r.width / 2) + 'px';
    s.style.top = (r.top + r.height / 2) + 'px';
    fx.appendChild(s); setTimeout(function () { s.remove(); }, 1050);
  }

  function showCombo(n) {
    if (!fx) return;
    var s = document.createElement('div');
    s.className = 'combo'; s.textContent = '连击 x' + n;
    fx.appendChild(s); setTimeout(function () { s.remove(); }, 1050);
  }

  /* ---------------- 面板 ---------------- */
  function showPanel(html) {
    var p = $('panel'); if (!p) return;
    p.innerHTML = html; p.onclick = null;
    $('overlay').classList.add('on');
  }
  function hidePanel() {
    var o = $('overlay'); if (o) o.classList.remove('on');
  }

  /* ---------------- 主对象 ---------------- */
  var UI = {
    cfg: null,
    game: null,
    timer: null,
    started: false,

    init: function (cfg) {
      this.cfg = cfg;
      this.game = cfg.game;
      this.finished = false;
      fx = $('fx');

      /* 音频来源：
         - cfg.audio        内嵌的 slug -> data URI
         - cfg.audioBase    后端渲染地址（在线版，形如 /api/audio/ ）
         两者都没有就退回浏览器 TTS（挑 en-US 女声）。 */
      if (cfg.audio) AUDIO = cfg.audio;
      if (cfg.audioBase) serverAudioBase = cfg.audioBase;
      if (cfg.voice) {
        try {
          var vv = pickVoice();
          if (vv) { voicesCache = [vv]; }
        } catch (e) { }
      }

      var self = this;
      /* core 发的事件 → 界面动画 */
      this.game.onEvent = function (evt) { self.onEvent(evt); };

      /* 牌面点击 */
      var board = $('board');
      board.addEventListener('click', function (ev) {
        var el = ev.target.closest('.card');
        if (!el) return;
        var t = el.getAttribute('data-t');
        var id = +el.getAttribute('data-id');
        self.onCard(t, id, el);
      });

      /* 底部按钮 */
      var b = function (id, fn) { var e = $(id); if (e) e.onclick = fn; };
      b('btn-help', function () { self.showHelp(); });
      b('btn-full', function () {
        try {
          var el = document.documentElement;
          var rq = el.requestFullscreen || el.webkitRequestFullscreen || el.msRequestFullscreen;
          if (rq) { rq.call(el); return; }
        } catch (e) { }
        toast('请用浏览器菜单选择"全屏"');
      });
      b('btn-replay', function () {
        self.game.replay(); toast('本关已重置');
      });
      b('btn-restart', function () {
        self.finish();                 /* 先把这一局的成绩存下来 */
        self.stopTimer();
        self.game.restart();
        self.showHome();
      });

      window.addEventListener('resize', function () { self.layoutCols(); });
      document.addEventListener('touchmove', function (e) {
        if (e.touches.length > 1) e.preventDefault();
      }, { passive: false });

      self.showHome();
      self.render();
      return this;
    },

    /* ---- 首页 ---- */
    showHome: function () {
      this.stopTimer();
      var self = this;
      var cfg = this.cfg;
      var g = this.game;
      g.state.gen++;
      /* 词条数按题库里的真实词数算（关卡里的「复习」词不重复计入） */
      var total = cfg.wordTotal || g.levels.reduce(function (n, l) { return n + l.words.length; }, 0);

      var btns = '';
      g.levels.forEach(function (L, i) {
        btns += '<button data-l="' + i + '">第 ' + (i + 1) + ' 关 · ' +
          esc(L.name) + ' · ' + L.words.length + ' 词</button>';
      });

      var html = '<h1>' + esc(cfg.title || '词境 Lexica') + '</h1>' +
        '<p>' + esc(cfg.subtitle || '') + '<br>共 ' + total + ' 个词条 · ' +
        g.levels.length + ' 关</p>' +
        '<div class="rule">' +
        '<div><b>① 点英文卡片</b>：听发音，卡片高亮选中</div>' +
        '<div><b>② 点对应中文卡片</b>：配对成功，两个卡片一起消失</div>' +
        '<div><b>③ 计分</b>：配对 +100 分，连击额外加分；答错扣 3 秒</div>' +
        '<div><b>④ 时间</b>：每关 ' + g.levelTime + ' 秒，答错再扣 3 秒</div>' +
        '<div><b>⑤ 过关</b>：剩余时间全部折算成奖励分</div>' +
        '</div>' +
        '<div class="lvhead" style="text-align:center">' +
        (cfg.pickUnit ? '选择单元开始' : '选择关卡') + '</div>' +
        '<div class="lvbtn" id="lvpick">' + btns + '</div>' +
        (cfg.homeExtra || '') +
        '<button class="btn gold" id="ov-start" style="margin-top:14px">开始游戏</button>' +
        '<div style="display:flex;gap:8px;margin-top:8px">' +
        '<button class="btn ghost" id="ov-list">查看全部词表</button>';

      if (cfg.backHref) {
        html += '<button class="btn ghost" id="ov-back">返回</button>';
      }
      html += '</div>';

      showPanel(html);

      var picked = 0;
      var lp = $('lvpick');
      lp.onclick = function (ev) {
        var b2 = ev.target.closest('button');
        if (!b2) return;
        picked = +b2.getAttribute('data-l');
        Array.prototype.forEach.call(lp.children, function (x) { x.classList.remove('on'); });
        b2.classList.add('on');
      };
      $('ov-start').onclick = function () {
        hidePanel();
        self.finished = false;
        g.state.score = 0; g.state.best = 0; g.state.levelStats = [];
        g.state.limit = g.levelTime;
        g.start(picked);
      };
      $('ov-list').onclick = function () { self.showList(); };
      var back = $('ov-back');
      if (back) back.onclick = function () { location.href = cfg.backHref; };
    },

    /* ---- 玩法 / 词表 ---- */
    showHelp: function () {
      var self = this;
      var g = this.game;
      showPanel('<h2>玩法说明</h2>' +
        '<div class="rule">' +
        '<div><b>目标</b>：把英文卡片和中文意思配成一对</div>' +
        '<div><b>点英文</b>：朗读发音并选中该卡</div>' +
        '<div><b>点中文</b>：配对成功 → 星星特效 + 两张卡消失</div>' +
        '<div><b>答错</b>：卡片抖动，扣 3 秒、扣 20 分，连击清零</div>' +
        '<div><b>得分</b>：每对 +100，连击每级 +20（最高 +100）</div>' +
        '<div><b>过关</b>：剩余每秒折算 10 分奖励，下一关时间更长</div>' +
        '<div><b>时间</b>：每关 ' + g.levelTime + ' 秒，答错扣 3 秒</div>' +
        '</div>' +
        '<div style="display:flex;gap:8px;margin-top:12px">' +
        '<button class="btn ghost" id="ov-close">知道了</button>' +
        '<button class="btn" id="ov-list">查看全部词表</button></div>');
      $('ov-close').onclick = hidePanel;
      $('ov-list').onclick = function () { self.showList(); };
    },

    showList: function () {
      var self = this;
      var g = this.game;
      var html = '<h2>词汇表</h2><p style="font-size:12.5px">点任意一行可朗读该词</p><div class="list">';
      g.levels.forEach(function (L, i) {
        html += '<div class="lvhead">第 ' + (i + 1) + ' 关 · ' + esc(L.name) + '</div>';
        L.words.forEach(function (w) {
          html += '<div class="item" data-en="' + esc(w.en) + '">' +
            '<span class="e">' + esc(w.en) + '</span>' +
            (w.ipa ? '<span class="i">' + esc(w.ipa) + '</span>' : '') +
            '<span class="c">' + esc(w.cn) + '</span></div>';
        });
      });
      html += '</div><button class="btn" id="ov-close">关闭</button>';
      showPanel(html);
      $('panel').onclick = function (ev) {
        var it = ev.target.closest('.item');
        if (!it) return;
        speak(it.getAttribute('data-en'));
      };
      $('ov-close').onclick = hidePanel;
    },

    /* ---- 牌面（只把点击转交给 core，计分全在 core 里） ---- */
    onCard: function (t, id, el) {
      var g = this.game;
      if (!g.state.playing) return;
      var level = g.levels[g.state.lv];
      if (!level || !level.words[id]) return;
      g.pick({ t: t, id: id, el: el, word: level.words[id] });
    },

    renderBoard: function () {
      var g = this.game;
      var board = $('board');
      if (!board) return;
      var html = '';
      g.cards.forEach(function (c) {
        var w = c.word;
        if (c.t === 'en') {
          html += '<div class="card en" data-id="' + c.id + '" data-t="en">' +
            '<span class="tag">EN</span><div class="w">' + esc(w.en) + '</div>' +
            (w.ipa ? '<div class="ipa">' + esc(w.ipa) + '</div>' : '') +
            '<span class="say">🔊</span></div>';
        } else {
          html += '<div class="card cn" data-id="' + c.id + '" data-t="cn">' +
            '<span class="tag">中</span><div class="w">' + esc(w.cn) + '</div></div>';
        }
      });
      board.innerHTML = html;
      this.layoutCols();
    },

    layoutCols: function () {
      var b = $('board');
      if (!b) return;
      var w = b.clientWidth || window.innerWidth;
      var cols = w < 360 ? 2 : (w < 520 ? 3 : (w < 760 ? 4 : (w < 980 ? 5 : 6)));
      b.style.gridTemplateColumns = 'repeat(' + cols + ',1fr)';
    },

    render: function () {
      var st = this.game.state;
      var set = function (id, v) { var e = $(id); if (e) e.textContent = v; };
      set('s-level', (st.lv + 1) + '/' + this.game.levels.length);
      set('s-time', fmtTime(st.timeLeft));
      set('s-prog', st.matched + '/' + st.total_pairs);
      set('s-score', st.score);
      set('s-combo', st.combo);
      set('s-total', '总分 ' + st.score);
      var tb = $('s-timebox');
      if (tb) tb.classList.toggle('warn', st.timeLeft <= 10 && st.playing);
      var bar = $('s-bar');
      if (bar) bar.style.width = (st.total_pairs ? st.matched / st.total_pairs * 100 : 0) + '%';
      var tip = $('s-tip');
      if (tip) {
        tip.textContent = this.cfg.tip ||
          '点英文单词听发音，再点对应中文';
      }
    },

    /* ---- 计时 ---- */
    clearTimer: function () {
      if (this.timer) { clearInterval(this.timer); this.timer = null; }
    },
    startTimer: function () {
      var self = this;
      this.clearTimer();
      this.timer = setInterval(function () {
        var r = self.game.tick();
        if (r && r.type === 'timeUp') return;
        self.render();
      }, 200);
    },
    stopTimer: function () {
      this.clearTimer();
      this.game.state.playing = false;
    },

    /* ---- 结算面板（数据全部来自 core 的事件） ---- */
    showLevelClear: function (evt) {
      var g = this.game, st = g.state;
      this.stopTimer();
      sfx.win();
      var self = this;
      var hasNext = evt.hasNext;

      var html = '<h2>第 ' + (st.lv + 1) + ' 关 通关！</h2>' +
        '<div class="big">' + evt.score + '</div>' +
        '<div class="kv"><span>本关配对</span><b>' + st.total_pairs + ' / ' + st.total_pairs + '</b></div>' +
        '<div class="kv"><span>剩余时间奖励</span><b>+' + evt.bonus + ' 分</b></div>' +
        '<div class="kv"><span>最高连击</span><b>x' + evt.best + '</b></div>';
      if (hasNext) {
        html += '<p>下一关时间：' + evt.nextLimit + ' 秒（奖励 +' + evt.nextBonus + 's）</p>' +
          '<button class="btn gold" id="ov-next" style="margin-top:12px">进入第 ' + (st.lv + 2) + ' 关</button>';
      } else {
        html += '<p style="font-size:16px;color:#f0801a;font-weight:800">全部通关！总分 ' + evt.score + '</p>' +
          '<button class="btn gold" id="ov-next" style="margin-top:12px">再玩一次</button>';
      }
      html += '<div style="display:flex;gap:8px;margin-top:8px">' +
        '<button class="btn ghost" id="ov-replay">重玩本关</button>' +
        '<button class="btn ghost" id="ov-home">回到首页</button></div>';
      showPanel(html);

      $('ov-next').onclick = function () {
        hidePanel();
        if (hasNext) {
          g.next();
        } else {
          g.restart();
          self.showHome();
        }
      };
      $('ov-replay').onclick = function () { hidePanel(); g.replay(); };
      $('ov-home').onclick = function () {
        hidePanel(); self.finish(); g.restart(); self.showHome();
      };
      this.render();
      if (!hasNext) this.finish();
    },

    showTimeUp: function (evt) {
      var g = this.game, st = g.state;
      this.stopTimer();
      sfx.lose();
      var self = this;
      var html = '<h2>时间到！</h2><div class="big">' + evt.score + '</div>' +
        '<div class="kv"><span>本关配对</span><b>' + st.matched + ' / ' + st.total_pairs + '</b></div>' +
        '<div class="kv"><span>答错次数</span><b>' + st.wrong + '</b></div>' +
        '<p>再试一次，把剩下的词都消掉！</p>' +
        '<button class="btn gold" id="ov-retry" style="margin-top:10px">重玩本关</button>' +
        '<div style="margin-top:8px"><button class="btn ghost" id="ov-home">回到首页</button></div>';
      showPanel(html);
      $('ov-retry').onclick = function () { hidePanel(); g.replay(); };
      $('ov-home').onclick = function () {
        hidePanel(); self.finish(); g.restart(); self.showHome();
      };
      this.render();
      this.finish();
    },

    /** 一局结束（全部通关、时间到、或主动退出）→ 交给 adapter 落库 */
    finish: function () {
      if (this.finished) return;
      this.finished = true;
      var report = this.game.report();
      try {
        if (this.cfg.onFinish) this.cfg.onFinish(report);
      } catch (e) { }
    },

    /* ---- 生命周期钩子：只负责动画，不负责计分 ---- */
    onEvent: function (evt) {
      if (!evt) return;
      var self = this;
      if (evt.type === 'board') {
        this.finished = false;         /* 新的一局开始，允许重新记分 */
        this.renderBoard();
        this.startTimer();
        this.render();
      } else if (evt.type === 'select') {
        var st = this.game.state;
        if (st.sel && st.sel.card && st.sel.card.el) {
          st.sel.card.el.classList.add('sel');
        }
        speak(evt.word.en);
        sfx.click();
        this.render();
      } else if (evt.type === 'repeat') {
        speak(evt.word.en);
        sfx.click();
      } else if (evt.type === 'needEnglish') {
        toast('先点一个英文单词，再点中文');
        if (evt.card && evt.card.el) {
          evt.card.el.classList.add('hint');
          setTimeout(function () { evt.card.el.classList.remove('hint'); }, 1000);
        }
      } else if (evt.type === 'match') {
        var enEl = evt.enCard ? evt.enCard.el : null;
        var cnEl = evt.cnCard ? evt.cnCard.el : null;
        if (enEl) enEl.classList.remove('sel');
        sfx.right();
        if (evt.combo >= 2) { sfx.combo(); showCombo(evt.combo); }
        if (enEl) burst(enEl);
        if (cnEl) burst(cnEl);
        if (cnEl) floatPlus(cnEl, '+' + evt.gain);
        if (enEl) enEl.classList.add('matched');
        if (cnEl) cnEl.classList.add('matched');
        setTimeout(function () {
          if (enEl) enEl.style.display = 'none';
          if (cnEl) cnEl.style.display = 'none';
          self.render();
        }, 430);
        this.render();
      } else if (evt.type === 'miss') {
        sfx.wrong();
        var en = evt.enCard ? evt.enCard.el : null;
        var cn = evt.cnCard ? evt.cnCard.el : null;
        [cn, en].forEach(function (e) {
          if (!e) return;
          e.classList.remove('bad'); void e.offsetWidth; e.classList.add('bad');
        });
        if (en) en.classList.remove('sel');
        toast('不对哦，-3 秒');
        this.render();
      } else if (evt.type === 'levelClear') {
        setTimeout(function () { self.showLevelClear(evt); }, 520);
      } else if (evt.type === 'timeUp') {
        this.showTimeUp(evt);
      }
    }
  };

  global.WPGameUI = UI;
})(window);
