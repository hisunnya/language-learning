"""四级层级模型：学段 → 年级 → 册别 → 单元。

每一级都提供「自定义名称」选项，用户可以在任意一级填自己的名字。
内置词库（人教版 PEP）只是「可选项」之一，题目来源也可以是用户上传的资料。

层级
----
1. 学段：小学 / 初中 / 高中 / 大学 / 自定义
2. 年级：随学段变化（小学 一~六年级，初中 七~九年级，高中 高一~高三，大学 大一~大四）/ 自定义
3. 册别：上册 / 下册 / 全年（上下册，默认） / 自定义
4. 单元：全部单元 / 分单元 / 第 N 至第 M 单元 / 自定义
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
CURRICULUM = ROOT / "data" / "pep_curriculum.json"

STAGES = ["小学", "初中", "高中", "大学"]
GRADES_BY_STAGE = {
    "小学": ["一年级", "二年级", "三年级", "四年级", "五年级", "六年级"],
    "初中": ["七年级", "八年级", "九年级"],
    "高中": ["高一", "高二", "高三"],
    "大学": ["大一", "大二", "大三", "大四"],
}
TERMS = ["上册", "下册", "整学年"]
TERM_LABELS = {"上册": "上册", "下册": "下册", "整学年": "全年（上下册）"}
DEFAULT_TERM = "整学年"
UNIT_MODES = [
    ("all", "全部单元"),
    ("per-unit", "分单元"),
    ("range", "第 N 至第 M 单元"),
]
CUSTOM = "自定义"

# 默认题库：人教版初中九年级上册
DEFAULT_SELECTION = {
    "level1": "初中",
    "level2": "九年级",
    "level3": "上册",
    "level4": "全部单元",
}


class Curriculum:
    """内置词库（data/pep_curriculum.json）。"""

    def __init__(self, path: Path = CURRICULUM):
        self.path = path
        self.doc: dict[str, Any] = {"meta": {}, "volumes": []}
        if path.exists():
            self.doc = json.loads(path.read_text(encoding="utf-8"))

    @property
    def volumes(self) -> list[dict]:
        return self.doc.get("volumes", [])

    @property
    def meta(self) -> dict:
        return self.doc.get("meta", {})

    def stage_options(self) -> list[str]:
        have = {v["stage"] for v in self.volumes}
        return [s for s in STAGES if s in have] + [s for s in STAGES if s not in have]

    def grade_options(self, stage: str) -> list[str]:
        have: list[str] = []
        for v in self.volumes:
            if v["stage"] == stage and v["grade"] not in have:
                have.append(v["grade"])
        fallback = GRADES_BY_STAGE.get(stage, [])
        return have + [g for g in fallback if g not in have]

    def term_options(self, stage: str, grade: str) -> list[dict]:
        """返回该年级的册别选项，以及每个选项包含的册。"""
        vols = [v for v in self.volumes
                if v["stage"] == stage and v["grade"] == grade]
        out = []
        for term in TERMS:
            picked = vols if term == "整学年" else [v for v in vols if v["term"] == term]
            out.append({
                "key": term,
                "name": TERM_LABELS[term],
                "volumes": [{"key": v["key"], "name": v["name"]} for v in picked],
                "unit_count": sum(len(v["units"]) for v in picked),
                "available": bool(picked),
            })
        return out

    def select_units(self, stage: str, grade: str, term: str) -> list[dict]:
        """按学段/年级/册别取出单元列表（全年 = 上册 + 下册）。"""
        vols = [v for v in self.volumes
                if v["stage"] == stage and v["grade"] == grade]
        if term != "整学年":
            vols = [v for v in vols if v["term"] == term]
        units: list[dict] = []
        multi = len({v["term"] for v in vols}) > 1
        for v in vols:
            for u in v["units"]:
                units.append({
                    "name": u["name"],
                    "volume": v["name"],
                    "volume_key": v["key"],
                    "term": v["term"],
                    "label": f"{v['name']} {u['name']}" if multi else u["name"],
                    "words": u["words"],
                })
        return units

    def units_for(self, stage: str, grade: str, term: str) -> list[dict]:
        """只取单元元信息（不含词），给前端做下拉框用。"""
        return [
            {"index": i + 1, "name": u["label"], "volume": u["volume"],
             "count": len(u["words"])}
            for i, u in enumerate(self.select_units(stage, grade, term))
        ]


CURRICULUM_OBJ = Curriculum()


def level1_options() -> list[dict]:
    return [{"key": s, "name": s, "custom": False} for s in CURRICULUM_OBJ.stage_options()]


def level2_options(level1: str) -> list[dict]:
    grades = CURRICULUM_OBJ.grade_options(level1)
    return [{"key": g, "name": g, "custom": False} for g in grades]


def level3_options(level1: str, level2: str) -> list[dict]:
    opts = CURRICULUM_OBJ.term_options(level1, level2)
    return [{
        "key": o["key"], "name": o["name"], "default": o["key"] == DEFAULT_TERM,
        "unit_count": o["unit_count"], "available": o["available"],
        "custom": False,
    } for o in opts]


def level4_options(level1: str, level2: str, level3: str) -> list[dict]:
    units = CURRICULUM_OBJ.units_for(level1, level2, level3)
    return [{
        "key": key, "name": name, "custom": False, "unit_count": len(units),
    } for key, name in UNIT_MODES]


def describe() -> dict:
    """给前端的层级元数据。"""
    return {
        "stages": level1_options(),
        "grades": GRADES_BY_STAGE,
        "terms": TERMS,
        "term_labels": TERM_LABELS,
        "default_term": DEFAULT_TERM,
        "unit_modes": [{"key": k, "name": n} for k, n in UNIT_MODES],
        "custom": CUSTOM,
        "default_selection": DEFAULT_SELECTION,
        "curriculum": CURRICULUM_OBJ.meta,
    }
