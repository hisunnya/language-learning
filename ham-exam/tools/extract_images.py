#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从「总题库附图标记.pdf」提取附图并映射到题号。
关键：用 pdfplumber 取得版面位置与 XObject 名，用 pypdf 按名精确取原始字节，
避免 pdfimages 按对象ID输出导致的顺序错位。"""
import json
import os
import re

import pdfplumber
from pypdf import PdfReader

BANK = "/workspace/work/bank"
PDF = f"{BANK}/总题库附图标记.pdf"
OUT = "/workspace/work/images"
LAB_RE = re.compile(r"[A-Z]{2}\d{4}")

os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    os.remove(os.path.join(OUT, f))

reader = PdfReader(PDF)

bank = json.load(open("/workspace/work/merged_raw.json"))
expected = sorted({os.path.splitext(os.path.basename(q["f"]))[0] for q in bank.values() if q["f"]})
print("题库引用图片编号:", len(expected))

mapping = {}
with pdfplumber.open(PDF) as pdf:
    for pno, page in enumerate(pdf.pages, 1):
        imgs = sorted(page.images, key=lambda im: (round(im["top"]), im["x0"]))
        labels = [w for w in page.extract_words() if LAB_RE.fullmatch(w["text"])]

        # 按图像底边做容差聚类（同一行）
        rows = []
        for im in imgs:
            if rows and im["bottom"] - rows[-1][-1]["bottom"] <= 5:
                rows[-1].append(im)
            else:
                rows.append([im])
        rows = [sorted(r, key=lambda im: im["x0"]) for r in rows]

        used = set()
        for row in rows:
            btop = row[0]["bottom"]
            pool = sorted([w for w in labels
                           if abs(w["top"] - btop) < 45 and w["text"] not in used],
                          key=lambda w: w["x0"])
            if len(pool) == len(row):
                names = [w["text"] for w in pool]
            elif len(pool) < len(row):
                # 源 PDF 文字层缺标签 -> 用全局编号序列在带内插值
                pos = {e: i for i, e in enumerate(expected)}
                lo, hi = pos[pool[0]["text"]], pos[pool[-1]["text"]]
                names = expected[lo:hi + 1]
                assert len(names) == len(row), f"page{pno}: {names} vs {len(row)}"
                print(f"  page {pno} 插值补齐: {pool[0]['text']}..{pool[-1]['text']} -> {len(names)}")
            else:
                raise AssertionError(f"page {pno}: 标签数 {len(pool)} > 图数 {len(row)}")
            for im, name in zip(row, names):
                used.add(name)
                mapping[name] = (pno, im["name"])

missing = [e for e in expected if e not in mapping]
print("已配对", len(mapping), "| 待补", missing)
assert not missing

# 按 XObject 名精确落盘
for label, (pno, xname) in mapping.items():
    xo = reader.pages[pno - 1]["/Resources"]["/XObject"]
    obj = xo["/" + xname].get_object()
    data = obj.get_data()
    filt = obj.get("/Filter")
    ext = ".jpg" if str(filt) == "/DCTDecode" else ".png"
    with open(os.path.join(OUT, f"{label}{ext}"), "wb") as fp:
        fp.write(data)

final = {l: f"images/{l}.jpg" for l in mapping}
json.dump(final, open("/workspace/work/image_map.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(f"落盘 {len(final)} 张，全部映射完成")
