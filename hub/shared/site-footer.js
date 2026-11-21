/* =============================================================
   site-footer.js —— 全站页脚：ICP 备案号、公安备案号、隐私说明链接，以及第一次来访时的一条小提示。

   每个对外页面都加载它（主页、词境的每一页、化学 / 物理 / 话题 / 无线电、隐私说明页），
   改备案号只改下面 SITE 里的一行。备案号是公开信息，可以写在仓库里。

   语言跟着页面：读 <html lang>，页面切换语言时（各页面的机制不同，但最后都会改 lang）自动重画。
   颜色只用 currentColor 和透明度，任何配色下都不刺眼，不依赖某一套 CSS 变量。
   ============================================================= */
(function () {
  'use strict';

  var SITE = {
    icp: 'ICP备00000号',                       /* 拿到真号码后改成完整的，例如「京ICP备12345678号」 */
    icpUrl: 'https://beian.miit.gov.cn/',
    police: '',                                /* 公安备案号（例如「京公网安备 11010502000000号」），没有就留空，不显示 */
    policeUrl: 'https://beian.mps.gov.cn/#/query/webSearch',
    privacy: '/privacy.html'
  };
  var NOTICE_KEY = 'lx_notice_ok';

  var TEXT = {
    zh: { privacy: '隐私说明', notice: '本站用浏览器的本地存储记住你的语言、配色和得分，并记录访问情况用于统计。', more: '详见隐私说明', ok: '知道了', name: '词境' },
    en: { privacy: 'Privacy', notice: 'This site keeps your language, palette and scores in your browser and records visits for statistics.', more: 'See the privacy notice', ok: 'OK', name: 'Lexica' }
  };

  function lang() { return (document.documentElement.lang || '').indexOf('en') === 0 ? 'en' : 'zh'; }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }

  /* ICP 小徽章：一个盾形图标 + 号码。公安备案有官方图标，拿到号码后可以把 POLICE_ICON 换成官方图片 */
  var SHIELD = '<svg viewBox="0 0 24 24" width="13" height="13" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" ' +
    'stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l7 3v5c0 4.5-3 8.2-7 10-4-1.8-7-5.5-7-10V6z"/><path d="M9 12l2 2 4-4"/></svg>';
  var POLICE_ICON = SHIELD;

  /* [配色, 底色, 文字, 边框, 按钮底, 按钮字]：五套配色和网站一致；没有配色的页面用上面的默认深灰 */
  var NOTICE_THEMES = [
    ['indigo', '#1e1b4b', '#eef2ff', '#312e81', '#4f46e5', '#ffffff'],
    ['ink', '#142019', '#e8f4ee', '#34d399', '#34d399', '#062317'],
    ['amber', '#3d2a00', '#fbf6ec', '#92400e', '#d97706', '#ffffff'],
    ['lotus', '#4a1f33', '#fdf4f6', '#9d174d', '#db2777', '#ffffff'],
    ['obsidian', '#16161a', '#f3f0e5', '#d4af37', '#d4af37', '#15120a']
  ];

  var CSS = [
    '.lx-foot{margin:36px auto 18px;padding:14px 16px 4px;max-width:1100px;text-align:center;font-size:12.5px;line-height:1.9;',
    '  border-top:1px solid color-mix(in srgb,currentColor 14%,transparent);opacity:.78}',
    '.lx-foot a{color:inherit;text-decoration:none}',
    '.lx-foot a:hover{text-decoration:underline}',
    '.lx-foot .lx-row{display:flex;flex-wrap:wrap;justify-content:center;align-items:center;gap:8px 14px}',
    '.lx-badge{display:inline-flex;align-items:center;gap:6px;padding:2px 10px 2px 8px;border-radius:999px;',
    '  border:1px solid color-mix(in srgb,currentColor 22%,transparent);background:color-mix(in srgb,currentColor 5%,transparent)}',
    '.lx-badge:hover{text-decoration:none!important;border-color:color-mix(in srgb,currentColor 45%,transparent)}',
    '.lx-badge svg{flex:none}',
    '.lx-sep{opacity:.5}',
    '.lx-notice{position:fixed;left:50%;bottom:14px;transform:translateX(-50%);z-index:9999;width:min(640px,calc(100vw - 24px));',
    '  display:flex;align-items:center;gap:12px;padding:10px 12px 10px 16px;border-radius:12px;font-size:13px;line-height:1.55;',
    '  background:#1f2430;color:#f2f4f8;box-shadow:0 10px 30px rgba(0,0,0,.28)}',
    '.lx-notice a{color:inherit;text-decoration:underline}',
    '.lx-notice span{flex:1}',
    '.lx-notice button{flex:none;border:0;border-radius:8px;padding:6px 14px;font:inherit;font-weight:700;cursor:pointer;background:#f2f4f8;color:#1f2430}'
  ].concat(NOTICE_THEMES.map(function (th) {
    /* 每套配色：用它自己的深色当底、主色当按钮，换配色时跟着变，同时保持够醒目 */
    return 'html[data-theme="' + th[0] + '"] .lx-notice{background:' + th[1] + ';color:' + th[2] + ';border:1px solid ' + th[3] + '}' +
      'html[data-theme="' + th[0] + '"] .lx-notice button{background:' + th[4] + ';color:' + th[5] + '}';
  })).join('\n');

  function footerHtml(t) {
    var parts = ['<a class="lx-badge" href="' + SITE.icpUrl + '" target="_blank" rel="noopener">' + SHIELD + '<span>' + esc(SITE.icp) + '</span></a>'];
    if (SITE.police) {
      parts.push('<a class="lx-badge" href="' + SITE.policeUrl + '" target="_blank" rel="noopener">' + POLICE_ICON + '<span>' + esc(SITE.police) + '</span></a>');
    }
    parts.push('<a href="' + SITE.privacy + '">' + esc(t.privacy) + '</a>');
    return '<div class="lx-row"><span>© ' + new Date().getFullYear() + ' ' + esc(t.name) + '</span><span class="lx-sep">·</span>' +
      parts.join('<span class="lx-sep">·</span>') + '</div>';
  }

  function seen() { try { return localStorage.getItem(NOTICE_KEY) === '1'; } catch (e) { return true; } }

  var foot, notice;

  function render() {
    var t = TEXT[lang()];
    foot.innerHTML = footerHtml(t);
    foot.setAttribute('aria-label', lang() === 'en' ? 'Site information' : '网站信息');
    if (notice) {
      notice.innerHTML = '<span>' + esc(t.notice) + ' <a href="' + SITE.privacy + '">' + esc(t.more) + '</a></span>' +
        '<button type="button">' + esc(t.ok) + '</button>';
      notice.querySelector('button').onclick = function () {
        try { localStorage.setItem(NOTICE_KEY, '1'); } catch (e) { /* 存不了下次再提示 */ }
        notice.remove();
        notice = null;
      };
    }
  }

  function start() {
    if (document.querySelector('.lx-foot')) return;
    var style = document.createElement('style');
    style.textContent = CSS;
    document.head.appendChild(style);
    foot = document.createElement('footer');
    foot.className = 'lx-foot';
    var host = document.querySelector('.wrap') || document.body;      /* main 可能被单页应用整块重画，所以不挂在 main 里 */
    host.appendChild(foot);
    if (!seen() && location.pathname !== SITE.privacy) {
      notice = document.createElement('div');
      notice.className = 'lx-notice';
      notice.setAttribute('role', 'region');
      document.body.appendChild(notice);
    }
    render();
    /* 各页面切换语言的机制不同，但都会改 <html lang>，盯着它就行 */
    new MutationObserver(render).observe(document.documentElement, { attributes: true, attributeFilter: ['lang'] });
  }

  window.LexicaSite = SITE;
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
