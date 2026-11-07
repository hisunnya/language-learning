(function () {
  'use strict';

  var COPY = {
    zh: {
      stage: { junior: '初中', high: '高中', university: '大学' },
      mode: { elements: '元素速配', formulas: '化学式', reactions: '反应推理' },
      marks: { elements: 'ELEMENT LAB', formulas: 'FORMULA LAB', reactions: 'REACTION LAB', input: 'INPUT LAB', match: 'MATCH LAB', order: 'ORDER LAB', mistake: 'DEBUG LAB' },
      matchWrong: '配错了 {n} 次，全部一次配对正确才得分。',
      orderWrong: '正确顺序：{answer}',
      submit: '提交',
      yourAnswer: '你的答案',
      chooseSymbol: '选择「{name}」的元素符号。',
      chooseNumber: '「{symbol} · {name}」的原子序数是多少？',
      chooseMass: '「{symbol} · {name}」的标准原子量约是多少？',
      chooseFormula: '「{name}」的化学式是什么？',
      chooseAtomCount: '「{formula}」中含有几个「{symbol}」原子？',
      chooseMolarMass: '「{formula} · {name}」的摩尔质量约是多少？',
      chooseChemicalChange: '以下哪项变化生成了新物质？',
      balance: '选择配平系数：{reaction}',
      calculatePh: '「{name}」的 pH 约是多少？',
      answer: '选择一个答案',
      correct: '正确！继续保持好奇心。',
      wrong: '还差一点，正确答案是：{answer}',
      next: '下一题',
      feedbackRight: '答对 +10',
      streak: '连续答对',
      element: '元素',
      number: '原子序数',
      mass: '原子量',
      formula: '化学式'
    },
    en: {
      stage: { junior: 'Middle school', high: 'High school', university: 'University' },
      mode: { elements: 'Elements', formulas: 'Formulas', reactions: 'Reactions' },
      marks: { elements: 'ELEMENT LAB', formulas: 'FORMULA LAB', reactions: 'REACTION LAB', input: 'INPUT LAB', match: 'MATCH LAB', order: 'ORDER LAB', mistake: 'DEBUG LAB' },
      matchWrong: '{n} wrong pairing(s). You score only when every pair is right first time.',
      orderWrong: 'Correct order: {answer}',
      submit: 'Submit',
      yourAnswer: 'Your answer',
      chooseSymbol: 'Choose the symbol for {name}.',
      chooseNumber: 'What is the atomic number of {symbol} · {name}?',
      chooseMass: 'What is the standard atomic weight of {symbol} · {name}?',
      chooseFormula: 'Which formula represents {name}?',
      chooseAtomCount: 'How many {symbol} atoms are in {formula}?',
      chooseMolarMass: 'What is the approximate molar mass of {formula} · {name}?',
      chooseChemicalChange: 'Which change creates a new substance?',
      balance: 'Choose the balanced coefficients: {reaction}',
      calculatePh: 'What is the approximate pH of {name}?',
      answer: 'Choose one answer',
      correct: 'Correct! Keep exploring.',
      wrong: 'Not quite. The answer is: {answer}',
      next: 'Next question',
      feedbackRight: '+10 points',
      streak: 'Correct streak',
      element: 'Element',
      number: 'Atomic number',
      mass: 'Atomic weight',
      formula: 'Formula'
    }
  };

  var STAGES = {
    junior: { max: 20 },
    high: { max: 30 },
    university: { max: 30 }
  };
  var state = { stage: 'junior', mode: 'elements', round: 1, score: 0, streak: 0, answered: false, focus: null };
  var data = null;
  var Core = window.ChemistryCore;
  var CORE_MODES = { input: true, match: true, order: true, mistake: true };

  function $(id) { return document.getElementById(id); }
  function language() { return document.documentElement.lang.indexOf('en') === 0 ? 'en' : 'zh'; }
  function text(key, args) {
    var value = COPY[language()][key] || key;
    Object.keys(args || {}).forEach(function (name) {
      value = value.replace('{' + name + '}', args[name]);
    });
    return value;
  }
  function elementName(element) { return language() === 'en' ? element.en : element.zh; }
  function formulaText(formula) {
    return String(formula).replace(/[0-9]/g, function (n) {
      return '₀₁₂₃₄₅₆₇₈₉'[Number(n)];
    });
  }
  function shuffle(list) {
    var result = list.slice();
    for (var i = result.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var tmp = result[i]; result[i] = result[j]; result[j] = tmp;
    }
    return result;
  }
  function pickWrong(source, count, key, answer) {
    return shuffle(source.filter(function (item) { return item[key] !== answer; }))
      .slice(0, count - 1).map(function (item) { return item[key]; });
  }
  function formatMass(value) { return Number(value).toFixed(value < 10 ? 3 : 2); }
  function molarMass(formula) {
    var atoms = formula.atoms;
    return Object.keys(atoms).reduce(function (sum, symbol) {
      var element = data.elements.find(function (item) { return item.symbol === symbol; });
      return sum + element.mass * atoms[symbol];
    }, 0);
  }
  // 以正确答案为中心生成不重复、且为正数的干扰项，凑够 count 个。
  function nearbyNumbers(answer, offsets, count, precision) {
    var seen = {};
    seen[String(answer)] = true;
    var extras = [];
    offsets.forEach(function (offset) {
      var value = Number((answer + offset).toFixed(precision));
      if (value > 0 && !seen[String(value)]) {
        seen[String(value)] = true;
        extras.push(value);
      }
    });
    return shuffle([answer].concat(extras.slice(0, count - 1))).map(function (value) {
      return String(value);
    });
  }
  function distractorNumbers(answer, offsets, precision) {
    return nearbyNumbers(answer, offsets, 4, precision);
  }
  function currentElements() {
    return data.elements.filter(function (item) {
      return item.number <= STAGES[state.stage].max;
    });
  }

  function makeQuestion() {
    var elements = currentElements();
    var element = state.focus || elements[Math.floor(Math.random() * elements.length)];
    var formulas = data.formulas;
    if (state.mode === 'elements') {
      if (state.stage === 'junior') {
        return {
          kicker: text('element'), visual: elementName(element),
          prompt: text('chooseSymbol', { name: elementName(element) }),
          choices: shuffle([element.symbol].concat(pickWrong(elements, 4, 'symbol', element.symbol))),
          answer: element.symbol
        };
      }
      if (state.stage === 'high') {
        return {
          kicker: text('number'), visual: element.symbol,
          prompt: text('chooseNumber', { symbol: element.symbol, name: elementName(element) }),
          choices: shuffle([String(element.number)].concat(
            pickWrong(elements, 4, 'number', element.number).map(String))),
          answer: String(element.number)
        };
      }
      var mass = formatMass(element.mass);
      return {
        kicker: text('mass'), visual: element.symbol,
        prompt: text('chooseMass', { symbol: element.symbol, name: elementName(element) }),
        choices: shuffle([mass].concat([-1.1, -0.5, 0.7].map(function (delta) {
          return formatMass(Math.max(0.1, element.mass + delta));
        }))),
        answer: mass
      };
    }

    if (state.mode === 'formulas') {
      var pool = state.stage === 'junior' ? formulas.slice(0, 6)
        : state.stage === 'high' ? formulas.slice(0, 11) : formulas;
      var formula = pool[Math.floor(Math.random() * pool.length)];
      if (state.stage === 'junior') {
        return {
          kicker: text('formula'), visual: elementName(formula),
          prompt: text('chooseFormula', { name: elementName(formula) }),
          choices: shuffle([formula.formula].concat(pickWrong(formulas, 4, 'formula', formula.formula))),
          answer: formula.formula
        };
      }
      if (state.stage === 'high') {
        var symbols = Object.keys(formula.atoms);
        var symbol = symbols[Math.floor(Math.random() * symbols.length)];
        var count = formula.atoms[symbol];
        return {
          kicker: text('formula'), visual: formulaText(formula.formula),
          prompt: text('chooseAtomCount', { formula: formulaText(formula.formula), symbol: symbol }),
          choices: nearbyNumbers(count, [1, -1, 2, -2, 3, 4], 4, 0),
          answer: String(count)
        };
      }
      var weight = Number(molarMass(formula).toFixed(2));
      return {
        kicker: text('formula'), visual: formulaText(formula.formula),
        prompt: text('chooseMolarMass', { formula: formulaText(formula.formula), name: elementName(formula) }),
        choices: distractorNumbers(weight, [-10, -2, 4, 8, -1, 2, 16], 2),
        answer: String(weight)
      };
    }

    if (state.stage === 'junior') {
      var chemical = data.changes.filter(function (item) { return item.type === 'chemical'; });
      var physical = data.changes.filter(function (item) { return item.type !== 'chemical'; });
      var right = chemical[Math.floor(Math.random() * chemical.length)];
      var options = shuffle([right].concat(shuffle(physical).slice(0, 3)));
      return {
        kicker: text('mode').reactions, visual: '↔',
        prompt: text('chooseChemicalChange'),
        choices: options.map(function (item) { return elementName(item); }),
        answer: elementName(right)
      };
    }
    if (state.stage === 'high') {
      var reaction = data.balancedReactions[Math.floor(Math.random() * data.balancedReactions.length)];
      return {
        kicker: text('mode').reactions, visual: '⚖',
        prompt: text('balance', { reaction: reaction.prompt }),
        choices: shuffle(reaction.choices), answer: reaction.answer
      };
    }
    var ph = data.phQuestions[Math.floor(Math.random() * data.phQuestions.length)];
    return {
      kicker: text('mode').reactions, visual: 'pH',
      prompt: text('calculatePh', { name: elementName(ph) }),
      choices: nearbyNumbers(ph.answer, [1, -1, 2, -2, 3], 4, 0).filter(Boolean),
      answer: String(ph.answer)
    };
  }

  function renderQuestion() {
    if (!data) return;
    state.answered = false;
    $('answerExplain').textContent = '';
    $('formulaStage').classList.remove('steps');
    $('answerOptions').className = 'answer-options';
    if (CORE_MODES[state.mode]) { renderCoreQuestion(); return; }
    var question = makeQuestion();
    state.question = question;
    $('modeMark').textContent = COPY[language()].marks[state.mode];
    $('roundValue').textContent = state.round;
    $('questionKicker').textContent = question.kicker;
    $('questionTitle').textContent = question.prompt;
    $('formulaStage').textContent = question.visual;
    $('formulaStage').classList.toggle('empty', question.visual.length < 3);
    $('answerFeedback').textContent = '';
    $('answerFeedback').className = 'answer-feedback';
    $('nextQuestion').disabled = true;
    $('nextQuestion').querySelector('[data-module-zh]').textContent = text('next');
    $('answerOptions').replaceChildren();
    question.choices.forEach(function (choice, index) {
      var button = document.createElement('button');
      button.type = 'button';
      button.className = 'answer-option';
      button.textContent = choice;
      button.addEventListener('click', function () { chooseAnswer(button, choice); });
      $('answerOptions').appendChild(button);
    });
    updateStats();
  }


  /* ================= 新题型：数值填空 / 配对 / 排序 / 找错 ================= */
  function make(tag, className, text) {
    var el = document.createElement(tag);
    if (className) el.className = className;
    if (text !== undefined) el.textContent = text;
    return el;
  }

  function makeCoreQuestion() {
    if (state.mode === 'input') return Core.numericQuestion(data, state.stage);
    if (state.mode === 'match') return Core.matchQuestion(data, state.stage);
    if (state.mode === 'order') return Core.orderQuestion(data, state.stage);
    return Core.mistakeQuestion(data, state.stage);
  }

  function renderCoreQuestion() {
    var q = makeCoreQuestion();
    var lang = language();
    state.question = q;
    $('modeMark').textContent = COPY[lang].marks[state.mode];
    $('roundValue').textContent = state.round;
    $('questionKicker').textContent = q.kicker[lang];
    $('questionTitle').textContent = q[lang];
    $('formulaStage').textContent = q.visual;
    $('formulaStage').classList.toggle('steps', !!q.steps);
    $('formulaStage').classList.toggle('empty', !q.steps && q.visual.length < 3);
    $('answerFeedback').textContent = '';
    $('answerFeedback').className = 'answer-feedback';
    $('nextQuestion').disabled = true;
    var box = $('answerOptions');
    box.replaceChildren();
    box.className = 'answer-options' + (q.type ? ' is-' + q.type : '');
    if (q.type === 'numeric') renderNumeric(q);
    else if (q.type === 'match') renderMatch(q, lang);
    else if (q.type === 'order') renderOrder(q, lang);
    else renderKeyedChoices(q, lang);
    updateStats();
  }

  // 统一的收尾：加分/清零连击、显示反馈与解释、解锁「继续」
  function finishCore(correct, answerLabel, wrongText) {
    state.answered = true;
    var feedback = $('answerFeedback');
    if (correct) {
      state.score += 10;
      state.streak += 1;
      feedback.textContent = text('correct') + ' ' + text('feedbackRight');
      feedback.classList.add('correct');
    } else {
      state.streak = 0;
      feedback.textContent = wrongText || text('wrong', { answer: answerLabel });
      feedback.classList.add('wrong');
    }
    var q = state.question;
    $('answerExplain').textContent = language() === 'en' && q.explainEn ? q.explainEn : q.explain;
    state.round += 1;
    updateStats();
    $('nextQuestion').disabled = false;
  }

  function renderKeyedChoices(q, lang) {
    q.choices.forEach(function (choice) {
      var button = make('button', 'answer-option', choice[lang]);
      button.type = 'button';
      button.dataset.key = choice.key;
      button.addEventListener('click', function () {
        if (state.answered) return;
        var label = '';
        document.querySelectorAll('.answer-option').forEach(function (option) {
          option.disabled = true;
          if (option.dataset.key === q.answer) { option.classList.add('correct'); label = option.textContent; }
        });
        if (choice.key !== q.answer) button.classList.add('wrong');
        finishCore(choice.key === q.answer, label);
      });
      $('answerOptions').appendChild(button);
    });
  }

  function renderNumeric(q) {
    var input = make('input', 'numeric-input');
    input.type = 'text';
    input.id = 'numericInput';
    input.setAttribute('inputmode', 'decimal');
    input.setAttribute('autocomplete', 'off');
    input.setAttribute('aria-label', text('yourAnswer'));
    var unit = make('span', 'numeric-unit', q.unit);
    var submit = make('button', 'numeric-submit', text('submit'));
    submit.type = 'button';
    function send() {
      if (state.answered || !String(input.value).trim()) return;
      var correct = Core.checkNumeric(q, input.value);
      input.disabled = true;
      submit.disabled = true;
      input.classList.add(correct ? 'correct' : 'wrong');
      finishCore(correct, q.answerText);
    }
    submit.addEventListener('click', send);
    input.addEventListener('keydown', function (event) { if (event.key === 'Enter') send(); });
    $('answerOptions').append(input, unit, submit);
  }

  function renderMatch(q, lang) {
    var left = make('div', 'match-col');
    var right = make('div', 'match-col');
    var progress = { selected: null, matched: 0, mistakes: 0 };
    q.pairs.forEach(function (pair) {
      var button = make('button', 'answer-option match-left', pair.left[lang]);
      button.type = 'button';
      button.dataset.key = pair.key;
      button.addEventListener('click', function () {
        if (state.answered || button.disabled) return;
        if (progress.selected) progress.selected.classList.remove('is-selected');
        progress.selected = button;
        button.classList.add('is-selected');
      });
      left.appendChild(button);
    });
    shuffle(q.pairs).forEach(function (pair) {
      var button = make('button', 'answer-option match-right', pair.right[lang]);
      button.type = 'button';
      button.dataset.key = pair.key;
      button.addEventListener('click', function () {
        if (state.answered || button.disabled || !progress.selected) return;
        var mine = progress.selected;
        progress.selected = null;
        mine.classList.remove('is-selected');
        if (mine.dataset.key === button.dataset.key) {
          mine.classList.add('correct'); button.classList.add('correct');
          mine.disabled = true; button.disabled = true;
          progress.matched += 1;
          if (progress.matched === q.pairs.length) {
            finishCore(progress.mistakes === 0, '', text('matchWrong', { n: progress.mistakes }));
          }
        } else {
          progress.mistakes += 1;
          button.classList.add('wrong');
          setTimeout(function () { button.classList.remove('wrong'); }, 450);
        }
      });
      right.appendChild(button);
    });
    $('answerOptions').append(left, right);
  }

  function renderOrder(q, lang) {
    var pool = make('div', 'order-pool');
    var sequence = make('ol', 'order-sequence');
    var placed = [];
    var slots = [];
    var items = shuffle(q.items);
    function redraw() {
      pool.replaceChildren();
      sequence.replaceChildren();
      slots = [];
      items.forEach(function (item) {
        if (placed.indexOf(item) >= 0) return;
        var button = make('button', 'answer-option order-item', item[lang]);
        button.type = 'button';
        button.dataset.key = item.key;
        button.addEventListener('click', function () {
          if (state.answered) return;
          placed.push(item);
          redraw();
          if (placed.length === q.items.length) check();
        });
        pool.appendChild(button);
      });
      placed.forEach(function (item, index) {
        var row = make('li', 'order-slot');
        var button = make('button', 'answer-option order-placed', (index + 1) + '. ' + item[lang]);
        button.type = 'button';
        button.dataset.key = item.key;
        button.addEventListener('click', function () {
          if (state.answered) return;
          placed.splice(index, 1);
          redraw();
        });
        row.appendChild(button);
        sequence.appendChild(row);
        slots.push(button);
      });
    }
    function check() {
      var correct = placed.every(function (item, i) { return item.key === q.items[i].key; });
      slots.forEach(function (button, i) {
        button.disabled = true;
        button.classList.add(placed[i].key === q.items[i].key ? 'correct' : 'wrong');
      });
      var label = q.items.map(function (item) { return item[lang]; }).join(' → ');
      finishCore(correct, label, text('orderWrong', { answer: label }));
    }
    redraw();
    $('answerOptions').append(pool, sequence);
  }

  function chooseAnswer(button, choice) {
    if (state.answered) return;
    state.answered = true;
    var correct = String(choice) === String(state.question.answer);
    document.querySelectorAll('.answer-option').forEach(function (option) {
      option.disabled = true;
      if (String(option.textContent) === String(state.question.answer)) option.classList.add('correct');
    });
    var feedback = $('answerFeedback');
    if (correct) {
      state.score += 10;
      state.streak += 1;
      feedback.textContent = text('correct') + ' ' + text('feedbackRight');
      feedback.classList.add('correct');
      button.classList.add('correct');
    } else {
      state.streak = 0;
      feedback.textContent = text('wrong', { answer: state.question.answer });
      feedback.classList.add('wrong');
      button.classList.add('wrong');
    }
    state.round += 1;
    updateStats();
    $('nextQuestion').disabled = false;
  }

  function updateStats() {
    $('scoreValue').textContent = state.score;
    $('streakValue').textContent = state.streak;
    $('elementCount').textContent = currentElements().length;
  }

  function renderElements() {
    var list = $('elementList');
    list.replaceChildren();
    currentElements().forEach(function (element) {
      var button = document.createElement('button');
      button.type = 'button';
      button.className = 'element-tile' + (state.focus === element ? ' is-focus' : '');
      button.setAttribute('aria-label', element.symbol + ' ' + elementName(element));
      var number = document.createElement('span');
      number.className = 'atomic-number';
      number.textContent = element.number;
      var symbol = document.createElement('strong');
      symbol.textContent = element.symbol;
      var name = document.createElement('small');
      name.textContent = elementName(element);
      button.append(number, symbol, name);
      button.addEventListener('click', function () {
        state.focus = element;
        renderElements();
        renderQuestion();
      });
      list.appendChild(button);
    });
  }

  function setStage(stage) {
    if (!STAGES[stage]) return;
    state.stage = stage;
    state.focus = null;
    document.querySelectorAll('[data-stage]').forEach(function (button) {
      button.setAttribute('aria-pressed', String(button.dataset.stage === stage));
    });
    renderElements();
    renderQuestion();
  }

  function setMode(mode) {
    state.mode = mode;
    state.focus = null;
    document.querySelectorAll('[data-mode]').forEach(function (button) {
      button.setAttribute('aria-selected', String(button.dataset.mode === mode));
    });
    renderElements();
    renderQuestion();
  }

  // 已作答的题不能重新出题，否则切换语言就能刷分；下一题自然会用新语言。
  function applyDynamicLanguage() {
    renderElements();
    if (!state.answered) renderQuestion();
  }

  // 给测试用：读出当前题目，界面逻辑本身不依赖它
  window.ChemQuiz = { current: function () { return state.question; } };

  fetch('data/chemistry.json').then(function (response) {
    if (!response.ok) throw new Error('Chemistry data failed to load');
    return response.json();
  }).then(function (json) {
    data = json;
    document.querySelectorAll('[data-stage]').forEach(function (button) {
      button.addEventListener('click', function () { setStage(button.dataset.stage); });
    });
    document.querySelectorAll('[data-mode]').forEach(function (button) {
      button.addEventListener('click', function () { setMode(button.dataset.mode); });
    });
    $('nextQuestion').addEventListener('click', renderQuestion);
    var langButton = $('portalLangBtn');
    if (langButton) langButton.addEventListener('click', function () { setTimeout(applyDynamicLanguage, 0); });
    renderElements();
    renderQuestion();
  }).catch(function (error) {
    $('questionTitle').textContent = error.message;
  });
})();
