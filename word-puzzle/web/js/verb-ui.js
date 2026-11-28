/* ============================================================
   verb-ui.js —— 动词猎手的网站版与离线版共用
   一局随机排列全部题目，每题独立随机五个选项。
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
    this.sourceItems = cfg.items || [];
    this.sourceOrds = cfg.ords || this.sourceItems.map(function (_, i) { return i; });
    this.pool = cfg.choices || (this.sourceItems[0] && this.sourceItems[0].choices) || [];
    this.totalItems = this.sourceItems.length;
    this.dragPointer = null;
    this.justDragged = false;
    this.restart();
  }

  Game.prototype.restart = function () {
    clearInterval(this.timer);
    if (this.cancelDrag) this.cancelDrag();
    this.done = false;
    this.finishPrompt = false;
    this.reviewing = false;
    this.timedOut = false;
    this.reward = '';
    this.loading = true;
    var seed = (Date.now() ^ Math.floor(Math.random() * 4294967296)) >>> 0;
    this.order = C.shuffle(this.sourceItems.length, seed);
    this.items = this.order.map(function (i) { return this.sourceItems[i]; }, this);
    this.ords = this.order.map(function (i) { return this.sourceOrds[i]; }, this);
    var dealt = C.dealVerbChoices(this.sourceItems, this.pool, (seed ^ 0x9e3779b9) >>> 0);
    this.choicesByItem = this.order.map(function (i) { return dealt[i]; });
    this.i = 0;
    this.states = this.items.map(function () {
      return { selected: null, wrong: 0, solved: false, skipped: false, feedback: '' };
    });
    var self = this, generation = this.generation = (this.generation || 0) + 1;
    this.mount.innerHTML = '<div class="card">' + esc(t('ig_starting')) + '</div>';
    C.begin(this.cfg, { ords: this.sourceOrds }, function (policy) {
      if (self.generation !== generation) return;
      self.round = new C.Round('verb', self.totalItems, policy);
      self.started = self.round.started;
      self.loading = false;
      self.render();
      self.timer = setInterval(function () { self.tick(); }, 250);
    }, function (err) {
      if (self.generation !== generation) return;
      self.mount.innerHTML = '<div class="card"><p>' + esc(err.message || t('ig_startFailed')) +
        '</p><button class="btn" id="vhRetry">' + esc(t('ig_again')) + '</button></div>';
      self.mount.querySelector('#vhRetry').onclick = function () { self.restart(); };
    });
  };

  Game.prototype.active = function () {
    if (this.done || this.loading) return false;
    if (this.round.left() <= 0) { this.finish(true); return false; }
    return true;
  };

  Game.prototype.timeLabel = function () {
    return t('vh_timeLeft', { time: C.clockLabel(this.round) });
  };

  Game.prototype.timerHtml = function () {
    return '<span class="verb-timer" id="vhTimer" role="timer">' + esc(this.timeLabel()) + '</span>';
  };

  Game.prototype.tick = function () {
    if (!this.active()) return;
    var timer = this.mount.querySelector('#vhTimer');
    if (timer) timer.textContent = this.timeLabel();
  };

  Game.prototype.total = function () {
    var base = this.states.reduce(function (sum, state) { return sum + C.verbPoints(state); }, 0);
    return this.round.finish(base, this.done && this.solvedCount() === this.totalItems);
  };

  Game.prototype.allResults = function () {
    return this.items.map(function (item, i) {
      return { item: item, state: this.states[i], ordinal: this.ords[i] };
    }, this);
  };

  Game.prototype.solvedCount = function () {
    return this.states.filter(function (state) { return state.solved; }).length;
  };

  Game.prototype.wrongCount = function () {
    return this.states.reduce(function (sum, state) { return sum + state.wrong; }, 0);
  };

  Game.prototype.render = function () {
    if (this.done) { this.renderSummary(); return; }
    if (!this.active()) return;
    if (this.finishPrompt) { this.renderFinishPrompt(); return; }
    var self = this, item = this.items[this.i], state = this.states[this.i];
    var choices = this.choicesByItem[this.i];
    var finished = state.solved;
    var selected = state.selected == null ? '' : choices[state.selected];
    var slotClass = 'verb-slot' + (finished ? ' right' : state.feedback === 'wrong' ? ' wrong' : '');
    var slot = '<button type="button" class="' + slotClass + '" data-slot="true" aria-label="' +
      esc(t('vh_slotLabel')) + '"' + (finished ? ' disabled' : '') + '>' +
      esc(finished ? item.answer : selected) + '</button>';
    var options = choices.map(function (word, i) {
      return '<button type="button" class="verb-word' + (state.selected === i ? ' selected' : '') +
        '" data-choice="' + i + '" aria-pressed="' + (state.selected === i) + '"' +
        (finished ? ' disabled' : '') + '>' + esc(word) + '</button>';
    }).join('');
    var feedback = finished ? t('vh_right', { n: C.verbPoints(state) })
      : state.feedback === 'wrong' ? t('vh_wrong', {
        n: C.verbPoints({ solved: true, wrong: state.wrong })
      })
        : state.feedback === 'empty' ? t('vh_empty')
          : state.skipped ? t('vh_skippedInfo') : '';
    var messageClass = finished ? 'ok' : state.feedback ? 'bad' : 'info';

    this.mount.innerHTML =
      '<div class="card ig-card verb-card">' +
      '<div class="ig-top"><span class="ig-progress">' + esc(t('vh_progress', { i: this.i + 1, n: this.totalItems })) + '</span>' +
      this.timerHtml() +
      '<span class="ig-points">' + esc(t('ig_points', { n: this.total() })) + '</span></div>' +
      '<p class="sub">' + esc(C.policyText(this.round, t)) + '</p>' +
      (this.reward ? '<div class="ig-reward" role="status">' + esc(this.reward) + '</div>' : '') +
      '<div class="ig-bar"><i style="width:' + Math.round(this.i / this.totalItems * 100) + '%"></i></div>' +
      '<div class="verb-bilingual">' +
      '<div class="verb-phrase" lang="en">' + (item.before ? '<span>' + esc(item.before) + '</span> ' : '') + slot +
      (item.after ? ' <span>' + esc(item.after) + '</span>' : '') + '</div>' +
      '<div class="verb-cn" lang="zh-CN">' + esc(item.cn) + '</div></div>' +
      '<p class="verb-instruction">' + esc(t('vh_dragTip')) + '</p>' +
      '<div class="verb-pool" aria-label="' + esc(t('vh_poolLabel')) + '">' + options + '</div>' +
      '<div class="ig-msg ' + messageClass + '" id="vhMsg" role="status">' + esc(feedback) + '</div>' +
      '<div class="ig-actions verb-actions">' +
      '<button type="button" class="btn ghost" id="vhPrev"' + (this.i === 0 ? ' disabled' : '') + '>' +
      esc(t('vh_prev')) + '</button>' +
      '<button type="button" class="btn ghost" id="vhNext">' +
      esc(t(this.i + 1 >= this.totalItems ? 'vh_complete' : 'vh_next')) + '</button>' +
      '<button type="button" class="btn ghost" id="vhSkip"' + (finished || state.skipped ? ' disabled' : '') + '>' +
      esc(state.skipped ? t('vh_skipped') : t('vh_skip')) + '</button>' +
      (this.reviewing ? '<button type="button" class="btn" id="vhFinish">' +
        esc(t('vh_finish')) + '</button>' : '') + '</div>' +
      '<p class="verb-finish-note">' + esc(t(this.reviewing ? 'vh_reviewHint' : 'vh_finishHint')) + '</p>' +
      '</div>';

    this.mount.querySelector('#vhPrev').onclick = function () { self.move(-1); };
    this.mount.querySelector('#vhNext').onclick = function () { self.move(1); };
    this.mount.querySelector('#vhSkip').onclick = function () { self.skip(); };
    if (this.reviewing) this.mount.querySelector('#vhFinish').onclick = function () { self.requestFinish(); };
    if (!finished) {
      this.mount.querySelector('[data-slot]').onclick = function () {
        if (!self.active()) return;
        state.selected = null;
        state.feedback = '';
        self.render();
      };
      this.mount.querySelectorAll('[data-choice]').forEach(function (button) {
        button.onclick = function () {
          if (!self.active() || self.justDragged) return;
          state.selected = parseInt(button.getAttribute('data-choice'), 10);
          state.skipped = false;
          state.feedback = '';
          self.render();
        };
        button.addEventListener('pointerdown', function (ev) { self.dragFrom(ev, button); });
      });
    }
  };

  Game.prototype.submit = function () {
    if (!this.active()) return false;
    var state = this.states[this.i], item = this.items[this.i];
    if (state.solved) return true;
    if (state.selected == null) { state.feedback = 'empty'; this.render(); return false; }
    if (C.verbCheck(this.choicesByItem[this.i][state.selected], item.answer)) {
      state.solved = true;
      state.skipped = false;
      state.feedback = '';
      var gain = this.round.hit(C.VERB.full, !state.wrong, this.ords[this.i]);
      this.reward = gain.combo >= 2 ? t('ig_comboReward', { n: gain.combo, points: gain.points, seconds: gain.seconds }) : '';
      this.checkpoint();
      if (this.solvedCount() === this.totalItems) this.finish();
      else this.render();
      return true;
    }
    state.wrong += 1;
    this.round.miss(this.ords[this.i]);
    this.reward = '';
    state.feedback = 'wrong';
    this.checkpoint();
    this.render();
    return false;
  };

  Game.prototype.move = function (delta) {
    if (!this.active()) return;
    if (delta > 0) {
      var state = this.states[this.i];
      if (!state.solved) {
        if (state.selected != null) {
          if (!this.submit() || this.done) return;
        } else {
          if (!state.skipped) this.round.miss(this.ords[this.i]);
          state.skipped = true;
          state.feedback = '';
          this.checkpoint();
        }
      }
      if (this.i + 1 >= this.totalItems) { this.requestFinish(); return; }
    }
    var next = this.i + delta;
    if (next < 0 || next >= this.totalItems) return;
    this.i = next;
    this.render();
  };

  Game.prototype.skip = function () {
    if (!this.active()) return;
    var state = this.states[this.i];
    if (state.solved || state.skipped) return;
    this.round.miss(this.ords[this.i]);
    this.reward = '';
    state.skipped = true;
    state.selected = null;
    state.feedback = '';
    this.move(1);
  };

  Game.prototype.dragFrom = function (ev, button) {
    var self = this;
    if (!this.active() || ev.button > 0 || this.dragPointer != null) return;
    var pointer = ev.pointerId, sx = ev.clientX, sy = ev.clientY, ghost = null;
    this.dragPointer = pointer;
    function move(e) {
      if (e.pointerId !== pointer) return;
      if (!ghost) {
        if (Math.abs(e.clientX - sx) + Math.abs(e.clientY - sy) < 8) return;
        var rect = button.getBoundingClientRect();
        ghost = button.cloneNode(true);
        ghost.classList.add('ig-ghost');
        ghost.style.width = rect.width + 'px';
        document.body.appendChild(ghost);
        button.style.visibility = 'hidden';
      }
      e.preventDefault();
      ghost.style.transform = 'translate(' + (e.clientX - sx + button.getBoundingClientRect().left) + 'px,' +
        (e.clientY - sy + button.getBoundingClientRect().top) + 'px) rotate(-2deg) scale(1.06)';
    }
    function end(e) {
      if (e && e.pointerId !== pointer) return;
      document.removeEventListener('pointermove', move);
      document.removeEventListener('pointerup', end);
      document.removeEventListener('pointercancel', end);
      self.dragPointer = null;
      self.cancelDrag = null;
      if (!ghost) return;
      ghost.remove();
      button.style.visibility = '';
      if (!self.active()) return;
      var slot = self.mount.querySelector('[data-slot]'), rect = slot && slot.getBoundingClientRect();
      if (e && e.type !== 'pointercancel' && rect && e.clientX >= rect.left - 18 && e.clientX <= rect.right + 18 &&
          e.clientY >= rect.top - 18 && e.clientY <= rect.bottom + 18) {
        self.states[self.i].selected = parseInt(button.getAttribute('data-choice'), 10);
        self.states[self.i].skipped = false;
        self.states[self.i].feedback = '';
      }
      self.justDragged = true;
      setTimeout(function () { self.justDragged = false; }, 0);
      self.render();
    }
    document.addEventListener('pointermove', move, { passive: false });
    document.addEventListener('pointerup', end);
    document.addEventListener('pointercancel', end);
    this.cancelDrag = function () { end(null); };
  };

  Game.prototype.requestFinish = function () {
    if (!this.active()) return;
    var state = this.states[this.i];
    if (!state.solved && state.selected != null && (!this.submit() || this.done)) return;
    if (this.solvedCount() === this.totalItems) { this.finish(); return; }
    this.finishPrompt = true;
    this.render();
  };

  Game.prototype.renderFinishPrompt = function () {
    var self = this, remaining = this.totalItems - this.solvedCount();
    this.mount.innerHTML = '<div class="card ig-card">' + this.timerHtml() +
      '<h2>' + esc(t('vh_unansweredTitle')) + '</h2><p>' + esc(t('vh_unansweredInfo', { n: remaining })) + '</p>' +
      '<div class="ig-actions"><button type="button" class="btn" id="vhReview">' + esc(t('vh_review')) +
      '</button><button type="button" class="btn ghost" id="vhFinishNow">' + esc(t('vh_finishNow')) +
      '</button></div></div>';
    this.mount.querySelector('#vhReview').onclick = function () {
      if (!self.active()) return;
      self.finishPrompt = false;
      self.reviewing = true;
      self.i = self.states.findIndex(function (state) { return !state.solved; });
      self.render();
    };
    this.mount.querySelector('#vhFinishNow').onclick = function () {
      if (self.active()) self.finish();
    };
  };

  Game.prototype.checkpoint = function () {
    if (this.cfg.progress) this.cfg.progress(this.report());
  };

  Game.prototype.report = function () {
    var results = this.allResults(), solved = this.solvedCount();
    var report = {
      score: this.total(), matched: solved, total_pairs: results.length,
      wrong: this.wrongCount(), best_combo: this.round.best,
      duration: this.round.elapsed(),
      level_count: 1,
      detail: results.map(function (result, i) {
        return {
          i: i, ord: result.ordinal, wrong: result.state.wrong, solved: result.state.solved,
          skipped: result.state.skipped, points: C.verbPoints(result.state)
        };
      })
    };
    return Object.assign(report, this.round.report());
  };

  Game.prototype.finish = function (timedOut) {
    if (this.done) return;
    this.done = true;
    this.round.pause();
    this.timedOut = !!timedOut;
    clearInterval(this.timer);
    if (this.cancelDrag) this.cancelDrag();
    this.states.forEach(function (state, i) {
      if (!state.solved && !state.skipped) {
        this.round.miss(this.ords[i]);
        state.skipped = true;
      }
    }, this);
    if (this.cfg.save) this.cfg.save(this.report());
    this.renderSummary();
  };

  Game.prototype.renderSummary = function () {
    var self = this, results = this.allResults();
    var rows = results.map(function (result) {
      var item = result.item, state = result.state;
      var status = state.solved ? t('vh_resRight', { w: state.wrong })
        : state.skipped ? t('vh_resSkipped', { w: state.wrong }) : t('vh_resMissed');
      var phrase = (item.before ? esc(item.before) + ' ' : '') +
        '<mark class="ig-key">' + esc(item.answer) + '</mark>' +
        (item.after ? ' ' + esc(item.after) : '');
      return '<tr><td>' + esc(item.cn) + '</td><td>' + phrase + '</td><td>' +
        esc(status) + '</td><td class="num">' + C.verbPoints(state) + '</td></tr>';
    }).join('');
    var solved = this.solvedCount();
    var skipped = this.states.filter(function (state) { return state.skipped && !state.solved; }).length;
    this.mount.innerHTML = '<div class="card ig-summary">' +
      '<h2>' + esc(t('vh_resultsTitle')) + '</h2><div class="ig-big">' + esc(t('ig_points', { n: this.total() })) + '</div>' +
      (this.timedOut ? '<p class="sub">' + esc(t('vh_timeout')) + '</p>' : '') +
      '<p class="sub">' + esc(t('vh_summary', { right: solved, skipped: skipped, n: results.length })) + '</p>' +
      '<div class="scroll"><table><thead><tr><th>' + esc(t('sp_colCn')) + '</th><th>' + esc(t('vh_colPhrase')) + '</th><th>' +
      esc(t('sp_colResult')) + '</th><th>' + esc(t('ig_colPoints')) + '</th></tr></thead><tbody>' + rows + '</tbody></table></div>' +
      '<div class="ig-actions"><button type="button" class="btn" id="vhAgain">' + esc(t('ig_again')) + '</button>' +
      (this.cfg.backHref ? '<a class="btn ghost" href="' + esc(this.cfg.backHref) + '">' + esc(t('ig_back')) + '</a>' : '') + '</div></div>';
    this.mount.querySelector('#vhAgain').onclick = function () { self.restart(); };
  };

  global.WPVerbUI = {
    start: function (mount, cfg) {
      var game = new Game(mount, cfg);
      if (global.WPI18N && global.WPI18N.onChange) global.WPI18N.onChange(function () { game.render(); });
      return game;
    }
  };
})(window);
