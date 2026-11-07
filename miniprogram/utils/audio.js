/* ============================================================
   audio.js —— 单词发音（美式女声）
   ------------------------------------------------------------
   音频由网站版 server/tts.py 批量预生成（Edge Neural en-US-AriaNeural，
   失败时整体回退 espeak-ng 的美式女声，不会混用两种音色），
   上传到云开发存储后，这里只负责播放，不在运行时合成。

   用法：
     audio.setBase('https://<云存储域名>/audio/');
     audio.preload(levels[0].words);   // 进关前预取本关的词
     audio.play('apple');              // 点卡片时立即出声

   没配置 base 时全部静默，不影响游戏。
   ============================================================ */

var base = '';
var ctx = null;
var localCache = {};
var pending = {};

function setBase(url) {
  base = (url || '').replace(/\/+$/, '');
  if (base) base = base + '/';
}

function enabled() {
  return !!base;
}

function ensureCtx() {
  if (ctx) return ctx;
  ctx = wx.createInnerAudioContext();
  ctx.obeyMuteSwitch = false;
  ctx.onError(function () {
    /* 播放失败就安静地算了，不打断游戏 */
  });
  return ctx;
}

function fileUrl(word) {
  return base + encodeURIComponent(word) + '.mp3';
}

function localPath(word) {
  return localCache[word] || '';
}

function fetchOne(word) {
  return new Promise(function (resolve) {
    pending[word] = true;
    wx.downloadFile({
      url: fileUrl(word),
      success: function (res) {
        if (res.statusCode === 200) localCache[word] = res.tempFilePath;
        pending[word] = false;
        resolve(1);
      },
      fail: function () {
        pending[word] = false;
        resolve(0);
      }
    });
  });
}

function preload(words) {
  if (!enabled() || !words || !words.length) return Promise.resolve(0);
  var tasks = [];
  words.forEach(function (item) {
    var en = item && item.en;
    if (!en || localCache[en] || pending[en]) return;
    tasks.push(fetchOne(en));
  });
  return Promise.all(tasks).then(function (list) {
    return list.length;
  });
}

function play(word) {
  if (!word) return;
  var player = ensureCtx();
  var path = localPath(word);
  if (path) {
    player.stop();
    player.src = path;
    player.play();
    return;
  }
  if (!enabled()) return;

  wx.downloadFile({
    url: fileUrl(word),
    success: function (res) {
      if (res.statusCode !== 200) return;
      localCache[word] = res.tempFilePath;
      player.stop();
      player.src = res.tempFilePath;
      player.play();
    },
    fail: function () {}
  });
}

function dispose() {
  if (ctx) {
    ctx.destroy();
    ctx = null;
  }
}

module.exports = {
  setBase: setBase,
  enabled: enabled,
  preload: preload,
  play: play,
  dispose: dispose
};
