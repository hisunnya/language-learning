/* =============================================================
   config.js —— 部署相关的配置（改这里就行）

   这里只放「每个子站在哪儿」这种部署相关的地址，
   页面上的文案都在 hub.js 的 i18n 表里。

   三种常见部署方式，选一种，把对应的路径填上：

   A) 同一台服务器（默认）
      hub 在 80 端口，词境在 8082 端口，话题和 Ham Exam
      分别挂在 /topics/ 和 /ham/ 下。

   B) 不同端口
      把 href 改成完整地址，例如 http://10.1.1.93:8765/

   C) 不同域名
      把 href 改成完整地址，例如 http://lexica.lan/
   ============================================================= */
window.LINGUA_PROJECTS = {
   // 词境页面使用根路径资源，单独端口部署以免和 hub 冲突。
   lexica: window.location.protocol + "//" + window.location.hostname + ":8082/",

  // 每日话题 Daily Topics —— 纯前端
  topics: "/topics/",

  // 无线电执照 Ham Exam —— 纯前端
  ham: "/ham/",
};
