/* ============================================================
   bank.js —— 题库切关（移植自 word-puzzle/server/bank.py）
   ------------------------------------------------------------
   规则与网站版一致：
     1. 一个单元按 maxPairs 切开，多出来的部分叫「Unit N（1/3）」；
     2. 不足 maxPairs 的关卡，从前面已经出现过的词里取词补齐（复习），
        补进来的词在本关里不会和已有词重复——英文和中文都不重复；
     3. 补过词的关卡名字后面标「含复习」。
   ============================================================ */

var MAX_PAIRS = 12;
var MIN_PAIRS = 4;
var MAX_PAIRS_LIMIT = 40;

function chunkGroups(groups, maxPairs) {
  var parts = [];

  for (var g = 0; g < groups.length; g++) {
    var words = (groups[g].words || []).slice();
    if (!words.length) continue;
    var unit = groups[g].name || '';

    if (maxPairs <= 0 || words.length <= maxPairs) {
      parts.push({ unit: unit, words: words });
      continue;
    }

    var count = Math.ceil(words.length / maxPairs);
    for (var i = 0; i < count; i++) {
      parts.push({
        unit: unit + '（' + (i + 1) + '/' + count + '）',
        words: words.slice(i * maxPairs, (i + 1) * maxPairs)
      });
    }
  }

  var pool = [];
  var poolKeys = {};

  for (var p = 0; p < parts.length; p++) {
    var part = parts[p];

    /* 同一关里英文或中文重复会让配对变得含糊（两张卡片看起来都对），
       所以先做一次去重，再做复习补齐。 */
    var seenEn = {};
    var seenCn = {};
    var kept = [];
    for (var d = 0; d < part.words.length; d++) {
      var item = part.words[d];
      if (seenEn[item.en] || seenCn[item.cn]) continue;
      seenEn[item.en] = 1;
      seenCn[item.cn] = 1;
      kept.push(item);
    }
    part.words = kept;

    var usedEn = {};
    var usedCn = {};
    for (var w = 0; w < part.words.length; w++) {
      usedEn[part.words[w].en] = 1;
      usedCn[part.words[w].cn] = 1;
    }

    var added = 0;
    for (var k = 0; k < pool.length; k++) {
      if (part.words.length >= maxPairs) break;
      var cand = pool[k];
      if (usedEn[cand.en] || usedCn[cand.cn]) continue;
      part.words.push({ en: cand.en, cn: cand.cn, ipa: cand.ipa, pos: cand.pos });
      usedEn[cand.en] = 1;
      usedCn[cand.cn] = 1;
      added++;
    }
    if (added) part.unit = part.unit + ' · 含复习';

    for (var m = 0; m < part.words.length; m++) {
      var key = part.words[m].en + '\u0000' + part.words[m].cn;
      if (!poolKeys[key]) {
        poolKeys[key] = 1;
        pool.push(part.words[m]);
      }
    }
  }

  return parts;
}

function buildLevels(book, unitIndex, maxPairs) {
  var limit = maxPairs || MAX_PAIRS;
  if (limit < MIN_PAIRS || limit > MAX_PAIRS_LIMIT) limit = MAX_PAIRS;

  var groups;
  if (unitIndex === 'all' || unitIndex === undefined || unitIndex === null) {
    groups = book.units || [];
  } else {
    var unit = (book.units || [])[unitIndex];
    groups = unit ? [unit] : [];
  }

  var parts = chunkGroups(groups, limit);
  return parts.map(function (part) {
    return { name: part.unit, words: part.words };
  });
}

module.exports = {
  MAX_PAIRS: MAX_PAIRS,
  MIN_PAIRS: MIN_PAIRS,
  MAX_PAIRS_LIMIT: MAX_PAIRS_LIMIT,
  chunkGroups: chunkGroups,
  buildLevels: buildLevels
};
