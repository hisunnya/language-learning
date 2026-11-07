/* ============================================================
   build-data.js —— 把网站版的词库整理成小程序内置题库
   ------------------------------------------------------------
   用法（在 miniprogram/ 目录下）：
     node tools/build-data.js

   默认取人教版九年级（初三），对应网站版 data/pep_curriculum.json。
   换学段时改 GRADE 常量即可（七年级 / 八年级 / 九年级 / 高一 …）。

   做的事：
     1. 只保留指定年级的册与单元；
     2. 同一单元里英文相同的词条合并成一条（释义用「；」拼接去重），
        否则同一关里会出现两张一样的英文卡片，配对会变含糊；
     3. 输出 data/grade9.js，供小程序直接 require。
   ============================================================ */

const fs = require('fs');
const path = require('path');

const GRADE = '九年级';
const SOURCE = path.join(__dirname, '../../word-puzzle/data/pep_curriculum.json');
const TARGET = path.join(__dirname, '../data/grade9.js');

function splitMeanings(cn) {
  return String(cn || '')
    .split(/[；;，,、\s]+/)
    .map(function (s) { return s.trim(); })
    .filter(Boolean);
}

function mergeWords(words) {
  const order = [];
  const map = {};

  words.forEach(function (w) {
    const en = String(w.en || '').trim();
    if (!en) return;
    if (!map[en]) {
      map[en] = {
        en: en,
        cn: [],
        ipa: w.ipa || '',
        pos: w.pos || ''
      };
      order.push(en);
    }
    splitMeanings(w.cn).forEach(function (m) {
      if (map[en].cn.indexOf(m) === -1) map[en].cn.push(m);
    });
    if (!map[en].ipa && w.ipa) map[en].ipa = w.ipa;
    if (!map[en].pos && w.pos) map[en].pos = w.pos;
  });

  return order.map(function (en) {
    const item = map[en];
    return { en: item.en, cn: item.cn.join('；'), ipa: item.ipa, pos: item.pos };
  });
}

function main() {
  if (!fs.existsSync(SOURCE)) {
    console.error('找不到词库：' + SOURCE);
    process.exit(1);
  }

  const curriculum = JSON.parse(fs.readFileSync(SOURCE, 'utf8'));
  const volumes = curriculum.volumes.filter(function (v) {
    return v.grade === GRADE;
  });

  if (!volumes.length) {
    console.error('词库里没有「' + GRADE + '」的册别');
    process.exit(1);
  }

  const out = {
    stage: volumes[0].stage || '初中',
    grade: GRADE,
    note: '人教版 PEP ' + GRADE + '。官方为全一册，此处按 Unit 1–7 / Unit 8–14 分为上下册。',
    books: volumes.map(function (v) {
      return {
        key: v.key,
        name: v.name,
        term: v.term,
        units: v.units.map(function (u) {
          return { name: u.name, words: mergeWords(u.words) };
        })
      };
    })
  };

  const total = out.books.reduce(function (a, b) {
    return a + b.units.reduce(function (x, u) { return x + u.words.length; }, 0);
  }, 0);

  const js = 'module.exports = ' + JSON.stringify(out, null, 1) + ';\n';
  fs.writeFileSync(TARGET, js);

  out.books.forEach(function (b) {
    const n = b.units.reduce(function (x, u) { return x + u.words.length; }, 0);
    console.log(b.name + '：' + b.units.length + ' 单元 / ' + n + ' 词');
  });
  console.log('合计 ' + total + ' 词 → ' + path.relative(process.cwd(), TARGET));
}

main();
