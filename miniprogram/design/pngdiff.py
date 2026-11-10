#!/usr/bin/env python3
"""比较两张 PNG：逐像素差异 + 墨迹包围盒（纯标准库解码 PNG）。"""
import struct
import sys
import zlib


def read_png(path):
    with open(path, 'rb') as f:
        d = f.read()
    assert d[:8] == b'\x89PNG\r\n\x1a\n', '不是 PNG'
    p = 8
    w = h = depth = ctype = None
    idat = b''
    plte = None
    while p < len(d):
        ln = struct.unpack('>I', d[p:p + 4])[0]
        tag = d[p + 4:p + 8]
        body = d[p + 8:p + 8 + ln]
        if tag == b'IHDR':
            w, h, depth, ctype = struct.unpack('>IIBB', body[:10])
            interlace = body[12]
            assert interlace == 0, '不支持隔行扫描'
        elif tag == b'IDAT':
            idat += body
        elif tag == b'PLTE':
            plte = body
        elif tag == b'IEND':
            break
        p += 12 + ln
    assert depth == 8, '只支持 8 位色深，当前 %s' % depth
    nch = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
    raw = zlib.decompress(idat)
    stride = w * nch
    out = bytearray(w * h * nch)
    prev = bytearray(stride)
    pos = 0
    for y in range(h):
        ft = raw[pos]
        pos += 1
        line = bytearray(raw[pos:pos + stride])
        pos += stride
        if ft == 1:
            for i in range(nch, stride):
                line[i] = (line[i] + line[i - nch]) & 0xFF
        elif ft == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif ft == 3:
            for i in range(stride):
                a = line[i - nch] if i >= nch else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif ft == 4:
            for i in range(stride):
                a = line[i - nch] if i >= nch else 0
                b = prev[i]
                c = prev[i - nch] if i >= nch else 0
                pp = a + b - c
                pa, pb, pc = abs(pp - a), abs(pp - b), abs(pp - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        out[y * stride:(y + 1) * stride] = line
        prev = line
    # 统一成 RGB
    rgb = bytearray(w * h * 3)
    if ctype == 2:
        rgb[:] = out
    elif ctype == 6:
        for i in range(w * h):
            rgb[i * 3:i * 3 + 3] = out[i * 4:i * 4 + 3]
    elif ctype == 3:
        for i in range(w * h):
            idx = out[i]
            rgb[i * 3:i * 3 + 3] = plte[idx * 3:idx * 3 + 3]
    else:
        raise SystemExit('暂不支持色彩类型 %s' % ctype)
    return w, h, rgb


def ink_bbox(w, h, rgb, lum_thresh=150):
    x0, y0, x1, y1 = w, h, -1, -1
    for y in range(h):
        row = y * w * 3
        for x in range(w):
            i = row + x * 3
            lum = (rgb[i] * 299 + rgb[i + 1] * 587 + rgb[i + 2] * 114) // 1000
            if lum >= lum_thresh:
                if x < x0: x0 = x
                if x > x1: x1 = x
                if y < y0: y0 = y
                if y > y1: y1 = y
    return x0, y0, x1, y1


def main():
    a, b = sys.argv[1], sys.argv[2]
    w1, h1, p1 = read_png(a)
    w2, h2, p2 = read_png(b)
    if (w1, h1) != (w2, h2):
        print('尺寸不同：%dx%d vs %dx%d' % (w1, h1, w2, h2))
        return
    n = w1 * h1 * 3
    total = 0
    mx = 0
    over = 0
    for i in range(0, n, 3):
        d0 = abs(p1[i] - p2[i])
        d1 = abs(p1[i + 1] - p2[i + 1])
        d2 = abs(p1[i + 2] - p2[i + 2])
        m = d0 if d0 > d1 else d1
        if d2 > m: m = d2
        total += m
        if m > mx: mx = m
        if m > 40: over += 1
    print('图像 %dx%d' % (w1, h1))
    print('  平均通道差 %.3f / 255' % (total / (n / 3)))
    print('  最大通道差 %d / 255' % mx)
    print('  明显不同(>40)的像素 %d 个 (%.3f%%)' % (over, 100.0 * over / (w1 * h1)))
    bb1 = ink_bbox(w1, h1, p1)
    bb2 = ink_bbox(w2, h2, p2)
    print('  墨迹包围盒 A = %s  宽%d 高%d' % (bb1, bb1[2] - bb1[0] + 1, bb1[3] - bb1[1] + 1))
    print('  墨迹包围盒 B = %s  宽%d 高%d' % (bb2, bb2[2] - bb2[0] + 1, bb2[3] - bb2[1] + 1))
    print('  包围盒偏移 = %s' % (tuple(bb2[i] - bb1[i] for i in range(4)),))


if __name__ == '__main__':
    main()
