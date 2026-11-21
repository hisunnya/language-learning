"""新题型的题目：单词大比拼（spell，短语填空）和排排坐（order，把英文片段排成句子再朗读）。

题库表 banks 多一个 ``game_type``（match = 原来的中英配对，spell，order）；新题型的每道题是 bank_items 里的一行，
``data`` 是 JSON：

* spell：``{"before": "", "answer": "domestic", "after": "economy", "cn": "国内经济", "text": "domestic economy"}``
  —— 学生看到中文和短语，括号的位置是输入框；``text`` 是整个短语，答完朗读用。
* order：``{"cn": "…", "fragments": [{"segs": [["you should ", 0], ["keep on", 1]]}, …], "answer": "…"}``
  —— ``segs`` 是这个片段的文字，第二项 1 = 重点短语（资料里的黄色高亮），页面上照样高亮；片段按正确顺序存，
  游戏里打乱；``answer`` 是整句（资料里的绿色参考答案），朗读和识别都以它为准。

资料是老师写的 Word 文档（.docx），格式见 parse_spell / parse_order。只用标准库读 docx（它就是一个 zip 包）。
"""
from __future__ import annotations

import io
import re
import zipfile
from xml.etree import ElementTree as ET

GAME_TYPES = ("match", "spell", "order")
ITEM_TYPES = ("spell", "order")
PER_LEVEL = {"spell": 12, "order": 6}          # 一关最多几道题

_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_CJK = re.compile(r"[㐀-鿿豈-﫿]")
_NUMBERED = re.compile(r"^\s*(\d+)\s*[.．、]\s*(.+)$")


class ItemError(ValueError):
    pass


# ------------------------------------------------------------------ docx

def docx_paragraphs(data: bytes) -> list[list[tuple[str, str]]]:
    """docx → 段落列表；每段是 [(文字, 高亮颜色或 '')]。表格里的段落也按出现顺序算进来。"""
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            xml = z.read("word/document.xml")
    except (zipfile.BadZipFile, KeyError) as exc:
        raise ItemError("不是有效的 Word（.docx）文件") from exc
    root = ET.fromstring(xml)
    out = []
    for p in root.iter(_W + "p"):
        runs = []
        for r in p.iter(_W + "r"):
            text = "".join((t.text or "") for t in r.iter(_W + "t"))
            if r.find(_W + "tab") is not None:
                text += " "
            if not text:
                continue
            hl = r.find(_W + "rPr/" + _W + "highlight")
            runs.append((text, hl.get(_W + "val", "") if hl is not None else ""))
        out.append(runs)
    return out


def _clean(text: str) -> str:
    """全角括号、全角空格换成半角，连续空白合成一个。"""
    text = text.replace("（", "(").replace("）", ")").replace("　", " ").replace(" ", " ")
    return re.sub(r"\s+", " ", text)


def normalize_sentence(text: str) -> str:
    """比较两句英文是否相同时用：空白合一、去首尾空格；引号、标点保持原样。"""
    return re.sub(r"\s+", " ", (text or "").replace(" ", " ")).strip()


def answer_key(text: str) -> str:
    """拼写判分用：不分大小写、空白合一。"""
    return normalize_sentence(text).lower()


# ------------------------------------------------------------------ 单词大比拼

def parse_spell(paragraphs: list[list[tuple[str, str]]]) -> tuple[list[dict], list[str], str]:
    """每一行：英文短语（括号里是要填的词）+ 中文意思，例如 ``（domestic）economy 国内经济``、``Incredibly (humble) 十分谦虚``。
    没有括号的行当作标题或说明（第一个当标题）。返回 (题目, 问题, 标题)。"""
    items, problems, title = [], [], ""
    for n, runs in enumerate(paragraphs, 1):
        line = _clean("".join(t for t, _ in runs)).strip()
        if not line:
            continue
        if "(" not in line:
            title = title or line
            continue
        m = _CJK.search(line)
        if not m:
            problems.append("第 %d 段没有中文意思：%s" % (n, line))
            continue
        english, cn = line[:m.start()].strip(), line[m.start():].strip()     # 「…out of…」末尾的省略号属于英文
        g = re.fullmatch(r"(.*?)\(\s*([^()]+?)\s*\)(.*)", english)
        if not g:
            problems.append("第 %d 段的括号不成对：%s" % (n, line))
            continue
        before, answer, after = g.group(1).strip(), g.group(2).strip(), g.group(3).strip()
        if not re.fullmatch(r"[A-Za-z][A-Za-z' -]*", answer):
            problems.append("第 %d 段括号里不是英文单词：%s" % (n, answer))
            continue
        text = normalize_sentence(" ".join(x for x in (before, answer, after) if x))
        items.append({"before": before, "answer": answer, "after": after, "cn": cn, "text": text})
    if not items:
        problems.append("没有找到题目：每行要有「英文短语（括号里是要填的词）+ 中文意思」")
    return items, problems, title


