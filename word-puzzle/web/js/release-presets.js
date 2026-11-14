/* ============================================================
   release-presets.js —— 老师「批量开放」的预设范围（纯计算，不碰页面）
   ------------------------------------------------------------
   一本书按单元拆成了 total 个题库（按单元顺序排好）。老师不用逐个点，选一个预设：
     all        整本书
     firstHalf  上半部分（上学期）：前 ceil(total / 2) 个
     secondHalf 下半部分（下学期）：其余的
     firstN     前 n 个单元（n 超出范围会被收进 0 ~ total）
     none       清空
   返回被选中的位置（从 0 开始，升序）。
   ============================================================ */
(function (global) {
  'use strict';

  function range(from, to) {
    var out = [];
    for (var i = from; i < to; i++) out.push(i);
    return out;
  }

  function indexes(kind, total, n) {
    total = Math.max(0, total | 0);
    switch (kind) {
      case 'all': return range(0, total);
      case 'firstHalf': return range(0, Math.ceil(total / 2));
      case 'secondHalf': return range(Math.ceil(total / 2), total);
      case 'firstN': return range(0, Math.min(total, Math.max(0, parseInt(n, 10) || 0)));
      default: return [];
    }
  }

  global.WPRelease = { indexes: indexes, KINDS: ['all', 'firstHalf', 'secondHalf', 'firstN', 'none'] };
})(window);
