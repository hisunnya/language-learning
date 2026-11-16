/* ============================================================
   practice-ui.js —— 读音练习：单词纵向排列，点单词听发音，中文默认藏起来
   ------------------------------------------------------------
   网站版（practice.html）和离线单文件版共用这一份。
   * 点单词：发音（网站版取后端 /api/audio/，离线版用内嵌的语音）；
   * 第二列是中文意思，默认藏着：点它、或者在这一行上向右滑（手指 / 鼠标都行）就显示，再点或向左滑又藏起来；
   * 竖着滚动不受影响（行上 touch-action: pan-y）；滑动之后不会误触发发音；
   * 键盘：Tab 到一行，Enter / 空格 = 发音，→ 显示中文，← 隐藏。
   ============================================================ */
(function (global) {
  'use strict';

  var SWIPE_MIN = 48;                     /* 横向至少滑这么多像素才算 */
  var SUPPRESS_CLICK_MS = 450;            /* 滑完之后这段时间里的点击不当作「点单词」 */

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function t(key, params) { return global.WPI18N ? WPI18N.t(key, params) : key; }

  /* 手势判断：向右 → 'reveal'，向左 → 'hide'，其他（竖着滚、滑得太短、斜着滑）→ null */
  function swipe(dx, dy) {
    if (Math.abs(dx) < SWIPE_MIN || Math.abs(dy) > Math.abs(dx) * 0.6) return null;
    return dx > 0 ? 'reveal' : 'hide';
  }

  function audioKey(en) { return String(en || '').trim().toLowerCase(); }

  /* ---------------- 发音 ---------------- */

  /* cfg.audio：内嵌的 {小写单词: data URI}（离线版）；cfg.base：后端地址前缀（网站版，形如 /word-puzzle/api/audio/） */
  function createPlayer(cfg) {
    var cache = {}, current = null;
    function url(en) {
      if (cfg.audio) return cfg.audio[audioKey(en)] || '';
      return cfg.base ? cfg.base + encodeURIComponent(String(en).trim()) : '';
    }
    function stop() {
      if (current) { try { current.pause(); } catch (e) { } current = null; }
    }
    function play(en) {
      var key = audioKey(en), u = url(en);
      if (!key || !u) { if (cfg.onError) cfg.onError(en); return false; }
      stop();
      var a = cache[key];
      if (!a) {
        a = cache[key] = new Audio(u);
        a.addEventListener('error', function () { cache[key] = null; if (cfg.onError) cfg.onError(en); });
      }
      try { a.currentTime = 0; } catch (e) { }
      current = a;
      var p = a.play();
      if (p && p.catch) p.catch(function () { if (cfg.onError) cfg.onError(en); });
      return true;
    }
    /* 网站版：先悄悄把前面的词取回来（浏览器会缓存），点的时候就不用等合成；一次只取两个，别压垮服务器 */
    function prefetch(words, limit) {
      if (cfg.audio || !cfg.base || typeof fetch !== 'function') return;
      var queue = words.slice(0, limit || 30), active = 0;
      function next() {
        while (active < 2 && queue.length) {
          active++;
          fetch(url(queue.shift()), { credentials: 'same-origin' }).catch(function () { }).then(function () { active--; next(); });
        }
      }
      next();
    }
    return { play: play, stop: stop, prefetch: prefetch, url: url };
  }

  /* ---------------- 页面 ---------------- */

  function rowHtml(w, index) {
    return '<div class="prac-row" role="listitem" data-i="' + index + '" data-en="' + esc(w.en) + '" tabindex="-1">' +
      '<button type="button" class="prac-word" data-act="play" aria-label="' + esc(t('prac_play', { word: w.en })) + '">' +
        '<span class="prac-icon" aria-hidden="true">🔊</span>' +
        '<span class="prac-text"><span class="prac-en">' + esc(w.en) + '</span>' +
        (w.ipa ? '<span class="prac-ipa">' + esc(w.ipa) + '</span>' : '') + '</span></button>' +
      '<button type="button" class="prac-cn" data-act="cn" aria-expanded="false" aria-label="' + esc(t('prac_reveal')) + '">' +
        '<span class="prac-cn-text" aria-hidden="true">' + esc(w.cn) + '</span>' +
        '<span class="prac-cn-hint">' + esc(t('prac_hint')) + '</span></button></div>';
  }

  function listHtml(groups) {
    var index = 0;
    var many = groups.length > 1;
    return groups.map(function (g) {
      var head = many ? '<h3 class="prac-unit">' + esc(g.unit || g.name || '') +
        ' <small>' + esc(t(g.words.length === 1 ? 'prac_countOne' : 'prac_count', { n: g.words.length })) + '</small></h3>' : '';
      return '<section class="prac-group">' + head + '<div class="prac-list" role="list">' +
        g.words.map(function (w) { return rowHtml(w, index++); }).join('') + '</div></section>';
    }).join('');
  }

  function setRevealed(row, on) {
    row.classList.toggle('on', on);
    var cn = row.querySelector('.prac-cn');
    cn.setAttribute('aria-expanded', String(on));
    cn.querySelector('.prac-cn-text').setAttribute('aria-hidden', String(!on));
    cn.setAttribute('aria-label', t(on ? 'prac_hide' : 'prac_reveal'));
  }

  /* cfg: { mount, groups: [{unit, words:[{en,cn,ipa}]}], player, now? } 返回 { revealAll(on), allRevealed() } */
  function init(cfg) {
    var mount = cfg.mount, player = cfg.player, groups = cfg.groups;
    var clock = cfg.now || function () { return Date.now(); };
    mount.innerHTML = listHtml(groups);
    var start = null, suppressUntil = 0;

    function rows() { return mount.querySelectorAll('.prac-row'); }
    function allRevealed() {
      var all = rows();
      return all.length > 0 && Array.prototype.every.call(all, function (r) { return r.classList.contains('on'); });
    }
    function revealAll(on) {
      Array.prototype.forEach.call(rows(), function (r) { setRevealed(r, on); });
    }

    var speakingTimer = null;
    function speak(row) {
      Array.prototype.forEach.call(mount.querySelectorAll('.prac-row.speaking'), function (r) { r.classList.remove('speaking'); });
      if (!player.play(row.getAttribute('data-en'))) return;
      row.classList.add('speaking');
      clearTimeout(speakingTimer);
      speakingTimer = setTimeout(function () { row.classList.remove('speaking'); }, 1500);
    }

    mount.addEventListener('click', function (ev) {
      var btn = ev.target.closest('[data-act]');
      if (!btn || clock() < suppressUntil) return;          /* 刚滑完：这次点击是滑动带出来的，不算 */
      var row = btn.closest('.prac-row');
      if (btn.getAttribute('data-act') === 'play') speak(row);
      else setRevealed(row, !row.classList.contains('on'));
    });

    mount.addEventListener('pointerdown', function (ev) {
      var row = ev.target.closest('.prac-row');
      start = row ? { row: row, x: ev.clientX, y: ev.clientY } : null;
    });
    function finish(ev) {
      if (!start) return;
      var kind = swipe(ev.clientX - start.x, ev.clientY - start.y);
      if (kind) {
        setRevealed(start.row, kind === 'reveal');
        suppressUntil = clock() + SUPPRESS_CLICK_MS;
      }
      start = null;
    }
    mount.addEventListener('pointerup', finish);
    mount.addEventListener('pointercancel', function () { start = null; });

    mount.addEventListener('keydown', function (ev) {
      var row = ev.target.closest('.prac-row');
      if (!row) return;
      if (ev.key === 'ArrowRight') { setRevealed(row, true); ev.preventDefault(); }
      else if (ev.key === 'ArrowLeft') { setRevealed(row, false); ev.preventDefault(); }
    });

    /* 切换语言：提示文字是脚本画的，要重画；保留哪些行已经显示了中文 */
    function redraw() {
      var open = {};
      Array.prototype.forEach.call(rows(), function (r) { if (r.classList.contains('on')) open[r.getAttribute('data-i')] = true; });
      mount.innerHTML = listHtml(groups);
      Array.prototype.forEach.call(rows(), function (r) { if (open[r.getAttribute('data-i')]) setRevealed(r, true); });
    }
    if (global.WPI18N && WPI18N.onChange) WPI18N.onChange(redraw);

    return { revealAll: revealAll, allRevealed: allRevealed, redraw: redraw };
  }

  global.WPPractice = {
    SWIPE_MIN: SWIPE_MIN, swipe: swipe, audioKey: audioKey, createPlayer: createPlayer,
    rowHtml: rowHtml, listHtml: listHtml, setRevealed: setRevealed, init: init
  };
})(window);
