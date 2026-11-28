/* ============================================================
   spell-ui.js —— 单词大比拼的页面部分（网站版和离线单文件页共用）
   ------------------------------------------------------------
   WPSpellUI.start(mountEl, cfg)
     cfg.items      这一关的题目（server/items.py 的 spell 格式）
     cfg.audioUrl   function(i) → 第 i 道题整个短语的读音地址（没有读音返回 ''）
     cfg.save       function(report) 交成绩（网站：/api/scores；离线：存在浏览器里）
     cfg.backHref   「返回」去哪
   判分规则在 item-core.js。输入框关掉了自动纠错、自动大写：不让手机输入法替学生拼对。
   ============================================================ */
(function (global) {
  'use strict';

  var C = global.WPItemCore;
  function t(key, params) { return global.WPI18N ? global.WPI18N.t(key, params) : key; }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function Game(mount, cfg) {
    this.mount = mount;
    this.cfg = cfg;
    this.items = cfg.items || [];
    this.restart();
  }

  Game.prototype.restart = function () {
    clearInterval(this.timer);
    var self = this, generation = this.generation = (this.generation || 0) + 1;
    this.i = 0;
    this.states = this.items.map(function () { return { hints: 0, wrong: 0, solved: false, gaveUp: false, typed: '' }; });
    this.started = Date.now();
    this.done = false;
    this.reward = '';
    this.loading = true;
    this.mount.innerHTML = '<div class="card">' + esc(t('ig_starting')) + '</div>';
    C.begin(this.cfg, { ords: this.cfg.ords }, function (policy) {
      if (self.generation !== generation) return;
      self.round = new C.Round('spell', self.items.length, policy);
      self.loading = false;
      self.started = self.round.started;
      self.render();
      self.timer = setInterval(function () { self.tick(); }, 200);
    }, function (err) {
      if (self.generation !== generation) return;
      self.mount.innerHTML = '<div class="card"><p>' + esc(err.message || t('ig_startFailed')) +
        '</p><button class="btn" id="spRetry">' + esc(t('ig_again')) + '</button></div>';
      document.getElementById('spRetry').onclick = function () { self.restart(); };
    });
  };

  Game.prototype.active = function () {
    if (this.done || this.loading) return false;
    if (this.round.left() <= 0) { this.finish(); return false; }
    return true;
  };
  Game.prototype.tick = function () {
    if (!this.active()) return;
    var el = document.getElementById('spTimer');
    if (el) el.textContent = t('ig_timeLeft', { time: C.clockLabel(this.round) });
  };
  Game.prototype.total = function () {
    var base = this.states.reduce(function (sum, s) { return sum + C.spellPoints(s); }, 0);
    return this.round ? this.round.finish(base, this.done && this.states.every(function (s) { return s.solved; })) : 0;
  };

  Game.prototype.play = function (i) {
    var url = this.cfg.audioUrl ? this.cfg.audioUrl(i) : '';
    if (!url) return;
    try { new Audio(url).play().catch(function () { }); } catch (e) { }
  };

  Game.prototype.render = function () {
    if (this.loading) return;
    if (this.done) { this.renderSummary(); return; }
    var self = this, item = this.items[this.i], st = this.states[this.i], n = this.items.length;
    var finished = st.solved || st.gaveUp;
    this.mount.innerHTML =
      '<div class="card ig-card">' +
      '<div class="ig-top"><span class="ig-progress">' + esc(t('sp_progress', { i: this.i + 1, n: n })) + '</span>' +
      '<span class="ig-timer" id="spTimer" role="timer">' + esc(t('ig_timeLeft', { time: C.clockLabel(this.round) })) + '</span>' +
      '<span class="ig-points">' + esc(t('ig_points', { n: this.total() })) + '</span></div>' +
      '<p class="sub">' + esc(C.policyText(this.round, t)) + '</p>' +
      (this.reward ? '<div class="ig-reward" role="status">' + esc(this.reward) + '</div>' : '') +
      '<div class="ig-bar"><i style="width:' + Math.round(this.i / n * 100) + '%"></i></div>' +
      '<div class="ig-cn">' + esc(item.cn) + '</div>' +
      '<div class="ig-phrase">' + (item.before ? '<span>' + esc(item.before) + '</span>' : '') +
      '<input type="text" id="spInput" autocomplete="off" autocorrect="off" autocapitalize="none" spellcheck="false" ' +
      'enterkeyhint="done" aria-label="' + esc(t('sp_inputLabel')) + '" size="' + Math.max(6, item.answer.length + 2) + '"' +
      (finished ? ' readonly' : '') + ' class="' + (st.solved ? 'right' : '') + '" value="' + esc(finished ? item.answer : st.typed) + '">' +
      (item.after ? '<span>' + esc(item.after) + '</span>' : '') + '</div>' +
      '<div class="ig-hint" id="spHint">' + (st.hints && !finished ? esc(C.spellHint(item.answer, st.hints)) : '') + '</div>' +
      '<div class="ig-msg" id="spMsg" role="status"></div>' +
      '<div class="ig-actions">' +
      (finished
        ? '<button type="button" class="btn ghost" id="spListen">' + esc(t('ig_listen')) + '</button>' +
          '<button type="button" class="btn" id="spNext">' + esc(t(this.i + 1 < n ? 'ig_next' : 'ig_finish')) + '</button>'
        : '<button type="button" class="btn" id="spCheck">' + esc(t('sp_check')) + '</button>' +
          '<button type="button" class="btn ghost" id="spHintBtn"' + (st.hints >= 2 ? ' disabled' : '') + '>' +
          esc(t(st.hints ? 'sp_hint2' : 'sp_hint1')) + '</button>' +
          '<button type="button" class="btn ghost" id="spGiveUp">' + esc(t('sp_giveUp')) + '</button>') +
      '</div></div>';
    var input = document.getElementById('spInput');
    if (finished) {
      this.say(st.solved ? t('sp_right', { n: C.spellPoints(st) }) : t('sp_answerIs', { w: item.answer }), st.solved ? 'ok' : 'info');
      document.getElementById('spListen').onclick = function () { self.play(self.i); };
      var next = document.getElementById('spNext');
      next.onclick = function () { self.next(); };
      next.focus();
      return;
    }
    input.oninput = function () { st.typed = input.value; input.classList.remove('bad'); };
    input.onkeydown = function (ev) { if (ev.key === 'Enter') { ev.preventDefault(); self.check(); } };
    document.getElementById('spCheck').onclick = function () { self.check(); };
    document.getElementById('spHintBtn').onclick = function () { self.hint(); };
    document.getElementById('spGiveUp').onclick = function () { self.giveUp(); };
    input.focus();
  };

  Game.prototype.say = function (text, kind) {
    var el = document.getElementById('spMsg');
    if (el) { el.className = 'ig-msg ' + (kind || 'info'); el.textContent = text; }
  };

  Game.prototype.check = function () {
    if (!this.active()) return;
    var item = this.items[this.i], st = this.states[this.i];
    if (st.solved || st.gaveUp) return;
    var input = document.getElementById('spInput');
    var result = C.spellCheck(input.value, item.answer);
    if (result === 'empty') { this.say(t('sp_empty'), 'info'); input.focus(); return; }
    if (result === 'right') {
      st.solved = true;
      st.typed = input.value;
      var gain = this.round.hit(C.SPELL.full, !st.hints && !st.wrong,
        this.cfg.ords ? this.cfg.ords[this.i] : this.i);
      this.reward = gain.combo >= 2 ? t('ig_comboReward', { n: gain.combo, points: gain.points, seconds: gain.seconds }) : '';
      this.checkpoint();
      this.render();
      this.play(this.i);
      return;
    }
    st.wrong += 1;
    this.round.miss(this.cfg.ords ? this.cfg.ords[this.i] : this.i);
    this.reward = '';
    this.checkpoint();
    input.classList.remove('bad');
    void input.offsetWidth;                      /* 重新触发抖动动画 */
    input.classList.add('bad');
    this.say(t(result === 'close' ? 'sp_close' : 'sp_wrong'), 'bad');
    input.select();
  };

  Game.prototype.hint = function () {
    if (!this.active()) return;
    var st = this.states[this.i];
    if (st.solved || st.gaveUp) return;
    st.hints = Math.min(2, st.hints + 1);
    this.round.miss(this.cfg.ords ? this.cfg.ords[this.i] : this.i);
    this.reward = '';
    st.typed = document.getElementById('spInput').value;
    this.checkpoint();
    this.render();
  };

  Game.prototype.giveUp = function () {
    if (!this.active()) return;
    if (this.states[this.i].solved || this.states[this.i].gaveUp) return;
    this.round.miss(this.cfg.ords ? this.cfg.ords[this.i] : this.i);
    this.reward = '';
    this.states[this.i].gaveUp = true;
    this.checkpoint();
    this.render();
    this.play(this.i);
  };

  Game.prototype.next = function () {
    if (!this.active()) return;
    if (this.i + 1 < this.items.length) { this.i += 1; this.render(); return; }
    this.finish();
  };

  Game.prototype.checkpoint = function () {
    if (this.cfg.progress) this.cfg.progress(this.report());
  };

  Game.prototype.report = function () {
    var solved = this.states.filter(function (s) { return s.solved; }).length;
    var report = {
      score: this.total(), matched: solved, total_pairs: this.items.length,
      wrong: this.states.reduce(function (sum, s) { return sum + s.wrong; }, 0), best_combo: this.round.best,
      duration: this.round.elapsed(), level_count: 1,
      detail: this.states.map(function (s, i) {
        return { i: i, ord: this.cfg.ords ? this.cfg.ords[i] : i, hints: s.hints, wrong: s.wrong, solved: s.solved,
          gave_up: s.gaveUp, points: C.spellPoints(s) };
      }, this)
    };
    Object.assign(report, this.round.report());
    return report;
  };

  Game.prototype.finish = function () {
    if (this.done || this.loading) return;
    this.done = true;
    this.round.pause();
    clearInterval(this.timer);
    if (this.cfg.save) this.cfg.save(this.report());
    this.renderSummary();
  };

  Game.prototype.renderSummary = function () {
    var self = this;
    var rows = this.items.map(function (item, i) {
      var s = self.states[i];
      return '<tr><td>' + esc(item.cn) + '</td><td>' + esc([item.before, item.answer, item.after].filter(Boolean).join(' ')) + '</td>' +
        '<td>' + esc(s.solved ? t('sp_resRight', { w: s.wrong, h: s.hints }) : t('sp_resGaveUp')) + '</td>' +
        '<td class="num">' + C.spellPoints(s) + '</td></tr>';
    }).join('');
    var solved = this.states.filter(function (s) { return s.solved; }).length;
    this.mount.innerHTML = '<div class="card ig-summary">' +
      '<h2>' + esc(t('ig_doneTitle')) + '</h2>' +
      '<div class="ig-big">' + esc(t('ig_points', { n: this.total() })) + '</div>' +
      (this.round.left() <= 0 ? '<p class="sub">' + esc(t('ig_timedOut')) + '</p>' : '') +
      '<p class="sub">' + esc(t('sp_summary', { right: solved, n: this.items.length })) + '</p>' +
      '<div class="scroll"><table><thead><tr><th>' + esc(t('sp_colCn')) + '</th><th>' + esc(t('sp_colPhrase')) + '</th><th>' +
      esc(t('sp_colResult')) + '</th><th>' + esc(t('ig_colPoints')) + '</th></tr></thead><tbody>' + rows + '</tbody></table></div>' +
      '<div class="ig-actions"><button type="button" class="btn" id="spAgain">' + esc(t('ig_again')) + '</button>' +
      (this.cfg.backHref ? '<a class="btn ghost" href="' + esc(this.cfg.backHref) + '">' + esc(t('ig_back')) + '</a>' : '') + '</div></div>';
    document.getElementById('spAgain').onclick = function () { self.restart(); };
  };

  global.WPSpellUI = {
    start: function (mount, cfg) {
      var game = new Game(mount, cfg);
      if (global.WPI18N && global.WPI18N.onChange) global.WPI18N.onChange(function () { game.render(); });
      return game;
    }
  };
})(window);
