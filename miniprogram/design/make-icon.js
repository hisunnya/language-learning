/* 词境 图标生成器 —— 改下面的 P 就能出新的 PNG/SVG。
   用法： node make-icon.js
   依赖： glyphs-cuan.js（由 ttf2path.py 从字体提取的字形路径，已转曲线，不依赖字体安装） */
const fs = require('fs');
const path = require('path');
const G = require('./glyphs-cuan.js');

/* ============ 参数区：改这里 ============ */
const P = {
  canvas: 1024,           // 画布边长
  rotation: -9,           // 整体倾斜角度（度，顺时针为正）

  // 背景渐变：三段色 + 各自位置（0~1）
  bg: ['#2a6049', '#1a4233', '#0e2a1f'],
  bgStops: [0, 0.55, 1],

  // 字色渐变：两段色（左上 → 右下）
  ink: ['#f4e9cf', '#e4d4ae'],

  chars: ['词', '境'],    // 双字构图用的两个字

  // 单字构图：size 是字号（unitsPerEm=1000 下的等效字号），center 是墨迹中心
  single: { size: 1278, center: [508, 508] },

  // 双字构图：两个字各自的字号与墨迹中心；size 越大字越大、重叠越多
  pair: {
    size: 776,
    p1: [400, 282],       // 「词」的墨迹中心
    p2: [648, 744]        // 「境」的墨迹中心
  },

  out: {
    svg: 'icon.svg',            // 生产用：颜色写死，兼容性最好
    svgParam: 'icon-param.svg'  // 可调版：颜色走 CSS 变量
  }
};
/* ======================================= */

/* 把字形摆到 (CX,CY)：字体坐标 y 向上、SVG y 向下，所以纵向 scale 取负。
   外层 translate 把「墨迹中心」而不是「字身框」对准目标点，这样不同字面率的字重心一致。 */
function place(ch, size, cx, cy) {
  const g = G.glyphs[ch];
  if (!g) throw new Error('字形里没有「' + ch + '」，用 ttf2path.py 重新提取');
  const s = size / G.unitsPerEm;
  const bx = (g.bbox[0] + g.bbox[2]) / 2;
  const by = (g.bbox[1] + g.bbox[3]) / 2;
  const t = 'translate(' + cx + ' ' + cy + ') scale(' + +s.toFixed(5) + ' ' + -(+s.toFixed(5)) +
    ') translate(' + -bx + ' ' + -by + ')';
  return '<path transform="' + t + '" d="' + g.d + '"/>';
}

function body(G_OPTS) {
  const rot = P.rotation ? ' transform="rotate(' + P.rotation + ' ' + P.canvas / 2 + ' ' + P.canvas / 2 + ')"' : '';
  const a = place(P.chars[0], P.pair.size, P.pair.p1[0], P.pair.p1[1]);
  const b = place(P.chars[1], P.pair.size, P.pair.p2[0], P.pair.p2[1]);
  return '  <g' + rot + ' fill="' + G_OPTS.ink + '">\n    ' + a + '\n    ' + b + '\n  </g>\n';
}

function defs(G_OPTS) {
  let s = '  <defs>\n';
  s += '    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">\n';
  P.bg.forEach(function (c, i) {
    s += '      <stop offset="' + P.bgStops[i] + '" class="b' + (i + 1) + '" stop-color="' + c + '"/>\n';
  });
  s += '    </linearGradient>\n';
  s += '    <linearGradient id="ink" x1="0" y1="0" x2="0.6" y2="1">\n';
  P.ink.forEach(function (c, i) {
    s += '      <stop offset="' + i + '" class="i' + (i + 1) + '" stop-color="' + c + '"/>\n';
  });
  s += '    </linearGradient>\n  </defs>\n';
  return s;
}

const head = '<?xml version="1.0" encoding="UTF-8"?>\n' +
  '<svg xmlns="http://www.w3.org/2000/svg" width="' + P.canvas + '" height="' + P.canvas + '" ' +
  'viewBox="0 0 ' + P.canvas + ' ' + P.canvas + '">\n' +
  '  <title>词境 · 单词消消乐</title>\n';

