/* ============================================================
   recent.js —— 最近玩过的题库（记在这台设备的浏览器里）
   ------------------------------------------------------------
   游戏页成功打开一个题库就记一笔；首页把最近的几个放在最上面，点一下接着玩。
   * 按账号分开记（同一台设备换了账号，各看各的）；没登录的访客记在 'guest' 下；
   * 每个账号最多记 8 个，同一个题库只留最近一次；
   * 首页只显示「现在还看得到」的题库（老师收回了标签就不会再出现）；
   * 存不了（隐私模式、存储满）就悄悄不记，不影响游戏。
   ============================================================ */
(function (global) {
  'use strict';

  var KEY = 'wp_recent';
  var MAX = 8;

  function userKey(info) { return info && info.user ? 'u' + info.user.id : 'guest'; }

  function load(storage) {
    try {
      var data = JSON.parse(storage.getItem(KEY) || '{}');
      return data && typeof data === 'object' && !Array.isArray(data) ? data : {};
    } catch (e) { return {}; }
  }

  function add(storage, key, bankId, now) {
    var id = parseInt(bankId, 10);
    if (!id) return;
    var data = load(storage);
    var list = (Array.isArray(data[key]) ? data[key] : []).filter(function (x) { return x && x.id !== id; });
    list.unshift({ id: id, t: now });
    data[key] = list.slice(0, MAX);
    try { storage.setItem(KEY, JSON.stringify(data)); } catch (e) { }
  }

  /* 最近玩过、并且现在还看得到的题库（banks 是首页取回来的列表），最近的在前 */
  function list(storage, key, banks, limit) {
    var byId = {};
    (banks || []).forEach(function (b) { byId[b.id] = b; });
    var out = [];
    (load(storage)[key] || []).forEach(function (x) {
      if (x && byId[x.id] && out.length < (limit || 4)) out.push({ bank: byId[x.id], t: x.t });
    });
    return out;
  }

  /* 「多久以前」：返回 { key, n }，由页面用词条翻译 */
  function ago(t, now) {
    var sec = Math.max(0, Math.round((now - t) / 1000));
    if (sec < 60) return { key: 'home_agoNow', n: 0 };
    if (sec < 3600) return { key: 'home_agoMin', n: Math.floor(sec / 60) };
    if (sec < 86400) return { key: 'home_agoHour', n: Math.floor(sec / 3600) };
    var days = Math.floor(sec / 86400);
    if (days === 1) return { key: 'home_agoYesterday', n: 1 };
    return { key: 'home_agoDays', n: days };
  }

  global.WPRecent = { KEY: KEY, MAX: MAX, userKey: userKey, add: add, list: list, ago: ago };
})(window);
