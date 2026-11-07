(function () {
  'use strict';

  var Core = window.PhysicsCore;
  var COPY = {
    zh: {
      marks: { units: 'UNIT LAB', calc: 'CALC LAB', input: 'INPUT LAB', match: 'MATCH LAB', order: 'ORDER LAB', mistake: 'DEBUG LAB', concepts: 'CONCEPT LAB' },
      correct: '正确！继续保持好奇心。',
      wrong: '还差一点，正确答案是：{answer}',
      matchWrong: '配错了 {n} 次，全部一次配对正确才得分。',
      orderWrong: '正确顺序：{answer}',
      feedbackRight: '答对 +10',
      submit: '提交',
      yourAnswer: '你的答案'
    },
    en: {
      marks: { units: 'UNIT LAB', calc: 'CALC LAB', input: 'INPUT LAB', match: 'MATCH LAB', order: 'ORDER LAB', mistake: 'DEBUG LAB', concepts: 'CONCEPT LAB' },
      correct: 'Correct! Keep exploring.',
      wrong: 'Not quite. The answer is: {answer}',
      matchWrong: '{n} wrong pairing(s). You score only when every pair is right first time.',
      orderWrong: 'Correct order: {answer}',
      feedbackRight: '+10 points',
      submit: 'Submit',
      yourAnswer: 'Your answer'
    }
  };
  var state = { stage: 'junior', mode: 'units', score: 0, streak: 0, round: 1, answered: false, focus: null, question: null };
  var data = null;

  function $(id) { return document.getElementById(id); }
  function language() { return document.documentElement.lang.indexOf('en') === 0 ? 'en' : 'zh'; }
  function copy() { return COPY[language()]; }
  function quantityName(q) { return language() === 'en' ? q.en : q.zh; }
  function currentQuantities() { return Core.visibleQuantities(data, state.stage); }
  function make(tag, className, text) {
    var el = document.createElement(tag);
    if (className) el.className = className;
    if (text !== undefined) el.textContent = text;
    return el;
  }
  function shuffled(list) {
    var out = list.slice();
    for (var i = out.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var tmp = out[i]; out[i] = out[j]; out[j] = tmp;
    }
    return out;
  }

  function makeQuestion() {
    switch (state.mode) {
      case 'calc': return Core.calcQuestion(state.stage);
      case 'input': return Core.numericQuestion(state.stage);
      case 'match': return Core.matchQuestion(data, state.stage);
      case 'order': return Core.orderQuestion(data, state.stage);
      case 'mistake': return Core.mistakeQuestion(state.stage);
      case 'concepts': return Core.conceptQuestion(data, state.stage);
      default: return Core.unitsQuestion(data, state.stage, state.focus);
    }
  }

  function renderQuestion() {
    if (!data) return;
    state.answered = false;
    var q = makeQuestion();
    state.question = q;
    var lang = language();
    $('modeMark').textContent = copy().marks[state.mode];
    $('roundValue').textContent = state.round;
    $('questionKicker').textContent = q.kicker[lang];
    $('questionTitle').textContent = q[lang];
    $('formulaStage').textContent = q.visual;
    $('formulaStage').classList.toggle('steps', !!q.steps);
    $('formulaStage').classList.toggle('empty', !q.steps && q.visual.length < 3);
    $('answerFeedback').textContent = '';
    $('answerFeedback').className = 'answer-feedback';
    $('answerExplain').textContent = '';
    $('nextQuestion').disabled = true;
    var box = $('answerOptions');
    box.replaceChildren();
    box.className = 'answer-options' + (q.type ? ' is-' + q.type : '');
    if (q.type === 'numeric') renderNumeric(q, lang);
    else if (q.type === 'match') renderMatch(q, lang);
    else if (q.type === 'order') renderOrder(q, lang);
    else renderChoices(q, lang);
    updateStats();
  }

  function explainText(q) {
    if (q.explain) return q.explain;
    return language() === 'en' ? q.explainEn : q.explainZh;
  }

  // 统一的收尾：加分/清零连击、显示反馈与解题步骤、解锁「继续」
  function finish(correct, answerLabel, wrongText) {
    state.answered = true;
    var feedback = $('answerFeedback');
    if (correct) {
      state.score += 10;
      state.streak += 1;
      feedback.textContent = copy().correct + ' ' + copy().feedbackRight;
      feedback.classList.add('correct');
    } else {
      state.streak = 0;
      feedback.textContent = wrongText || copy().wrong.replace('{answer}', answerLabel);
      feedback.classList.add('wrong');
    }
    $('answerExplain').textContent = explainText(state.question);
    state.round += 1;
    updateStats();
    $('nextQuestion').disabled = false;
  }

  /* ---- 选择题（含找错、概念） ---- */
  function renderChoices(q, lang) {
    q.choices.forEach(function (choice) {
      var button = make('button', 'answer-option', choice[lang]);
      button.type = 'button';
      button.dataset.key = choice.key;
      button.addEventListener('click', function () { chooseAnswer(button, choice); });
      $('answerOptions').appendChild(button);
    });
  }

  function chooseAnswer(button, choice) {
    if (state.answered) return;
    var q = state.question;
    var correct = choice.key === q.answer;
    var label = '';
    document.querySelectorAll('.answer-option').forEach(function (option) {
      option.disabled = true;
      if (option.dataset.key === q.answer) { option.classList.add('correct'); label = option.textContent; }
    });
    if (!correct) button.classList.add('wrong');
    finish(correct, label);
  }

  /* ---- 数值填空 ---- */
  function renderNumeric(q, lang) {
    var input = make('input', 'numeric-input');
    input.type = 'text';
    input.id = 'numericInput';
    input.setAttribute('inputmode', 'decimal');
    input.setAttribute('autocomplete', 'off');
    input.setAttribute('aria-label', copy().yourAnswer);
    var unit = make('span', 'numeric-unit', q.unit);
    var submit = make('button', 'numeric-submit', copy().submit);
    submit.type = 'button';
    submit.id = 'numericSubmit';
    function send() {
      if (state.answered || !String(input.value).trim()) return;
      var correct = Core.checkNumeric(q, input.value);
      input.disabled = true;
      submit.disabled = true;
      input.classList.add(correct ? 'correct' : 'wrong');
      finish(correct, q.answerText);
    }
    submit.addEventListener('click', send);
    input.addEventListener('keydown', function (event) { if (event.key === 'Enter') send(); });
    $('answerOptions').append(input, unit, submit);
  }

  /* ---- 配对：先点左边，再点它对应的右边 ---- */
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
    shuffled(q.pairs).forEach(function (pair) {
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
            finish(progress.mistakes === 0, '', copy().matchWrong.replace('{n}', progress.mistakes));
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

  /* ---- 排序：按顺序点选，点已选的可以撤回 ---- */
  function renderOrder(q, lang) {
    var pool = make('div', 'order-pool');
    var sequence = make('ol', 'order-sequence');
    var placed = [];
    var slots = [];
    var items = shuffled(q.items);
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
      finish(correct, label, copy().orderWrong.replace('{answer}', label));
    }
    redraw();
    $('answerOptions').append(pool, sequence);
  }

  function updateStats() {
    $('scoreValue').textContent = state.score;
    $('streakValue').textContent = state.streak;
    $('refCount').textContent = currentQuantities().length;
  }

  function renderQuantities() {
    var list = $('refList');
    list.replaceChildren();
    currentQuantities().forEach(function (q) {
      var button = make('button', 'ref-tile' + (state.focus === q ? ' is-focus' : ''));
      button.type = 'button';
      button.setAttribute('aria-label', q.symbol + ' ' + quantityName(q) + ' ' + q.unit);
      var unit = make('span', 'ref-sub', q.unit);
      var symbol = make('strong', '', q.symbol);
      var name = make('small', '', quantityName(q));
      button.append(unit, symbol, name);
      button.addEventListener('click', function () {
        state.focus = q;
        setModeButtons('units');
        state.mode = 'units';
        renderQuantities();
        renderQuestion();
      });
      list.appendChild(button);
    });
  }

  function setModeButtons(mode) {
    document.querySelectorAll('[data-mode]').forEach(function (button) {
      button.setAttribute('aria-selected', String(button.dataset.mode === mode));
    });
  }

  function setStage(stage) {
    if (Core.STAGES.indexOf(stage) < 0) return;
    state.stage = stage;
    state.focus = null;
    document.querySelectorAll('[data-stage]').forEach(function (button) {
      button.setAttribute('aria-pressed', String(button.dataset.stage === stage));
    });
    renderQuantities();
    renderQuestion();
  }

  function setMode(mode) {
    state.mode = mode;
    state.focus = null;
    setModeButtons(mode);
    renderQuantities();
    renderQuestion();
  }

  // 已作答的题不能重新出题，否则切换语言就能刷分；下一题自然会用新语言。
  function applyDynamicLanguage() {
    renderQuantities();
    if (!state.answered) renderQuestion();
  }

  // 给测试用：读出当前题目，界面逻辑本身不依赖它
  window.PhysicsQuiz = { current: function () { return state.question; } };

  fetch('data/physics.json').then(function (response) {
    if (!response.ok) throw new Error('Physics data failed to load');
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
    renderQuantities();
    renderQuestion();
  }).catch(function (error) {
    $('questionTitle').textContent = error.message;
  });
})();