# ------------------------------------------------------------------ 排排坐

def _segments(runs: list[tuple[str, str]]) -> list[list]:
    """一个片段的文字 → [[文字, 是否重点短语]]：空白合一、去首尾空格，相邻同类合并。"""
    segs: list[list] = []
    for text, hl in runs:
        text = _clean(text)
        flag = 1 if hl == "yellow" else 0
        if segs and segs[-1][1] == flag:
            segs[-1][0] += text
        else:
            segs.append([text, flag])
    joined = ""
    out: list[list] = []
    for text, flag in segs:
        if joined.endswith(" ") or not joined:
            text = text.lstrip()
        text = re.sub(r" {2,}", " ", text)
        if text:
            out.append([text, flag])
            joined += text
    if out:
        out[-1][0] = out[-1][0].rstrip()
        if not out[-1][0]:
            out.pop()
    return out


def fragment_text(fragment: dict) -> str:
    return "".join(s[0] for s in fragment["segs"])


def _is_answer(runs: list[tuple[str, str]]) -> bool:
    texts = [(t, hl) for t, hl in runs if t.strip()]
    return bool(texts) and all(hl == "green" for _, hl in texts)


def parse_order(paragraphs: list[list[tuple[str, str]]]) -> tuple[list[dict], list[str], str]:
    """每道题：一行「1. 中文句子」，下面每行一个英文片段（按正确顺序；黄色高亮 = 重点短语），
    最后一行整句绿色高亮 = 参考答案。片段拼起来必须和参考答案一致（空格多少不算）。返回 (题目, 问题, 标题)。"""
    items, problems, title = [], [], ""
    current: dict | None = None

    def finish(item: dict | None) -> None:
        if not item:
            return
        if not item["fragments"]:
            problems.append("第 %d 题没有英文片段" % item["no"])
            return
        joined = normalize_sentence(" ".join(fragment_text(f) for f in item["fragments"]))
        answer = item.get("answer") or joined
        if not item.get("answer"):
            problems.append("第 %d 题没有绿色的参考答案，按片段拼出来的句子当答案：%s" % (item["no"], joined))
        elif joined != answer:
            problems.append("第 %d 题的片段拼起来和参考答案不一样：\n  片段：%s\n  答案：%s" % (item["no"], joined, answer))
            return
        if len(item["fragments"]) < 2:
            problems.append("第 %d 题只有一个片段，排不了顺序" % item["no"])
            return
        items.append({"cn": item["cn"], "fragments": item["fragments"], "answer": answer})

    for runs in paragraphs:
        line = _clean("".join(t for t, _ in runs)).strip()
        if not line:
            continue
        m = _NUMBERED.match(line)
        if m and _CJK.search(m.group(2)):
            finish(current)
            current = {"no": int(m.group(1)), "cn": m.group(2).strip(), "fragments": [], "answer": ""}
            continue
        if current is None:
            title = title or line
            continue
        if _is_answer(runs):
            current["answer"] = normalize_sentence(line)
            finish(current)
            current = None
            continue
        segs = _segments(runs)
        if segs:
            current["fragments"].append({"segs": segs})
    finish(current)
    if not items and not problems:
        problems.append("没有找到题目：每道题要有一行「1. 中文句子」，下面是英文片段")
    return items, problems, title


def parse(game_type: str, data: bytes) -> tuple[list[dict], list[str], str]:
    if game_type not in ITEM_TYPES:
        raise ItemError("游戏类型只能是 spell 或 order")
    paragraphs = docx_paragraphs(data)
    return (parse_spell if game_type == "spell" else parse_order)(paragraphs)


def levels(game_type: str, items: list[dict], unit: str = "") -> list[dict]:
    """把题目分成关：每关最多 PER_LEVEL 道。"""
    size = PER_LEVEL.get(game_type, 10)
    chunks = [items[i:i + size] for i in range(0, len(items), size)] or [[]]
    total = len(chunks)
    return [{"unit": unit if total == 1 else "%s（%d/%d）" % (unit, i + 1, total), "items": chunk}
            for i, chunk in enumerate(chunks)]


def speech_text(game_type: str, item: dict) -> str:
    """这道题朗读的英文：拼写是整个短语，排排坐是整句。"""
    return item.get("text") if game_type == "spell" else item.get("answer", "")
