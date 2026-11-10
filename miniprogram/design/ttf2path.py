#!/usr/bin/env python3
"""从 TrueType 字体提取字形轮廓，输出 SVG path 数据（纯标准库，无第三方依赖）。

用法：
    python3 ttf2path.py <字体路径> <字符> [<字符> ...]      # 打印路径
    python3 ttf2path.py --js <字体路径> <输出.js> <字符>...  # 生成 JS 模块

坐标保持字体原始单位（未缩放、未翻转），交给调用方用 transform 处理。
TrueType 用二次贝塞尔曲线（Q），SVG 原生支持，无损。
"""
import struct
import sys


class Font:
    def __init__(self, path):
        with open(path, 'rb') as f:
            self.d = f.read()
        base = 0
        if self.d[:4] == b'ttcf':
            base = struct.unpack('>I', self.d[12:16])[0]
        self.base = base
        self.tables = self._tables(base)
        head = self.tables['head'][0]
        self.units_per_em = struct.unpack('>H', self.d[head + 18:head + 20])[0]
        self.index_to_loc = struct.unpack('>h', self.d[head + 50:head + 52])[0]
        maxp = self.tables['maxp'][0]
        self.num_glyphs = struct.unpack('>H', self.d[maxp + 4:maxp + 6])[0]
        self._cmap = self._parse_cmap()

    def _tables(self, base):
        n = struct.unpack('>H', self.d[base + 4:base + 6])[0]
        t = {}
        for i in range(n):
            off = base + 12 + 16 * i
            tag = self.d[off:off + 4].decode('latin1')
            o, l = struct.unpack('>II', self.d[off + 8:off + 16])
            t[tag] = (o, l)
        return t

    def _parse_cmap(self):
        """只取 Unicode 子表（format 4 / 12），返回 char -> glyph id。"""
        o = self.tables['cmap'][0]
        n = struct.unpack('>H', self.d[o + 2:o + 4])[0]
        best = None
        for i in range(n):
            pid, eid, sub = struct.unpack('>HHI', self.d[o + 4 + 8 * i:o + 12 + 8 * i])
            if (pid, eid) in ((3, 1), (3, 10), (0, 3), (0, 4)):
                best = o + sub
        m = {}
        if best is None:
            return m
        fmt = struct.unpack('>H', self.d[best:best + 2])[0]
        if fmt == 4:
            seg_x2 = struct.unpack('>H', self.d[best + 6:best + 8])[0]
            seg = seg_x2 // 2
            end_o = best + 14
            start_o = end_o + seg_x2 + 2
            delta_o = start_o + seg_x2
            range_o = delta_o + seg_x2
            for k in range(seg):
                end = struct.unpack('>H', self.d[end_o + 2 * k:end_o + 2 * k + 2])[0]
                start = struct.unpack('>H', self.d[start_o + 2 * k:start_o + 2 * k + 2])[0]
                delta = struct.unpack('>h', self.d[delta_o + 2 * k:delta_o + 2 * k + 2])[0]
                ro = struct.unpack('>H', self.d[range_o + 2 * k:range_o + 2 * k + 2])[0]
                if start == 0xFFFF:
                    continue
                for c in range(start, end + 1):
                    if ro == 0:
                        g = (c + delta) & 0xFFFF
                    else:
                        gi = range_o + 2 * k + ro + 2 * (c - start)
                        if gi + 2 > len(self.d):
                            continue
                        g = struct.unpack('>H', self.d[gi:gi + 2])[0]
                        if g:
                            g = (g + delta) & 0xFFFF
                    if g:
                        m[c] = g
        elif fmt == 12:
            ng = struct.unpack('>I', self.d[best + 12:best + 16])[0]
            for k in range(ng):
                p = best + 16 + 12 * k
                s, e, g = struct.unpack('>III', self.d[p:p + 12])
                for c in range(s, e + 1):
                    m[c] = g + (c - s)
        return m

    def glyph_id(self, ch):
        return self._cmap.get(ord(ch))

    def _loca(self):
        o = self.tables['loca'][0]
        if self.index_to_loc == 0:
            return [struct.unpack('>H', self.d[o + 2 * i:o + 2 * i + 2])[0] * 2
                    for i in range(self.num_glyphs + 1)]
        return [struct.unpack('>I', self.d[o + 4 * i:o + 4 * i + 4])[0]
                for i in range(self.num_glyphs + 1)]

    def contours(self, gid, depth=0):
        """返回 [ [(x, y, on_curve), ...], ... ]，字体原始坐标（y 向上）。"""
        loca = self._loca()
        g0, g1 = loca[gid], loca[gid + 1]
        if g0 == g1:
            return []
        go = self.tables['glyf'][0] + g0
        nc = struct.unpack('>h', self.d[go:go + 2])[0]
        if nc >= 0:
            return self._simple(go, nc)
        if depth > 6:
            return []
        return self._composite(go, depth)

    def _simple(self, go, nc):
        ends = [struct.unpack('>H', self.d[go + 10 + 2 * i:go + 12 + 2 * i])[0] for i in range(nc)]
        p = go + 10 + 2 * nc
        ilen = struct.unpack('>H', self.d[p:p + 2])[0]
        p += 2 + ilen
        npts = ends[-1] + 1 if ends else 0
        flags = []
        while len(flags) < npts:
            f = self.d[p]
            p += 1
            flags.append(f)
            if f & 0x08:
                rep = self.d[p]
                p += 1
                flags.extend([f] * rep)
        flags = flags[:npts]
        xs = []
        v = 0
        for f in flags:
            if f & 0x02:
                dx = self.d[p]
                p += 1
                v += dx if f & 0x10 else -dx
            elif not f & 0x10:
                v += struct.unpack('>h', self.d[p:p + 2])[0]
                p += 2
            xs.append(v)
        ys = []
        v = 0
        for f in flags:
            if f & 0x04:
                dy = self.d[p]
                p += 1
                v += dy if f & 0x20 else -dy
            elif not f & 0x20:
                v += struct.unpack('>h', self.d[p:p + 2])[0]
                p += 2
            ys.append(v)
        out = []
        s = 0
        for e in ends:
            out.append([(xs[i], ys[i], bool(flags[i] & 0x01)) for i in range(s, e + 1)])
            s = e + 1
        return out

    def _composite(self, go, depth):
        p = go + 10
        out = []
        while True:
            flags, gidx = struct.unpack('>HH', self.d[p:p + 4])
            p += 4
            if flags & 0x0001:
                a1, a2 = struct.unpack('>hh', self.d[p:p + 4])
                p += 4
            else:
                a1, a2 = struct.unpack('>bb', self.d[p:p + 2])
                p += 2
            dx, dy = (a1, a2) if flags & 0x0002 else (0, 0)
            sx = sy = 1.0
            shx = shy = 0.0
            if flags & 0x0008:
                sx = sy = struct.unpack('>h', self.d[p:p + 2])[0] / 16384.0
                p += 2
            elif flags & 0x0040:
                sx = struct.unpack('>h', self.d[p:p + 2])[0] / 16384.0
                sy = struct.unpack('>h', self.d[p + 2:p + 4])[0] / 16384.0
                p += 4
            elif flags & 0x0080:
                sx = struct.unpack('>h', self.d[p:p + 2])[0] / 16384.0
                shy = struct.unpack('>h', self.d[p + 2:p + 4])[0] / 16384.0
                shx = struct.unpack('>h', self.d[p + 4:p + 6])[0] / 16384.0
                sy = struct.unpack('>h', self.d[p + 6:p + 8])[0] / 16384.0
                p += 8
            for c in self.contours(gidx, depth + 1):
                out.append([(x * sx + y * shx + dx, x * shy + y * sy + dy, on) for x, y, on in c])
            if not flags & 0x0020:
                break
        return out


