/* ============================================================
   audio.js —— 单词发音（美式女声）
   ------------------------------------------------------------
   音频由网站版 server/tts.py 批量预生成，上传到小程序云开发存储（或任意
   HTTPS 静态地址）。学生进入某一关时，自动下载这一关要用到的单词发音；
   点英文卡片时直接播放本地文件。

   最重要的一条：**声音永远是加分项，绝不能影响游戏。**
     * 没配置、没网络、文件不存在、下载超时、播放出错，全部静默跳过，不抛异常；
     * 下载失败的词一段时间内不重试（避免一直卡网络），之后再点会再试；
     * 同一个词同时只下载一次；点得太快，只播放最后点的那个词。

   用法（见 config.js）：
     audio.configure({ cloudPrefix: 'cloud://<环境ID>.xxx/audio/' });  // 云开发存储
     audio.configure({ base: 'https://<域名>/audio/' });               // 或者 HTTPS 地址
     audio.preload(words);   // 进关时调用，返回本次成功下载的个数
     audio.play('apple');    // 点卡片时调用

   文件名规则：<目录>/<编码后的英文>.mp3，例如 audio/apple.mp3。
   ============================================================ */

var RETRY_AFTER_MS = 20000;

var source = null;          // { type: 'http' | 'cloud', url }
var downloader = null;      // function(word) -> Promise<localPath>，测试时可替换
var ctx = null;
var cache = {};             // word -> 本地临时文件路径
var inflight = {};          // word -> Promise
var failedAt = {};          // word -> 上次失败的时间
var latest = '';            // 最近一次想播放的词
var now = function () { return Date.now(); };

function trimSlash(url) {
  return String(url || '').replace(/\/+$/, '');
}

function configure(opts) {
  opts = opts || {};
  source = null;
  if (opts.cloudPrefix) {
    source = { type: 'cloud', url: String(opts.cloudPrefix).replace(/\/*$/, '/') };
  } else if (opts.base) {
    source = { type: 'http', url: trimSlash(opts.base) + '/' };
  }
  downloader = typeof opts.download === 'function' ? opts.download : null;
}

function enabled() {
  return !!(source || downloader);
}

function fileUrl(word) {
  return source.url + encodeURIComponent(word) + '.mp3';
}

function defaultDownload(word) {
  return new Promise(function (resolve, reject) {
    var done = function (res) {
      if (res && res.statusCode === 200 && res.tempFilePath) resolve(res.tempFilePath);
      else reject(new Error('download failed'));
    };
    try {
      if (source.type === 'cloud') {
        wx.cloud.downloadFile({ fileID: fileUrl(word), success: done, fail: reject });
      } else {
        wx.downloadFile({ url: fileUrl(word), success: done, fail: reject });
      }
    } catch (e) {
      reject(e);
    }
  });
}

/* 取得某个词的本地文件；失败时 resolve('')，绝不 reject */
function fetchOne(word, force) {
  if (!enabled() || !word) return Promise.resolve('');
  if (cache[word]) return Promise.resolve(cache[word]);
  if (inflight[word]) return inflight[word];
  if (!force && failedAt[word] && now() - failedAt[word] < RETRY_AFTER_MS) return Promise.resolve('');

  var job;
  try {
    job = Promise.resolve((downloader || defaultDownload)(word));
  } catch (e) {
    job = Promise.reject(e);
  }
  inflight[word] = job.then(function (path) {
    delete inflight[word];
    if (path) {
      cache[word] = path;
      delete failedAt[word];
      return path;
    }
    failedAt[word] = now();
    return '';
  }, function () {
    delete inflight[word];
    failedAt[word] = now();
    return '';
  });
  return inflight[word];
}

/* 进关前预取一批词；返回成功（含已缓存）的个数 */
function preload(words) {
  if (!enabled() || !words || !words.length) return Promise.resolve(0);
  var seen = {};
  var tasks = [];
  words.forEach(function (item) {
    var en = item && item.en;
    if (!en || seen[en]) return;
    seen[en] = true;
    tasks.push(fetchOne(en, false));
  });
  return Promise.all(tasks).then(function (paths) {
    return paths.filter(Boolean).length;
  });
}

function ensureCtx() {
  if (ctx) return ctx;
  try {
    ctx = wx.createInnerAudioContext();
    ctx.obeyMuteSwitch = false;
    ctx.onError(function () { /* 播放失败就安静地算了 */ });
  } catch (e) {
    ctx = null;
  }
  return ctx;
}

function playPath(path) {
  var player = ensureCtx();
  if (!player || !path) return;
  try {
    player.stop();
    player.src = path;
    player.play();
  } catch (e) { /* 忽略 */ }
}

function play(word) {
  if (!word || !enabled()) return;
  latest = word;
  if (cache[word]) {
    playPath(cache[word]);
    return;
  }
  fetchOne(word, true).then(function (path) {
    // 下载期间玩家又点了别的词，就不要再播这个了
    if (path && latest === word) playPath(path);
  });
}

function dispose() {
  if (ctx) {
    try { ctx.destroy(); } catch (e) { /* 忽略 */ }
    ctx = null;
  }
}

/* 只给测试用 */
function _reset(clock) {
  source = null;
  downloader = null;
  cache = {};
  inflight = {};
  failedAt = {};
  latest = '';
  now = clock || function () { return Date.now(); };
  dispose();
}

module.exports = {
  configure: configure,
  enabled: enabled,
  preload: preload,
  play: play,
  dispose: dispose,
  RETRY_AFTER_MS: RETRY_AFTER_MS,
  _reset: _reset
};