/* 1. 生产版：颜色写死 */
const plain =
  head + defs({ ink: 'url(#ink)' }) +
  '  <rect width="' + P.canvas + '" height="' + P.canvas + '" fill="url(#bg)"/>\n' +
  body({ ink: 'url(#ink)' }) +
  '</svg>\n';

/* 2. 可调版：颜色走 CSS 变量，改 :root 里的 5 个色值即可 */
const param =
  '<?xml version="1.0" encoding="UTF-8"?>\n' +
  '<!-- 词境图标 · 可调版\n' +
  '     改色：只改下面 style 里 :root 的 5 个色值（bg-1/2/3 是背景三段，ink-1/2 是字色）\n' +
  '     改大小：改每个 path 的 transform 里 scale 的第 1 个数（保持正数）\n' +
  '     改位置：改每个 path 的 transform 里 translate 的前两个数\n' +
  '     改倾斜：改外层 g 的 rotate 角度\n' +
  '     字形已转曲线，不依赖字体安装，任何机器打开都一致\n' +
  '     注意：XML 注释里不能出现连续两个减号，所以这里不写变量全名 -->\n' +
  '<svg xmlns="http://www.w3.org/2000/svg" width="' + P.canvas + '" height="' + P.canvas + '" ' +
  'viewBox="0 0 ' + P.canvas + ' ' + P.canvas + '">\n' +
  '  <title>词境 · 单词消消乐</title>\n' +
  '  <style>\n' +
  '    :root {\n' +
  '      --bg-1: ' + P.bg[0] + ';\n' +
  '      --bg-2: ' + P.bg[1] + ';\n' +
  '      --bg-3: ' + P.bg[2] + ';\n' +
  '      --ink-1: ' + P.ink[0] + ';\n' +
  '      --ink-2: ' + P.ink[1] + ';\n' +
  '    }\n' +
  '    .b1 { stop-color: var(--bg-1) }\n' +
  '    .b2 { stop-color: var(--bg-2) }\n' +
  '    .b3 { stop-color: var(--bg-3) }\n' +
  '    .i1 { stop-color: var(--ink-1) }\n' +
  '    .i2 { stop-color: var(--ink-2) }\n' +
  '  </style>\n' +
  defs({ ink: 'url(#ink)' }) +
  '  <rect width="' + P.canvas + '" height="' + P.canvas + '" fill="url(#bg)"/>\n' +
  body({ ink: 'url(#ink)' }) +
  '</svg>\n';

const dir = __dirname;
fs.writeFileSync(path.join(dir, P.out.svg), plain);
fs.writeFileSync(path.join(dir, P.out.svgParam), param);

/* 同时导出一份单字版，方便以后改主意 */
function writeSingle(file) {
  const rot = ' transform="rotate(' + P.rotation + ' ' + P.canvas / 2 + ' ' + P.canvas / 2 + ')"';
  const svg = head + defs({ ink: 'url(#ink)' }) +
    '  <rect width="' + P.canvas + '" height="' + P.canvas + '" fill="url(#bg)"/>\n' +
    '  <g' + rot + ' fill="url(#ink)">\n    ' +
    place(P.chars[0], P.single.size, P.single.center[0], P.single.center[1]) +
    '\n  </g>\n</svg>\n';
  fs.writeFileSync(path.join(dir, file), svg);
}
writeSingle('icon-single.svg');

console.log('已生成：');
console.log('  ' + P.out.svg + '        ' + fs.statSync(path.join(dir, P.out.svg)).size + ' B');
console.log('  ' + P.out.svgParam + '   ' + fs.statSync(path.join(dir, P.out.svgParam)).size + ' B');
console.log('  icon-single.svg   ' + fs.statSync(path.join(dir, 'icon-single.svg')).size + ' B');
