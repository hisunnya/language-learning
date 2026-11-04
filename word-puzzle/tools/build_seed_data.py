#!/usr/bin/env python3
"""把 data/raw/ 下的原始词表整理成 data/pep_curriculum.json（内置题库种子）。

原始数据来源
------------
* 初中：``henry1786580051-lang/english-test`` 的 ``src/data/grade{7a,7b,8a,8b,9}.json``
  （整理自人教版 PEP 初中英语课本，词条含 unit / english / chinese / partOfSpeech）
* 高中：``lfcypo/pep-senior-eng-vocab-json`` 的 ``vocabulary.json``
  （人教版普通高中英语新教材七册词表，词条含 book / unit / english / meanings）

两者都已随仓库放进 ``data/raw/``，本脚本只做整理，不联网。

可选：音标
----------
脚本会尝试从 ECDICT（``skywind3000/ECDICT``）补齐音标。ECDICT 体积大、不随仓库分发，
缺失时静默跳过，音标字段留空即可（游戏里不显示音标也能玩）。

用法::

    python3 tools/build_seed_data.py                # 生成 data/pep_curriculum.json
    python3 tools/build_seed_data.py --ecdict PATH  # 指定本地 ecdict.csv 补音标
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "pep_curriculum.json"

# ---------------------------------------------------------------- 初中

# 人教版 PEP 初中英语共 5 册。来源数据里九年级是「全一册」，
# 这里按 Unit 1–7 / Unit 8–14 拆成上下册（该划分写进 JSON 的 split_note 字段，
# 需要改成别的划分只改这个常量即可）。
JUNIOR_BOOKS = [
    ("7a", "七年级", "上册", "七年级上册"),
    ("7b", "七年级", "下册", "七年级下册"),
    ("8a", "八年级", "上册", "八年级上册"),
    ("8b", "八年级", "下册", "八年级下册"),
]

GRADE9_SPLIT = (7, 7)  # 上册 Unit 1–7，下册 Unit 8–14

# ---------------------------------------------------------------- 高中

# 人教版普通高中英语新教材七册 → 年级 / 学期
SENIOR_BOOKS = [
    ("必修第一册", "高一", "上册"),
    ("必修第二册", "高一", "下册"),
    ("必修第三册", "高二", "上册"),
    ("选必修第一册", "高二", "下册"),
    ("选必修第二册", "高三", "上册"),
    ("选必修第三册", "高三", "下册"),
    ("选必修第四册", "高三", "下册"),
]


def slug(text: str) -> str:
    out = []
    for ch in text.strip().lower():
        if ch.isalnum() and ch.isascii():
            out.append(ch)
        elif ch in " -_":
            out.append("-")
    s = "".join(out)
    while "--" in s:
        s = s.replace("--", "-")
    return s.strip("-")


def unit_sort_key(name: str):
    """Unit 10 要排在 Unit 2 后面；非 Unit 开头的（Welcome Unit 等）排在最前。"""
    digits = ""
    for ch in name:
        if ch.isdigit():
            digits += ch
        elif digits:
            break
    if not digits:
        return (0, 0, name)
    return (1, int(digits), name)


def clean_cn(text: str) -> str:
    return " ".join(str(text).split()).strip()


def norm_junior() -> list[dict]:
    volumes = []
    for key, grade, term, display in JUNIOR_BOOKS:
        path = RAW / f"pep_junior_{key}.json"
        if not path.exists():
            sys.stderr.write(f"!! 缺少 {path}\n")
            continue
        raw = json.loads(path.read_text(encoding="utf-8"))
        units = []
        for unit in raw.get("units", []):
            words = []
            for w in unit.get("words", []):
                en = str(w.get("english", "")).strip()
                cn = clean_cn(w.get("chinese", ""))
                if not en or not cn:
                    continue
                words.append({
                    "en": en,
                    "cn": cn,
                    "pos": (w.get("partOfSpeech") or "").strip(),
                    "ipa": "",
                })
            if words:
                units.append({
                    "name": unit.get("unit", "").strip() or "Unit",
                    "words": words,
                })
        units.sort(key=lambda u: unit_sort_key(u["name"]))
        volumes.append({
            "key": f"junior-{key}",
            "name": display,
            "stage": "初中",
            "grade": grade,
            "grade_key": slug(grade),
            "term": term,
            "book": display,
            "split_note": "",
            "units": units,
        })

    # 九年级全一册 → 上册 / 下册
    path = RAW / "pep_junior_9.json"
    if path.exists():
        raw = json.loads(path.read_text(encoding="utf-8"))
        all_units = []
        for unit in raw.get("units", []):
            words = []
            for w in unit.get("words", []):
                en = str(w.get("english", "")).strip()
                cn = clean_cn(w.get("chinese", ""))
                if not en or not cn:
                    continue
                words.append({
                    "en": en,
                    "cn": cn,
                    "pos": (w.get("partOfSpeech") or "").strip(),
                    "ipa": "",
                })
            if words:
                all_units.append({
                    "name": unit.get("unit", "").strip() or "Unit",
                    "words": words,
                })
        all_units.sort(key=lambda u: unit_sort_key(u["name"]))
        n_up = GRADE9_SPLIT[0]
        note = ("来源教材为「人教版九年级全一册」，本仓库按 Unit 1–{} / Unit {}–{} "
                "拆为上、下两册。".format(n_up, n_up + 1, len(all_units)))
        for term, units in (("上册", all_units[:n_up]), ("下册", all_units[n_up:])):
            volumes.append({
                "key": f"junior-9{term[0]}",
                "name": f"九年级{term}",
                "stage": "初中",
                "grade": "九年级",
                "grade_key": "j9",
                "term": term,
                "book": "九年级全一册",
                "split_note": note,
                "units": units,
            })
    return volumes


def norm_senior() -> list[dict]:
    path = RAW / "pep_senior.json"
    if not path.exists():
        sys.stderr.write(f"!! 缺少 {path}\n")
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    buckets: dict[tuple[str, str], dict] = {}
    for item in raw:
        book = str(item.get("book", "")).strip()
        unit = str(item.get("unit", "")).strip() or "Unit"
        en = str(item.get("english", "")).strip()
        meanings = item.get("meanings") or []
        cn = "；".join(clean_cn(m.get("chinese", "")) for m in meanings
                       if clean_cn(m.get("chinese", "")))
        pos = " ".join(sorted({str(m.get("pos", "")).strip()
                               for m in meanings if m.get("pos")}))
        if not en or not cn:
            continue
        for book_name, grade, term in SENIOR_BOOKS:
            if book_name == book:
                break
        else:
            sys.stderr.write(f"!! 未映射的册次: {book}\n")
            continue
        bucket = buckets.setdefault((book_name, grade, term), {
            "units": {},
            "order": [],
        })
        if unit not in bucket["units"]:
            bucket["units"][unit] = []
            bucket["order"].append(unit)
        bucket["units"][unit].append({
            "en": en,
            "cn": cn,
            "pos": pos,
            "ipa": "",
        })

    volumes = []
    for book_name, grade, term in SENIOR_BOOKS:
        bucket = buckets.get((book_name, grade, term))
        if not bucket:
            continue
        units = [{"name": u, "words": bucket["units"][u]} for u in bucket["order"]]
        units.sort(key=lambda u: unit_sort_key(u["name"]))
        volumes.append({
            "key": f"senior-{slug(book_name)}",
            "name": book_name,
            "stage": "高中",
            "grade": grade,
            "grade_key": slug(grade),
            "term": term,
            "book": book_name,
            "split_note": "",
            "units": units,
        })
    return volumes


# ---------------------------------------------------------------- 音标

def load_ipa(path: Path) -> dict:
    """从 ECDICT csv 抽取音标，形如 /ˈtrɪʌmf/ 。"""
    ipa: dict = {}
    if not path.exists():
        return ipa
    with path.open(encoding="utf-8", errors="replace", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            word = (row.get("word") or "").strip().lower()
            ph = (row.get("phonetic") or "").strip()
            if not word or not ph:
                continue
            if not ph.startswith("/"):
                ph = "/" + ph + "/"
            ipa[word] = ph
    return ipa


def apply_ipa(volumes: list[dict], ipa: dict) -> int:
    hit = 0
    total = 0
    for vol in volumes:
        for unit in vol["units"]:
            for w in unit["words"]:
                total += 1
                ph = ipa.get(w["en"].lower())
                if ph:
                    w["ipa"] = ph
                    hit += 1
    return hit, total


# ---------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ecdict", default="", help="本地 ecdict.csv 路径（可选）")
    args = ap.parse_args()

    volumes = norm_junior() + norm_senior()
    if not volumes:
        sys.stderr.write("没有解析到任何词表\n")
        return 1

    ipa = {}
    if args.ecdict:
        ipa = load_ipa(Path(args.ecdict))
    else:
        cached = ROOT / "data" / "raw" / "ecdict.csv"
        if cached.exists():
            ipa = load_ipa(cached)
    hit, total = apply_ipa(volumes, ipa)

    doc = {
        "meta": {
            "title": "人教版 PEP 英语词汇（初中 + 高中）",
            "generated": "2026-11-04",
            "word_total": sum(len(u["words"]) for v in volumes for u in v["units"]),
            "unit_total": sum(len(v["units"]) for v in volumes),
            "ipa_coverage": f"{hit}/{total}",
            "sources": [
                {
                    "name": "人教版 PEP 初中英语课本词汇",
                    "repo": "henry1786580051-lang/english-test",
                    "path": "src/data/grade{7a,7b,8a,8b,9}.json",
                    "license": "见原仓库",
                    "note": "整理自人教版课本，参考 TapXWorld/ChinaTextbook 的教材数据",
                },
                {
                    "name": "人教版普通高中英语新教材词汇总表（七册）",
                    "repo": "lfcypo/pep-senior-eng-vocab-json",
                    "path": "vocabulary.json",
                    "license": "见原仓库",
                    "note": "必修一~三、选择性必修一~四",
                },
                {
                    "name": "ECDICT（音标补充，可选）",
                    "repo": "skywind3000/ECDICT",
                    "path": "ecdict.csv",
                    "license": "MIT / 见原仓库",
                    "note": "仅用于补音标",
                },
            ],
            "copyright": "课本原始内容版权归人民教育出版社所有；本仓库仅用于个人学习。",
        },
        "volumes": volumes,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")),
                   encoding="utf-8")

    print(f"已写出 {OUT}")
    print(f"  册数 {len(volumes)}  单元 {doc['meta']['unit_total']}  "
          f"词条 {doc['meta']['word_total']}  音标覆盖 {doc['meta']['ipa_coverage']}")
    for v in volumes:
        n = sum(len(u["words"]) for u in v["units"])
        print(f"    {v['stage']:>4} {v['grade']} {v['term']:>3} {v['name']:<12} "
              f"{len(v['units']):>2} 单元 {n:>4} 词")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
