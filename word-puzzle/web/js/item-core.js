/* ============================================================
   item-core.js —— 新题型的纯运算（不碰页面）：单词大比拼（spell）、排排坐（order）、动词猎手（verb）
   ------------------------------------------------------------
   网站版和离线单文件页共用；node 里也能直接跑（tests/js/item_core.test.js）。
   计分规则（和 server/items.py 的 ORDER_* 保持一致，排排坐的最终分数由服务器按同样规则算）：
     拼写：每题 10 分；用一次提示扣 3 分，拼错一次扣 2 分；最后拼对至少得 1 分；看答案得 0 分。
     动词猎手：每题 10 分；每次选错扣 2 分；总共提交五次才答对得 0 分；跳过得 0 分。
     排排坐：每句拼接 10 分，每检查出错一次扣 2 分、最少 2 分；提交有效朗读 30 分；
             朗读和标准句子越接近，额外奖励越多，最多 20 分（服务器识别后给）。
   ============================================================ */
(function (global) {
  'use strict';

  var SPELL = { full: 10, hint: 3, wrong: 2, floor: 1 };
  var VERB = { full: 10, wrong: 2, floor: 0, maxAttempts: 5 };
  var ORDER = { arrange: 10, wrong: 2, floor: 2, recording: 30, bonusMax: 20 };

  function squash(text) { return String(text == null ? '' : text).replace(/\s+/g, ' ').trim(); }
  function key(text) { return squash(text).toLowerCase(); }

  /* 两个词差几个字母（编辑距离）；只用来判断「差一点」 */
  function distance(a, b) {
    var prev = [], cur, i, j;
    for (j = 0; j <= b.length; j++) prev[j] = j;
    for (i = 1; i <= a.length; i++) {
      cur = [i];
      for (j = 1; j <= b.length; j++) {
        cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a.charAt(i - 1) === b.charAt(j - 1) ? 0 : 1));
      }
      prev = cur;
    }
    return prev[b.length];
  }

  /* 拼写判分：不分大小写、多余空格不算。right / close（差一两个字母）/ wrong / empty */
  function spellCheck(typed, answer) {
    var a = key(typed), b = key(answer);
    if (!a) return 'empty';
    if (a === b) return 'right';
    var d = distance(a, b);
    return (d <= 1 || (b.length >= 7 && d <= 2)) ? 'close' : 'wrong';
  }

  function spellPoints(state) {
    if (state.gaveUp || !state.solved) return 0;
    return Math.max(SPELL.floor, SPELL.full - SPELL.hint * (state.hints || 0) - SPELL.wrong * (state.wrong || 0));
  }

  function verbPoints(state) {
    if (!state.solved) return 0;
    if ((state.wrong || 0) + 1 >= VERB.maxAttempts) return 0;
    return Math.max(VERB.floor, VERB.full - VERB.wrong * (state.wrong || 0));
  }

  function verbCheck(choice, answer) {
    return choice != null && key(choice) === key(answer);
  }

  /* 提示：第一次只给字母个数，第二次再给首字母 */
  function spellHint(answer, level) {
    var letters = String(answer).split('');
    return letters.map(function (ch, i) {
      if (ch === ' ' || ch === '-' || ch === "'") return ch;
      return (level >= 2 && i === 0) ? ch : '_';
    }).join(' ');
  }

  /* 可重现的随机数（同一个种子同样的顺序，方便测试） */
  function rng(seed) {
    var s = (seed >>> 0) || 1;
    return function () { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; };
  }

  /* 打乱片段：返回下标的排列；两个以上片段时保证和原来的顺序不一样 */
  function shuffle(n, seed) {
    var r = rng(seed), out = [], i, j, tmp, tries = 0;
    do {
      out = [];
      for (i = 0; i < n; i++) out.push(i);
      for (i = n - 1; i > 0; i--) { j = Math.floor(r() * (i + 1)); tmp = out[i]; out[i] = out[j]; out[j] = tmp; }
      tries++;
    } while (n > 1 && tries < 20 && out.every(function (v, k) { return v === k; }));
    if (n > 1 && out.every(function (v, k) { return v === k; })) { tmp = out[0]; out[0] = out[1]; out[1] = tmp; }
    return out;
  }

  /* 每题从完整词库随机抽四个非答案词，与正确答案一起打乱。 */
  function dealVerbChoices(items, pool, seed) {
    if (!Array.isArray(items) || !Array.isArray(pool) || !items.length) throw new Error('verb_choices_invalid');
    var answerKeys = {}, poolKeys = {};
    items.forEach(function (item) {
      var k = key(item && item.answer);
      if (!k || answerKeys[k]) throw new Error('verb_choices_invalid');
      answerKeys[k] = true;
    });
    pool.forEach(function (word) {
      var k = key(word);
      if (!k || poolKeys[k]) throw new Error('verb_choices_invalid');
      poolKeys[k] = true;
    });
    Object.keys(answerKeys).forEach(function (k) {
      if (!poolKeys[k]) throw new Error('verb_choices_invalid');
    });
    return items.map(function (item, k) {
      var answerKey = key(item.answer);
      var candidates = pool.filter(function (word) { return key(word) !== answerKey; });
      if (candidates.length < 4) throw new Error('verb_choices_invalid');
      var decoys = shuffle(candidates.length, (seed + (k + 1) * 1013904223) >>> 0)
        .slice(0, 4).map(function (i) { return candidates[i]; });
      var options = [item.answer].concat(decoys);
      var order = shuffle(options.length, (seed + (k + 1) * 2654435761) >>> 0);
      return order.map(function (i) { return options[i]; });
    });
  }

  function fragmentText(fragment) {
    return (fragment.segs || []).map(function (s) { return s[0]; }).join('');
  }

  /* 排好的顺序对不对：按文字比（两个片段文字一样时换位置也算对）。firstWrong = 第一个放错的位置，-1 = 全对 */
  function orderCheck(fragments, placed) {
    var firstWrong = -1;
    for (var i = 0; i < fragments.length; i++) {
      var got = placed[i] == null ? null : squash(fragmentText(fragments[placed[i]]));
      if (got !== squash(fragmentText(fragments[i]))) { firstWrong = i; break; }
    }
    return { ok: firstWrong < 0 && placed.length === fragments.length, firstWrong: firstWrong };
  }

  function orderSentence(fragments, placed) {
    return squash(placed.map(function (i) { return fragmentText(fragments[i]); }).join(' '));
  }

  /* 拖动放片段：fromSlot = 从下面框里第几个拖出来（从上面拖来的是 null）；index = 松手时它在框里的位置
     （按拿掉它之后剩下的片段数）；index 为 null = 拖到框外松手（从框里拖出来的就退回上面）。返回新的顺序，不改原数组 */
  function placeAt(placed, frag, index, fromSlot) {
    var out = placed.slice();
    if (fromSlot != null) out.splice(fromSlot, 1);
    if (index == null) return out;
    index = Math.max(0, Math.min(out.length, index));
    out.splice(index, 0, frag);
    return out;
  }

  function orderArrangePoints(wrong) {
    return Math.max(ORDER.floor, ORDER.arrange - ORDER.wrong * (wrong || 0));
  }

  /* 一句的总分：拼接 + 有效朗读 + 奖励（奖励由服务器给，没识别完时是 0） */
  function orderPoints(state) {
    if (!state.arranged) return 0;
    return orderArrangePoints(state.wrong) + (state.recordingValid ? ORDER.recording : 0) + (state.bonus || 0);
  }

  /* 关名：服务器给 {unit, part, parts}（见 server/items.py 的 levels）。t 是翻译函数（WPI18N.t），
     由页面传进来，这个文件本身不依赖界面。单元名空着就叫「第 k+1 关」；一个单元分成几段时加上「(i/n)」。 */
  function levelName(group, k, t) {
    var unit = group.unit || t('ig_level', { n: k + 1 });
    if ((group.parts || 1) > 1 && group.unit) return t('ig_levelPart', { unit: unit, i: group.part, n: group.parts });
    return unit;
  }

  global.WPItemCore = {
    SPELL: SPELL, VERB: VERB, ORDER: ORDER,
    squash: squash, key: key, distance: distance,
    spellCheck: spellCheck, spellPoints: spellPoints, spellHint: spellHint,
    verbCheck: verbCheck, verbPoints: verbPoints, dealVerbChoices: dealVerbChoices,
    rng: rng, shuffle: shuffle, fragmentText: fragmentText,
    orderCheck: orderCheck, orderSentence: orderSentence, placeAt: placeAt,
    orderArrangePoints: orderArrangePoints, orderPoints: orderPoints, levelName: levelName
  };
})(typeof window !== 'undefined' ? window : this);
