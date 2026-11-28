/* ============================================================
   order-ui.js —— 排排坐的页面部分（网站版和离线单文件页共用）
   ------------------------------------------------------------
   WPOrderUI.start(mountEl, cfg)
     cfg.items      这一关的题目（server/items.py 的 order 格式）
     cfg.ords       每道题在整个题库里的序号（读音、录音按它找题）
     cfg.audioUrl   function(i) → 第 i 句整句读音的地址
     cfg.upload     function(i, blob, mime, ms, playToken) → Promise({id, valid, bonus, status, transcript, accuracy})；
                    没有（离线页）= 可以录音、回放，但不评分
     cfg.save       function(report) → Promise<boolean>；失败保留本句及令牌，供原地重试
     cfg.begin      function({level, ords, previous_play_token}) → Promise(单句计分策略)；离线页省略
     cfg.phase      function(playToken, phase) → Promise；通知服务器进入录音 / 评分阶段
     cfg.recording  function(id) → Promise(录音当前评分)；离开当前句后仍可更新旧句的得分
     cfg.progress   function(report) → Promise；及时提交非最终快照，供服务器确认截止前的答题进展
     cfg.playToken  旧离线适配器的备用令牌；线上始终使用 begin 返回的单句令牌
     cfg.backHref   结束页「返回」按钮的地址（可选）
   每句的录音阶段 s.stage：idle → starting（等麦克风）→ recording → stopping（等浏览器交出录音）→ idle（有 take 可回放）
     → uploading → scoring → idle；麦克风被拒绝是 denied，其他打不开的情况是 micError（可以再试）。
     拼句限时 30 秒，答对即冻结；录音阶段最多 120 秒（含权限、重录、回放、上传，接受录音即结束限时）。
     每句只成功保存一次成绩，失败不换句、不换令牌；不等评分时由服务器补记准确分。
     最终保存先提交进展、确认评分阶段，再交成绩。语言切换只重画，不重开时钟或麦克风。
   玩法：点上面的片段放到下面的空位，点下面的片段退回去；全放好了点「检查」。拼对后可以听整句，
   然后录一遍自己的朗读，回放满意了再提交（不满意可以重录）。没有麦克风可以跳过录音，只拿拼接分。
   ============================================================ */
