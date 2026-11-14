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
所以词条按 :data:`MAX_PAIRS_PER_LEVEL` 切块：37 个词的 ``Unit 1`` 会变成
四关，每关最多 12 个词。最后一关不足时，从前面出现过的词里补齐（复习），
补进来的词在本关里不会重复。
"""
from __future__ import annotations

import hashlib
import random
import re
from typing import Any

from . import hierarchy
from .db import Database
from .hierarchy import CURRICULUM_OBJ

UNIT_MODE_LABELS = dict(hierarchy.UNIT_MODES)

# 一关最多多少对词。单元词多时按这个上限切块。
MAX_PAIRS_PER_LEVEL = 12
# 允许的范围（太小一关只有几个词，太大牌面会挤）
MIN_PAIRS_PER_LEVEL = 4
MAX_PAIRS_PER_LEVEL_LIMIT = 40


def _to_int(value, default: int) -> int:
    """前端传来的单元号可能是任意输入，转不成整数就按「单元区间不合法」处理。"""
    if value in (None, ""):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        raise BankError("单元区间不合法") from None


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
            lo = _to_int(payload.get("unit_from"), 1)
            hi = _to_int(payload.get("unit_to"), 0)
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
        lo = max(1, _to_int(unit_from, 1))
        hi = _to_int(unit_to, total) or total
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


def _unique_take(candidates: list[dict], max_pairs: int) -> tuple[list[dict], list[dict]]:
    """从 candidates 里按顺序取出一关的词：英文、中文都不能重复，也不超过 max_pairs。

    取不进来的词原样返回，调用方把它们顺延到下一关，而不是丢掉。
    """
    kept: list[dict] = []
    rest: list[dict] = []
    seen_en: set[str] = set()
    seen_cn: set[str] = set()
    for word in candidates:
        en = word.get("en", "")
        cn = word.get("cn", "")
        full = max_pairs > 0 and len(kept) >= max_pairs
        if full or en in seen_en or cn in seen_cn:
            rest.append(word)
            continue
        seen_en.add(en)
        seen_cn.add(cn)
        kept.append(word)
    return kept, rest


def _resolve_duplicates(parts: list[dict], unit: str, max_pairs: int) -> list[dict]:
    """同一单元内：一关里英文或中文相同的词会让配对含糊（两张卡片看起来都对），
    所以把重复的词顺延到本单元的下一关；到了单元末尾还有剩的，单独成一关「补充」。
    一个词都不会丢。"""
    resolved: list[dict] = []
    carry: list[dict] = []
    for part in parts:
        kept, carry = _unique_take(carry + part["words"], max_pairs)
        resolved.append({"unit": part["unit"], "words": kept})
    extra = 0
    while carry:
        extra += 1
        kept, carry = _unique_take(carry, max_pairs)
        suffix = "补充" if extra == 1 else f"补充{extra}"
        resolved.append({"unit": f"{unit}（{suffix}）", "words": kept})
    return resolved


def _shuffled(items: list[dict], rng) -> list[dict]:
    """Fisher-Yates 洗牌，只用 rng() 给出的 [0,1) 小数：和小程序的 bank.js 逐步一致，
    测试里给两边同一串小数就能得到同一个结果。"""
    out = list(items)
    for i in range(len(out) - 1, 0, -1):
        j = int(rng() * (i + 1))
        out[i], out[j] = out[j], out[i]
    return out


def chunk_groups(groups: list[dict],
                 max_pairs: int = MAX_PAIRS_PER_LEVEL,
                 rng=None) -> list[dict]:
    """把词量大的单元拆成多个关卡，并给不足的关卡补上复习词。

    切分
    ----
    一个单元按 max_pairs 切开：37 个词的 ``Unit 1`` 变成四关，每关最多 12 词。

    补齐
    ------
    不足 max_pairs 的关卡，从**前面已经出现过的关卡**里**随机**取词补齐（相当于复习），
    这样最后一关也正好是 max_pairs 个词；每次生成取到的复习词都不一样，
    不会总是重复最前面那几个词。
    补进来的词在本关里不会和已有词重复——英文和中文都不重复，
    所以一关里不会出现两张一模一样的卡片（那会让配对变得含糊）。
    补过词的关卡名字后面会标上「含复习」。

    rng 是返回 [0,1) 小数的函数，默认 ``random.random``；测试里可以传固定序列。
    """
    rng = rng or random.random
    parts: list[dict] = []
    for group in groups:
        words = list(group.get("words") or [])
        if not words:
            continue
        unit = str(group.get("unit") or "")
        group_parts: list[dict] = []
        if max_pairs <= 0 or len(words) <= max_pairs:
            group_parts.append({"unit": unit, "words": words})
        else:
            parts_count = (len(words) + max_pairs - 1) // max_pairs
            for index in range(parts_count):
                chunk = words[index * max_pairs:(index + 1) * max_pairs]
                group_parts.append({
                    "unit": f"{unit}（{index + 1}/{parts_count}）",
                    "words": chunk,
                })
        parts.extend(_resolve_duplicates(group_parts, unit, max_pairs))

    # 补齐：把之前出现过的词拿来复习，但本关里不重复
    pool: list[dict] = []
    pool_keys: set[tuple[str, str]] = set()
    for part in parts:
        words = part["words"]
        used_en = {w.get("en", "") for w in words}
        used_cn = {w.get("cn", "") for w in words}
        added = 0
        # 只有真的不够数才洗牌（并且只在这时消耗随机数）
        candidates = _shuffled(pool, rng) if (pool and len(words) < max_pairs) else []
        for word in candidates:
            if len(words) >= max_pairs:
                break
            en = word.get("en", "")
            cn = word.get("cn", "")
            if en in used_en or cn in used_cn:
                continue
            words.append(dict(word))
            used_en.add(en)
            used_cn.add(cn)
            added += 1
        if added:
            part["unit"] = f"{part['unit']} · 含复习"
        for word in words:
            key = (word.get("en", ""), word.get("cn", ""))
            if key not in pool_keys:
                pool_keys.add(key)
                pool.append(word)
    return parts


def resolve_pairs_per_level(payload: dict) -> int:
    """读取「每关词数」，超范围就用默认值。"""
    try:
        value = int(payload.get("pairs_per_level") or MAX_PAIRS_PER_LEVEL)
    except (TypeError, ValueError):
        return MAX_PAIRS_PER_LEVEL
    if value < MIN_PAIRS_PER_LEVEL or value > MAX_PAIRS_PER_LEVEL_LIMIT:
        return MAX_PAIRS_PER_LEVEL
    return value


def create_bank(db: Database, payload: dict, owner_id: int | None = None) -> dict:
    """生成并落库一个题库，返回题库元信息。owner_id 是创建者（家庭版里用来区分各人的题库）。"""
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
        "pairs_per_level": resolve_pairs_per_level(payload),
        "owner_id": owner_id,
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
        "bank": dict({k: bank[k] for k in
                      ("id", "title", "level1", "level2", "level3", "level4",
                       "source", "unit_mode", "unit_from", "unit_to",
                       "pairs_per_level", "word_count", "unit_count", "created_at",
                       "category")}, tags=db.bank_tags(bid)),
        "groups": chunk_groups([{"unit": u, "words": groups[u]} for u in order],
                               max_pairs=int(bank.get("pairs_per_level")
                                             or MAX_PAIRS_PER_LEVEL)),
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
    carried = None      # 重建时带走老师设好的分类和标签，否则词库一更新，学生就看不到题库了

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
                if int(b.get("pairs_per_level") or 0) != MAX_PAIRS_PER_LEVEL:
                    db.execute("UPDATE banks SET pairs_per_level=? WHERE id=?",
                               (MAX_PAIRS_PER_LEVEL, b["id"]))
                default_banks.append(b)
                continue
            carried = (b.get("category") or "", list(b.get("tags") or []))
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
    if carried:
        db.set_bank_meta(bank["id"], carried[0], carried[1])
    return bank["id"]


def seed_curriculum_banks(db: Database) -> list[int]:
    """把每一册内置教材作为可直接游玩的题库展示，重复启动时不重复建库。"""
    seeded = []
    for volume in CURRICULUM_OBJ.volumes:
        stage = volume["stage"]
        grade = volume["grade"]
        term = volume["term"]
        default_volume = (
            stage == hierarchy.DEFAULT_SELECTION["level1"]
            and grade == hierarchy.DEFAULT_SELECTION["level2"]
            and term == hierarchy.DEFAULT_SELECTION["level3"]
            and volume["name"] == "九年级上册"
        )
        if default_volume:
            continue

        title = (f"人教版{stage}{grade}{term}" if stage == "初中"
                 else f"人教版高中{grade}{volume['name']}")
        units = [{
            "name": unit["name"],
            "label": unit["name"],
            "volume": volume["name"],
            "words": unit["words"],
        } for unit in volume["units"]]
        words = build_words(units)
        existing = next((bank for bank in db.list_banks()
                         if bank["source"] == "seed"
                         and bank["title"] == title
                         and bank["level1"] == stage
                         and bank["level2"] == grade
                         and bank["level3"] == term
                         and bank["unit_mode"] == "all"), None)
        if existing:
            if _fingerprint(db.bank_words(existing["id"])) == _fingerprint(words):
                if int(existing.get("pairs_per_level") or 0) != MAX_PAIRS_PER_LEVEL:
                    db.execute("UPDATE banks SET pairs_per_level=? WHERE id=?",
                               (MAX_PAIRS_PER_LEVEL, existing["id"]))
                seeded.append(existing["id"])
                continue
            carried = (existing.get("category") or "", list(existing.get("tags") or []))
            db.delete_bank(existing["id"])
        else:
            carried = None

        new_id = db.insert_bank({
            "title": title,
            "level1": stage,
            "level2": grade,
            "level3": term,
            "level4": "全部单元",
            "source": "seed",
            "unit_mode": "all",
            "unit_from": 1,
            "unit_to": len(units),
            "pairs_per_level": MAX_PAIRS_PER_LEVEL,
        }, words)
        if carried:
            db.set_bank_meta(new_id, carried[0], carried[1])
        seeded.append(new_id)
    return seeded
