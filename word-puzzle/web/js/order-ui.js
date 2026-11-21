/* ============================================================
   order-ui.js —— 排排坐的页面部分（网站版和离线单文件页共用）
   ------------------------------------------------------------
   WPOrderUI.start(mountEl, cfg)
     cfg.items      这一关的题目（server/items.py 的 order 格式）
     cfg.ords       每道题在整个题库里的序号（读音、录音按它找题）
     cfg.audioUrl   function(i) → 第 i 句整句读音的地址
     cfg.upload     function(i, blob, mime, ms, playToken) → Promise({id, valid, bonus, status, transcript, accuracy})；
                    没有（离线页）= 可以录音、回放，但不评分
     cfg.save       function(report) 交成绩
     cfg.playToken  function() → 这一局的编号（录音和成绩据此连起来；每次「再玩一次」重新取）
     cfg.backHref   结束页「返回」按钮的地址（可选）
   每句的录音阶段 s.stage：idle → starting（等麦克风）→ recording → stopping（等浏览器交出录音）→ idle（有 take 可回放）
     → uploading → idle（有 rec = 服务器的评分）；麦克风被拒绝是 denied，其他打不开的情况是 micError（可以再试）。
     starting / recording / stopping 期间不能离开这一句（录音还没收尾），也不因切换语言重画。
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
    global.clearInterval(this.timer);
    if (this.raf) global.cancelAnimationFrame(this.raf);
    this.analyser = null;
    return new Promise(function (resolve) {
      var finish = function () {
        var ms = Date.now() - self.began;
        if (self.stream) self.stream.getTracks().forEach(function (tr) { tr.stop(); });      /* 关掉麦克风（手机上的录音标志会消失） */
        if (self.ctx && self.ctx.close) self.ctx.close().catch(function () { });
        resolve({ blob: new Blob(self.chunks, { type: self.mime }), mime: self.mime, ms: ms });
      };
      if (!self.rec || self.rec.state === 'inactive') { finish(); return; }
      self.rec.onstop = finish;
      self.rec.stop();
    });
  };

  /* ---------------- 游戏 ---------------- */

  function Game(mount, cfg) {
    this.mount = mount;
    this.cfg = cfg;
    this.items = cfg.items || [];
    this.restart();
  }

  /* 这些阶段麦克风还开着或录音还没交出来：不能换句、不能结束、不因切换语言重画 */
  Game.BUSY = { starting: true, recording: true, stopping: true };

  Game.prototype.restart = function () {
    var seed = Date.now() & 0xffff;
    this.i = 0;
    this.done = false;
    this.started = Date.now();
    this.token = this.cfg.playToken ? this.cfg.playToken() : '';
    this.states = this.items.map(function (item, k) {
      return { pool: C.shuffle(item.fragments.length, seed + k * 7919), placed: [], wrong: 0, arranged: false,
               rec: null, take: null, skipped: false, stage: 'idle' };
    });
    this.render();
  };

  Game.prototype.st = function () { return this.states[this.i]; };
  Game.prototype.points = function (s) {
    return C.orderPoints({ arranged: s.arranged, wrong: s.wrong, recordingValid: !!(s.rec && s.rec.valid), bonus: s.rec ? s.rec.bonus || 0 : 0 });
  };
  Game.prototype.total = function () {
    var self = this;
    return this.states.reduce(function (sum, s) { return sum + self.points(s); }, 0);
  };

  Game.prototype.play = function (i) {
    var url = this.cfg.audioUrl ? this.cfg.audioUrl(i) : '';
    if (!url) return;
    try { if (this.audio) this.audio.pause(); this.audio = new Audio(url); this.audio.play().catch(function () { }); } catch (e) { }
  };

  Game.prototype.render = function () {
    if (this.done) { this.renderSummary(); return; }
    var self = this, item = this.items[this.i], s = this.st(), n = this.items.length;
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
        '<div class="ig-msg" id="orMsg" role="status"></div>' +
        '<div class="ig-actions"><button type="button" class="btn" id="orCheck"' + (s.placed.length < item.fragments.length ? ' disabled' : '') + '>' +
        esc(t('or_check')) + '</button><button type="button" class="btn ghost" id="orClear"' + (s.placed.length ? '' : ' disabled') + '>' +
        esc(t('or_clear')) + '</button></div>';
    } else {
      body = '<div class="ig-sentence" id="orSentence" role="button" tabindex="0" title="' + esc(t('or_listenTip')) + '">' +
        s.placed.map(function (f) { return fragHtml(item.fragments[f]); }).join(' ') + '</div>' +
        '<div class="ig-msg ok" id="orMsg" role="status">' + esc(t('or_arranged', { n: C.orderArrangePoints(s.wrong) })) + '</div>' +
        this.recorderHtml(s);
    }
    this.mount.innerHTML = '<div class="card ig-card">' +
      '<div class="ig-top"><span class="ig-progress">' + esc(t('or_progress', { i: this.i + 1, n: n })) + '</span>' +
      '<span class="ig-points">' + esc(t('ig_points', { n: this.total() })) + '</span></div>' +
      '<div class="ig-bar"><i style="width:' + Math.round(this.i / n * 100) + '%"></i></div>' +
      '<div class="ig-cn">' + esc(item.cn) + '</div>' + body + '</div>';
    this.bind();
  };

  Game.prototype.recorderHtml = function (s) {
    var canUpload = !!this.cfg.upload;
    var next = '<button type="button" class="btn" id="orNext">' + esc(t(this.i + 1 < this.items.length ? 'or_nextSentence' : 'ig_finish')) + '</button>';
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
      html += '<div class="ig-rec-row"><audio controls src="' + s.take.url + '"></audio></div>' +
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
    if (r.status === 'pending') lines += '<p class="ig-heard">' + esc(t('or_pending')) + '</p>';
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
      var res = C.orderCheck(item.fragments, s.placed);
      if (res.ok) { s.arranged = true; self.render(); self.play(self.i); return; }
      s.wrong += 1;
      s.badAt = res.firstWrong;
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
  };

  Game.prototype.dropTake = function () {
    var s = this.st();
    if (s.take && s.take.url) { try { URL.revokeObjectURL(s.take.url); } catch (e) { } }
    s.take = null;
  };

  Game.prototype.record = function () {
    var self = this, s = this.st();
    if (this.audio) this.audio.pause();
    this.recorder = new Recorder();
    s.stage = 'starting';                         /* 麦克风真正开始录之前不给「停止」：太早停会得到一段空录音 */
    this.render();
    this.recorder.start(function (level) {
      var bar = document.getElementById('orLevel');
      if (bar) bar.style.width = Math.round(level * 100) + '%';
    }, function (ms) {
      var el = document.getElementById('orTime');
      if (el) el.textContent = (ms / 1000).toFixed(1) + 's / 30s';
    }, function () { self.stopRecording(); }).then(function () {
      s.stage = 'recording';
      self.render();
    }).catch(function (err) {
      /* 用户或浏览器拒绝了权限 → denied；设备被占用、找不到麦克风、录音格式不支持… → micError（可以再试） */
      var name = err && err.name;
      s.stage = (name === 'NotAllowedError' || name === 'SecurityError' || name === 'PermissionDeniedError') ? 'denied' : 'micError';
      self.render();
    });
  };

  Game.prototype.stopRecording = function () {
    var self = this, s = this.st();
    if (!this.recorder || s.stage !== 'recording') return;
    s.stage = 'stopping';
    this.render();                                 /* 「停止」按钮马上换成「正在保存录音」，免得再点一次 */
    this.recorder.stop().then(function (take) {
      self.dropTake();
      take.url = URL.createObjectURL(take.blob);
      take.tooShort = take.ms < 800 || take.blob.size < 1000;      /* 没录上 / 太短：不让交，直接请他重录 */
      s.take = take;
      s.stage = 'idle';
      self.render();
    });
  };

  Game.prototype.submit = function () {
    var self = this, s = this.st(), i = this.i;
    if (!s.take || !this.cfg.upload) return;
    s.stage = 'uploading';
    this.render();
    this.cfg.upload(i, s.take.blob, s.take.mime, s.take.ms, this.token).then(function (rec) {
      s.rec = rec;
      s.stage = 'idle';
      if (rec.valid) self.dropTake();
      if (self.i === i) self.render();
    }).catch(function (err) {
      s.stage = 'idle';
      s.rec = { valid: false, status: 'failed', message: err && err.message };
      if (self.i === i) self.render();
    });
  };

  Game.prototype.next = function () {
    if (Game.BUSY[this.st().stage]) return;
    if (this.audio) this.audio.pause();
    this.dropTake();
    if (this.i + 1 < this.items.length) { this.i += 1; this.render(); return; }
    this.finish();
  };

  Game.prototype.finish = function () {
    var self = this;
    this.done = true;
    var report = {
      score: this.total(), matched: this.states.filter(function (s) { return s.arranged; }).length,
      total_pairs: this.items.length, wrong: this.states.reduce(function (sum, s) { return sum + s.wrong; }, 0),
      best_combo: 0, duration: Math.round((Date.now() - this.started) / 1000), level_count: 1, play_token: this.token,
      detail: this.states.map(function (s, k) {
        return { i: k, ord: self.cfg.ords ? self.cfg.ords[k] : k, wrong: s.wrong, arranged: s.arranged,
                 recording_id: s.rec && s.rec.id ? s.rec.id : null, skipped: s.skipped };
      })
    };
    try { if (this.cfg.save) this.cfg.save(report); } catch (e) { }
    this.renderSummary();
  };

  Game.prototype.renderSummary = function () {
    var self = this, pending = false;
    var rows = this.items.map(function (item, k) {
      var s = self.states[k], r = s.rec;
      if (r && r.status === 'pending') pending = true;
      var rec = !r ? t(s.skipped ? 'or_resSkipped' : 'or_resNone') : !r.valid ? t('or_resInvalid')
        : r.status === 'done' ? t('or_resBonus', { n: r.bonus || 0 }) : r.status === 'pending' ? t('or_resPending') : t('or_resNoBonus');
      return '<tr><td>' + esc(item.cn) + '</td><td class="num">' + (s.arranged ? C.orderArrangePoints(s.wrong) : 0) + '</td>' +
        '<td>' + esc(rec) + '</td><td class="num">' + self.points(s) + '</td></tr>';
    }).join('');
    this.mount.innerHTML = '<div class="card ig-summary">' +
      '<h2>' + esc(t('ig_doneTitle')) + '</h2><div class="ig-big">' + esc(t('ig_points', { n: this.total() })) + '</div>' +
      (pending ? '<p class="sub">' + esc(t('or_pendingSummary')) + '</p>' : '') +
      '<div class="scroll"><table><thead><tr><th>' + esc(t('or_colSentence')) + '</th><th>' + esc(t('or_colArrange')) + '</th><th>' +
      esc(t('or_colRecording')) + '</th><th>' + esc(t('ig_colPoints')) + '</th></tr></thead><tbody>' + rows + '</tbody></table></div>' +
      '<div class="ig-actions"><button type="button" class="btn" id="orAgain">' + esc(t('ig_again')) + '</button>' +
      (this.cfg.backHref ? '<a class="btn ghost" href="' + esc(this.cfg.backHref) + '">' + esc(t('ig_back')) + '</a>' : '') + '</div></div>';
    document.getElementById('orAgain').onclick = function () { self.restart(); };
  };

  global.WPOrderUI = {
    Recorder: Recorder,
    start: function (mount, cfg) {
      var game = new Game(mount, cfg);
      if (global.WPI18N && global.WPI18N.onChange) {
        global.WPI18N.onChange(function () {
          var st = game.states[game.i];
          if (!st || !Game.BUSY[st.stage]) game.render();
        });
      }
      return game;
    }
  };
})(window);
