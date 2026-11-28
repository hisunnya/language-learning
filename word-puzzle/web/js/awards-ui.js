/* ============================================================
   awards-ui.js —— 奖状和徽章的样子（「我的」页面、积分榜共用）
   ------------------------------------------------------------
   WPAwards.badge(award, size)        徽章 SVG：铜（10 天）/ 银（15 天）/ 金（30 天）
   WPAwards.mini(award)               积分榜名字旁边的小徽章
   WPAwards.draw(canvas, award)       在 canvas 上画奖状（2400×1697，A4 横版比例），中英双语
   WPAwards.save(award, type)         画好并下载 PNG / JPG（Promise；失败时弹提示并 reject）
   奖状不跟网站配色走：深蓝底、象牙白纸、按档次的金属色（固定颜色，打印、转发都一样好看）。
   ============================================================ */
(function (global) {
  'use strict';

  var METAL = {
    gold:   { a: '#FFF4C8', b: '#E2B33C', c: '#8E6510', ink: '#5A3D00', en: 'GOLD', zh: '金奖' },
    silver: { a: '#FFFFFF', b: '#C3CCDA', c: '#6D788B', ink: '#2E3A4D', en: 'SILVER', zh: '银奖' },
    bronze: { a: '#FFE2C6', b: '#CF8A55', c: '#7E4521', ink: '#4E260C', en: 'BRONZE', zh: '铜奖' }
  };
  var GAME = {
    all:   { zh: '总分', en: 'Overall' },
    match: { zh: '中英配对', en: 'Matching' },
    spell: { zh: '单词大比拼', en: 'Spell It' },
    order: { zh: '翻译排排坐', en: 'Translation Line-Up' },
    verb: { zh: '动词猎手', en: 'Verb Hunter' }
  };
  var NAVY = '#0E1F3D', IVORY = '#FFFCF4';
  var SERIF_EN = 'Georgia, "Times New Roman", "Noto Serif", serif';
  var SERIF_ZH = '"Songti SC", "STSong", "Noto Serif CJK SC", "Source Han Serif SC", "SimSun", serif';

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function metal(award) { return METAL[award.tier] || METAL.bronze; }
  function gameName(game, lang) { return (GAME[game] || GAME.all)[lang === 'en' ? 'en' : 'zh']; }

  function lang() { return global.WPI18N && global.WPI18N.lang() === 'en' ? 'en' : 'zh'; }
  /* 徽章的说明文字（提示、读屏）：金奖 · 总分 · 周榜累计 30 天第一 */
  function label(award) {
    var m = metal(award), l = lang();
    return l === 'en' ? m.en.charAt(0) + m.en.slice(1).toLowerCase() + ' · ' + gameName(award.game, 'en') + ' · No. 1 on the weekly board for ' + award.days + ' days'
      : m.zh + ' · ' + gameName(award.game, 'zh') + ' · 周榜累计 ' + award.days + ' 天第一';
  }

  var uid = 0;

  /* 徽章：一枚带丝带的勋章——外圈齿边、双圈、桂叶、中间是天数 */
  function badge(award, size) {
    var m = metal(award), g = 'wpAwG' + (++uid), n = award.days;
    size = size || 96;
    var teeth = '';
    for (var i = 0; i < 24; i++) {
      var ang = i * 15 * Math.PI / 180;
      teeth += '<circle cx="' + (50 + 33 * Math.cos(ang)).toFixed(1) + '" cy="' + (52 + 33 * Math.sin(ang)).toFixed(1) + '" r="4.2"/>';
    }
    var leaves = '';
    for (var k = 0; k < 7; k++) {
      var a1 = (200 + k * 18) * Math.PI / 180, a2 = (340 - k * 18) * Math.PI / 180;
      [a1, a2].forEach(function (a, side) {
        var x = 50 + 21 * Math.cos(a), y = 52 + 21 * Math.sin(a);
        var rot = a * 180 / Math.PI + (side ? -60 : 60);
        leaves += '<ellipse cx="' + x.toFixed(1) + '" cy="' + y.toFixed(1) + '" rx="3.4" ry="1.6" transform="rotate(' + rot.toFixed(0) + ' ' + x.toFixed(1) + ' ' + y.toFixed(1) + ')"/>';
      });
    }
    return '<svg class="aw-badge" width="' + size + '" height="' + Math.round(size * 1.18) + '" viewBox="0 0 100 118" role="img" aria-label="' +
      esc(label(award)) + '">' +
      '<defs><linearGradient id="' + g + '" x1="0.15" y1="0" x2="0.85" y2="1"><stop offset="0" stop-color="' + m.a + '"/>' +
      '<stop offset="0.55" stop-color="' + m.b + '"/><stop offset="1" stop-color="' + m.c + '"/></linearGradient></defs>' +
      '<path d="M30 78 L22 116 L36 108 L44 118 L50 84 Z" fill="' + NAVY + '"/><path d="M70 78 L78 116 L64 108 L56 118 L50 84 Z" fill="#1C3566"/>' +
      '<path d="M30 78 L22 116 L36 108 L44 118 L50 84 Z" fill="none" stroke="' + m.b + '" stroke-width="1"/>' +
      '<path d="M70 78 L78 116 L64 108 L56 118 L50 84 Z" fill="none" stroke="' + m.b + '" stroke-width="1"/>' +
      '<g fill="url(#' + g + ')">' + teeth + '</g><circle cx="50" cy="52" r="33" fill="url(#' + g + ')"/>' +
      '<circle cx="50" cy="52" r="27" fill="none" stroke="' + m.c + '" stroke-opacity=".6" stroke-width="1.4"/>' +
      '<circle cx="50" cy="52" r="24.5" fill="none" stroke="#fff" stroke-opacity=".45" stroke-width=".8"/>' +
      '<g fill="' + m.c + '" fill-opacity=".75">' + leaves + '</g>' +
      '<text x="50" y="57" text-anchor="middle" font-family=\'' + SERIF_EN.replace(/"/g, '') + '\' font-size="' + (n >= 10 ? 21 : 24) +
      '" font-weight="700" fill="' + m.ink + '">' + n + '</text>' +
      '<text x="50" y="67" text-anchor="middle" font-family="Georgia, serif" font-size="6.5" letter-spacing="1.2" fill="' + m.ink + '">DAYS</text>' +
      '</svg>';
  }

  function mini(award) {
    var m = metal(award);
    return '<span class="aw-mini" title="' + esc(label(award)) + '" style="--a:' + m.a +
      ';--b:' + m.b + ';--c:' + m.c + ';--ink:' + m.ink + '">' + award.days + '</span>';
  }

  /* ---------------- 奖状 ---------------- */

  var W = 2400, H = 1697;

  function metalGradient(ctx, m, x0, y0, x1, y1) {
    var g = ctx.createLinearGradient(x0, y0, x1, y1);
    g.addColorStop(0, m.c); g.addColorStop(0.3, m.b); g.addColorStop(0.5, m.a); g.addColorStop(0.7, m.b); g.addColorStop(1, m.c);
    return g;
  }

  function wrap(ctx, text, maxWidth, splitter) {
    var parts = splitter === '' ? text.split('') : text.split(' ');
    var lines = [], line = '';
    parts.forEach(function (p) {
      var test = line ? line + splitter + p : p;
      if (ctx.measureText(test).width > maxWidth && line) { lines.push(line); line = p; } else line = test;
    });
    if (line) lines.push(line);
    return lines;
  }

  function spaced(ctx, text, x, y, spacing) {
    /* 拉开字距的标题（canvas 的 letterSpacing 不是每个浏览器都有，自己一个字一个字排） */
    var chars = text.split(''), widths = chars.map(function (c) { return ctx.measureText(c).width; });
    var total = widths.reduce(function (a, b) { return a + b; }, 0) + spacing * (chars.length - 1);
    var cx = x - total / 2;
    ctx.textAlign = 'left';
    chars.forEach(function (c, i) { ctx.fillText(c, cx, y); cx += widths[i] + spacing; });
    ctx.textAlign = 'center';
  }

  function sprig(ctx, x, y, dir, len, color) {
    /* 一枝桂叶：从 (x, y) 向外（dir = -1 往左，1 往右）微微上扬的枝条，两边交替长叶子，越往外越小 */
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(dir, 1);
    ctx.strokeStyle = color; ctx.fillStyle = color; ctx.lineWidth = 3; ctx.lineCap = 'round';
    function at(t) { return { x: t * len, y: -Math.sin(t * Math.PI * 0.55) * len * 0.22 }; }
    ctx.beginPath();
    for (var i = 0; i <= 20; i++) { var p = at(i / 20); ctx[i ? 'lineTo' : 'moveTo'](p.x, p.y); }
    ctx.stroke();
    for (var k = 0; k < 7; k++) {
      var t = 0.12 + k * 0.13, p0 = at(t), p1 = at(t + 0.02);
      var ang = Math.atan2(p1.y - p0.y, p1.x - p0.x), size = 1 - k * 0.08;
      [-1, 1].forEach(function (side) {
        ctx.save();
        ctx.translate(p0.x, p0.y);
        ctx.rotate(ang + side * 0.75);
        ctx.beginPath();
        ctx.ellipse(16 * size, 0, 17 * size, 6.5 * size, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      });
    }
    var tip = at(1);
    ctx.beginPath(); ctx.ellipse(tip.x + 8, tip.y - 2, 12, 5, -0.3, 0, Math.PI * 2); ctx.fill();
    ctx.restore();
  }

  /* 中文换行：标点不放在行首（挪到上一行末尾） */
  function wrapZh(ctx, text, maxWidth) {
    var lines = wrap(ctx, text, maxWidth, '');
    for (var i = 1; i < lines.length; i++) {
      while (lines[i] && '，。、；：！？）」』》,.;:!?)'.indexOf(lines[i].charAt(0)) >= 0) {
        lines[i - 1] += lines[i].charAt(0);
        lines[i] = lines[i].slice(1);
      }
    }
    return lines.filter(Boolean);
  }

  function seal(ctx, award, cx, cy) {
    var m = metal(award), R = 150;
    /* 丝带 */
    ctx.fillStyle = NAVY;
    [[-1, '#0E1F3D'], [1, '#1C3566']].forEach(function (s) {
      ctx.fillStyle = s[1];
      ctx.beginPath();
      ctx.moveTo(cx + s[0] * 40, cy + 60);
      ctx.lineTo(cx + s[0] * 85, cy + 225);
      ctx.lineTo(cx + s[0] * 55, cy + 200);
      ctx.lineTo(cx + s[0] * 28, cy + 232);
      ctx.lineTo(cx + s[0] * 5, cy + 90);
      ctx.closePath();
      ctx.fill();
    });
    /* 齿边圆盘 */
    ctx.fillStyle = metalGradient(ctx, m, cx - R, cy - R, cx + R, cy + R);
    ctx.beginPath();
    for (var i = 0; i <= 72; i++) {
      var a = i * Math.PI * 2 / 72, rr = i % 2 ? R : R - 12;
      ctx[i ? 'lineTo' : 'moveTo'](cx + rr * Math.cos(a), cy + rr * Math.sin(a));
    }
    ctx.closePath();
    ctx.fill();
    ctx.strokeStyle = m.c; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.arc(cx, cy, R - 30, 0, Math.PI * 2); ctx.stroke();
    ctx.strokeStyle = 'rgba(255,255,255,.55)'; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.arc(cx, cy, R - 38, 0, Math.PI * 2); ctx.stroke();
    /* 圆周上的字 */
    ctx.save();
    ctx.fillStyle = m.ink;
    ctx.font = '600 21px ' + SERIF_EN;
    var ring = '★ LEXICA · ' + m.en + ' AWARD · ' + award.days + ' DAYS AT No.1 ★ ';
    var step = Math.PI * 2 / ring.length;
    for (var k = 0; k < ring.length; k++) {
      ctx.save();
      ctx.translate(cx, cy);
      ctx.rotate(-Math.PI / 2 + k * step);
      ctx.fillText(ring[k], 0, -(R - 52));
      ctx.restore();
    }
    ctx.restore();
    ctx.fillStyle = m.ink;
    ctx.textAlign = 'center';
    ctx.font = '700 104px ' + SERIF_EN;
    ctx.fillText(String(award.days), cx, cy + 30);
    ctx.font = '600 24px ' + SERIF_EN;
    ctx.fillText('DAYS · 天', cx, cy + 66);
  }

  function draw(canvas, award) {
    var m = metal(award), ctx = canvas.getContext('2d');
    canvas.width = W; canvas.height = H;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'alphabetic';

    /* 深蓝外框 + 象牙白纸 */
    ctx.fillStyle = NAVY; ctx.fillRect(0, 0, W, H);
    var pad = 70, paper = ctx.createLinearGradient(0, 0, W, H);
    paper.addColorStop(0, IVORY); paper.addColorStop(1, '#F4ECDA');
    ctx.fillStyle = paper; ctx.fillRect(pad, pad, W - pad * 2, H - pad * 2);

    /* 水印：细线花饰 + LEXICA 字样（很淡） */
    ctx.save();
    ctx.translate(W / 2, H / 2 + 40);
    ctx.strokeStyle = 'rgba(14,31,61,.045)'; ctx.lineWidth = 1.4;
    for (var i = 0; i < 48; i++) { ctx.rotate(Math.PI / 24); ctx.beginPath(); ctx.ellipse(0, 0, 520, 160, 0, 0, Math.PI * 2); ctx.stroke(); }
    ctx.restore();
    ctx.fillStyle = 'rgba(14,31,61,.035)';
    ctx.font = '700 300px ' + SERIF_EN;
    ctx.fillText('LEXICA', W / 2, H / 2 + 150);

    /* 金属色双线边框 + 四角装饰 */
    var mg = metalGradient(ctx, m, 0, 0, W, H);
    ctx.strokeStyle = mg; ctx.lineWidth = 10; ctx.strokeRect(pad + 34, pad + 34, W - (pad + 34) * 2, H - (pad + 34) * 2);
    ctx.lineWidth = 3; ctx.strokeRect(pad + 56, pad + 56, W - (pad + 56) * 2, H - (pad + 56) * 2);
    [[pad + 56, pad + 56, 1, 1], [W - pad - 56, pad + 56, -1, 1], [pad + 56, H - pad - 56, 1, -1], [W - pad - 56, H - pad - 56, -1, -1]].forEach(function (c) {
      ctx.save(); ctx.translate(c[0], c[1]); ctx.scale(c[2], c[3]);
      ctx.fillStyle = mg;
      ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(90, 0); ctx.lineTo(0, 90); ctx.closePath(); ctx.fill();
      ctx.strokeStyle = mg; ctx.lineWidth = 3;
      ctx.beginPath(); ctx.arc(0, 0, 130, 0, Math.PI / 2); ctx.stroke();
      ctx.beginPath(); ctx.arc(0, 0, 150, 0, Math.PI / 2); ctx.stroke();
      ctx.restore();
    });

    /* 顶部：词境 · LEXICA，两侧桂枝 */
    ctx.fillStyle = m.c;
    ctx.font = '600 34px ' + SERIF_EN;
    spaced(ctx, 'LEXICA  ·  词境', W / 2, 270, 8);
    sprig(ctx, W / 2 - 215, 262, -1, 170, m.b);
    sprig(ctx, W / 2 + 215, 262, 1, 170, m.b);

    /* 标题 */
    ctx.fillStyle = NAVY;
    ctx.font = '700 104px ' + SERIF_EN;
    spaced(ctx, 'CERTIFICATE OF EXCELLENCE', W / 2, 420, 10);
    ctx.fillStyle = m.c;
    ctx.font = '700 64px ' + SERIF_ZH;
    spaced(ctx, '荣誉证书', W / 2, 510, 40);
    ctx.strokeStyle = mg; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.moveTo(W / 2 - 420, 560); ctx.lineTo(W / 2 - 40, 560); ctx.moveTo(W / 2 + 40, 560); ctx.lineTo(W / 2 + 420, 560); ctx.stroke();
    ctx.fillStyle = m.b; ctx.beginPath(); ctx.moveTo(W / 2, 546); ctx.lineTo(W / 2 + 14, 560); ctx.lineTo(W / 2, 574); ctx.lineTo(W / 2 - 14, 560); ctx.fill();

    /* 授予 */
    ctx.fillStyle = '#56607A';
    ctx.font = 'italic 40px ' + SERIF_EN;
    ctx.fillText('This certificate is proudly presented to', W / 2, 650);
    ctx.font = '36px ' + SERIF_ZH;
    ctx.fillText('兹授予', W / 2, 702);

    /* 名字 */
    ctx.fillStyle = NAVY;
    var nameSize = 150;
    ctx.font = '700 ' + nameSize + 'px ' + SERIF_ZH;
    while (ctx.measureText(award.name || '').width > 1300 && nameSize > 80) { nameSize -= 8; ctx.font = '700 ' + nameSize + 'px ' + SERIF_ZH; }
    ctx.fillText(award.name || '', W / 2, 860);
    ctx.strokeStyle = mg; ctx.lineWidth = 4;
    ctx.beginPath(); ctx.moveTo(W / 2 - 560, 900); ctx.lineTo(W / 2 + 560, 900); ctx.stroke();
    if (award.class_name) {
      ctx.fillStyle = '#56607A';
      ctx.font = '34px ' + SERIF_ZH;
      ctx.fillText(award.class_name, W / 2, 952);
    }

    /* 正文：英文、中文 */
    var label = award.board_label || '';                         /* 总榜的标题，或者班级名 */
    var gameEn = award.game === 'all' ? 'overall' : gameName(award.game, 'en');
    var gameZh = award.game === 'all' ? '总分' : gameName(award.game, 'zh');
    var en = 'for holding the No. 1 position on the weekly ' + gameEn + ' leaderboard' + (label ? ' (' + label + ')' : '') +
      ' on ' + award.days + ' days in total, from ' + award.start_day + ' to ' + award.end_day + '.';
    var zh = '在' + (label ? '「' + label + '」的' : '') + gameZh + '周榜上，累计 ' + award.days + ' 天位居榜首（' +
      award.start_day + ' 至 ' + award.end_day + '），成绩卓越，特发此证，以资鼓励。';
    /* 宽度和行数都有上限：右下角是印章，正文不能伸进去（班级名很长时字号自动变小） */
    ctx.fillStyle = '#25304A';
    var size = 40, enLines, zhLines;
    for (;;) {
      ctx.font = size + 'px ' + SERIF_EN;
      enLines = wrap(ctx, en, 1460, ' ');
      ctx.font = (size - 2) + 'px ' + SERIF_ZH;
      zhLines = wrapZh(ctx, zh, 1420);
      if (enLines.length + zhLines.length <= 4 || size <= 28) break;
      size -= 2;
    }
    var y = 1020, gap = Math.round(size * 1.38);
    ctx.font = size + 'px ' + SERIF_EN;
    enLines.forEach(function (line) { ctx.fillText(line, W / 2, y); y += gap; });
    ctx.font = (size - 2) + 'px ' + SERIF_ZH;
    y += 12;
    zhLines.forEach(function (line) { ctx.fillText(line, W / 2, y); y += gap; });

    /* 印章（右下）、签名和日期（左下）、编号（底部中间） */
    seal(ctx, award, W - 450, 1335);
    var issued = new Date((award.created_at || Date.now() / 1000) * 1000);
    var date = issued.getFullYear() + '-' + ('0' + (issued.getMonth() + 1)).slice(-2) + '-' + ('0' + issued.getDate()).slice(-2);
    [[480, award.teacher || '', 'Teacher · 指导老师'], [1010, date, 'Date of Issue · 颁发日期']].forEach(function (col) {
      ctx.fillStyle = NAVY;
      ctx.font = 'italic 46px ' + SERIF_ZH;
      ctx.fillText(col[1], col[0], 1370);
      ctx.strokeStyle = '#8B93A6'; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.moveTo(col[0] - 210, 1395); ctx.lineTo(col[0] + 210, 1395); ctx.stroke();
      ctx.fillStyle = '#56607A';
      ctx.font = '28px ' + SERIF_EN;
      ctx.fillText(col[2], col[0], 1440);
    });
    ctx.fillStyle = '#8B93A6';
    ctx.font = '26px ' + SERIF_EN;
    ctx.fillText('Certificate No. ' + (award.serial || '') + '  ·  ' + m.en + ' · ' + m.zh, W / 2 - 230, H - pad - 90);
  }

  function filename(award, type) {
    return 'Lexica-' + (award.name || '') + '-' + gameName(award.game, 'zh') + '-' + award.days + '天-' + award.end_day + '.' + (type === 'jpeg' ? 'jpg' : 'png');
  }

  function render(award) {
    var canvas = document.createElement('canvas');
    var ready = (document.fonts && document.fonts.ready) ? document.fonts.ready : Promise.resolve();
    return ready.then(function () { draw(canvas, award); return canvas; });
  }

  function save(award, type) {
    type = type === 'jpeg' ? 'jpeg' : 'png';
    return render(award).then(function (canvas) {
      return new Promise(function (resolve, reject) {
        function download(href, revoke) {
          var a = document.createElement('a');
          a.href = href;
          a.download = filename(award, type);
          document.body.appendChild(a);
          a.click();
          a.remove();
          if (revoke) setTimeout(function () { URL.revokeObjectURL(href); }, 60000);
          resolve();
        }
        try {
          /* toBlob 在内存不够等情况下会给 null：退回到 dataURL（大一些，但能下载） */
          canvas.toBlob(function (blob) {
            try {
              if (blob) download(URL.createObjectURL(blob), true);
              else download(canvas.toDataURL('image/' + type, 0.93), false);
            } catch (e) { reject(e); }
          }, 'image/' + type, 0.93);
        } catch (e) { reject(e); }
      });
    }).catch(function (e) {
      if (global.API && global.API.toast) global.API.toast(t('me_saveFailed'), 5000);
      throw e;
    });
  }

  /* ---------------- 列表、徽章墙、查看窗口（「我的」和「成绩记录」共用） ---------------- */

  function t(key, params) { return global.WPI18N ? global.WPI18N.t(key, params) : key; }
  function tierName(tier) { return t('me_tier_' + tier); }
  function title(a) { return t('me_certTitle', { tier: tierName(a.tier), game: gameName(a.game, lang()), n: a.days }); }

  function wall(awards) {
    if (!awards.length) return '<div class="empty">' + esc(t('me_noBadges')) + '</div>';
    var seen = {}, list = [];
    awards.forEach(function (a) {
      var k = a.game + '|' + a.days;
      if (!seen[k]) { seen[k] = { award: a, n: 0 }; list.push(seen[k]); }
      seen[k].n++;
    });
    list.sort(function (x, y) { return y.award.days - x.award.days; });
    return list.map(function (x) {
      return '<div class="aw-cell">' + badge(x.award, 88) + '<b>' + esc(tierName(x.award.tier)) + (x.n > 1 ? ' ×' + x.n : '') + '</b>' +
        '<small>' + esc(gameName(x.award.game, lang()) + ' · ' + t('me_daysTop', { n: x.award.days })) + '</small></div>';
    }).join('');
  }

  /* 奖状列表：opts.who = 每行前面写上学生姓名、班级（老师看）；opts.empty = 没有奖状时的提示词条 */
  function rows(awards, opts) {
    opts = opts || {};
    if (!awards.length) return '<div class="empty">' + esc(t(opts.empty || 'me_noCerts')) + '</div>';
    return awards.map(function (a, i) {
      var who = opts.who ? '<span class="aw-who">' + esc(a.name) + (a.class_name ? ' · ' + esc(a.class_name) : '') + '</span>' : '';
      return '<div class="item aw-row' + (a.seen === false && !opts.who ? ' is-new' : '') + '"><div class="aw-row-badge">' + badge(a, 46) + '</div>' +
        '<div class="main">' + who + '<b>' + esc(title(a)) + '</b>' +
        (a.seen === false && !opts.who ? ' <span class="pill good">' + esc(t('me_new')) + '</span>' : '') +
        '<small>' + esc((a.board_label ? a.board_label + ' · ' : '') + a.start_day + ' — ' + a.end_day + (a.serial ? ' · ' + a.serial : '')) + '</small></div>' +
        '<div class="ops"><button type="button" class="btn sm" data-aw-view="' + i + '">' + esc(t('me_view')) + '</button>' +
        '<button type="button" class="btn sm ghost" data-aw-save="' + i + '" data-type="png">PNG</button>' +
        '<button type="button" class="btn sm ghost" data-aw-save="' + i + '" data-type="jpeg">JPG</button></div></div>';
    }).join('');
  }

  /* 列表里的「查看 / PNG / JPG」：getAwards() 返回这个列表当前对应的奖状数组 */
  function bind(box, getAwards) {
    box.addEventListener('click', function (ev) {
      var b = ev.target.closest('button');
      if (!b) return;
      var list = getAwards();
      if (b.hasAttribute('data-aw-view')) view(list[+b.getAttribute('data-aw-view')]);
      if (b.hasAttribute('data-aw-save')) {
        b.disabled = true;
        var again = function () { b.disabled = false; };
        save(list[+b.getAttribute('data-aw-save')], b.getAttribute('data-type')).then(again, again);
      }
    });
  }

  var modal = null, viewSeq = 0;
  function view(a) {
    if (!a) return;
    if (!modal) {
      modal = document.createElement('div');
      modal.className = 'aw-modal';
      modal.setAttribute('role', 'dialog');
      modal.setAttribute('aria-modal', 'true');
      modal.innerHTML = '<div class="aw-modal-box"><img alt=""><p class="hint"></p><div class="actions">' +
        '<button type="button" class="btn" data-k="png"></button><button type="button" class="btn ghost" data-k="jpeg"></button>' +
        '<button type="button" class="btn ghost" data-k="close"></button></div></div>';
      document.body.appendChild(modal);
      modal.addEventListener('click', function (ev) {
        if (ev.target === modal || (ev.target.getAttribute && ev.target.getAttribute('data-k') === 'close')) modal.hidden = true;
      });
    }
    var img = modal.querySelector('img'), msg = modal.querySelector('.hint');
    modal.querySelector('[data-k="png"]').textContent = t('me_dlPng');
    modal.querySelector('[data-k="jpeg"]').textContent = t('me_dlJpg');
    modal.querySelector('[data-k="close"]').textContent = t('me_close');
    modal.querySelector('[data-k="png"]').onclick = function () { save(a, 'png').catch(function () { }); };
    modal.querySelector('[data-k="jpeg"]').onclick = function () { save(a, 'jpeg').catch(function () { }); };
    modal.hidden = false;
    img.removeAttribute('src');
    msg.textContent = t('me_drawing');
    var seq = ++viewSeq;                       /* 连着点两张奖状：只显示最后点的那一张（先点的可能后画完） */
    render(a).then(function (canvas) {
      if (seq !== viewSeq) return;
      img.src = canvas.toDataURL('image/png');
      img.alt = title(a);
      msg.textContent = t('me_longPress');
    }).catch(function () { if (seq === viewSeq) msg.textContent = t('me_saveFailed'); });
  }

  /* 样张：示例学生的金、银、铜三张（老师预览用，也能下载） */
  function samples(teacher) {
    var today = new Date(), out = [];
    function day(offset) {
      var d = new Date(today.getFullYear(), today.getMonth(), today.getDate() - offset);
      return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2);
    }
    [[30, 'gold', 'all'], [15, 'silver', 'spell'], [10, 'bronze', 'order']].forEach(function (x, i) {
      out.push({ id: 0, days: x[0], tier: x[1], game: x[2], board: 'sample', board_label: t('me_sampleClass'),
                 name: t('me_sampleName'), class_name: t('me_sampleClass'), teacher: teacher || '', start_day: day(x[0]), end_day: day(1),
                 created_at: Math.floor(Date.now() / 1000), serial: 'LX-SAMPLE-' + (i + 1), seen: true });
    });
    return out;
  }

  global.WPAwards = { badge: badge, mini: mini, label: label, wall: wall, rows: rows, bind: bind, view: view, samples: samples, title: title, draw: draw, render: render, save: save, gameName: gameName, METAL: METAL, filename: filename };
})(window);
