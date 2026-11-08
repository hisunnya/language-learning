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

/* 从 candidates 里按顺序取出一关的词：英文、中文都不能重复，也不超过 maxPairs。
   取不进来的词原样返回，调用方把它们顺延到下一关，而不是丢掉。 */
function uniqueTake(candidates, maxPairs) {
  var kept = [];
  var rest = [];
  var seenEn = {};
  var seenCn = {};
  for (var i = 0; i < candidates.length; i++) {
    var word = candidates[i];
    var full = maxPairs > 0 && kept.length >= maxPairs;
    if (full || seenEn[word.en] || seenCn[word.cn]) {
      rest.push(word);
      continue;
    }
    seenEn[word.en] = 1;
    seenCn[word.cn] = 1;
    kept.push(word);
  }
  return { kept: kept, rest: rest };
}

/* 同一单元内：一关里英文或中文相同的词会让配对含糊，所以把重复的词顺延到本单元的
   下一关；到了单元末尾还有剩的，单独成一关「补充」。一个词都不会丢。 */
function resolveDuplicates(parts, unit, maxPairs) {
  var resolved = [];
  var carry = [];
  for (var i = 0; i < parts.length; i++) {
    var taken = uniqueTake(carry.concat(parts[i].words), maxPairs);
    carry = taken.rest;
    resolved.push({ unit: parts[i].unit, words: taken.kept });
  }
  var extra = 0;
  while (carry.length) {
    extra++;
    var more = uniqueTake(carry, maxPairs);
    carry = more.rest;
    resolved.push({ unit: unit + '（' + (extra === 1 ? '补充' : '补充' + extra) + '）', words: more.kept });
  }
  return resolved;
}

function chunkGroups(groups, maxPairs) {
  var parts = [];

  for (var g = 0; g < groups.length; g++) {
    var words = (groups[g].words || []).slice();
    if (!words.length) continue;
    var unit = groups[g].name || '';

    var groupParts = [];
    if (maxPairs <= 0 || words.length <= maxPairs) {
      groupParts.push({ unit: unit, words: words });
    } else {
      var count = Math.ceil(words.length / maxPairs);
      for (var i = 0; i < count; i++) {
        groupParts.push({
          unit: unit + '（' + (i + 1) + '/' + count + '）',
          words: words.slice(i * maxPairs, (i + 1) * maxPairs)
        });
      }
    }
    parts = parts.concat(resolveDuplicates(groupParts, unit, maxPairs));
  }

  var pool = [];
  var poolKeys = {};

  for (var p = 0; p < parts.length; p++) {
    var part = parts[p];

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
