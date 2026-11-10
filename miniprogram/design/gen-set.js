/* 生成「字体 × 构图 × 配色」的图标矩阵。
   用法： node gen-set.js [fontKey|all]
   fontKey 见 FONTS，默认 songti；传 all 则全部生成。

   字号不写死：每个字体在 1000px 下的实测墨迹尺寸存在 METRICS 里（Chrome canvas
   measureText 以 alphabetic 基线测得），生成时按目标墨迹尺寸反算字号，并按墨迹框
   反算坐标 —— 这样不同字面率、不同基线位置的字体，视觉重心都落在同一处。 */
const fs = require('fs');
const path = require('path');

const D = 1024;                    // 画布边长
const TARGET_SINGLE = 1080;        // 单字：墨迹最长边（略溢出画布）
const TARGET_PAIR_H = 510;         // 双字：「词」的墨迹高
const C_SINGLE = [508, 508];       // 单字墨迹中心
const C_P1 = [400, 282];           // 双字「词」墨迹中心
const C_P2 = [648, 744];           // 双字「境」墨迹中心

/* 1000px / alphabetic 基线下的实测墨迹：w 宽、h 高、hOff 横向偏移、asc/desc 上下伸出 */
const METRICS = {
  songti:    { ci: { w: 911, h: 931, hOff: -9.5,  asc: 752, desc: 179 }, jing: { w: 958, h: 948, hOff: 4.0,  asc: 778, desc: 170 } },
  cuan:      { ci: { w: 845, h: 657, hOff: -0.5,  asc: 683, desc: -26 }, jing: { w: 805, h: 894, hOff: -6.5, asc: 801, desc: 93 } },
  cms:       { ci: { w: 899, h: 848, hOff: -26.5, asc: 759, desc: 89 }, jing: { w: 942, h: 927, hOff: 12.0, asc: 814, desc: 113 } },
  xiongfeng: { ci: { w: 891, h: 892, hOff: -0.5,  asc: 796, desc: 96 },  jing: { w: 901, h: 873, hOff: 0.5,  asc: 785, desc: 88 } },
  yunmo:     { ci: { w: 843, h: 813, hOff: 1.5,   asc: 759, desc: 54 },  jing: { w: 911, h: 865, hOff: 5.5,  asc: 783, desc: 82 } },
  heibian:   { ci: { w: 831, h: 830, hOff: -30.5, asc: 754, desc: 76 },  jing: { w: 923, h: 924, hOff: 0.5,  asc: 819, desc: 105 } }
};

const FONTS = {
  cuan:      { family: 'FZCuanBaoZiBeiKaiShuJF', weight: 400, label: '爨宝子碑楷书', note: '招行/招证同源 · 粗笔画' },
  cms:       { family: 'CMS Font',               weight: 700, label: '招商证券体',   note: '招证官方字库 · 最接近行标' },
  xiongfeng: { family: 'ZKTXFKJ',                weight: 400, label: '字酷堂雄风楷', note: '魏碑方笔 · 骨力强' },
  yunmo:     { family: 'ZKTYMKSJ',               weight: 400, label: '字酷堂云墨楷书', note: '墨迹洇润 · 楷书底' },
  heibian:   { family: 'FZHeiBianS-R-GB',        weight: 400, label: '方正黑变',     note: '黑体变形 · 现代感' },
  songti:    { family: 'Songti SC',              weight: 700, label: '宋体',         note: '细笔画 · 文气重' }
};