(function (global) {
  'use strict';

  var C = global.WPItemCore;
  var MAX_MS = 30000;
  function t(key, params) { return global.WPI18N ? global.WPI18N.t(key, params) : key; }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function fragHtml(fragment) {
    return (fragment.segs || []).map(function (s) {
      return s[1] ? '<mark class="ig-key">' + esc(s[0]) + '</mark>' : esc(s[0]);
    }).join('');
  }

  /* ---------------- 录音 ---------------- */

  function pickMime() {
    var R = global.MediaRecorder;
    if (!R || !R.isTypeSupported) return '';
    var list = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/ogg;codecs=opus', 'audio/aac'];
    for (var i = 0; i < list.length; i++) if (R.isTypeSupported(list[i])) return list[i];
    return '';
  }

  function Recorder() { this.chunks = []; }
  Recorder.supported = function () {
    return !!(global.navigator && navigator.mediaDevices && navigator.mediaDevices.getUserMedia && global.MediaRecorder);
  };
  Recorder.prototype.start = function (onLevel, onTick, onAutoStop) {
    var self = this;
    return navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } }).then(function (stream) {
      if (self.cancelled) { stream.getTracks().forEach(function (tr) { tr.stop(); }); return; }
      self.stream = stream;
      try {
        var mime = pickMime();
        self.rec = mime ? new MediaRecorder(stream, { mimeType: mime }) : new MediaRecorder(stream);
        self.mime = self.rec.mimeType || mime || 'audio/webm';
        self.chunks = [];
        self.rec.ondataavailable = function (ev) { if (ev.data && ev.data.size) self.chunks.push(ev.data); };
        self.began = Date.now();
        self.rec.start(250);
      } catch (e) {
        stream.getTracks().forEach(function (tr) { tr.stop(); });     /* 录音器起不来：把已经打开的麦克风关掉，再把错误交出去 */
        throw e;
      }
      try {
        var Ctx = global.AudioContext || global.webkitAudioContext;
        self.ctx = new Ctx();
        if (self.ctx.state === 'suspended' && self.ctx.resume) self.ctx.resume().catch(function () { });   /* iOS 上新建的是暂停状态 */
        var source = self.ctx.createMediaStreamSource(stream);
        self.analyser = self.ctx.createAnalyser();
        self.analyser.fftSize = 512;
        source.connect(self.analyser);
        var buf = new Uint8Array(self.analyser.fftSize);
        (function loop() {
          if (!self.analyser) return;
          self.analyser.getByteTimeDomainData(buf);
          var peak = 0;
          for (var i = 0; i < buf.length; i++) peak = Math.max(peak, Math.abs(buf[i] - 128));
          onLevel(Math.min(1, peak / 64));
          self.raf = global.requestAnimationFrame(loop);
        })();
      } catch (e) { /* 没有音量条也能录 */ }
      self.timer = global.setInterval(function () {
        var ms = Date.now() - self.began;
        onTick(ms);
        if (ms >= MAX_MS) onAutoStop();
      }, 200);
    });
  };
  Recorder.prototype.stop = function () {
    var self = this;
    var stoppedMs = Date.now() - self.began;
    global.clearInterval(this.timer);
    if (this.raf) global.cancelAnimationFrame(this.raf);
    this.analyser = null;
    return new Promise(function (resolve) {
      var finish = function () {
        if (self.stream) self.stream.getTracks().forEach(function (tr) { tr.stop(); });      /* 关掉麦克风（手机上的录音标志会消失） */
        if (self.ctx && self.ctx.close) self.ctx.close().catch(function () { });
        resolve({ blob: new Blob(self.chunks, { type: self.mime }), mime: self.mime, ms: stoppedMs });
      };
      if (!self.rec || self.rec.state === 'inactive') { finish(); return; }
      self.rec.onstop = finish;
      self.rec.stop();
    });
  };

  Recorder.prototype.cancel = function () {
    this.cancelled = true;
    global.clearInterval(this.timer);
    if (this.raf) global.cancelAnimationFrame(this.raf);
    this.analyser = null;
    if (this.stream) this.stream.getTracks().forEach(function (tr) { tr.stop(); });
    if (this.rec && this.rec.state !== 'inactive') { try { this.rec.stop(); } catch (e) { } }
    if (this.ctx && this.ctx.close) this.ctx.close().catch(function () { });
  };

  /* ---------------- 游戏 ---------------- */

  function Game(mount, cfg) {
    this.mount = mount;
    this.cfg = cfg;
    this.items = cfg.items || [];
    this.restart();
  }

  /* 麦克风尚未收尾时禁止手动换句；看门狗仍可强制关麦并结算。 */
  Game.BUSY = { starting: true, recording: true, stopping: true };

  Game.prototype.restart = function () {
    if (this.states && this.st() && (this.st().finalizing || this.st().saveError)) { this.render(); return false; }
    this.cleanup();
    this.generation = (this.generation || 0) + 1;
    var seed = Date.now() & 0xffff;
    this.i = 0;
    this.done = false;
    this.started = Date.now();
    this.states = this.items.map(function (item, k) {
      return { pool: C.shuffle(item.fragments.length, seed + k * 7919), placed: [], wrong: 0, arranged: false,
               rec: null, take: null, skipped: false, stage: 'idle', saved: false, closed: false };
    });
    this.beginSentence();
  };

  Game.prototype.st = function () { return this.states[this.i]; };
  Game.prototype.ord = function (i) { return this.cfg.ords ? this.cfg.ords[i] : i; };
  Game.prototype.current = function (s, generation) {
    return this.generation === generation && this.st() === s && !this.done && !s.closed && !s.finalizing && !s.saveError;
  };
  Game.prototype.beginSentence = function () {
    var self = this, s = this.st(), generation = this.generation;
    if (!s) { this.finish(); return; }
    s.stage = 'beginning';
    this.render();
    var previous = this.i ? this.states[this.i - 1] : null;
    var meta = { level: 0, ords: [this.ord(this.i)] };
    if (previous && previous.round) meta.previous_play_token = previous.token;
    C.begin(this.cfg, meta, function (policy) {
      if (!self.current(s, generation)) return;
      if (!self.cfg.begin && previous && previous.round) policy.combo_seed = previous.round.combo;
      s.round = new C.Round('order', 1, policy);
      s.token = policy.play_token || (self.cfg.playToken ? self.cfg.playToken() : '');
      s.stage = 'idle';
      self.render();
      self.clock = global.setInterval(function () { self.tick(); }, 100);
    }, function () {
      if (!self.current(s, generation)) return;
      s.stage = 'beginError';
      self.render();
    });
  };
  Game.prototype.stopAudio = function () {
    this.audioSerial = (this.audioSerial || 0) + 1;
    if (this.audio) { this.audio.onended = this.audio.onpause = this.audio.onerror = null; this.audio.pause(); }
    this.audio = null;
    this.playing = false;
  };
  Game.prototype.cleanup = function () {
    global.clearInterval(this.clock);
    this.clock = null;
    this.stopAudio();
    if (this.cancelDrag) this.cancelDrag();
    if (this.recorder) this.recorder.cancel();
    this.recorder = null;
    (this.states || []).forEach(function (s) {
      global.clearTimeout(s.poll);
      global.clearTimeout(s.pollRequestTimeout);
      if (s.take && s.take.url) URL.revokeObjectURL(s.take.url);
      s.take = null;
    });
  };
  Game.prototype.destroy = function () { this.disposed = true; this.cleanup(); this.generation += 1; this.done = true; };
  Game.prototype.tick = function () {
    if (this.done) return;
    var s = this.st();
    if (!s.round || s.closed || s.finalizing || s.saveError) return;
    if (!s.arranged && s.round.left() <= 0) { s.round.miss(this.ord(this.i)); s.skipped = true; this.next(true); return; }
    if (s.arranged && s.watchdog && Date.now() >= s.watchdog) { s.skipped = !s.rec; this.next(true); return; }
    if (s.autoAt && !this.playing && Date.now() >= s.autoAt) { this.next(); return; }
    var timer = document.getElementById('orTimer');
    if (timer) timer.textContent = C.clockLabel(s.round);
    var auto = document.getElementById('orAutoNext');
    if (auto) auto.textContent = t('or_autoNext', { n: this.playing ? 10 : Math.max(0, Math.ceil((s.autoAt - Date.now()) / 1000)) });
  };
  Game.prototype.points = function (s) {
    if (!s.round) return 0;
    var base = C.orderPoints({ arranged: s.arranged, wrong: s.wrong, recordingValid: !!(s.rec && s.rec.valid),
      bonus: s.rec ? Math.max(0, Math.min(35, Math.round(s.rec.bonus || 0))) : 0 });
    var arrangement = s.arranged ? C.orderArrangePoints(s.wrong) : 0;
    var speed = s.arranged ? (arrangement + s.round.extra) * .2 * Math.min(1, s.round.left() / s.round.limit) : 0;
    var factor = s.round.policy.score_factor == null ? 1 : s.round.policy.score_factor;
    /* 朗读与准确分不参与速度奖励；全部分项合并后只乘一次系数、取整一次。 */
    return Math.round((base + s.round.extra + speed) * factor);
  };
  Game.prototype.total = function () {
    var self = this;
    return this.states.reduce(function (sum, s) { return sum + self.points(s); }, 0);
  };

  Game.prototype.play = function (i, ownUrl) {
    var self = this, s = this.st(), generation = this.generation;
    var url = ownUrl || (this.cfg.audioUrl ? this.cfg.audioUrl(i) : '');
    if (!url) return;
    this.stopAudio();
    var serial = this.audioSerial;
    this.playing = true;
    s.autoAt = s.resolved ? Date.now() + 10000 : null;
    function ended() {
      if (serial !== self.audioSerial || !self.current(s, generation)) return;
      self.playing = false;
      if (s.resolved) s.autoAt = Date.now() + 10000;
    }
    try {
      this.audio = new Audio(url);
      this.audio.onended = this.audio.onpause = this.audio.onerror = ended;
      var promise = this.audio.play();
      if (promise && promise.catch) promise.catch(ended);
    } catch (e) { ended(); }
  };

  Game.prototype.render = function () {
    if (this.done) { this.renderSummary(); return; }
    var self = this, item = this.items[this.i], s = this.st(), n = this.items.length;
    if (s.finalizing || s.saveError) {
      this.mount.innerHTML = '<div class="card ig-card"><div class="ig-cn">' + esc(item.cn) + '</div><p role="status">' +
        esc(t(s.saveError ? 'or_saveRetry' : 'or_saving')) + '</p>' +
        (s.saveError ? '<button type="button" class="btn" id="orSaveRetry">' + esc(t('ig_retry')) + '</button>' : '') + '</div>';
      var saveRetry = document.getElementById('orSaveRetry');
      if (saveRetry) saveRetry.onclick = function () { self.finalize(s.finalAction || 'next'); };
      return;
    }
    if (s.stage === 'beginning' || s.stage === 'beginError') {
      this.mount.innerHTML = '<div class="card ig-card"><p role="status">' +
        esc(t(s.stage === 'beginning' ? 'ig_starting' : 'ig_beginFailed')) + '</p>' +
        (s.stage === 'beginError' ? '<button class="btn" type="button" id="orBeginRetry">' + esc(t('ig_retry')) + '</button>' : '') + '</div>';
      var retry = document.getElementById('orBeginRetry');
      if (retry) retry.onclick = function () { self.beginSentence(); };
      return;
    }
    var slots = s.placed.map(function (f, k) {
      return '<button type="button" class="ig-frag placed' + (s.arranged ? ' locked' : '') + (s.badAt === k ? ' wrong' : '') +
        '" data-slot="' + k + '">' + fragHtml(item.fragments[f]) + '</button>';
    }).join('');
    var pool = s.pool.map(function (f) {
      return '<button type="button" class="ig-frag" data-frag="' + f + '"' + (s.placed.indexOf(f) >= 0 ? ' hidden' : '') + '>' +
        fragHtml(item.fragments[f]) + '</button>';
    }).join('');
    var body;
    if (!s.arranged) {
      body = '<div class="ig-slots" id="orSlots" data-empty="' + esc(t('or_slotsEmpty')) + '">' + slots + '</div>' +
        '<div class="ig-pool" id="orPool">' + pool + '</div>' +
        '<div class="ig-msg' + (s.badAt != null ? ' bad' : '') + '" id="orMsg" role="status">' +
        (s.badAt != null ? esc(t('or_wrongAt', { k: s.badAt + 1 })) : '') + '</div>' +
        '<div class="ig-actions"><button type="button" class="btn" id="orCheck"' + (s.placed.length < item.fragments.length ? ' disabled' : '') + '>' +
        esc(t('or_check')) + '</button><button type="button" class="btn ghost" id="orClear"' + (s.placed.length ? '' : ' disabled') + '>' +
        esc(t('or_clear')) + '</button></div>';
    } else {
      body = '<div class="ig-sentence" id="orSentence" role="button" tabindex="0" title="' + esc(t('or_listenTip')) + '">' +
        s.placed.map(function (f) { return fragHtml(item.fragments[f]); }).join(' ') + '</div>' +
        '<div class="ig-msg ok" id="orMsg" role="status">' + esc(t('or_arranged', { n: C.orderArrangePoints(s.wrong) })) + '</div>' +
        (s.reward && s.reward.combo >= 2 ? '<div class="reward-toast" role="status">' + esc(t('ig_comboReward', {
          n: s.reward.combo, points: s.reward.points, seconds: s.reward.seconds })) + '</div>' : '') + this.recorderHtml(s);
    }
    this.mount.innerHTML = '<div class="card ig-card">' +
      '<div class="ig-top"><span class="ig-progress">' + esc(t('or_progress', { i: this.i + 1, n: n })) + '</span>' +
      '<span class="ig-points">' + esc(t('ig_points', { n: this.total() })) + '</span></div>' +
      '<div class="ig-timer" id="orTimer">' + esc(C.clockLabel(s.round)) + '</div>' +
      '<p class="ig-policy">' + esc(C.policyText(s.round, t)) + '</p>' +
      '<div class="ig-bar"><i style="width:' + Math.round(this.i / n * 100) + '%"></i></div>' +
      '<div class="ig-cn">' + esc(item.cn) + '</div>' +
      (s.progressError ? '<p class="ig-msg bad" role="status">' + esc(t('ig_scoreNotSaved')) + '</p>' : '') + body + '</div>';
    this.bind();
  };

  Game.prototype.recorderHtml = function (s) {
    var canUpload = !!this.cfg.upload;
    var next = '<button type="button" class="btn" id="orNext">' + esc(t(this.i + 1 < this.items.length ? 'or_nextSentence' : 'ig_finish')) + '</button>';
    if (s.stage === 'scoring' || s.stage === 'uploading') {
      return '<div class="ig-rec"><div class="or-scoring-progress" role="progressbar" aria-label="' + esc(t('or_scoring')) +
        '"><i></i></div><p class="or-scoring-label" role="status">' + esc(t('or_scoring')) + '</p>' +
        (s.rec && s.rec.valid ? this.resultHtml(s) : '') +
        (s.pollStopped ? '<p class="ig-heard">' + esc(t('or_scoringRetry')) + '</p><button type="button" class="btn ghost" id="orPollRetry">' +
          esc(t('ig_retry')) + '</button>' : '') +
        (s.rec && s.rec.id ? '<button type="button" class="btn" id="orSkipWait">' + esc(t('or_skipWait')) + '</button>' : '') + '</div>';
    }
    if (s.resolved) return '<div class="ig-rec">' + (s.rec ? this.resultHtml(s) : '') +
      '<p class="ig-msg ok">' + esc(t('or_sentenceScore', { n: this.points(s) })) + '</p>' +
      '<p id="orAutoNext">' + esc(t('or_autoNext', { n: this.playing ? 10 : Math.max(0, Math.ceil((s.autoAt - Date.now()) / 1000)) })) +
      '</p><div class="ig-actions">' + next + '</div>' +
      (s.take || (s.rec && s.rec.id && this.cfg.recordingUrl) ? '<button type="button" class="btn ghost" id="orOwn">' + esc(t('or_listenOwn')) + '</button>' : '') + '</div>';
    if (!Recorder.supported() || s.stage === 'denied' || s.stage === 'micError') {
      var why = !Recorder.supported() ? 'or_noMic' : s.stage === 'denied' ? 'or_micDenied' : 'or_micFailed';
      var retry = Recorder.supported() ? '<button type="button" class="btn ghost" id="orRetry">' + esc(t('or_micRetry')) + '</button>' : '';
      return '<div class="ig-rec"><h3>' + esc(t('or_recTitle')) + '</h3><p class="ig-heard">' +
        esc(t(why)) + '</p><div class="ig-actions">' + retry + next + '</div></div>';
    }
    var html = '<div class="ig-rec"><h3>' + esc(t(canUpload ? 'or_recTitle' : 'or_recTitleOffline')) + '</h3>';
    if (s.rec) {
      html += this.resultHtml(s);
      if (s.rec.valid) return html + '<div class="ig-actions">' + next + '</div></div>';
    }
    if (s.stage === 'starting') {
      html += '<p class="ig-heard">' + esc(t('or_micStarting')) + '</p>';
    } else if (s.stage === 'recording') {
      html += '<div class="ig-rec-row"><button type="button" class="btn rec-on" id="orStop">' + esc(t('or_stop')) + '</button>' +
        '<span class="ig-rec-time" id="orTime">0.0s</span><span class="ig-level"><i id="orLevel"></i></span></div>';
    } else if (s.stage === 'stopping') {
      html += '<p class="ig-heard">' + esc(t('or_stopping')) + '</p>';
    } else if (s.stage === 'uploading') {
      html += '<p class="ig-heard">' + esc(t('or_uploading')) + '</p>';
    } else if (s.take && s.take.tooShort) {
      html += '<p class="ig-msg bad">' + esc(t('or_tooShort')) + '</p><div class="ig-actions"><button type="button" class="btn" id="orRedo">' +
        esc(t('or_redo')) + '</button></div>';
    } else if (s.take) {
      html += '<div class="ig-rec-row"><button type="button" class="btn ghost" id="orOwn">' + esc(t('or_listenOwn')) + '</button></div>' +
        '<div class="ig-actions"><button type="button" class="btn ghost" id="orRedo">' + esc(t('or_redo')) + '</button>' +
        (canUpload ? '<button type="button" class="btn green" id="orSubmit">' + esc(t('or_submit')) + '</button>' : '') + '</div>';
    } else {
      html += '<p class="ig-heard">' + esc(t('or_recHint')) + '</p><div class="ig-rec-row"><button type="button" class="btn" id="orRecord">' +
        esc(t('or_record')) + '</button></div>';
    }
    var busy = Game.BUSY[s.stage] || s.stage === 'uploading';
    if (canUpload && !(s.rec && s.rec.valid) && !busy) {
      html += '<div class="ig-actions"><button type="button" class="btn ghost sm" id="orSkip">' + esc(t('or_skip')) + '</button></div>';
    }
    if (!canUpload && !Game.BUSY[s.stage]) html += '<div class="ig-actions">' + next + '</div>';     /* 离线页：录不录都能往下走 */
    return html + '</div>';
  };

  Game.prototype.resultHtml = function (s) {
    var r = s.rec;
    if (!r.valid) return '<p class="ig-msg bad">' + esc(t(r.status === 'failed' ? 'or_recFailed' : 'or_notHeard')) + '</p>';
    var lines = '<p class="ig-msg ok">' + esc(t('or_recOk', { n: C.ORDER.recording })) +
      (r.status === 'done' ? ' ' + esc(t('or_bonus', { n: r.bonus || 0 })) : '') + '</p>';
    if (r.status === 'pending' || r.status === 'processing') lines += '<p class="ig-heard">' + esc(t('or_pending')) + '</p>';
    else if (r.status === 'noasr') lines += '<p class="ig-heard">' + esc(t('or_noAsr')) + '</p>';
    else if (r.transcript) lines += '<p class="ig-heard">' + esc(t('or_heard')) + ' <b>' + esc(r.transcript) + '</b>（' +
      esc(t('or_accuracy', { p: Math.round((r.accuracy || 0) * 100) })) + '）</p>';
    return lines;
  };

  Game.prototype.bind = function () {
    var self = this, s = this.st(), item = this.items[this.i];
    function on(id, fn) { var el = document.getElementById(id); if (el) el.onclick = fn; }
    var pool = document.getElementById('orPool');
    if (pool) pool.onclick = function (ev) {
      var b = ev.target.closest('[data-frag]');
      if (!b || self.justDragged) return;
      s.placed.push(parseInt(b.getAttribute('data-frag'), 10));
      s.badAt = null;
      self.render();
    };
    var slots = document.getElementById('orSlots');
    if (slots) slots.onclick = function (ev) {
      var b = ev.target.closest('[data-slot]');
      if (!b || s.arranged || self.justDragged) return;
      s.placed.splice(parseInt(b.getAttribute('data-slot'), 10), 1);
      s.badAt = null;
      self.render();
    };
    this.enableDrag();
    on('orClear', function () { s.placed = []; s.badAt = null; self.render(); });
    on('orCheck', function () {
      if (!s.round || s.arranged || s.closed) return;
      if (s.round.left() <= 0) { self.tick(); return; }
      var res = C.orderCheck(item.fragments, s.placed);
      if (res.ok) {
        s.arranged = true;
        s.reward = s.round.hit(C.orderArrangePoints(s.wrong), s.wrong === 0, self.ord(self.i));
        s.round.pause();
        s.watchdog = Date.now() + 120000;
        var generation = self.generation;
        s.phaseReady = self.checkpoint(s, self.i).then(function (accepted) {
          if (!accepted) throw new Error('progress_failed');
          if (!self.current(s, generation)) throw new Error('round_closed');
          return self.phase(s, 'recording');
        });
        s.phaseReady.catch(function () { });
        self.render();
        self.play(self.i);
        return;
      }
      s.wrong += 1;
      s.round.miss(self.ord(self.i));
      s.badAt = res.firstWrong;
      self.checkpoint(s, self.i);
      self.render();
      var msg = document.getElementById('orMsg');
      msg.className = 'ig-msg bad';
      msg.textContent = t('or_wrongAt', { k: res.firstWrong + 1 });
    });
    var sentence = document.getElementById('orSentence');
    if (sentence) {
      sentence.onclick = function () { self.play(self.i); };
      sentence.onkeydown = function (ev) { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); self.play(self.i); } };
    }
    on('orRecord', function () { self.record(); });
    on('orRetry', function () { s.stage = 'idle'; self.record(); });
    on('orStop', function () { self.stopRecording(); });
    on('orRedo', function () { self.dropTake(); s.rec = null; self.render(); self.record(); });
    on('orSubmit', function () { self.submit(); });
    on('orOwn', function () {
      var url = s.take ? s.take.url : self.cfg.recordingUrl ? self.cfg.recordingUrl(s.rec.id) : '';
      self.play(self.i, url);
    });
    on('orSkipWait', function () { self.next(); });
    on('orPollRetry', function () { self.retryPolling(s); });
    on('orSkip', function () { if (global.confirm(t('or_skipConfirm'))) { s.skipped = true; self.next(); } });
    on('orNext', function () { self.next(); });
  };

  /* 拖动：按住片段拖，片段像卡片一样浮起来跟着走，框里出现一个虚线空位，松手就放到那里。
     拖框里的片段 = 换位置，拖到框外松手 = 退回上面；从上面拖进框里可以放到任意位置。
     移动不到 8 像素就当作点击（点击的逻辑不变）。用指针事件，手指和鼠标都行。 */
  Game.prototype.enableDrag = function () {
    var self = this, s = this.st();
    var slots = document.getElementById('orSlots');
    if (!slots || s.arranged) return;
    Array.prototype.forEach.call(this.mount.querySelectorAll('#orSlots [data-slot], #orPool [data-frag]'), function (el) {
      el.addEventListener('pointerdown', function (ev) { self.dragFrom(ev, el, slots); });
    });
  };

  Game.prototype.dragFrom = function (ev, el, slots) {
    var self = this, s = this.st();
    if (ev.button > 0 || s.arranged || self.dragPointer != null) return;    /* 一次只跟一根手指：第二根手指按下来不算 */
    var pointer = ev.pointerId;
    self.dragPointer = pointer;
    var fromSlot = el.hasAttribute('data-slot') ? parseInt(el.getAttribute('data-slot'), 10) : null;
    var frag = fromSlot != null ? s.placed[fromSlot] : parseInt(el.getAttribute('data-frag'), 10);
    var sx = ev.clientX, sy = ev.clientY, drag = null;

    function begin(e) {
      var r = el.getBoundingClientRect();
      var ghost = el.cloneNode(true);
      ghost.classList.add('ig-ghost');
      ghost.classList.remove('wrong');
      ghost.style.width = r.width + 'px';
      document.body.appendChild(ghost);
      var hole = document.createElement('span');
      hole.className = 'ig-hole';
      hole.style.width = r.width + 'px';
      hole.style.height = r.height + 'px';
      if (fromSlot != null) el.parentNode.replaceChild(hole, el);       /* 原来的位置先留一个空位 */
      else el.style.visibility = 'hidden';
      return { ghost: ghost, hole: hole, dx: sx - r.left, dy: sy - r.top };
    }
    function over(e) {
      var r = slots.getBoundingClientRect(), m = 18;
      return e.clientX > r.left - m && e.clientX < r.right + m && e.clientY > r.top - m && e.clientY < r.bottom + m;
    }
    function place(e) {
      if (!over(e)) { if (drag.hole.parentNode) drag.hole.parentNode.removeChild(drag.hole); return; }
      var cards = Array.prototype.slice.call(slots.querySelectorAll('[data-slot]'));
      var index = cards.filter(function (c) {             /* 指针前面（按阅读顺序）有几张卡片 */
        var r = c.getBoundingClientRect();
        return e.clientY > r.bottom || (e.clientY >= r.top && e.clientX > r.left + r.width / 2);
      }).length;
      var anchor = cards[index] || null;
      if (drag.hole.nextSibling !== anchor || drag.hole.parentNode !== slots) slots.insertBefore(drag.hole, anchor);
    }
    function move(e) {
      if (e.pointerId !== pointer) return;
      if (!drag) {
        if (Math.abs(e.clientX - sx) + Math.abs(e.clientY - sy) < 8) return;
        drag = begin(e);
      }
      e.preventDefault();
      drag.ghost.style.transform = 'translate(' + (e.clientX - drag.dx) + 'px,' + (e.clientY - drag.dy) + 'px) rotate(-2deg) scale(1.06)';
      place(e);
    }
    function end(e) {
      if (e && e.pointerId !== pointer) return;
      document.removeEventListener('pointermove', move);
      document.removeEventListener('pointerup', end);
      document.removeEventListener('pointercancel', end);
      self.dragPointer = null;
      self.cancelDrag = null;
      if (!drag) return;                                   /* 没拖动：交给点击处理 */
      var index = null;
      if (drag.hole.parentNode === slots) {
        index = 0;
        for (var n = drag.hole.previousElementSibling; n; n = n.previousElementSibling) if (n.hasAttribute('data-slot')) index++;
      }
      drag.ghost.remove();
      s.placed = C.placeAt(s.placed, frag, index, fromSlot);
      s.badAt = null;
      self.justDragged = true;                             /* 松手后浏览器还会补一个 click，别让它再放一次 / 退回一次 */
      setTimeout(function () { self.justDragged = false; }, 0);
      self.render();
    }
    document.addEventListener('pointermove', move, { passive: false });
    document.addEventListener('pointerup', end);
    document.addEventListener('pointercancel', end);
    self.cancelDrag = function () {
      document.removeEventListener('pointermove', move);
      document.removeEventListener('pointerup', end);
      document.removeEventListener('pointercancel', end);
      self.dragPointer = null;
      if (drag) { drag.ghost.remove(); if (drag.hole.parentNode) drag.hole.parentNode.removeChild(drag.hole); }
      self.cancelDrag = null;
    };
  };

  Game.prototype.dropTake = function (s) {
    s = s || this.st();
    if (s.take && s.take.url) { try { URL.revokeObjectURL(s.take.url); } catch (e) { } }
    s.take = null;
  };

  Game.prototype.record = function () {
    var self = this, s = this.st(), generation = this.generation;
    if (!s.arranged || s.closed || s.resolved || Game.BUSY[s.stage] || s.stage === 'uploading' || s.stage === 'scoring') return;
    this.stopAudio();
    var recorder = this.recorder = new Recorder();
    s.stage = 'starting';                         /* 麦克风真正开始录之前不给「停止」：太早停会得到一段空录音 */
    this.render();
    recorder.start(function (level) {
      if (!self.current(s, generation)) return;
      var bar = document.getElementById('orLevel');
      if (bar) bar.style.width = Math.round(level * 100) + '%';
    }, function (ms) {
      if (!self.current(s, generation)) return;
      var el = document.getElementById('orTime');
      if (el) el.textContent = (ms / 1000).toFixed(1) + 's / 30s';
    }, function () { if (self.current(s, generation)) self.stopRecording(); }).then(function () {
      if (!self.current(s, generation) || recorder.cancelled) { recorder.cancel(); return; }
      s.stage = 'recording';
      self.render();
    }).catch(function (err) {
      if (!self.current(s, generation)) return;
      /* 用户或浏览器拒绝了权限 → denied；设备被占用、找不到麦克风、录音格式不支持… → micError（可以再试） */
      var name = err && err.name;
      s.stage = (name === 'NotAllowedError' || name === 'SecurityError' || name === 'PermissionDeniedError') ? 'denied' : 'micError';
      self.render();
    });
  };

  Game.prototype.stopRecording = function () {
    var self = this, s = this.st(), generation = this.generation;
    if (!this.recorder || s.stage !== 'recording') return;
    s.stage = 'stopping';
    this.render();                                 /* 「停止」按钮马上换成「正在保存录音」，免得再点一次 */
    this.recorder.stop().then(function (take) {
      if (!self.current(s, generation)) return;
      self.recorder = null;
      self.dropTake(s);
      take.url = URL.createObjectURL(take.blob);
      take.tooShort = take.ms < 1000 || take.blob.size < 1000;
      s.take = take;
      s.stage = 'idle';
      self.render();
    });
  };

  Game.prototype.submit = function () {
    var self = this, s = this.st(), i = this.i, generation = this.generation;
    if (!s.take || s.take.tooShort || !this.cfg.upload || s.stage === 'uploading' || s.closed) return;
    s.stage = 'uploading';
    this.stopAudio();
    this.render();
    var take = s.take;
    Promise.resolve(s.phaseReady).then(function () {
      if (!self.current(s, generation)) return null;
      return self.cfg.upload(i, take.blob, take.mime, take.ms, s.token);
    }).then(function (rec) {
      if (!rec || self.generation !== generation) return;
      self.phase(s, 'scoring').catch(function () { });
      self.acceptRecording(s, rec, generation);
    }).catch(function (err) {
      if (self.generation !== generation) return;
      s.stage = 'idle';
      s.rec = { valid: false, status: 'failed', message: err && err.message };
      if (self.current(s, generation)) self.render();
    });
  };

  Game.prototype.phase = function (s, phase) {
    if (s.serverPhase === phase) return Promise.resolve(true);
    s.phaseRequests = s.phaseRequests || {};
    if (s.phaseRequests[phase]) return s.phaseRequests[phase];
    var request;
    try { request = this.cfg.phase ? this.cfg.phase(s.token, phase) : true; } catch (e) { request = Promise.reject(e); }
    s.phaseRequests[phase] = Promise.resolve(request).then(function (result) {
      delete s.phaseRequests[phase];
      if (result === false) throw new Error('phase_failed');
      s.serverPhase = phase;
      return true;
    }, function (err) { delete s.phaseRequests[phase]; throw err; });
    return s.phaseRequests[phase];
  };
  Game.prototype.retryPolling = function (s) {
    s.pollUntil = Date.now() + 600000;
    s.pollFailures = 0;
    this.acceptRecording(s, s.rec, this.generation);
  };
  Game.prototype.acceptRecording = function (s, rec, generation, failed) {
    var self = this;
    global.clearTimeout(s.poll);
    s.rec = rec;
    s.rec.bonus = Math.max(0, Math.min(35, Math.round(Number(rec.bonus) || 0)));
    if (rec.valid) s.watchdog = null;
    s.pollFailures = failed ? (s.pollFailures || 0) + 1 : 0;
    var pending = rec.status === 'pending' || rec.status === 'processing' || rec.status === 'queued';
    if (!s.finalizing && !s.saveError) s.stage = pending ? 'scoring' : 'idle';
    if (pending && !s.pollUntil) s.pollUntil = Date.now() + 600000;
    s.pollStopped = pending && (s.pollFailures >= 5 || Date.now() >= s.pollUntil);
    if (pending && this.cfg.recording && rec.id && !s.pollStopped) {
      s.poll = global.setTimeout(function () {
        if (self.generation !== generation) return;
        if (Date.now() >= s.pollUntil) { self.acceptRecording(s, rec, generation); return; }
        var request = Promise.resolve().then(function () { return self.cfg.recording(rec.id); });
        var timeout = new Promise(function (resolve, reject) {
          s.pollRequestTimeout = global.setTimeout(function () { reject(new Error('recording_status_timeout')); }, 10000);
        });
        Promise.race([request, timeout]).then(function (updated) {
          global.clearTimeout(s.pollRequestTimeout);
          if (self.generation === generation) self.acceptRecording(s, updated, generation);
        }).catch(function () {
          global.clearTimeout(s.pollRequestTimeout);
          if (self.generation === generation) self.acceptRecording(s, rec, generation, true);
        });
      }, 1500);
    } else if (!pending && rec.valid) {
      s.resolved = true;
      s.autoAt = Date.now() + 10000;
    }
    if (this.current(s, generation) || this.done) this.render();
  };
  Game.prototype.sentenceReport = function (s, i) {
    var report = s.round.report();
    report.score = this.points(s);
    report.matched = s.arranged ? 1 : 0;
    report.total_pairs = report.level_count = 1;
    report.wrong = s.wrong;
    report.best_combo = s.round.best;
    report.duration = s.round.elapsed();
    report.play_token = s.token;
    report.detail = [{ i: i, ord: this.ord(i), wrong: s.wrong, arranged: s.arranged,
      recording_id: s.rec && s.rec.id ? s.rec.id : null, skipped: s.skipped }];
    return report;
  };
  Game.prototype.checkpoint = function (s, i) {
    if (!this.cfg.progress || !s.round) return Promise.resolve(true);
    var self = this, generation = this.generation, revision = (s.progressRevision || 0) + 1;
    s.progressRevision = revision;
    function settled(accepted) {
      if (self.generation !== generation || s.progressRevision !== revision) return accepted;
      var changed = !!s.progressError !== !accepted;
      s.progressError = !accepted;
      if (changed && (self.current(s, generation) || self.done)) self.render();
      return accepted;
    }
    try {
      return Promise.resolve(this.cfg.progress(this.sentenceReport(s, i))).then(function (result) {
        return settled(result !== false);
      }, function () { return settled(false); });
    } catch (e) { settled(false); return Promise.resolve(false); }
  };
  Game.prototype.saveSentence = function (s, i) {
    if (s.saved) return true;
    if (s.saving) return s.saving;
    if (!s.round) return false;
    s.round.pause();
    if (!this.cfg.progress && !this.cfg.phase && !this.cfg.save) { s.saved = true; return true; }
    var self = this;
    var checkpoint = s.round.left() > 0 ? this.checkpoint(s, i) : Promise.resolve(true);
    s.saving = checkpoint.then(function () {
      return self.phase(s, 'scoring').then(function () {
        return self.cfg.save ? self.cfg.save(self.sentenceReport(s, i)) : true;
      });
    }).then(function (result) {
      s.saving = null;
      s.saved = result !== false;
      if (s.saved) s.progressError = false;
      return s.saved;
    }, function () { s.saving = null; s.saved = false; return false; });
    return s.saving;
  };
  Game.prototype.next = function (force) {
    if (this.done) return;
    var s = this.st();
    if (!s.round || s.closed || s.finalizing || (!force && (Game.BUSY[s.stage] || s.stage === 'uploading'))) return;
    this.finalize(s.finalAction || 'next');
  };
  Game.prototype.finalize = function (action) {
    var self = this, s = this.st(), i = this.i, generation = this.generation;
    if (this.done || !s || s.closed || s.finalizing) return;
    this.stopAudio();
    if (this.recorder) this.recorder.cancel();
    this.recorder = null;
    this.dropTake();
    global.clearInterval(this.clock);
    s.finalAction = action;
    s.finalizing = true;
    s.saveError = false;
    this.render();
    function complete(saved) {
      if (self.generation !== generation || self.st() !== s || self.disposed) return;
      s.finalizing = false;
      if (!saved) { s.saveError = true; self.render(); return; }
      s.closed = true;
      if (action === 'next' && i + 1 < self.items.length) { self.i += 1; self.beginSentence(); }
      else self.finish();
    }
    var saving = this.saveSentence(s, i);
    if (saving && saving.then) saving.then(complete);
    else complete(saving);
  };

  Game.prototype.finish = function () {
    if (this.done) return;
    var s = this.st();
    if (s && !s.closed) { this.finalize('finish'); return; }
    global.clearInterval(this.clock);
    this.stopAudio();
    if (this.recorder) this.recorder.cancel();
    this.recorder = null;
    if (s) this.dropTake(s);
    this.done = true;
    this.renderSummary();
  };

  Game.prototype.renderSummary = function () {
    var self = this, pending = false;
    var rows = this.items.map(function (item, k) {
      var s = self.states[k], r = s.rec;
      if (r && (r.status === 'pending' || r.status === 'processing' || r.status === 'queued')) pending = true;
      var rec = !r ? t(s.skipped ? 'or_resSkipped' : 'or_resNone') : !r.valid ? t('or_resInvalid')
        : r.status === 'done' ? t('or_resBonus', { n: r.bonus || 0 }) :
          (r.status === 'pending' || r.status === 'processing' || r.status === 'queued') ? t('or_resPending') : t('or_resNoBonus');
      return '<tr><td>' + esc(item.cn) + '</td><td class="num">' + (s.arranged ? C.orderArrangePoints(s.wrong) : 0) + '</td>' +
        '<td>' + esc(rec) + (s.pollStopped ? '<button type="button" class="btn ghost sm" id="orPollRetry' + k + '">' +
          esc(t('ig_retry')) + '</button>' : '') + '</td><td class="num">' + self.points(s) + '</td></tr>';
    }).join('');
    this.mount.innerHTML = '<div class="card ig-summary">' +
      '<h2>' + esc(t('ig_doneTitle')) + '</h2><div class="ig-big">' + esc(t('ig_points', { n: this.total() })) + '</div>' +
      (this.states.some(function (s) { return s.progressError; }) ?
        '<p class="ig-msg bad" role="status">' + esc(t('ig_scoreNotSaved')) + '</p>' : '') +
      (pending ? '<p class="sub">' + esc(t('or_pendingSummary')) + '</p>' : '') +
      '<div class="scroll"><table><thead><tr><th>' + esc(t('or_colSentence')) + '</th><th>' + esc(t('or_colArrange')) + '</th><th>' +
      esc(t('or_colRecording')) + '</th><th>' + esc(t('ig_colPoints')) + '</th></tr></thead><tbody>' + rows + '</tbody></table></div>' +
      '<div class="ig-actions"><button type="button" class="btn" id="orAgain">' + esc(t('ig_again')) + '</button>' +
      (this.cfg.backHref ? '<a class="btn ghost" href="' + esc(this.cfg.backHref) + '">' + esc(t('ig_back')) + '</a>' : '') + '</div></div>';
    document.getElementById('orAgain').onclick = function () { self.restart(); };
    this.states.forEach(function (s, k) {
      var retry = document.getElementById('orPollRetry' + k);
      if (retry) retry.onclick = function () { self.retryPolling(s); };
    });
  };

  global.WPOrderUI = {
    Recorder: Recorder,
    start: function (mount, cfg) {
      if (mount.wpOrderGame) mount.wpOrderGame.destroy();
      var game = new Game(mount, cfg);
      mount.wpOrderGame = game;
      if (global.WPI18N && global.WPI18N.onChange) {
        global.WPI18N.onChange(function () {
          if (!game.disposed) { if (game.cancelDrag) game.cancelDrag(); game.render(); }
        });
      }
      if (global.addEventListener) global.addEventListener('pagehide', function () { game.disposed = true; game.destroy(); });
      return game;
    }
  };
})(window);
