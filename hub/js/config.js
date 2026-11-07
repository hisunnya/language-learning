/* =============================================================
   config.js —— 部署相关的配置（改这里就行）

   这里只放「每个子站在哪儿」这种部署相关的地址，
   页面上的文案都在 hub.js 的 i18n 表里。

   三种常见部署方式，选一种，把对应的路径填上：

   A) 同一台服务器（默认）
      hub 在 80 端口，四个项目分别挂在 /word-puzzle/、
      /topics/、/ham/ 和 /chemistry/ 下。

   B) 不同端口
      把 href 改成完整地址，例如 http://10.1.1.93:8765/

   C) 不同域名
      把 href 改成完整地址，例如 http://lexica.lan/
   ============================================================= */
window.LINGUA_PROJECTS = {
   // 词境静态资源和 API 都通过 nginx 的同域子路径提供。
   lexica: "/word-puzzle/",

  // 每日话题 Daily Topics —— 纯前端
  topics: "/topics/",

  // 无线电执照 Ham Exam —— 纯前端
  ham: "/ham/",

   // 化学探秘 Chem Quest —— 纯前端
   chemistry: "/chemistry/",
};
