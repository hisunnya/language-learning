/* ============================================================
   i18n.js —— 界面文字（中文 / English）
   ------------------------------------------------------------
   所有可见文字都在这里，WXML 里写 {{t.xxx}}，JS 里用 format()。
   zh 和 en 两张表必须有完全相同的键（tests/ 里有测试守着）。
   单词卡本身的内容（英文词、中文释义）来自题库，不在这里。
   ============================================================ */

var STRINGS = {
  zh: {
    navTitleIndex: '词境 · 九年级',
    navTitleGame: '单词消消乐',
    brandName: '词境',
    title: '单词消消乐',
    subtitle: '初中 · 九年级 · 人教版 PEP',
    summary: '共 {words} 词 · 约 {levels} 关',
    rules: '玩法',
    startAll: '全部单元',
    startAllDesc: '按顺序把所有单元玩一遍',
    unitMeta: '{count} 词 · {levels} 关',
    noteGrade: '人教版 PEP 九年级。官方为全一册，此处按 Unit 1–7 / Unit 8–14 分为上下册。',
    copyright: '课本内容版权归人民教育出版社所有，仅供个人学习使用。',
    paletteLabel: '配色',
    langAria: '切换到 English',
    hudTime: '时间',
    hudScore: '得分',
    hudBest: '最高连击',
    levelLine: '第 {no}/{total} 关 · {name}',
    btnRules: '玩法',
    btnReplay: '重玩本关',
    btnRestart: '从头开始',
    clearTitle: '本关通过',
    clearBonus: '剩余时间奖励',
    clearNext: '下一关加时',
    clearNextValue: '+{n} 秒',
    btnFinish: '结束',
    btnNextLevel: '下一关',
    btnTotal: '看总成绩',
    overTitle: '时间到',
    overSub: '这一关没在时间内配完，再来一次？',
    rulesTitle: '怎么玩',
    rulesBody:
      '英文和中文都可以先点，点第二张时配对。\n\n' +
      '每对 +100 分；连击每多一次 +20 分，最高 +100。\n' +
      '配错扣 20 分、扣 3 秒，连击清零。\n\n' +
      '每关 120 秒，过关后剩余时间每秒折算 10 分，' +
      '并按剩余时间给下一关加时，最多 150 秒。\n\n' +
      '切到别的应用时计时会暂停；重玩本关会收回这一关已得的分。',
    gotIt: '知道了',
    restartTitle: '从头开始',
    restartBody: '分数会清零，从第一关重新来。确定吗？',
    restartConfirm: '重新开始',
    toastNoBank: '题库未找到',
    toastNoWords: '这个范围内没有单词',
    hintPickedEn: '刚选的是英文，再点中文配对',
    hintPickedCn: '刚选的是中文，再点英文配对'
  },
  en: {
    navTitleIndex: 'Lexica · Grade 9',
    navTitleGame: 'Word Match',
    brandName: 'Lexica',
    title: 'Word Match',
    subtitle: 'Middle school · Grade 9 · PEP edition',
    summary: '{words} words · about {levels} levels',
    rules: 'Rules',
    startAll: 'All units',
    startAllDesc: 'Play every unit in order',
    unitMeta: '{count} words · {levels} levels',
    noteGrade: 'PEP Grade 9. The official book is a single volume; here it is split into Units 1–7 and Units 8–14.',
    copyright: 'Textbook content is copyright of People’s Education Press, for personal study only.',
    paletteLabel: 'Palette',
    langAria: 'Switch to 中文',
    hudTime: 'Time',
    hudScore: 'Score',
    hudBest: 'Best combo',
    levelLine: 'Level {no}/{total} · {name}',
    btnRules: 'Rules',
    btnReplay: 'Replay level',
    btnRestart: 'Restart',
    clearTitle: 'Level cleared',
    clearBonus: 'Time bonus',
    clearNext: 'Next level extra time',
    clearNextValue: '+{n} s',
    btnFinish: 'Finish',
    btnNextLevel: 'Next level',
    btnTotal: 'See total',
    overTitle: 'Time’s up',
    overSub: 'You did not finish this level in time. Try again?',
    rulesTitle: 'How to play',
    rulesBody:
      'Tap an English or a Chinese card first, then tap its partner.\n\n' +
      'Each pair scores 100; every extra combo adds 20, up to +100.\n' +
      'A wrong pair costs 20 points and 3 seconds, and resets the combo.\n\n' +
      'Each level lasts 120 seconds. Leftover time scores 10 per second ' +
      'and carries over to the next level, up to 150 seconds.\n\n' +
      'The clock pauses when you leave the app. Replaying a level takes back the points earned in it.',
    gotIt: 'Got it',
    restartTitle: 'Restart',
    restartBody: 'Your score resets and you start again from level 1. Sure?',
    restartConfirm: 'Restart',
    toastNoBank: 'Word bank not found',
    toastNoWords: 'No words in this range',
    hintPickedEn: 'You picked an English card. Now tap the Chinese one.',
    hintPickedCn: 'You picked a Chinese card. Now tap the English one.'
  }
};

var GRADE_EN = {
  '七年级': 'Grade 7', '八年级': 'Grade 8', '九年级': 'Grade 9',
  '高一': 'Senior 1', '高二': 'Senior 2', '高三': 'Senior 3'
};

function normalize(lang) {
  return lang === 'en' ? 'en' : 'zh';
}

function dict(lang) {
  return STRINGS[normalize(lang)];
}

function format(template, vars) {
  return String(template).replace(/\{(\w+)\}/g, function (all, key) {
    return vars && vars[key] !== undefined ? vars[key] : all;
  });
}

/* 册名：中文直接用题库里的名字，英文按「年级 · 上/下册」拼 */
function bookLabel(book, grade, lang) {
  if (normalize(lang) === 'zh') return book.name;
  var vol = book.term === '上册' ? 'Vol. 1' : book.term === '下册' ? 'Vol. 2' : book.term;
  return (GRADE_EN[grade] || grade) + ' · ' + vol;
}

/* 关卡名里由切关逻辑加的中文后缀，英文界面里换成英文 */
function localizeLevel(name, lang) {
  if (normalize(lang) === 'zh') return name;
  return String(name)
    .replace(/（补充(\d*)）/g, function (all, n) { return n ? ' (extra ' + n + ')' : ' (extra)'; })
    .replace(/（(\d+\/\d+)）/g, ' ($1)')
    .replace(/ · 含复习/g, ' · incl. review');
}

/* 连点同一侧的两张卡：提示「刚选的是哪一侧」。side 是新点的那张的侧别 */
function switchHint(lang, side) {
  var t = dict(lang);
  return side === 'en' ? t.hintPickedEn : t.hintPickedCn;
}

module.exports = {
  STRINGS: STRINGS,
  normalize: normalize,
  dict: dict,
  format: format,
  bookLabel: bookLabel,
  localizeLevel: localizeLevel,
  switchHint: switchHint
};
