"""题库生成：把「层级选择 + 上传资料」变成一份可玩的题库。

层级选择
--------
前端传 ``level1..level4``（选项 key）和 ``custom.level1..level4``（自定义名称）。
自定义名称非空时覆盖该级的显示名，但**取词仍然按 key 走**——自定义只是换个叫法。

单元范围
--------
``unit_mode``：

* ``all``      全部单元：所有选中的单元都进来，游戏按单元逐关推进
* ``per-unit`` 分单元：同样的词，但首页多一个「挑单元开始」的入口
* ``range``    第 N 至第 M 单元：只保留该区间（按选中后的单元序号，1 起）

一关放不下
----------
有些单元词很多（三十几个），一关全放进去卡片会挤成一团。
所以词条按 :data:`MAX_PAIRS_PER_LEVEL` 切块：``Unit 1`` 会变成
``Unit 1（1/3）``、``Unit 1（2/3）``、``Unit 1（3/3）``，
每关最多 8 个词。词少的单元保持原样。
"""
from __future__ import annotations

import hashlib
import re
from typing import Any

from . import hierarchy
from .db import Database
from .hierarchy import CURRICULUM_OBJ

UNIT_MODE_LABELS = dict(hierarchy.UNIT_MODES)

# 一关最多多少对词。单元词多时按这个上限切块。
MAX_PAIRS_PER_LEVEL = 8


class BankError(Exception):
    """生成题库失败，message 直接展示给用户。"""


def _safe_name(text: str, fallback: str = "") -> str:
    """把层级名清理成可以用作文件名的片段。"""
    s = re.sub(r"[/\\:*?\"<>|\r\n\t]+", " ", str(text or "")).strip()
    s = re.sub(r"\s+", " ", s)
    return s or fallback


def resolve_levels(payload: dict) -> dict[str, str]:
    """把选项 key 和自定义名合并成最终的四个显示名。"""
    custom = payload.get("custom") or {}
    names = {}
    for i, key in enumerate(("level1", "level2", "level3", "level4"), start=1):
        base = str(payload.get(key) or "").strip()
        over = str(custom.get(key) or "").strip()
        if key == "level3" and base in hierarchy.TERM_LABELS:
            base = hierarchy.TERM_LABELS[base]
        names[key] = over or base or f"第{i}级"
    # 第四级传上来的是单元模式 key，翻译成中文显示名
    if names["level4"] in UNIT_MODE_LABELS:
        mode = str(payload.get("unit_mode") or "all")
        if mode == "range":
            lo = int(payload.get("unit_from") or 1)
            hi = int(payload.get("unit_to") or 0)
            names["level4"] = (f"第{lo}至第{hi}单元" if hi >= lo
                               else "第 N 至第 M 单元")
        else:
            names["level4"] = UNIT_MODE_LABELS.get(mode, names["level4"])
    return names


def _collect_units(payload: dict, db: Database) -> list[dict]:
    source = payload.get("source", "seed")
    if source == "material":
        mid = payload.get("material_id")
        if not mid:
            raise BankError("请先选择一份已上传的资料")
        material = db.get_material(int(mid))
        if not material:
            raise BankError("资料不存在，可能已被删除")
        rows = db.material_words(int(mid))
        buckets: dict[str, list[dict]] = {}
        for r in rows:
            buckets.setdefault(r["unit"], []).append({
                "en": r["en"], "cn": r["cn"], "ipa": r["ipa"], "pos": r["pos"],
            })
        return [{"name": u, "label": u, "volume": material["name"], "words": ws}
                for u, ws in buckets.items()]

    l1 = str(payload.get("level1") or "")
    l2 = str(payload.get("level2") or "")
    l3 = str(payload.get("level3") or hierarchy.DEFAULT_TERM)
    units = CURRICULUM_OBJ.select_units(l1, l2, l3)
    if not units:
        raise BankError(
            f"内置词库里没有「{l1} {l2} {l3}」的内容，"
            "可以改用上传的资料，或调整层级")
    return units


def apply_unit_mode(units: list[dict], mode: str,
                    unit_from: int = 0, unit_to: int = 0) -> list[dict]:
    if mode == "range":
        total = len(units)
        lo = max(1, int(unit_from or 1))
        hi = int(unit_to or total)
        hi = min(hi, total)
        if lo > hi:
            raise BankError("单元区间不合法")
        return units[lo - 1:hi]
    return units


def build_words(units: list[dict]) -> list[dict]:
    out = []
    for u in units:
        label = u.get("label") or u.get("name") or "Unit"
        for w in u["words"]:
            out.append({
                "unit": label,
                "en": w["en"],
                "cn": w["cn"],
                "ipa": w.get("ipa", ""),
                "pos": w.get("pos", ""),
            })
    return out


def chunk_groups(groups: list[dict],
                 max_pairs: int = MAX_PAIRS_PER_LEVEL) -> list[dict]:
    """把词量大的单元拆成多个小组（每组一关）。

    词数不超过 max_pairs 的单元原样保留；超过的按顺序切块，
    名字标成「单元名（i/n）」。词条顺序和数量都不变。

    切块是**均分**的：41 个词、每关最多 8 个，会切成 7/7/7/7/7/6，
    而不是 8/8/8/8/8/1 —— 不留只有一两个词的空关。
    """
    out: list[dict] = []
    for group in groups:
        words = list(group.get("words") or [])
        if not words:
            continue
        unit = str(group.get("unit") or "")
        if max_pairs <= 0 or len(words) <= max_pairs:
            out.append({"unit": unit, "words": words})
            continue
        total_words = len(words)
        parts_count = (total_words + max_pairs - 1) // max_pairs
        size, extra = divmod(total_words, parts_count)
        parts: list[list[dict]] = []
        index = 0
        for part in range(parts_count):
            length = size + (1 if part < extra else 0)
            parts.append(words[index:index + length])
            index += length
        for part_index, part in enumerate(parts, start=1):
            out.append({"unit": f"{unit}（{part_index}/{parts_count}）",
                        "words": part})
    return out


