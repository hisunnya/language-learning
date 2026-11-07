/* 物理探秘的出题层：纯计算，不碰 DOM，所以可以在 node 里直接测。
 *
 * 公式题全部参数化——每次抽新的数字，题目取之不尽；
 * 错误选项来自「典型错误」（漏掉 ½、忘了换单位、把除当成乘），而不是随机数。 */
(function (root) {
  'use strict';

  var STAGES = ['junior', 'high', 'university'];
  var RANK = { junior: 0, high: 1, university: 2 };
  var G = 10;            // 初高中取 g = 10 m/s²
  var R_GAS = 8.314;     // J/(mol·K)，CODATA
  var HC_EV_NM = 1239.84; // h·c，单位 eV·nm

  function pick(list, rng) { return list[Math.floor(rng() * list.length)]; }

  function shuffle(list, rng) {
    var out = list.slice();
    for (var i = out.length - 1; i > 0; i--) {
      var j = Math.floor(rng() * (i + 1));
      var tmp = out[i]; out[i] = out[j]; out[j] = tmp;
    }
    return out;
  }

  // 三位有效数字，去掉多余的 0：12.0 → "12"，0.6283 → "0.628"
  function fmt(value) { return String(Number(value.toPrecision(3))); }

  /* ---------------- 公式题模板 ----------------
   * lhs / formula 拼成舞台上的公式；badFormula、badUnit 是「找错」题里故意写错的公式和单位。
   * build(rng) 返回：输入、正确值、几个典型错误值、代入式 sub，以及中英文题干。 */
  var CALC = {
    junior: [
      { id: 'speed', lhs: 'v', formula: 's ÷ t', badFormula: 's × t', unit: 'km/h', badUnit: 'm/s', build: function (rng) {
        var t = pick([2, 3, 4, 5, 6], rng), v = pick([20, 30, 40, 50, 60, 80], rng), s = v * t;
        return { inputs: { s: s, t: t }, value: v, wrong: [s * t, s - t, s / (t * 2)], sub: s + ' ÷ ' + t,
          zh: '一辆汽车匀速行驶 ' + t + ' 小时，通过了 ' + s + ' km，它的速度是多少？',
          en: 'A car drives at constant speed for ' + t + ' h and covers ' + s + ' km. What is its speed?' };
      } },
      { id: 'density', lhs: 'ρ', formula: 'm ÷ V', badFormula: 'V ÷ m', unit: 'g/cm³', badUnit: 'kg/m³', build: function (rng) {
        var vol = pick([2, 4, 5, 10], rng), rho = pick([0.8, 1, 2.7, 7.8, 8.9], rng), m = Number((rho * vol).toFixed(1));
        return { inputs: { m: m, V: vol }, value: m / vol, wrong: [m * vol, vol / m, m - vol], sub: m + ' ÷ ' + vol,
          zh: '一块物体质量 ' + m + ' g，体积 ' + vol + ' cm³，它的密度是多少？',
          en: 'An object has mass ' + m + ' g and volume ' + vol + ' cm³. What is its density?' };
      } },
      { id: 'ohm', lhs: 'I', formula: 'U ÷ R', badFormula: 'U × R', unit: 'A', badUnit: 'V', build: function (rng) {
        var U = pick([6, 12, 24, 36], rng), Rr = pick([2, 3, 4, 6, 12], rng);
        return { inputs: { U: U, R: Rr }, value: U / Rr, wrong: [U * Rr, Rr / U, U - Rr], sub: U + ' ÷ ' + Rr,
          zh: '把 ' + Rr + ' Ω 的电阻接在 ' + U + ' V 的电源两端，通过它的电流是多少？',
          en: 'A ' + Rr + ' Ω resistor is connected across ' + U + ' V. What current flows through it?' };
      } },
      { id: 'work', lhs: 'W', formula: 'F · s', badFormula: 'F ÷ s', unit: 'J', badUnit: 'N', build: function (rng) {
        var F = pick([10, 20, 50, 100], rng), s = pick([2, 3, 5, 10], rng);
        return { inputs: { F: F, s: s }, value: F * s, wrong: [F / s, F + s, F * s / 2], sub: F + ' × ' + s,
          zh: '用 ' + F + ' N 的力沿力的方向推动物体前进 ' + s + ' m，做了多少功？',
          en: 'A force of ' + F + ' N moves an object ' + s + ' m along its direction. How much work is done?' };
      } }
    ],
    high: [
      { id: 'velocity', lhs: 'v', formula: 'v₀ + a·t', badFormula: 'a·t', unit: 'm/s', badUnit: 'm/s²', build: function (rng) {
        var v0 = pick([2, 5, 10], rng), a = pick([2, 3, 4, 5], rng), t = pick([2, 3, 4, 5], rng);
        return { inputs: { v0: v0, a: a, t: t }, value: v0 + a * t, wrong: [a * t, v0 + a * t * t, (v0 + a) * t], sub: v0 + ' + ' + a + ' × ' + t,
          zh: '物体初速度 ' + v0 + ' m/s，以 ' + a + ' m/s² 的加速度匀加速 ' + t + ' s，末速度是多少？',
          en: 'A body starts at ' + v0 + ' m/s and accelerates at ' + a + ' m/s² for ' + t + ' s. What is its final speed?' };
      } },
      { id: 'newton', lhs: 'a', formula: 'F ÷ m', badFormula: 'F × m', unit: 'm/s²', badUnit: 'm/s', build: function (rng) {
        var m = pick([2, 4, 5, 10], rng), a = pick([2, 3, 4, 6], rng), F = m * a;
        return { inputs: { F: F, m: m }, value: a, wrong: [F * m, m / F, F - m], sub: F + ' ÷ ' + m,
          zh: '质量 ' + m + ' kg 的物体受到 ' + F + ' N 的合力，加速度是多少？',
          en: 'A ' + m + ' kg body is acted on by a net force of ' + F + ' N. What is its acceleration?' };
      } },
      { id: 'parallel', lhs: 'R', formula: 'R₁R₂ ÷ (R₁ + R₂)', badFormula: 'R₁ + R₂', unit: 'Ω', badUnit: 'kΩ', build: function (rng) {
        var pair = pick([[3, 6], [6, 12], [4, 12], [12, 12], [10, 15], [20, 30], [30, 60]], rng);
        var r1 = pair[0], r2 = pair[1], total = r1 * r2 / (r1 + r2);
        return { inputs: { r1: r1, r2: r2 }, value: total, wrong: [r1 + r2, (r1 + r2) / 2, r1 * r2], sub: r1 + ' × ' + r2 + ' ÷ (' + r1 + ' + ' + r2 + ')',
          zh: '把 ' + r1 + ' Ω 和 ' + r2 + ' Ω 的两个电阻并联，等效电阻是多少？',
          en: 'A ' + r1 + ' Ω and a ' + r2 + ' Ω resistor are connected in parallel. What is the equivalent resistance?' };
      } },
      { id: 'kinetic', lhs: 'Eₖ', formula: '½ m v²', badFormula: 'm v²', unit: 'J', badUnit: 'N', build: function (rng) {
        var m = pick([2, 4, 10], rng), v = pick([2, 4, 6, 10], rng), e = 0.5 * m * v * v;
        return { inputs: { m: m, v: v }, value: e, wrong: [m * v * v, 0.5 * m * v, m * v], sub: '½ × ' + m + ' × ' + v + '²',
          zh: '质量 ' + m + ' kg 的物体以 ' + v + ' m/s 运动，动能是多少？',
          en: 'A ' + m + ' kg body moves at ' + v + ' m/s. What is its kinetic energy?' };
      } },
      { id: 'potential', lhs: 'Eₚ', formula: 'm g h', badFormula: 'm h', unit: 'J', badUnit: 'W', build: function (rng) {
        var m = pick([2, 5, 10], rng), h = pick([2, 5, 10, 20], rng);
        return { inputs: { m: m, h: h }, value: m * G * h, wrong: [m * h, m * G, m * G * h / 2], sub: m + ' × 10 × ' + h,
          zh: '质量 ' + m + ' kg 的物体被举高 ' + h + ' m（取 g = 10 m/s²），重力势能增加多少？',
          en: 'A ' + m + ' kg body is lifted ' + h + ' m (take g = 10 m/s²). By how much does its gravitational potential energy rise?' };
      } }
    ],
    university: [
      { id: 'gas', lhs: 'p', formula: 'nRT ÷ V', badFormula: 'nRV ÷ T', unit: 'kPa', badUnit: 'Pa', build: function (rng) {
        var n = pick([1, 2, 3], rng), T = pick([273, 300, 350, 400], rng), V = pick([0.02, 0.05, 0.1], rng);
        var p = n * R_GAS * T / V / 1000;
        return { inputs: { n: n, T: T, V: V }, value: p, wrong: [p * 2, p / 2, p * 10], sub: n + ' × 8.314 × ' + T + ' ÷ ' + V + ' ÷ 1000',
          zh: n + ' mol 理想气体在 ' + T + ' K、体积 ' + V + ' m³ 时，压强约是多少？（R = 8.314 J/(mol·K)）',
          en: n + ' mol of ideal gas at ' + T + ' K occupies ' + V + ' m³. What is its pressure? (R = 8.314 J/(mol·K))' };
      } },
      { id: 'rc', lhs: 'τ', formula: 'R · C', badFormula: 'R ÷ C', unit: 'ms', badUnit: 's', build: function (rng) {
        var Rk = pick([1, 2, 5, 10], rng), C = pick([1, 2, 5, 10, 100], rng);
        return { inputs: { R: Rk, C: C }, value: Rk * C, wrong: [Rk + C, Rk * C * 10, Rk * C / 10], sub: Rk + ' × ' + C,
          zh: 'RC 电路中 R = ' + Rk + ' kΩ，C = ' + C + ' μF，时间常数 τ 是多少？',
          en: 'In an RC circuit R = ' + Rk + ' kΩ and C = ' + C + ' μF. What is the time constant τ?' };
      } },
      { id: 'shm', lhs: 'T', formula: '2π √(m ÷ k)', badFormula: '2π √(k ÷ m)', unit: 's', badUnit: 'Hz', build: function (rng) {
        var m = pick([0.1, 0.25, 0.5, 1], rng), k = pick([10, 25, 40, 100], rng), T = 2 * Math.PI * Math.sqrt(m / k);
        return { inputs: { m: m, k: k }, value: T, wrong: [Math.sqrt(m / k), 2 * Math.PI * Math.sqrt(k / m), 2 * Math.PI * m / k], sub: '2π √(' + m + ' ÷ ' + k + ')',
          zh: '质量 ' + m + ' kg 的物块挂在劲度系数 ' + k + ' N/m 的弹簧上做简谐振动，周期是多少？',
          en: 'A ' + m + ' kg mass hangs on a spring of stiffness ' + k + ' N/m and oscillates. What is the period?' };
      } },
      { id: 'capacitor', lhs: 'E', formula: '½ C V²', badFormula: 'C V²', unit: 'μJ', badUnit: 'J', build: function (rng) {
        var C = pick([1, 2, 10, 100], rng), V = pick([5, 12, 24], rng), e = 0.5 * C * V * V;
        return { inputs: { C: C, V: V }, value: e, wrong: [C * V * V, 0.5 * C * V, C * V], sub: '½ × ' + C + ' × ' + V + '²',
          zh: '一个 ' + C + ' μF 的电容器充电到 ' + V + ' V，储存的能量是多少？',
          en: 'A ' + C + ' μF capacitor is charged to ' + V + ' V. How much energy does it store?' };
      } },
      { id: 'photon', lhs: 'E', formula: 'hc ÷ λ', badFormula: 'hc × λ', unit: 'eV', badUnit: 'J', build: function (rng) {
        var lam = pick([400, 500, 620, 700], rng), e = HC_EV_NM / lam;
        return { inputs: { lambda: lam }, value: e, wrong: [e * 2, e / 10, e * 10], sub: '1239.84 ÷ ' + lam,
          zh: '波长 ' + lam + ' nm 的光子能量约是多少？（hc ≈ 1240 eV·nm）',
          en: 'What is the energy of a photon of wavelength ' + lam + ' nm? (hc ≈ 1240 eV·nm)' };
      } }
    ]
  };

  // 选项统一写成 {key, zh, en}：key 用来判对错，zh / en 是两种语言下显示的文字。
  function same(text) { return { key: text, zh: text, en: text }; }

  /* 把数值选项排成 4 个互不相同、都为正的字符串；错误选项不够时用倍数补齐 */
  function numericChoices(value, wrong, unit, rng) {
    var answer = fmt(value);
    var seen = {}; seen[answer] = true;
    var extras = [];
    function add(v) {
      if (!(v > 0) || !isFinite(v)) return;
      var text = fmt(v);
      if (seen[text]) return;
      seen[text] = true;
      extras.push(text);
    }
    wrong.forEach(add);
    [2, 0.5, 1.5, 3, 0.1, 10].forEach(function (f) { add(value * f); });
    var choices = shuffle([answer].concat(extras.slice(0, 3)), rng);
    return { answer: answer + ' ' + unit, choices: choices.map(function (c) { return same(c + ' ' + unit); }) };
  }

  function drawCalc(stage, rng) {
    var template = pick(CALC[stage] || CALC.junior, rng);
    var built = template.build(rng);
    var fullSteps = template.lhs + ' = ' + template.formula + ' = ' + built.sub + ' = ' +
      fmt(built.value) + ' ' + template.unit;
    return { template: template, built: built, explain: fullSteps };
  }

  function calcQuestion(stage, rng) {
    rng = rng || Math.random;
    var d = drawCalc(stage, rng);
    var made = numericChoices(d.built.value, d.built.wrong, d.template.unit, rng);
    return {
      id: d.template.id, kicker: { zh: '公式速算', en: 'Quick calculation' },
      visual: d.template.lhs + ' = ' + d.template.formula, zh: d.built.zh, en: d.built.en,
      explain: d.explain, inputs: d.built.inputs, value: d.built.value,
      answer: made.answer, choices: made.choices
    };
  }

  /* 数值填空：同一批公式模板，改成自己算、自己填；允许 1.5% 的四舍五入误差 */
  var TOLERANCE = 0.015;

  function numericQuestion(stage, rng) {
    rng = rng || Math.random;
    var d = drawCalc(stage, rng);
    return {
      id: d.template.id, type: 'numeric', kicker: { zh: '数值填空', en: 'Fill in the number' },
      visual: d.template.lhs + ' = ?', zh: d.built.zh, en: d.built.en,
      explain: d.explain, inputs: d.built.inputs, value: d.built.value,
      unit: d.template.unit, tolerance: TOLERANCE,
      answerText: fmt(d.built.value) + ' ' + d.template.unit
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

  /* 找错：给出三步解答，其中最多一步是错的；选出第一处错误，或者选「没有错误」 */
  function mistakeQuestion(stage, rng) {
    rng = rng || Math.random;
    var d = drawCalc(stage, rng);
    var t = d.template, b = d.built;
    var num = fmt(b.value);
    var kind = pick(['none', 'formula', 'arithmetic', 'unit'], rng);
    var s1 = t.lhs + ' = ' + t.formula, s3unit = t.unit, shown = num, first = '0', why;
    if (kind === 'formula') {
      s1 = t.lhs + ' = ' + t.badFormula; first = '1';
      why = '第 ① 步公式写错了，应为 ' + t.lhs + ' = ' + t.formula + '。';
    } else if (kind === 'arithmetic') {
      var bad = b.wrong.filter(function (v) { return v > 0 && fmt(v) !== num; })[0];
      shown = fmt(bad === undefined ? b.value * 2 : bad); first = '2';
      why = '第 ② 步算错了，' + b.sub + ' 应该等于 ' + num + '。';
    } else if (kind === 'unit') {
      s3unit = t.badUnit; first = '3';
      why = '第 ③ 步单位写错了，应为 ' + t.unit + '。';
    } else {
      why = '三步都正确：' + d.explain;
    }
    var lines = ['① ' + s1, '② ' + t.lhs + ' = ' + b.sub + ' = ' + shown,
      '③ ' + t.lhs + ' = ' + shown + ' ' + s3unit];
    var choices = [
      { key: '1', zh: '第 ① 步', en: 'Step ①' }, { key: '2', zh: '第 ② 步', en: 'Step ②' },
      { key: '3', zh: '第 ③ 步', en: 'Step ③' }, { key: '0', zh: '没有错误', en: 'No mistake' }];
    return {
      id: t.id, kicker: { zh: '找错', en: 'Spot the mistake' }, visual: lines.join('\n'), steps: true,
      zh: b.zh + ' 下面的解答从哪一步开始出错？', en: b.en + ' In which step does the working first go wrong?',
      explain: why, answer: first, choices: shuffle(choices, rng), kind: kind, inputs: b.inputs
    };
  }

  /* ---------------- 量与单位 ---------------- */
  function visibleQuantities(data, stage) {
    return data.quantities.filter(function (q) { return RANK[q.stage] <= RANK[stage]; });
  }

  function unitsQuestion(data, stage, focus, rng) {
    rng = rng || Math.random;
    var pool = visibleQuantities(data, stage);
    // 大学阶段不出「A 用基本单位怎么写」这种自己等于自己的题，除非用户专门点选了它。
    var askable = stage === 'university' ? pool.filter(function (x) { return x.base !== x.unit; }) : pool;
    var q = focus && pool.indexOf(focus) >= 0 ? focus : pick(askable, rng);
    var en = q.en.charAt(0).toLowerCase() + q.en.slice(1);
    var others = shuffle(pool.filter(function (item) { return item !== q; }), rng);
    var modes = {
      junior: { kicker: { zh: '量与单位', en: 'Quantity and unit' }, visual: q.symbol,
        zh: '「' + q.zh + '」的国际单位符号是什么？', en: 'What is the SI unit symbol of ' + en + '?',
        option: function (x) { return same(x.unit); },
        explain: q.zh + '（' + q.symbol + '）的单位是' + q.unitZh + '，符号 ' + q.unit + '。' },
      high: { kicker: { zh: '单位反查', en: 'From unit to quantity' }, visual: q.unit,
        zh: '单位 ' + q.unit + ' 对应哪个物理量？', en: 'Which quantity is measured in ' + q.unit + '?',
        option: function (x) { return { key: x.zh, zh: x.zh, en: x.en }; },
        explain: q.unit + '（' + q.unitZh + '）是' + q.zh + '的单位。' },
      university: { kicker: { zh: '基本单位表达式', en: 'Base-unit expression' }, visual: q.unit,
        zh: '「' + q.zh + '」的单位 ' + q.unit + ' 用 SI 基本单位怎么写？',
        en: 'Write the unit of ' + en + ' (' + q.unit + ') in SI base units.',
        option: function (x) { return same(x.base); },
        explain: q.base === q.unit ? q.unit + ' 本身就是 SI 基本单位。' : q.unit + ' = ' + q.base + '。' }
    }[stage];
    var right = modes.option(q);
    var seen = {}; seen[right.key] = true;
    var wrong = [];
    others.forEach(function (item) {
      var choice = modes.option(item);
      if (wrong.length < 3 && !seen[choice.key]) { seen[choice.key] = true; wrong.push(choice); }
    });
    return { id: 'units', kicker: modes.kicker, visual: modes.visual, zh: modes.zh, en: modes.en,
      explain: modes.explain, answer: right.key, choices: shuffle([right].concat(wrong), rng) };
  }

  /* ---------------- 配对：四组「左边 ↔ 右边」，点一个左边再点它对应的右边 ---------------- */
  function matchQuestion(data, stage, rng) {
    rng = rng || Math.random;
    var pool = visibleQuantities(data, stage);
    var spec = {
      junior: { kicker: { zh: '名称配单位', en: 'Match quantity to unit' },
        zh: '把物理量和它的国际单位配成对', en: 'Pair each quantity with its SI unit',
        left: function (q) { return { zh: q.zh, en: q.en }; }, right: function (q) { var u = q.unit; return { zh: u, en: u }; } },
      high: { kicker: { zh: '符号配名称', en: 'Match symbol to quantity' },
        zh: '把物理量的符号和它的名称配成对', en: 'Pair each symbol with its quantity',
        left: function (q) { return { zh: q.symbol, en: q.symbol }; }, right: function (q) { return { zh: q.zh, en: q.en }; } },
      university: { kicker: { zh: '单位配基本单位', en: 'Match unit to base units' },
        zh: '把导出单位和它的 SI 基本单位表达式配成对', en: 'Pair each derived unit with its SI base-unit form',
        left: function (q) { return { zh: q.unit, en: q.unit }; }, right: function (q) { return { zh: q.base, en: q.base }; } }
    }[stage];
    var chosen = [], leftSeen = {}, rightSeen = {};
    shuffle(pool, rng).forEach(function (q) {
      var l = spec.left(q), r = spec.right(q);
      if (chosen.length < 4 && !leftSeen[l.zh] && !rightSeen[r.zh] && !(stage === 'university' && q.base === q.unit)) {
        leftSeen[l.zh] = true; rightSeen[r.zh] = true;
        chosen.push({ key: l.zh, left: l, right: r });
      }
    });
    return { id: 'match', type: 'match', kicker: spec.kicker, visual: '⇄', zh: spec.zh, en: spec.en,
      pairs: chosen, explain: chosen.map(function (p) { return p.left.zh + ' ↔ ' + p.right.zh; }).join('；') };
  }

  /* ---------------- 排序：把四件东西按量级排好 ---------------- */
  var SUPERSCRIPT = { '-': '⁻', '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹' };

  function fmtMagnitude(value) {
    if (value >= 0.01 && value < 100000) return fmt(value);
    var exp = Math.floor(Math.log10(value));
    var mant = Number((value / Math.pow(10, exp)).toPrecision(2));
    if (mant >= 10) { mant = 1; exp += 1; }
    return mant + '×10' + String(exp).split('').map(function (c) { return SUPERSCRIPT[c]; }).join('');
  }

  // 随机取 4 项，相邻两项至少相差 3 倍，避免「差不多大」的争议
  function spreadFour(items, rng) {
    var sorted = items.slice().sort(function (a, b) { return a.value - b.value; });
    for (var attempt = 0; attempt < 200; attempt++) {
      var idx = shuffle(sorted.map(function (_, i) { return i; }), rng).slice(0, 4).sort(function (a, b) { return a - b; });
      var ok = true;
      for (var i = 1; i < idx.length; i++) {
        if (sorted[idx[i]].value / sorted[idx[i - 1]].value < 3) { ok = false; break; }
      }
      if (ok) return idx.map(function (i) { return sorted[i]; });
    }
    return sorted.slice(0, 4);
  }

  function orderQuestion(data, stage, rng) {
    rng = rng || Math.random;
    var cats = data.magnitudes.filter(function (c) { return RANK[c.stage] <= RANK[stage]; });
    var cat = pick(cats, rng);
    var ascending = rng() < 0.5;
    var four = spreadFour(cat.items, rng);
    if (!ascending) four.reverse();
    return {
      id: 'order', type: 'order', kicker: { zh: '量级排序', en: 'Order of magnitude' }, visual: '↕',
      zh: '把下列' + cat.zh + '按' + (ascending ? '由小到大' : '由大到小') + '排序',
      en: 'Sort these ' + cat.en + ' values from ' + (ascending ? 'smallest to largest' : 'largest to smallest'),
      items: four.map(function (it) { return { key: it.zh, zh: it.zh, en: it.en, value: it.value }; }),
      explain: four.map(function (it) { return it.zh + ' ' + fmtMagnitude(it.value) + ' ' + cat.unit; }).join(' ＜ ').replace(/ ＜ /g, ascending ? ' ＜ ' : ' ＞ ')
    };
  }

  /* ---------------- 现象与概念 ---------------- */
  function conceptQuestion(data, stage, rng) {
    rng = rng || Math.random;
    var item = pick(data.concepts.filter(function (c) { return c.stage === stage; }), rng);
    var all = [{ key: item.answerZh, zh: item.answerZh, en: item.answerEn }];
    item.wrongZh.forEach(function (zh, i) { all.push({ key: zh, zh: zh, en: item.wrongEn[i] }); });
    return {
      id: 'concept', kicker: { zh: '现象与概念', en: 'Concepts' }, visual: '?',
      zh: item.zh, en: item.en, explainZh: item.whyZh, explainEn: item.whyEn,
      answer: item.answerZh, choices: shuffle(all, rng)
    };
  }

  root.PhysicsCore = {
    STAGES: STAGES, fmt: fmt, calcQuestion: calcQuestion, unitsQuestion: unitsQuestion,
    conceptQuestion: conceptQuestion, visibleQuantities: visibleQuantities, CALC: CALC,
    numericQuestion: numericQuestion, checkNumeric: checkNumeric, mistakeQuestion: mistakeQuestion,
    matchQuestion: matchQuestion, orderQuestion: orderQuestion, fmtMagnitude: fmtMagnitude
  };
})(typeof window !== 'undefined' ? window : globalThis);