const PALETTES = [
  { key: 'vermilion', name: '朱红', bg: ['#d8442f', '#c5331f', '#a72716'], fg: ['#fdf3df', '#f2dfbd'] },
  { key: 'ink', name: '墨黑', bg: ['#2b2b2f', '#191919', '#0b0b0c'], fg: ['#f6ecd6', '#e8d8b6'] },
  { key: 'indigo', name: '靛蓝', bg: ['#3a4ccb', '#27339b', '#171f6b'], fg: ['#f5ecd6', '#e6d6b4'] },
  { key: 'forest', name: '墨绿', bg: ['#2a6049', '#1a4233', '#0e2a1f'], fg: ['#f4e9cf', '#e4d4ae'] },
  { key: 'ochre', name: '赭橙', bg: ['#ef8f34', '#dc6f1c', '#b85410'], fg: ['#2a1c0e', '#1a1006'] },
  { key: 'paper', name: '米白', bg: ['#f6ecd6', '#ebdaba', '#dcc59c'], fg: ['#c9381f', '#a72716'] }
];

const arg = process.argv[2] || 'songti';
const keys = arg === 'all' ? Object.keys(FONTS) : [arg];
keys.forEach(function (k) { if (!FONTS[k]) { console.error('未知字体：' + k); process.exit(1); } });

/* 由墨迹反算字号与坐标 */
function solve(k) {
  const M = METRICS[k];
  const singleMax = Math.max(M.ci.w, M.ci.h);
  const size1 = 1000 * TARGET_SINGLE / singleMax;
  const size2 = 1000 * TARGET_PAIR_H / M.ci.h;
  const s1 = size1 / 1000, s2 = size2 / 1000;
  return {
    size1: size1, size2: size2,
    x1: C_SINGLE[0] - M.ci.hOff * s1,
    y1: C_SINGLE[1] + (M.ci.asc - M.ci.desc) * s1 / 2,
    x2a: C_P1[0] - M.ci.hOff * s2,
    y2a: C_P1[1] + (M.ci.asc - M.ci.desc) * s2 / 2,
    x2b: C_P2[0] - M.jing.hOff * s2,
    y2b: C_P2[1] + (M.jing.asc - M.jing.desc) * s2 / 2
  };
}

function defs(id, p) {
  return `  <defs>
    <linearGradient id="bg-${id}" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="${p.bg[0]}"/>
      <stop offset="0.55" stop-color="${p.bg[1]}"/>
      <stop offset="1" stop-color="${p.bg[2]}"/>
    </linearGradient>
    <linearGradient id="ink-${id}" x1="0" y1="0" x2="0.6" y2="1">
      <stop offset="0" stop-color="${p.fg[0]}"/>
      <stop offset="1" stop-color="${p.fg[1]}"/>
    </linearGradient>
  </defs>`;
}

function build(id, p, comp, S, F) {
  const head = `<svg xmlns="http://www.w3.org/2000/svg" width="${D}" height="${D}" viewBox="0 0 ${D} ${D}">\n${defs(id, p)}\n` +
    `  <rect width="${D}" height="${D}" fill="url(#bg-${id})"/>\n  <g transform="rotate(-9 512 512)">\n`;
  const fam = `font-family="${F.family}" font-weight="${F.weight}" text-anchor="middle" fill="url(#ink-${id})"`;
  const single = `    <text x="${S.x1.toFixed(1)}" y="${S.y1.toFixed(1)}" font-size="${S.size1.toFixed(1)}" ${fam}>词</text>\n`;
  const pair = `    <text x="${S.x2a.toFixed(1)}" y="${S.y2a.toFixed(1)}" font-size="${S.size2.toFixed(1)}" ${fam}>词</text>\n` +
    `    <text x="${S.x2b.toFixed(1)}" y="${S.y2b.toFixed(1)}" font-size="${S.size2.toFixed(1)}" ${fam}>境</text>\n`;
  return head + (comp === 'single' ? single : pair) + '  </g>\n</svg>\n';
}

let dir = __dirname;