def create_bank(db: Database, payload: dict) -> dict:
    """生成并落库一个题库，返回题库元信息。"""
    names = resolve_levels(payload)
    mode = str(payload.get("unit_mode") or "all")
    if mode not in UNIT_MODE_LABELS:
        raise BankError("单元模式不合法")

    units = _collect_units(payload, db)
    units = apply_unit_mode(units, mode,
                            payload.get("unit_from", 0), payload.get("unit_to", 0))
    words = build_words(units)
    if not words:
        raise BankError("选中的范围内没有单词，换个范围试试")

    level4 = names["level4"]

    title = str(payload.get("title") or "").strip()
    if not title:
        title = "-".join([names["level1"], names["level2"], names["level3"], level4])

    meta = {
        "title": title,
        "level1": names["level1"],
        "level2": names["level2"],
        "level3": names["level3"],
        "level4": level4,
        "source": payload.get("source", "seed"),
        "material_id": payload.get("material_id"),
        "unit_mode": mode,
        "unit_from": int(payload.get("unit_from") or 0),
        "unit_to": int(payload.get("unit_to") or 0),
    }
    bid = db.insert_bank(meta, words)
    bank = db.get_bank(bid)
    bank["units"] = [
        {"index": i + 1, "name": u.get("label") or u.get("name"),
         "count": len(u["words"])}
        for i, u in enumerate(units)
    ]
    return bank


def bank_payload(db: Database, bid: int) -> dict:
    """给前端游戏用的完整题库数据（词条 + 分组）。"""
    bank = db.get_bank(bid)
    if not bank:
        raise BankError("题库不存在")
    words = db.bank_words(bid)
    groups: dict[str, list[dict]] = {}
    order: list[str] = []
    for w in words:
        if w["unit"] not in groups:
            groups[w["unit"]] = []
            order.append(w["unit"])
        groups[w["unit"]].append({
            "en": w["en"], "cn": w["cn"], "ipa": w.get("ipa", ""),
        })
    return {
        "bank": {k: bank[k] for k in
                 ("id", "title", "level1", "level2", "level3", "level4",
                  "source", "unit_mode", "unit_from", "unit_to",
                  "word_count", "unit_count", "created_at")},
        "groups": chunk_groups([{"unit": u, "words": groups[u]} for u in order]),
    }


def _fingerprint(words: list[dict]) -> str:
    """词条内容指纹：单元+英文+中文+音标。"""
    h = hashlib.sha1()
    for w in words:
        h.update(f"{w.get('unit','')}|{w['en']}|{w['cn']}|{w.get('ipa','')}\n"
                 .encode("utf-8"))
    return h.hexdigest()


def seed_default_bank(db: Database) -> int:
    """首次启动时生成默认题库：人教版初中九年级上册。

    如果内置词库更新过（比如补了音标），词条指纹会对不上，
    这时把旧的默认题库删掉重建，保证默认题库始终跟得上词库。
    """
    payload = dict(hierarchy.DEFAULT_SELECTION)
    payload.update({
        "source": "seed",
        "unit_mode": "all",
        "title": "人教版初中九年级上册",
    })

    expected = build_words(
        CURRICULUM_OBJ.select_units(
            hierarchy.DEFAULT_SELECTION["level1"],
            hierarchy.DEFAULT_SELECTION["level2"],
            hierarchy.DEFAULT_SELECTION["level3"],
        )
    )
    want = _fingerprint(expected)
    default_titles = {
        "人教版初中三年级上学期",
        "人教版初中九年级上册",
    }
    default_banks = []

    for b in db.list_banks():
        if b["source"] == "seed" and b["level3"] in hierarchy.TERM_LABELS:
            generated_title = "-".join((b["level1"], b["level2"], b["level3"], b["level4"]))
            if b["title"] == generated_title:
                normalized = "-".join((b["level1"], b["level2"],
                                        hierarchy.TERM_LABELS[b["level3"]], b["level4"]))
                if normalized != b["title"]:
                    db.execute("UPDATE banks SET title=? WHERE id=?",
                               (normalized, b["id"]))
        if (b["source"] == "seed"
                and b["title"] in default_titles
                and b["level1"] == hierarchy.DEFAULT_SELECTION["level1"]
                and b["level2"] == hierarchy.DEFAULT_SELECTION["level2"]
                and b["level3"] == hierarchy.DEFAULT_SELECTION["level3"]
                and b["unit_mode"] == "all"):
            if _fingerprint(db.bank_words(b["id"])) == want:
                default_banks.append(b)
                continue
            db.delete_bank(b["id"])          # 词库变了 → 重建

    if default_banks:
        primary = next((b for b in default_banks
                        if b["title"] == payload["title"]), default_banks[0])
        for b in default_banks:
            title = (payload["title"] if b["id"] == primary["id"]
                     else payload["title"] + "（历史副本）")
            if b["title"] != title:
                db.execute("UPDATE banks SET title=? WHERE id=?", (title, b["id"]))
        return primary["id"]

    bank = create_bank(db, payload)
    return bank["id"]