def _mid(a, b):
    return ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)


def _n(v):
    if abs(v - round(v)) < 0.01:
        return str(int(round(v)))
    return ('%.2f' % v).rstrip('0').rstrip('.')


def contour_to_path(pts):
    n = len(pts)
    if n == 0:
        return ''
    if pts[0][2]:
        start, idx = pts[0], 1
    elif pts[-1][2]:
        start, idx = pts[-1], 0
    else:
        start, idx = _mid(pts[-1], pts[0]) + (True,), 0
    out = ['M%s %s' % (_n(start[0]), _n(start[1]))]
    prev_off = None
    i = idx
    cnt = 0
    while cnt < n:
        p = pts[i % n]
        cnt += 1
        if p[2]:
            if prev_off is None:
                out.append('L%s %s' % (_n(p[0]), _n(p[1])))
            else:
                out.append('Q%s %s %s %s' % (_n(prev_off[0]), _n(prev_off[1]), _n(p[0]), _n(p[1])))
                prev_off = None
        else:
            if prev_off is not None:
                m = _mid(prev_off, p)
                out.append('Q%s %s %s %s' % (_n(prev_off[0]), _n(prev_off[1]), _n(m[0]), _n(m[1])))
            prev_off = p
        i += 1
    if prev_off is not None:
        out.append('Q%s %s %s %s' % (_n(prev_off[0]), _n(prev_off[1]), _n(start[0]), _n(start[1])))
    out.append('Z')
    return ''.join(out)


def glyph_path(font, ch):
    gid = font.glyph_id(ch)
    if gid is None:
        raise SystemExit('字体里没有「%s」这个字' % ch)
    cs = font.contours(gid)
    d = ''.join(contour_to_path(c) for c in cs)
    xs = [p[0] for c in cs for p in c if p[2]]
    ys = [p[1] for c in cs for p in c if p[2]]
    bbox = (min(xs), min(ys), max(xs), max(ys)) if xs else (0, 0, 0, 0)
    return d, bbox, len(cs)


def main(argv):
    if len(argv) >= 4 and argv[1] == '--js':
        path, out, chars = argv[2], argv[3], argv[4:]
        f = Font(path)
        lines = ['/* 由 ttf2path.py 从 %s 提取，勿手改。' % path.split('/')[-1],
                 '   坐标是字体原始单位（y 向上），使用时 transform="scale(s,-s)"。 */',
                 'module.exports = {',
                 '  unitsPerEm: %d,' % f.units_per_em,
                 '  glyphs: {']
        for i, ch in enumerate(chars):
            d, bbox, ncont = glyph_path(f, ch)
            lines.append('    \'%s\': {' % ch)
            lines.append('      ncontours: %d,' % ncont)
            lines.append('      bbox: [%s],' % ', '.join(str(v) for v in bbox))
            lines.append('      d: \'%s\'' % d)
            lines.append('    }' + (',' if i < len(chars) - 1 else ''))
        lines += ['  }', '};', '']
        with open(out, 'w') as fh:
            fh.write('\n'.join(lines))
        print('已写入 %s（unitsPerEm=%d，%d 个字形）' % (out, f.units_per_em, len(chars)))
        return
    path, chars = argv[1], argv[2:]
    f = Font(path)
    print('unitsPerEm = %d' % f.units_per_em)
    for ch in chars:
        d, bbox, n = glyph_path(f, ch)
        print('「%s」 contours=%d bbox=%s len(d)=%d' % (ch, n, bbox, len(d)))
        print(d)


if __name__ == '__main__':
    main(sys.argv)
