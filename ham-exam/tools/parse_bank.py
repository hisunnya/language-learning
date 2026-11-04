#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""解析 CRAC 题库 PDF -> 结构化 JSON
处理要点：
  - 精确剥离页脚页码（每页恰好一个独立数字行）
  - 兼容源 PDF 畸形标记（偶见 "A]xxx" 缺左方括号）
  - 字段跨行拼接
"""
import json
import re
import subprocess
from collections import Counter

BANK = "/workspace/work/bank"
MARK = re.compile(r"^\[([A-Z])\](.*)$")
BADMARK = re.compile(r"^([A-D])\](.*)$")   # 源 PDF 缺 '[' 的畸形标记


def raw_pages(path):
    out = subprocess.run(["pdftotext", path, "-"], capture_output=True, text=True).stdout
    for i, pg in enumerate(out.split("\f"), 1):
        yield "\n".join(l for l in pg.split("\n") if l.strip() != str(i))


def parse_file(path):
    questions, cur, field, buf = [], None, None, []

    def flush():
        if cur is not None and field:
            cur[field] = "\n".join(buf).strip()

    for page in raw_pages(path):
        for line in page.split("\n"):
            line = line.rstrip()
            m = MARK.match(line)
            if not m:
                # 畸形标记：仅当当前字段是答案且内容已是合法答案时才认定为新选项
                bm = BADMARK.match(line)
                pending = "\n".join(buf).strip() if buf else ""
                if bm and field == "t" and re.fullmatch(r"[A-D]+", pending):
                    flush()
                    field, buf = bm.group(1).lower(), [bm.group(2).strip()]
                    continue
                if cur is not None and field:
                    buf.append(line)
                continue
            flush()
            tag, rest = m.group(1), m.group(2).strip()
            if tag == "J":
                if cur:
                    questions.append(cur)
                cur = {k: "" for k in "jpqtabcdf"}
                field, buf = "j", ([rest] if rest else [])
            else:
                if cur is None:
                    continue
                field, buf = tag.lower(), ([rest] if rest else [])
    flush()
    if cur:
        questions.append(cur)

    out = []
    for q in questions:
        ans = re.sub(r"[^A-D]", "", q["t"].upper())
        if not q["q"] or not ans or not all(q[k] for k in "abcd"):
            continue
        out.append({
            "j": q["j"], "p": q["p"], "i": q["i"], "q": q["q"], "t": ans,
            "type": "single" if len(ans) == 1 else "multi",
            "opts": [q["a"], q["b"], q["c"], q["d"]], "f": q["f"],
        })
    return out


def main():
    srcs = {"all": f"{BANK}/总题库.pdf", "A": f"{BANK}/A类题库.pdf",
            "B": f"{BANK}/B类题库.pdf", "C": f"{BANK}/C类题库.pdf"}
    banks = {}
    for k, v in srcs.items():
        qs = parse_file(v)
        banks[k] = qs
        s = sum(1 for q in qs if q["type"] == "single")
        print(f"{k:4s} 题目 {len(qs):5d} | 单选 {s:5d} 多选 {len(qs)-s:4d} | 带图 {sum(1 for q in qs if q['f']):3d}")

    merged = {}
    for cls, qs in banks.items():
        for q in qs:
            key = q["i"] or ("J:" + q["j"])
            if key in merged:
                m = merged[key]
                m["cls"] = sorted(set(m["cls"] + [cls]))
                for f in ("q", "t", "p", "f", "j"):
                    if not m[f] and q[f]:
                        m[f] = q[f]
                if not all(m["opts"]):
                    m["opts"] = q["opts"]
            else:
                m = dict(q); m["cls"] = [cls]; merged[key] = m

    print(f"\n合并去重后: {len(merged)} 题")
    for c in ("A", "B", "C"):
        n = sum(1 for v in merged.values() if c in v["cls"])
        print(f"  {c} 类归属: {n}")

    A = [v for v in merged.values() if "A" in v["cls"]]
    Am = [v for v in A if len(v["t"]) > 1]
    print(f"\nA类 {len(A)} 题, 其中多选 {len(Am)} (官方口径 134)")
    print("A类多选答案长度分布:", dict(sorted(Counter(len(v['t']) for v in Am).items())))

    json.dump(merged, open("/workspace/work/merged_raw.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\n→ merged_raw.json")


if __name__ == "__main__":
    main()
