/* ============================================================
   game-ui.js —— 界面层
   ------------------------------------------------------------
   负责把 game-core 的状态画到 DOM 上：HUD、牌面、特效、结算面板。
   不做任何计分计算，也不直接读写后端（成绩由 adapter 负责）。
   ============================================================ */
(function (global) {
  'use strict';

  function $(id) { return document.getElementById(id); }
  function t(key, params) { return WPI18N.t(key, params); }

  /* 后端给关卡起的名字里带中文标记（「Unit 1（2/6） · 含复习」）。中文界面原样显示，
     英文界面把「含复习」和全角括号换成英文写法；单元名本身是教材数据，不翻译。 */
  function levelName(name) {
    name = String(name == null ? '' : name);
    if (WPI18N.lang() !== 'en') return name;
    return name.replace(/含复习/g, t('g_withReview')).replace(/（/g, ' (').replace(/）/g, ')').replace(/\s+/g, ' ').trim();
  }
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
    var key = String(en || '').toLowerCase();
    var legacyKey = slug || slugify(en);
    var embedded = AUDIO[key] || AUDIO[legacyKey];
    if (embedded) {
      try {
        if (!audioCache[key]) {
          var a = new Audio(embedded);
          a.preload = 'auto';
          a.addEventListener('error', function () {
            audioCache[key] = null; toast(t('g_audioEmbeddedFail'));
          });
          audioCache[key] = a;
        }
        var au = audioCache[key];
        if (au) {
          au.pause(); au.currentTime = 0;
          var pr = au.play();
          if (pr && pr.catch) pr.catch(function () { toast(t('g_audioEmbeddedFail')); });
          return true;
        }
      } catch (e) { }
    }
    /* 在线模式：优先用后端 Edge Neural 美式女声；合成失败时由后端回退到 eSpeak。 */
    if (serverAudioBase) {
      try {
        if (!audioCache[key]) {
          var sa = new Audio(serverAudioBase + encodeURIComponent(en));
          sa.preload = 'auto';
          sa.addEventListener('error', function () {
            audioCache[key] = null; toast(t('g_audioServerFail'));
          });
          audioCache[key] = sa;
        }
        var sau = audioCache[key];
        if (sau) {
          sau.pause(); sau.currentTime = 0;
          var spr = sau.play();
          if (spr && spr.catch) spr.catch(function () { toast(t('g_audioServerFail')); });
          return true;
        }
      } catch (e) { }
    }
    if (serverAudioBase || AUDIO[key] || AUDIO[legacyKey]) return false;
    return fallbackSpeak(en);
  }

  /* ---------------- 预取发音（在线版） ----------------
     第一次点英文词时，后端才开始合成，要等几秒。所以选了关就把这一关所有词的
     音频在后台取回来，存成本地 blob；点词时直接播放，不再等服务器。
     * 只在线上版（有 serverAudioBase）才做；离线页的音频已经内嵌。
     * 并发 3 个：后端每个词起一个 edge-tts 进程，容器只有 1 GB，不能一下子全发出去。
     * 换了关就丢掉没开始的队列，只取最新选的那一关；已经在取的让它取完。
     * 失败只忽略：点词时 speak() 会走原来的路径再试一次，提示也在那里。 */
  var PREFETCH_PARALLEL = 3;
  var prefetchQueue = [], prefetchActive = 0, prefetchPending = {};

  function audioKey(en) { return String(en || '').toLowerCase(); }

  function prefetchPump() {
    var win = global;
    while (prefetchActive < PREFETCH_PARALLEL && prefetchQueue.length) {
      var en = prefetchQueue.shift();
      var key = audioKey(en);
      if (audioCache[key] || prefetchPending[key]) continue;
      prefetchPending[key] = true;
      prefetchActive++;
      (function (en, key) {
        win.fetch(serverAudioBase + encodeURIComponent(en), { credentials: 'same-origin' })
          .then(function (r) {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.blob();
          })
          .then(function (blob) {
            if (audioCache[key]) return;      /* 等的时候用户已经点过，别覆盖正在播的 */
            var a = new win.Audio(win.URL.createObjectURL(blob));
            a.preload = 'auto';
            a.addEventListener('error', function () { audioCache[key] = null; });
            audioCache[key] = a;
          })
          .catch(function () { })
          .then(function () {
            delete prefetchPending[key];
            prefetchActive--;
            prefetchPump();
          });
      })(en, key);
    }
  }

  function prefetchWords(words) {
    if (!serverAudioBase || !global.fetch || !global.Audio ||
        !global.URL || !global.URL.createObjectURL) return;
    prefetchQueue = [];
    (words || []).forEach(function (w) {
      var key = audioKey(w && w.en);
      if (key && !audioCache[key] && !prefetchPending[key]) prefetchQueue.push(w.en);
    });
    prefetchPump();
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
    s.className = 'combo'; s.textContent = t('g_combo', { n: n });
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
    UI.panelBuild = null; UI.panelBind = null;
  }
  /* 面板 = 生成 HTML 的函数 + 绑定事件的函数；切换语言时用同一对函数重画开着的面板 */
  function openPanel(ui, build, bind) {
    ui.panelBuild = build; ui.panelBind = bind;
    showPanel(build()); bind();
  }

  /* ---------------- 主对象 ---------------- */
  var UI = {
    cfg: null,
    game: null,
    timer: null,
    started: false,

    /* 预取第 index 关的发音；这一关排在前面，下一关紧跟其后（只在线上版有效）。 */
    prefetchLevel: function (index) {
      var levels = (this.game && this.game.levels) || [];
      var words = [];
      [index, index + 1].forEach(function (i) {
        if (levels[i] && levels[i].words) words = words.concat(levels[i].words);
      });
      prefetchWords(words);
    },

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
        toast(t('g_fullscreenHint'));
      });
      b('btn-replay', function () {
        self.game.replay(); toast(t('g_levelReset'));
      });
      b('btn-restart', function () {
        self.finish();                 /* 先把这一局的成绩存下来 */
        self.stopTimer();
        self.game.restart();
        self.showHome();
      });

      window.addEventListener('resize', function () { self.layoutCols(); });
      /* 页面切到后台（切标签页、锁屏）时暂停计时，回来再继续，不让玩家白白被扣时间 */
      document.addEventListener('visibilitychange', function () {
        if (document.hidden) self.game.pause();
        else if (self.game.resume()) self.render();
      });
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
      var picked = 0, touched = false;

      var build = function () {
        /* 词条数按题库里的真实词数算（关卡里的「复习」词不重复计入） */
        var total = cfg.wordTotal || g.levels.reduce(function (n, l) { return n + l.words.length; }, 0);
        var btns = '';
        g.levels.forEach(function (L, i) {
          btns += '<button data-l="' + i + '"' + (touched && i === picked ? ' class="on"' : '') + '>' +
            esc(t('g_levelBtn', { n: i + 1, name: levelName(L.name), words: L.words.length })) + '</button>';
        });
        var html = '<h1>' + esc(cfg.title || t('g_defaultTitle')) + '</h1>' +
          '<p>' + esc(cfg.subtitle || '') + '<br>' + esc(t('g_totals', { total: total, levels: g.levels.length })) + '</p>' +
          self.rulesHtml() +
          '<div class="lvhead" style="text-align:center">' +
          esc(t(cfg.pickUnit ? 'g_pickUnit' : 'g_pickLevel')) + '</div>' +
          '<div class="lvbtn" id="lvpick">' + btns + '</div>' +
          (cfg.homeExtra || '') +
          '<button class="btn gold" id="ov-start" style="margin-top:14px">' + esc(t('g_start')) + '</button>' +
          '<div style="display:flex;gap:8px;margin-top:8px">' +
          '<button class="btn ghost" id="ov-list">' + esc(t('g_wordList')) + '</button>';
        if (cfg.backHref) {
          html += '<button class="btn ghost" id="ov-back">' + esc(t('g_back')) + '</button>';
        }
        return html + '</div>';
      };

      var bind = function () {
        var lp = $('lvpick');
        lp.onclick = function (ev) {
          var b2 = ev.target.closest('button');
          if (!b2) return;
          picked = +b2.getAttribute('data-l');
          touched = true;
          self.prefetchLevel(picked);
          Array.prototype.forEach.call(lp.children, function (x) { x.classList.remove('on'); });
          b2.classList.add('on');
        };
        $('ov-start').onclick = function () {
          hidePanel();
          self.finished = false;
          g.state.score = 0; g.state.best = 0; g.state.levelStats = [];
          g.state.limit = g.levelTime;
          self.prefetchLevel(picked);
          g.start(picked);
        };
        $('ov-list').onclick = function () { self.showList(); };
        var back = $('ov-back');
        if (back) back.onclick = function () { location.href = cfg.backHref; };
      };

      openPanel(this, build, bind);
    },

    /* ---- 玩法 / 词表 ---- */

    /* 玩法说明只留学生真正要问的四件事：配什么、怎么点、怎么算分、时间怎么算。
       首页速览和「玩法」面板共用这一份文案，改一处就够了。 */
    rulesHtml: function () {
      return '<div class="rule">' +
        '<div><b>' + esc(t('g_ruleGoalLabel')) + '</b>: ' + esc(t('g_ruleGoal')) + '</div>' +
        '<div><b>' + esc(t('g_ruleTapLabel')) + '</b>: ' + esc(t('g_ruleTap')) + '</div>' +
        '<div><b>' + esc(t('g_ruleScoreLabel')) + '</b>: ' + esc(t('g_ruleScore')) + '</div>' +
        '<div><b>' + esc(t('g_ruleTimeLabel')) + '</b>: ' + esc(t('g_ruleTime', { sec: this.game.levelTime })) + '</div>' +
        '</div>';
    },

    showHelp: function () {
      var self = this;
      openPanel(this, function () {
        return '<h2>' + esc(t('g_helpTitle')) + '</h2>' +
          self.rulesHtml() +
          '<div style="display:flex;gap:8px;margin-top:12px">' +
          '<button class="btn ghost" id="ov-close">' + esc(t('g_gotIt')) + '</button>' +
          '<button class="btn" id="ov-list">' + esc(t('g_wordList')) + '</button></div>';
      }, function () {
        $('ov-close').onclick = hidePanel;
        $('ov-list').onclick = function () { self.showList(); };
      });
    },

    showList: function () {
      var g = this.game;
      openPanel(this, function () {
        var html = '<h2>' + esc(t('g_listTitle')) + '</h2><p style="font-size:12.5px">' + esc(t('g_listHint')) + '</p><div class="list">';
        g.levels.forEach(function (L, i) {
          html += '<div class="lvhead">' + esc(t('g_levelHead', { n: i + 1, name: levelName(L.name) })) + '</div>';
          L.words.forEach(function (w) {
            html += '<div class="item" data-en="' + esc(w.en) + '">' +
              '<span class="e">' + esc(w.en) + '</span>' +
              (w.ipa ? '<span class="i">' + esc(w.ipa) + '</span>' : '') +
              '<span class="c">' + esc(w.cn) + '</span></div>';
          });
        });
        return html + '</div><button class="btn" id="ov-close">' + esc(t('g_close')) + '</button>';
      }, function () {
        $('panel').onclick = function (ev) {
          var it = ev.target.closest('.item');
          if (!it) return;
          speak(it.getAttribute('data-en'));
        };
        $('ov-close').onclick = hidePanel;
      });
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
            '<span class="tag">' + esc(t('g_tagCn')) + '</span><div class="w">' + esc(w.cn) + '</div></div>';
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
      set('s-total', t('g_totalScore', { n: st.score }));
      var tb = $('s-timebox');
      if (tb) tb.classList.toggle('warn', st.timeLeft <= 10 && st.playing);
      var bar = $('s-bar');
      if (bar) bar.style.width = (st.total_pairs ? st.matched / st.total_pairs * 100 : 0) + '%';
      var tip = $('s-tip');
      if (tip) {
        tip.textContent = this.cfg.tip || t('g_tip');
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
      var lv = st.lv, total = st.total_pairs;

      var build = function () {
        var homeLabel = t(self.cfg.backHref ? 'g_back' : 'g_toLevels');
        var html = '<h2>' + esc(t('g_clearTitle', { n: lv + 1 })) + '</h2>' +
          '<div class="big">' + evt.score + '</div>' +
          '<div class="kv"><span>' + esc(t('g_levelMatched')) + '</span><b>' + total + ' / ' + total + '</b></div>' +
          '<div class="kv"><span>' + esc(t('g_timeBonus')) + '</span><b>' + esc(t('g_bonusPts', { n: evt.bonus })) + '</b></div>' +
          '<div class="kv"><span>' + esc(t('g_bestCombo')) + '</span><b>x' + evt.best + '</b></div>';
        if (hasNext) {
          html += '<p>' + esc(t('g_nextTime', { limit: evt.nextLimit, bonus: evt.nextBonus })) + '</p>' +
            '<button class="btn gold" id="ov-next" style="margin-top:12px">' + esc(t('g_nextLevel', { n: lv + 2 })) + '</button>';
        } else {
          html += '<p style="font-size:16px;color:#f0801a;font-weight:800">' + esc(t('g_allClear', { score: evt.score })) + '</p>' +
            '<button class="btn gold" id="ov-next" style="margin-top:12px">' + esc(t('g_playAgain')) + '</button>';
        }
        return html + '<div style="display:flex;gap:8px;margin-top:8px">' +
          '<button class="btn ghost" id="ov-replay">' + esc(t('g_replay')) + '</button>' +
          '<button class="btn ghost" id="ov-home">' + esc(homeLabel) + '</button></div>';
      };

      var bind = function () {
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
          hidePanel(); self.finish();
          if (self.cfg.backHref) { location.href = self.cfg.backHref; return; }
          g.restart(); self.showHome();
        };
      };

      openPanel(this, build, bind);
      this.render();
      if (!hasNext) this.finish();
    },

    showTimeUp: function (evt) {
      var g = this.game, st = g.state;
      this.stopTimer();
      sfx.lose();
      var self = this;
      var matched = st.matched, total = st.total_pairs, wrong = st.wrong;

      var build = function () {
        var homeLabel = t(self.cfg.backHref ? 'g_back' : 'g_toLevels');
        return '<h2>' + esc(t('g_timeUp')) + '</h2><div class="big">' + evt.score + '</div>' +
          '<div class="kv"><span>' + esc(t('g_levelMatched')) + '</span><b>' + matched + ' / ' + total + '</b></div>' +
          '<div class="kv"><span>' + esc(t('g_wrongCount')) + '</span><b>' + wrong + '</b></div>' +
          '<p>' + esc(t('g_tryAgain')) + '</p>' +
          '<button class="btn gold" id="ov-retry" style="margin-top:10px">' + esc(t('g_replay')) + '</button>' +
          '<div style="margin-top:8px"><button class="btn ghost" id="ov-home">' + esc(homeLabel) + '</button></div>';
      };

      var bind = function () {
        $('ov-retry').onclick = function () { hidePanel(); g.replay(); };
        $('ov-home').onclick = function () {
          hidePanel(); self.finish();
          if (self.cfg.backHref) { location.href = self.cfg.backHref; return; }
          g.restart(); self.showHome();
        };
      };

      openPanel(this, build, bind);
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
        this.prefetchLevel(evt.level);  /* 下一关也顺手取，过关后不用再等 */
        this.renderBoard();
        this.startTimer();
        this.render();
      } else if (evt.type === 'select') {
        var st = this.game.state;
        if (st.sel && st.sel.card && st.sel.card.el) {
          st.sel.card.el.classList.add('sel');
        }
        if (evt.side === 'en') speak(evt.word.en);
        sfx.click();
        /* 中文卡只选择，不朗读；英文卡才播放发音。 */
        if (evt.side === 'cn') toast(t('g_hintCn'));
        this.render();
      } else if (evt.type === 'switch') {
        /* 连点同一侧：换了一个选中，提示该点另一侧了 */
        if (evt.prevCard && evt.prevCard.el) {
          evt.prevCard.el.classList.remove('sel');
        }
        if (evt.card && evt.card.el) evt.card.el.classList.add('sel');
        if (evt.side === 'en') speak(evt.word.en);
        sfx.click();
        toast(t(evt.prevSide === 'en' ? 'g_hintEn' : 'g_hintCnSwitch'));
        if (evt.card && evt.card.el) {
          evt.card.el.classList.add('hint');
          setTimeout(function () { evt.card.el.classList.remove('hint'); }, 1000);
        }
        this.render();
      } else if (evt.type === 'repeat') {
        if (evt.card && evt.card.t === 'en') speak(evt.word.en);
        sfx.click();
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
        toast(t('g_wrong'));
        this.render();
      } else if (evt.type === 'levelClear') {
        setTimeout(function () { self.showLevelClear(evt); }, 520);
      } else if (evt.type === 'timeUp') {
        this.showTimeUp(evt);
      }
    }
  };

  /* 给测试用：不经过 init（它要整页 DOM），直接设音频地址、喂词、看缓存 */
  UI._test = {
    levelName: levelName,
    setBase: function (b) { serverAudioBase = b; },
    prefetch: prefetchWords,
    cache: audioCache
  };
  /* 切换语言：状态栏、牌面上的「中 / CN」标签、开着的面板（首页 / 通关 / 玩法 / 词表）都重画 */
  WPI18N.onChange(function () {
    if (UI.game && UI.cfg) UI.render();
    Array.prototype.forEach.call(document.querySelectorAll('.card.cn .tag'), function (el) {
      el.textContent = t('g_tagCn');
    });
    var overlay = $('overlay');
    if (UI.panelBuild && overlay && overlay.classList.contains('on')) {
      var keepScroll = $('panel') ? $('panel').scrollTop : 0;
      showPanel(UI.panelBuild());
      UI.panelBind();
      if ($('panel')) $('panel').scrollTop = keepScroll;
    }
  });

  global.WPGameUI = UI;
})(window);
