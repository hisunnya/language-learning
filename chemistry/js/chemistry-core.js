/* 化学探秘的新题型出题层：数值填空、配对、排序、找错。纯计算，不碰 DOM，可以在 node 里直接测。
 * （原有的选择题仍在 chemistry.js 里。）
 *
 * 初中和高中用整数相对原子质量（H 1、C 12、O 16…），大学用 chemistry.json 里的 IUPAC 标准原子量。 */
(function (root) {
  'use strict';

  var STAGES = ['junior', 'high', 'university'];
  var TOLERANCE = 0.005;
  var INT_MASS = { H: 1, C: 12, N: 14, O: 16, F: 19, Na: 23, Mg: 24, Al: 27, Si: 28, P: 31, S: 32,
    Cl: 35.5, K: 39, Ca: 40, Mn: 55, Fe: 56, Cu: 64, Zn: 65, Ag: 108, Ba: 137 };
  var SUBSCRIPT = '₀₁₂₃₄₅₆₇₈₉';

  function pick(list, rng) { return list[Math.floor(rng() * list.length)]; }

  /* 按学段取题：初中只出初中题，高中出初中+高中题，大学出全部。
   * 数据里每条都带 level 标记（junior / high），不再靠数组顺序切片。 */
  function byLevel(items, stage) {
    if (!items || !items.length) return [];
    if (stage === 'junior') return items.filter(function (x) { return x.level === 'junior'; });
    if (stage === 'high') return items.filter(function (x) { return x.level === 'junior' || x.level === 'high'; });
    return items.slice();
  }
  function shuffle(list, rng) {
    var out = list.slice();
    for (var i = out.length - 1; i > 0; i--) {
      var j = Math.floor(rng() * (i + 1));
      var tmp = out[i]; out[i] = out[j]; out[j] = tmp;
    }
    return out;
  }
  function fmt(value) { return String(Number(value.toPrecision(4))); }
  function fmtMass(value) { return String(Number(value.toPrecision(5))); }
  function same(text) { return { key: text, zh: text, en: text }; }
  function sub(text) { return String(text).replace(/[0-9]/g, function (n) { return SUBSCRIPT[Number(n)]; }); }

  /* 解析化学式：Fe2O3 → {Fe:2, O:3}；支持括号，如 Ca(OH)2 */
  function parseFormula(text) {
    var pos = 0;
    function group() {
      var counts = {};
      while (pos < text.length && text[pos] !== ')') {
        if (text[pos] === '(') {
          pos++;
          var inner = group();
          pos++; // ')'
          var mult = number();
          Object.keys(inner).forEach(function (k) { counts[k] = (counts[k] || 0) + inner[k] * mult; });
        } else {
          var m = /^[A-Z][a-z]?/.exec(text.slice(pos));
          if (!m) throw new Error('化学式无法解析：' + text);
          pos += m[0].length;
          counts[m[0]] = (counts[m[0]] || 0) + number();
        }
      }
      return counts;
    }
    function number() {
      var m = /^\d+/.exec(text.slice(pos));
      if (!m) return 1;
      pos += m[0].length;
      return Number(m[0]);
    }
    return group();
  }

  function weigh(counts, table) {
    return Object.keys(counts).reduce(function (sum, symbol) { return sum + counts[symbol] * table[symbol]; }, 0);
  }
  function realMasses(data) {
    var table = {};
    data.elements.forEach(function (e) { table[e.symbol] = e.mass; });
    return table;
  }
  function weightText(counts, table, toText) {
    return Object.keys(counts).map(function (s) {
      return counts[s] === 1 ? toText(table[s]) : counts[s] + ' × ' + toText(table[s]);
    }).join(' + ');
  }

  /* ---------------- 数值填空 ---------------- */
  function numericQuestion(data, stage, rng) {
    rng = rng || Math.random;
    var f, value, unit = '', zh, en, visual, explain, id;
    if (stage === 'junior' || (stage === 'high' && rng() < 0.5)) {
      var pool = byLevel(data.formulas, stage);
      f = pick(pool, rng);
      var mr = weigh(f.atoms, INT_MASS);
      var parts = Object.keys(f.atoms).map(function (s) { return (f.atoms[s] === 1 ? '' : f.atoms[s] + '×') + INT_MASS[s]; }).join(' + ');
      if (stage === 'junior') {
        id = 'relative-mass'; value = mr; visual = sub(f.formula);
        zh = '「' + f.zh + '」（' + sub(f.formula) + '）的相对分子质量是多少？';
        en = 'What is the relative molecular mass of ' + f.en + ' (' + sub(f.formula) + ')?';
        explain = 'Mr(' + sub(f.formula) + ') = ' + parts + ' = ' + fmt(mr);
      } else {
        var n = pick([0.5, 1, 2, 3], rng);
        if (rng() < 0.5) {
          id = 'mass-from-moles'; value = n * mr; unit = 'g'; visual = 'm = n × M';
          zh = n + ' mol「' + f.zh + '」（' + sub(f.formula) + '）的质量是多少？';
          en = 'What is the mass of ' + n + ' mol of ' + f.en + ' (' + sub(f.formula) + ')?';
          explain = 'm = n × M = ' + n + ' × ' + fmt(mr) + ' = ' + fmt(value) + ' g（M = ' + parts + '）';
        } else {
          id = 'moles-from-mass'; value = n; unit = 'mol'; visual = 'n = m ÷ M';
          var grams = n * mr;
          zh = fmt(grams) + ' g「' + f.zh + '」（' + sub(f.formula) + '）的物质的量是多少？';
          en = 'How many moles are in ' + fmt(grams) + ' g of ' + f.en + ' (' + sub(f.formula) + ')?';
          explain = 'n = m ÷ M = ' + fmt(grams) + ' ÷ ' + fmt(mr) + ' = ' + n + ' mol（M = ' + parts + '）';
        }
      }
    } else {
      var kind = pick(['molar', 'conc', 'ph'], rng);
      if (kind === 'molar') {
        f = pick(data.formulas, rng);
        var table = realMasses(data);
        value = weigh(f.atoms, table); unit = 'g/mol'; id = 'molar-mass'; visual = sub(f.formula);
        zh = '「' + f.zh + '」（' + sub(f.formula) + '）的摩尔质量约是多少？';
        en = 'What is the approximate molar mass of ' + f.en + ' (' + sub(f.formula) + ')?';
        explain = 'M = ' + weightText(f.atoms, table, fmtMass) + ' = ' + fmt(value) + ' g/mol';
      } else if (kind === 'conc') {
        var mol = pick([0.1, 0.2, 0.5, 1, 2], rng), vol = pick([0.1, 0.25, 0.5, 2], rng);
        id = 'concentration'; value = mol / vol; unit = 'mol/L'; visual = 'c = n ÷ V';
        zh = '把 ' + mol + ' mol 溶质配成 ' + vol + ' L 溶液，物质的量浓度是多少？';
        en = 'A solution is made from ' + mol + ' mol of solute in ' + vol + ' L. What is its molar concentration?';
        explain = 'c = n ÷ V = ' + mol + ' ÷ ' + vol + ' = ' + fmt(value) + ' mol/L';
      } else {
        var ph = pick(data.phQuestions, rng);
        id = 'ph'; value = ph.answer; visual = 'pH';
        zh = '「' + ph.zh + '」的 pH 是多少？'; en = 'What is the pH of ' + ph.en + '?';
        explain = (ph.kind === 'acid' ? 'pH = −lg c(H⁺) = −lg ' + ph.molarity + ' = ' + ph.answer
          : 'pOH = −lg ' + ph.molarity + ' = ' + (14 - ph.answer) + '，pH = 14 − ' + (14 - ph.answer) + ' = ' + ph.answer);
      }
    }
    return {
      id: id, type: 'numeric', kicker: { zh: '数值填空', en: 'Fill in the number' }, visual: visual, zh: zh, en: en,
      explain: explain, value: value, unit: unit, tolerance: TOLERANCE,
      answerText: (fmt(value) + ' ' + unit).trim()
    };
  }

  function parseNumber(text) {
    var cleaned = String(text == null ? '' : text).trim().replace(/,/g, '.');
    if (!/^[-+]?(\d+\.?\d*|\.\d+)(e[-+]?\d+)?$/i.test(cleaned)) return NaN;
    return Number(cleaned);
  }
  function checkNumeric(question, text) {
    var got = parseNumber(text);
    if (!isFinite(got)) return false;
    return Math.abs(got - question.value) <= Math.abs(question.value) * question.tolerance;
  }

  /* ---------------- 配对 ---------------- */
  function matchQuestion(data, stage, rng) {
    rng = rng || Math.random;
    var table = realMasses(data);
    var spec = {
      junior: { kicker: { zh: '元素配符号', en: 'Match element to symbol' },
        zh: '把元素名称和它的元素符号配成对', en: 'Pair each element with its symbol',
        source: data.elements.filter(function (e) { return e.number <= 20; }),
        left: function (e) { return { zh: e.zh, en: e.en }; }, right: function (e) { return same(e.symbol); } },
      high: { kicker: { zh: '物质配化学式', en: 'Match substance to formula' },
        zh: '把物质名称和它的化学式配成对', en: 'Pair each substance with its formula',
        source: byLevel(data.formulas, 'high'),
        left: function (f) { return { zh: f.zh, en: f.en }; }, right: function (f) { return same(sub(f.formula)); } },
      university: { kicker: { zh: '化学式配摩尔质量', en: 'Match formula to molar mass' },
        zh: '把化学式和它的摩尔质量（g/mol）配成对', en: 'Pair each formula with its molar mass (g/mol)',
        source: data.formulas,
        left: function (f) { return same(sub(f.formula)); },
        right: function (f) { return same(weigh(f.atoms, table).toFixed(2) + ' g/mol'); } }
    }[stage];
    var chosen = [], l = {}, r = {};
    shuffle(spec.source, rng).forEach(function (item) {
      var left = spec.left(item), right = spec.right(item);
      if (chosen.length < 4 && !l[left.zh] && !r[right.zh]) {
        l[left.zh] = true; r[right.zh] = true;
        chosen.push({ key: left.zh, left: left, right: right });
      }
    });
    return { id: 'match', type: 'match', kicker: spec.kicker, visual: '', zh: spec.zh, en: spec.en, pairs: chosen,
      explain: chosen.map(function (p) { return p.left.zh + ' ↔ ' + p.right.zh; }).join('；') };
  }

  /* ---------------- 排序 ---------------- */
  /* 排四样东西：按数值排序后，从所有「相邻两项间距都够大」的四元组里随机挑一个。
   * 以前是随机试 300 次再退回到「排序后最前面四个」，那一步会悄悄破坏间距规则，
   * 现在把候选穷举出来再挑，既保证间距又保证有变化。 */
  function spread(items, valueOf, gap, rng) {
    var sorted = items.slice().sort(function (a, b) { return valueOf(a) - valueOf(b); });
    var n = sorted.length;
    if (n < 4) return sorted.slice(0, 4);
    var valid = [];
    var a, b, c, d, i;
    if (n <= 30) {
      for (a = 0; a < n - 3; a++) {
        for (b = a + 1; b < n - 2; b++) {
          for (c = b + 1; c < n - 1; c++) {
            for (d = c + 1; d < n; d++) {
              if (valueOf(sorted[b]) - valueOf(sorted[a]) >= gap - 1e-9 &&
                  valueOf(sorted[c]) - valueOf(sorted[b]) >= gap - 1e-9 &&
                  valueOf(sorted[d]) - valueOf(sorted[c]) >= gap - 1e-9) {
                valid.push([sorted[a], sorted[b], sorted[c], sorted[d]]);
              }
            }
          }
        }
      }
    } else {
      for (var attempt = 0; attempt < 500 && valid.length < 40; attempt++) {
        var idx = shuffle(sorted.map(function (_, k) { return k; }), rng).slice(0, 4).sort(function (x, y) { return x - y; });
        var win = idx.map(function (k) { return sorted[k]; });
        var ok = true;
        for (i = 1; i < 4; i++) {
          if (valueOf(win[i]) - valueOf(win[i - 1]) < gap - 1e-9) { ok = false; break; }
        }
        if (ok) valid.push(win);
      }
    }
    if (!valid.length) return sorted.slice(0, 4);
    return valid[Math.floor(rng() * valid.length)];
  }

  function orderQuestion(data, stage, rng) {
    rng = rng || Math.random;
    var table = realMasses(data);
    var asc = rng() < 0.5;
    var four, label, valueText, zh, en, kicker;
    if (stage === 'junior') {
      four = spread(data.elements.filter(function (e) { return e.number <= 20; }), function (e) { return e.number; }, 2, rng);
      label = function (e) { return { key: e.symbol, zh: e.symbol + ' · ' + e.zh, en: e.symbol + ' · ' + e.en, value: e.number }; };
      valueText = function (e) { return e.symbol + ' ' + e.number; };
      kicker = { zh: '原子序数排序', en: 'Order by atomic number' };
      zh = '把这些元素按原子序数' + (asc ? '由小到大' : '由大到小') + '排序';
      en = 'Sort these elements by atomic number, ' + (asc ? 'smallest to largest' : 'largest to smallest');
    } else if (stage === 'high') {
      four = spread(byLevel(data.phSubstances, stage), function (x) { return x.ph; }, 1.2, rng);
      label = function (x) { return { key: x.zh, zh: x.zh, en: x.en, value: x.ph }; };
      valueText = function (x) { return x.zh + ' pH ' + x.ph; };
      kicker = { zh: 'pH 排序', en: 'Order by pH' };
      zh = '把这些溶液按 pH ' + (asc ? '由小到大（酸性由强到弱）' : '由大到小（碱性由强到弱）') + '排序';
      en = 'Sort these by pH, ' + (asc ? 'lowest to highest (strongest acid first)' : 'highest to lowest (strongest base first)');
    } else {
      four = spread(data.formulas, function (f) { return weigh(f.atoms, table); }, 8, rng);
      label = function (f) { return { key: f.formula, zh: sub(f.formula), en: sub(f.formula), value: weigh(f.atoms, table) }; };
      valueText = function (f) { return sub(f.formula) + ' ' + weigh(f.atoms, table).toFixed(2); };
      kicker = { zh: '摩尔质量排序', en: 'Order by molar mass' };
      zh = '把这些物质按摩尔质量' + (asc ? '由小到大' : '由大到小') + '排序';
      en = 'Sort these by molar mass, ' + (asc ? 'smallest to largest' : 'largest to smallest');
    }
    if (!asc) four.reverse();
    return { id: 'order', type: 'order', kicker: kicker, visual: '', zh: zh, en: en,
      items: four.map(label), explain: four.map(valueText).join(asc ? ' ＜ ' : ' ＞ ') };
  }

  /* ---------------- 找错 ---------------- */
  var STEP_CHOICES = [
    { key: '1', zh: '第 ① 步', en: 'Step ①' }, { key: '2', zh: '第 ② 步', en: 'Step ②' },
    { key: '3', zh: '第 ③ 步', en: 'Step ③' }, { key: '0', zh: '没有错误', en: 'No mistake' }];

  function parseReaction(entry) {
    var sides = entry.prompt.split('→');
    var split = function (side) { return side.split('+').map(function (t) { return t.trim(); }); };
    return { reactants: split(sides[0]), products: split(sides[1]),
      coefficients: entry.answer.split(',').map(function (c) { return Number(c.trim()); }) };
  }

  // 返回方程式两边个数不相等的元素
  function unbalanced(reaction, coefficients) {
    var left = {}, right = {}, n = reaction.reactants.length;
    reaction.reactants.forEach(function (f, i) {
      var c = parseFormula(f);
      Object.keys(c).forEach(function (s) { left[s] = (left[s] || 0) + c[s] * coefficients[i]; });
    });
    reaction.products.forEach(function (f, i) {
      var c = parseFormula(f);
      Object.keys(c).forEach(function (s) { right[s] = (right[s] || 0) + c[s] * coefficients[n + i]; });
    });
    return Object.keys(left).filter(function (s) { return left[s] !== right[s]; }).sort();
  }

  function equationText(reaction, coefficients) {
    var n = reaction.reactants.length;
    var term = function (f, i) { return (coefficients[i] === 1 ? '' : coefficients[i] + ' ') + sub(f); };
    return reaction.reactants.map(function (f, i) { return term(f, i); }).join(' + ') + ' → ' +
      reaction.products.map(function (f, i) { return term(f, n + i); }).join(' + ');
  }

  /* ---------------- 配平题的选项：每次现算，不写死在题库里 ----------------
   * 以前每个反应在题库里写死 4 个系数选项，整个题库只有 8 道题、26 个不同的系数串，
   * 学生翻来覆去就是那几组数字。现在干扰项按学生真会犯的错现场生成：
   *   ① 某一个系数写错（+1 / −1 / +2 …）
   *   ② 两个系数对调
   *   ③ 某个系数忘了乘，抄成了 1
   * 每个干扰项都要用 unbalanced() 验算过：必须真的配不平，也不能和正确答案重复，
   * 所以这道题永远只有一个站得住脚的答案。 */
  function balanceChoices(reaction, rng) {
    rng = rng || Math.random;
    var correct = reaction.coefficients.slice();
    var n = correct.length;
    var correctKey = correct.join(',');
    var pool = [];
    function push(c) {
      if (!c || c.length !== n) return;
      for (var i = 0; i < c.length; i++) {
        if (!isFinite(c[i]) || c[i] < 1 || Math.floor(c[i]) !== c[i]) return;
      }
      var key = c.join(',');
      if (key === correctKey) return;
      for (var j = 0; j < pool.length; j++) if (pool[j].join(',') === key) return;
      if (!unbalanced(reaction, c).length) return;   /* 配平了就不算错误答案 */
      pool.push(c);
    }
    var i, j, k, c;
    for (i = 0; i < n; i++) {
      [1, -1, 2, -2, 3, -3].forEach(function (delta) {
        var cc = correct.slice(); cc[i] = cc[i] + delta; push(cc);
      });
    }
    for (i = 0; i < n; i++) {
      for (j = i + 1; j < n; j++) {
        c = correct.slice(); k = c[i]; c[i] = c[j]; c[j] = k; push(c);
      }
    }
    for (i = 0; i < n; i++) { c = correct.slice(); c[i] = 1; push(c); }
    /* 兜底：万一上面凑不满 3 个，就按系数逐一试 +/-1 再试整体缩放 */
    for (var extra = 0; extra < n && pool.length < 3; extra++) {
      for (var d = 1; d <= 4 && pool.length < 3; d++) {
        c = correct.slice(); c[extra % n] = c[extra % n] + d; push(c);
        c = correct.slice(); c[extra % n] = c[extra % n] - d; push(c);
      }
    }
    var picked = shuffle(pool, rng).slice(0, 3);
    var all = shuffle([correct].concat(picked), rng);
    return {
      answer: correct.join(', '),
      choices: all.map(function (cc) { return cc.join(', '); }),
      keys: all.map(function (cc) { return cc.join(','); })
    };
  }

  /* ---------------- pH 选项：围绕真实 pH 生成，而不是相邻整数 ----------------
   * 干扰项优先取「别的溶液的真实 pH」（学生最容易把胃液和柠檬汁搞混），
   * 凑不够再按 0.5 / 1 / 1.5 的步长偏移。 */
  function phChoices(item, pool, rng) {
    rng = rng || Math.random;
    var answer = Number(item.ph);
    /* 键统一用一位小数：题库里两种溶液常常是同一个 pH（柠檬汁和胃液都是 2.0），
       如果正确答案的键和干扰项的键写法不一样，那个同 pH 的溶液就会变成第二个
       「正确答案」——页面上就出现两个一模一样的选项。 */
    var used = {};
    used[answer.toFixed(1)] = true;
    var distractors = [];
    function add(value) {
      if (!isFinite(value) || value <= 0 || value > 14) return;
      var rounded = Math.round(value * 10) / 10;
      var key = rounded.toFixed(1);
      if (used[key]) return;
      used[key] = true;
      distractors.push(rounded);
    }
    /* 别的物质的真实 pH：最有迷惑性 */
    (pool || []).forEach(function (other) {
      if (other === item || other.ph === undefined) return;
      if (distractors.length < 3) add(Number(other.ph));
    });
    [0.5, -0.5, 1, -1, 1.5, -1.5, 2, -2, 0.2, -0.2, 0.3, -0.3, 2.5, -2.5].forEach(function (delta) {
      if (distractors.length < 3) add(answer + delta);
    });
    var picked = shuffle(distractors, rng).slice(0, 3);
    var all = shuffle([answer].concat(picked), rng);
    return {
      answer: answer.toFixed(1),
      choices: all.map(function (v) { return v.toFixed(1); }),
      keys: all.map(function (v) { return v.toFixed(1); })
    };
  }

  function describe(elements, balancedWord) {
    if (!elements.length) return { key: 'ok', zh: '已经配平', en: 'Already balanced' };
    var zh = elements.length === 1 ? '只有 ' + elements[0] + ' 不守恒' : elements.join('、') + ' 都不守恒';
    var en = elements.length === 1 ? 'Only ' + elements[0] + ' is unbalanced' : elements.join(', ') + ' are all unbalanced';
    return { key: elements.join(','), zh: zh, en: en };
  }

  function subsets(list) {
    var out = [[]];
    list.forEach(function (x) { out = out.concat(out.map(function (s) { return s.concat([x]); })); });
    return out.map(function (s) { return s.slice().sort(); });
  }

  function junior(data, rng) {
    var entry = pick(data.wrongFormulas, rng);
    /* 干扰项是三个**真的存在**的化学式：既不能是这道题的正确答案（那个化学式本身没写错），
       也不能和写错的那个一样（否则两个选项一模一样，学生没法选）。 */
    var valid = byLevel(data.formulas, 'junior').filter(function (f) {
      return f.formula !== entry.right && f.formula !== entry.wrong;
    });
    var good = shuffle(valid, rng).slice(0, 3).map(function (f) { return same(sub(f.formula)); });
    var wrong = same(sub(entry.wrong));
    return {
      id: 'wrong-formula', kicker: { zh: '找错', en: 'Spot the mistake' }, visual: '',
      zh: '下面四个化学式中，哪一个写错了？', en: 'Which of these four formulas is written wrongly?',
      explain: entry.zh + '：' + entry.whyZh + '（' + sub(entry.wrong) + ' ✗ → ' + sub(entry.right) + ' ✓）',
      explainEn: entry.en + ': ' + entry.whyEn,
      answer: wrong.key, choices: shuffle(good.concat([wrong]), rng), wrongFormula: entry.wrong
    };
  }

  function high(data, rng) {
    var entry = pick(data.balancedReactions, rng);
    var reaction = parseReaction(entry);
    var coefficients = reaction.coefficients.slice();
    if (rng() < 0.75) {
      var at = Math.floor(rng() * coefficients.length);
      coefficients[at] = coefficients[at] + pick([1, 2], rng);
    }
    var bad = unbalanced(reaction, coefficients);
    var all = [];
    reaction.reactants.concat(reaction.products).forEach(function (f) {
      Object.keys(parseFormula(f)).forEach(function (s) { if (all.indexOf(s) < 0) all.push(s); });
    });
    all.sort();
    var truth = describe(bad);
    var others = shuffle(subsets(all).map(function (s) { return describe(s); }).filter(function (d) { return d.key !== truth.key; }), rng);
    return {
      id: 'balance-check', kicker: { zh: '找错', en: 'Spot the mistake' }, visual: equationText(reaction, coefficients),
      zh: '这个方程式配平了吗？如果没有，哪些原子的个数左右不相等？',
      en: 'Is this equation balanced? If not, which atoms differ between the two sides?',
      explain: bad.length ? '不守恒的元素：' + bad.join('、') + '；正确系数是 ' + reaction.coefficients.join(', ') + '。'
        : '两边每种原子的个数都相等，系数 ' + coefficients.join(', ') + ' 正确。',
      answer: truth.key, choices: shuffle([truth].concat(others.slice(0, 3)), rng),
      reaction: reaction, shown: coefficients, unbalancedElements: bad
    };
  }

  function university(data, rng) {
    var f = pick(data.formulas.filter(function (x) { return Object.keys(x.atoms).length >= 2; }), rng);
    var table = realMasses(data);
    var symbols = Object.keys(f.atoms);
    var counts = {}, masses = {}, kind = pick(['none', 'composition', 'mass', 'sum'], rng);
    symbols.forEach(function (s) { counts[s] = f.atoms[s]; masses[s] = table[s]; });
    var first = '0', why;
    if (kind === 'composition') {
      var s1 = pick(symbols, rng);
      counts[s1] = counts[s1] + 1; first = '1';
      why = '第 ① 步把 ' + s1 + ' 的原子个数写成了 ' + counts[s1] + '，' + sub(f.formula) + ' 中应为 ' + f.atoms[s1] + '。';
    } else if (kind === 'mass') {
      var s2 = pick(symbols, rng);
      var swap = pick(data.elements.filter(function (e) { return symbols.indexOf(e.symbol) < 0 && e.number <= 20; }), rng);
      masses[s2] = swap.mass; first = '2';
      why = '第 ② 步把 ' + s2 + ' 的原子量写成了 ' + fmtMass(swap.mass) + '（那是 ' + swap.symbol + ' 的），应为 ' + fmtMass(table[s2]) + '。';
    }
    var total = weigh(counts, masses);
    var shown = total.toFixed(2);
    if (kind === 'sum') {
      shown = (total + pick([-10, -1, 1, 10], rng)).toFixed(2); first = '3';
      why = '第 ③ 步加错了，各项相加应为 ' + total.toFixed(2) + '。';
    }
    if (kind === 'none') why = '三步都正确：M = ' + total.toFixed(2) + ' g/mol。';
    var line1 = 'M(' + sub(f.formula) + ') = ' + symbols.map(function (s) { return counts[s] === 1 ? 'M(' + s + ')' : counts[s] + ' × M(' + s + ')'; }).join(' + ');
    var line2 = '= ' + weightText(counts, masses, fmtMass);
    return {
      id: 'molar-working', kicker: { zh: '找错', en: 'Spot the mistake' },
      visual: '① ' + line1 + '\n② ' + line2 + '\n③ = ' + shown + ' g/mol', steps: true,
      zh: '求「' + f.zh + '」（' + sub(f.formula) + '）的摩尔质量。下面的解答从哪一步开始出错？',
      en: 'Find the molar mass of ' + f.en + ' (' + sub(f.formula) + '). In which step does the working first go wrong?',
      explain: why, answer: first, choices: shuffle(STEP_CHOICES, rng), kind: kind, formula: f.formula, counts: counts, masses: masses
    };
  }

  function mistakeQuestion(data, stage, rng) {
    rng = rng || Math.random;
    return (stage === 'junior' ? junior : stage === 'high' ? high : university)(data, rng);
  }

  root.ChemistryCore = {
    STAGES: STAGES, fmt: fmt, sub: sub, parseFormula: parseFormula, unbalanced: unbalanced, parseReaction: parseReaction,
    numericQuestion: numericQuestion, checkNumeric: checkNumeric, matchQuestion: matchQuestion,
    orderQuestion: orderQuestion, mistakeQuestion: mistakeQuestion, INT_MASS: INT_MASS,
    byLevel: byLevel, balanceChoices: balanceChoices, phChoices: phChoices
  };
})(typeof window !== 'undefined' ? window : globalThis);
