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
"""
from __future__ import annotations

import hashlib
import re
from typing import Any

from . import hierarchy
from .db import Database
from .hierarchy import CURRICULUM_OBJ

UNIT_MODE_LABELS = dict(hierarchy.UNIT_MODES)


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
        "groups": [{"unit": u, "words": groups[u]} for u in order],
    }


def _fingerprint(words: list[dict]) -> str:
    """词条内容指纹：单元+英文+中文+音标。"""
    h = hashlib.sha1()
    for w in words:
        h.update(f"{w.get('unit','')}|{w['en']}|{w['cn']}|{w.get('ipa','')}\n"
                 .encode("utf-8"))
    return h.hexdigest()


def seed_default_bank(db: Database) -> int:
    """首次启动时生成默认题库：人教版初中三年级上学期。

    如果内置词库更新过（比如补了音标），词条指纹会对不上，
    这时把旧的默认题库删掉重建，保证默认题库始终跟得上词库。
    """
    payload = dict(hierarchy.DEFAULT_SELECTION)
    payload.update({
        "source": "seed",
        "unit_mode": "all",
        "title": "人教版初中三年级上学期",
    })

    expected = build_words(
        CURRICULUM_OBJ.select_units(
            hierarchy.DEFAULT_SELECTION["level1"],
            hierarchy.DEFAULT_SELECTION["level2"],
            hierarchy.DEFAULT_SELECTION["level3"],
        )
    )
    want = _fingerprint(expected)

    for b in db.list_banks():
        if (b["source"] == "seed"
                and b["title"] == "人教版初中三年级上学期"
                and b["level1"] == hierarchy.DEFAULT_SELECTION["level1"]
                and b["level2"] == hierarchy.DEFAULT_SELECTION["level2"]
                and b["level3"] == hierarchy.DEFAULT_SELECTION["level3"]
                and b["unit_mode"] == "all"):
            if _fingerprint(db.bank_words(b["id"])) == want:
                return b["id"]
            db.delete_bank(b["id"])          # 词库变了 → 重建

    bank = create_bank(db, payload)
    return bank["id"]