function renderFont(k) {
  const F = FONTS[k], S = solve(k);
  const outDir = path.join(dir, 'out-' + k);
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir);
  ['single', 'pair'].forEach(function (comp) {
    PALETTES.forEach(function (p) {
      const id = k + '-' + comp + '-' + p.key;
      fs.writeFileSync(path.join(outDir, id + '.svg'), build(id, p, comp, S, F));
    });
  });
  const row = function (comp) {
    return PALETTES.map(function (p) {
      return `<div class="col">
      <img class="big" src="out-${k}/${k}-${comp}-${p.key}.svg">
      <img class="sm" src="out-${k}/${k}-${comp}-${p.key}.svg">
      <div class="cap">${p.name}</div></div>`;
    }).join('');
  };
  const sheet = `<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8"><style>
  *{box-sizing:border-box}
  body{margin:0;padding:20px;background:#eef0f3;font-family:-apple-system,"PingFang SC",sans-serif}
  .h{font-size:12px;color:#666;margin:2px 0 4px 2px;letter-spacing:1px}
  .meta{font-size:11px;color:#9aa0a8;margin:0 0 12px 2px}
  .row{display:flex;gap:14px;margin-bottom:12px}
  .col{text-align:center}
  .big{width:178px;height:178px;border-radius:40px;display:block}
  .sm{width:44px;height:44px;border-radius:10px;margin-top:7px;display:inline-block}
  .cap{margin-top:6px;font-size:13px;color:#222}
  .h2{font-size:12px;color:#666;margin:2px 0 8px 2px;letter-spacing:1px}
</style></head><body>
  <div class="h">${F.label} · 单字「词」· 字号 ${S.size1.toFixed(0)}</div>
  <div class="meta">${F.note}</div>
  <div class="row">${row('single')}</div>
  <div class="h2">${F.label} · 双字「词境」· 字号 ${S.size2.toFixed(0)}</div>
  <div class="row">${row('pair')}</div>
</body></html>`;
  fs.writeFileSync(path.join(dir, 'sheet-' + k + '.html'), sheet);
  console.log('  ' + k.padEnd(11) + ' 单 ' + S.size1.toFixed(0).padStart(5) + '  双 ' + S.size2.toFixed(0).padStart(4));
}

keys.forEach(renderFont);

/* 主对比条：同一配色（朱红）下六种字体并排，看字形差异 */
if (arg === 'all') {
  const rows = keys.map(function (k) {
    const F = FONTS[k], S = solve(k);
    return `<div class="fr">
      <div class="info"><div class="nm">${F.label}</div><div class="nt">${F.note}</div></div>
      <img src="out-${k}/${k}-single-vermilion.svg">
      <img src="out-${k}/${k}-pair-vermilion.svg">
      <div class="sz">${S.size1.toFixed(0)}<span>/</span>${S.size2.toFixed(0)}</div>
    </div>`;
  }).join('');
  fs.writeFileSync(path.join(dir, 'all-fonts.html'), `<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8"><style>
  *{box-sizing:border-box}
  body{margin:0;padding:24px 26px;background:#eceef1;font-family:-apple-system,"PingFang SC",sans-serif;color:#1c1c1e}
  h1{font-size:16px;margin:0 0 3px;letter-spacing:.5px}
  .sub{font-size:11.5px;color:#7a7f88;margin-bottom:18px}
  .fr{display:flex;align-items:center;gap:18px;background:#fff;border-radius:14px;padding:12px 16px;margin-bottom:10px}
  .info{width:190px;flex:none}
  .nm{font-size:14px;font-weight:600}
  .nt{font-size:11px;color:#8a8f98;margin-top:3px}
  .fr img{width:134px;height:134px;border-radius:31px;display:block;flex:none}
  .sz{width:80px;flex:none;font-size:11px;color:#a8adb5;text-align:right;letter-spacing:.5px}
  .sz span{color:#d4d8dd;margin:0 2px}
</style></head><body>
  <h1>六种字体 · 朱红单色对比</h1>
  <div class="sub">每行：字体名 · 单字「词」· 双字「词境」· 实际字号（单/双）</div>
  ${rows}
</body></html>`);
  console.log('主对比条 → all-fonts.html');
}
