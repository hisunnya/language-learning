/* =============================================================
   config.js —— 部署相关的配置（改这里就行）

   这里只放「每个子站在哪儿」这种部署相关的地址，
   页面上的文案都在 hub.js 的 i18n 表里。

   三种常见部署方式，选一种，把对应的路径填上：

   A) 同一台服务器（默认）
      hub 在 80 端口，六个项目分别挂在 /word-puzzle/、/topics/、/ham/、/chemistry/、
      /physics/ 和 /nvidia-exam/ 下。

   B) 不同端口
      把 href 改成完整地址，例如 http://服务器地址:8765/

   C) 不同域名
      把 href 改成完整地址，例如 http://lexica.lan/
   ============================================================= */
window.LINGUA_PROJECTS = {
   // 主页上的词境是不用登录的公开版（只有初中、高中）；要登录的 /word-puzzle/ 不放在主页上。
   lexica: "/words/",

  // 每日话题 Daily Topics —— 纯前端
  topics: "/topics/",

  // 无线电执照 Ham Exam —— 纯前端
  ham: "/ham/",

   // 化学探秘 Chem Quest —— 纯前端
   chemistry: "/chemistry/",

   // 物理探秘 Phys Quest —— 纯前端
   physics: "/physics/",

   // NVIDIA 认证模拟考试 NVIDIA Exam —— 纯前端
   nvidia: "/nvidia-exam/",
};
