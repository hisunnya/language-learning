"""从任意文本里抽取「英文词 + 中文释义」。

Word / PDF / TXT / CSV 抽出来的都是**排版文本**，格式千奇百怪：

* ``Unit 3`` / ``第三单元`` —— 单元标题
* ``apple 苹果`` —— 英文 + 中文，空格/制表符分隔
* ``apple\\t/ˈæpl/\\tn.\\t苹果`` —— Word 表格的一整行
* ``1. apple  苹果`` —— 带序号
* ``apple n. 苹果`` —— 带词性
* ``apple  苹果   orange  橙子`` —— 一行两组（PDF 双栏）

这些行逐行按正则切太脆。这里改用**词法扫描**：
先把一行拆成「英文词 / 音标 / 词性 / 中文片段」四种 token，
再按顺序配对。英文短语（``take care of``）会先累积再跟中文配。

规则
----
1. **单元标题**：整行匹配 ``Unit N`` / ``Module N`` / ``第 N 单元`` 时，
   更新当前单元，不再当作词条。
2. **中英配对**：英文 token 累积到遇到中文片段时组成一对；
   也支持中文在前、英文在后（``苹果 apple``）。
3. **词性**：``n.`` ``v.`` ``adj.`` 等单独摘到 ``pos``。
4. **音标**：``/.../`` 或 ``[...]`` 摘到 ``ipa``。
5. 序号（``1.`` ``①``）和项目符号剥掉。
6. **分栏兜底**：PDF 里英文和中文有时会分在两列（各占一行），
   这种情况下按出现顺序把「只有英文的行」和「只有中文的行」配对。
"""
from __future__ import annotations

import re

# ------------------------------------------------------------------ 正则

# 单元标题：Unit 3 / Module 2 / Lesson 1 / 第3单元 / 第三单元
UNIT_RE = re.compile(
    r"^\s*(?:(?:starter|welcome)\s+)?"
    r"(unit|module|lesson|part|section)\s*\.?\s*([0-9]+|[一二三四五六七八九十]+)"
    r"\s*(.*?)\s*$",
    re.I,
)
UNIT_CN_RE = re.compile(
    r"^\s*第\s*([0-9一二三四五六七八九十]+)\s*(单元|课|部分|章)\s*(.*?)\s*$")

# 一个英文单词（允许 U.S.A / Mr. / well-used / don't）
EN_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z'’\-]*(?:\.[A-Za-z]+)*")

# 中文片段（含中文标点与数字；**不含** ASCII 字母，
# 这样「苹果apple」会拆成中文 + 英文两个 token）
CN_RUN_RE = re.compile(
    r"[㐀-䶿一-鿿豈-﫿]"
    r"(?:[㐀-䶿一-鿿豈-﫿　-〿＀-￯0-9])*")

# 音标
IPA_RE = re.compile(r"[/\[]\s*([^/\[\]]{1,60}?)\s*[/\]]")

# 词性标记（**不带 ^ $ 锚点**，才能在行中间定位；
# 靠「点号结尾 + 后面不是字母」来避免误抓）
POS_RE = re.compile(
    r"(?:n|v|vt|vi|adj|adv|prep|conj|pron|num|art|int|aux|abbr|"
    r"interj|det|modal)\.")

# 行首序号 / 项目符号
LEAD_NUM_RE = re.compile(
    r"^\s*(?:[①-⑳⓿]|\(?\d{1,3}[).、]|[a-z][).])\s+", re.I)

# 整行只有数字和符号（页码、目录页码）
NOISE_RE = re.compile(r"^[\W\d\s]*$")


# ------------------------------------------------------------------ token 扫描

class _Token:
    """一个 token：``kind`` 是 en / cn / ipa / pos。"""

    __slots__ = ("kind", "text")

    def __init__(self, kind: str, text: str):
        self.kind = kind
        self.text = text


def _tokenize(line: str) -> list[_Token]:
    """把一行拆成 token 序列。"""
    tokens: list[_Token] = []
    i = 0
    n = len(line)
    while i < n:
        ch = line[i]
        if ch.isspace():
            i += 1
            continue
        # 音标
        m = IPA_RE.match(line, i)
        if m and m.end() > m.start() + 1:
            tokens.append(_Token("ipa", m.group(1).strip()))
            i = m.end()
            continue
        # 词性（必须在英文之前判断：n. 否则会被当成单词 "n"）
        m = POS_RE.match(line, i)
        if m and (i + m.end() >= n or not line[i + m.end()].isalpha()):
            tokens.append(_Token("pos", m.group(0).lower()))
            i = m.end()
            continue
        # 英文词
        m = EN_TOKEN_RE.match(line, i)
        if m:
            tokens.append(_Token("en", m.group(0)))
            i = m.end()
            continue
        # 中文片段
        m = CN_RUN_RE.match(line, i)
        if m:
            tokens.append(_Token("cn", m.group(0)))
            i = m.end()
            continue
        i += 1
    return tokens


def _clean_en(text: str) -> str:
    """清理英文部分。"""
    t = text.strip()
    t = t.strip(" \t.,;:!?'\"()[]{}、，。；：！？")
    return t.strip()


def _clean_cn(text: str) -> str:
    """清理中文部分。"""
    t = text.strip()
    t = re.sub(r"\s+", " ", t)
    t = t.strip(" \t.,;:!?'\"()[]{}、，。；：！？")
    return t.strip()


def split_entry(line: str) -> dict | None:
    """把一行拆成 ``{en, cn, ipa, pos}``；不像词条就返回 None。"""
    entries = split_entries(line)
    return entries[0] if entries else None


def split_entries(line: str) -> list[dict]:
    """把一行拆成**一个或多个**词条。

    PDF 用 ``-layout`` 抽出来的文本，一行里可能有好几组
    「英文 中文」（双栏表格），所以这里返回列表。
    """
    if not line:
        return []
    raw = line.rstrip()
    if not raw.strip() or NOISE_RE.match(raw):
        return []

    body = LEAD_NUM_RE.sub("", raw).strip()
    if not body:
        return []

    # 行首如果带单元标题（"Unit 1 apple 苹果"），把标题剥掉再解析正文
    unit, rest = _split_unit_prefix(body)
    if unit:
        if not rest.strip():
            return []
        body = rest.strip()

    tokens = _tokenize(body)
    if not tokens:
        return []

    pairs: list[dict] = []
    pending_en: list[str] = []
    pending_ipa = ""
    pending_pos = ""
    leading_cn = ""

    for tok in tokens:
        if tok.kind == "en":
            word = _clean_en(tok.text)
            if word:
                pending_en.append(word)
        elif tok.kind == "ipa":
            if not pending_ipa and tok.text:
                pending_ipa = "/" + tok.text + "/"
        elif tok.kind == "pos":
            if not pending_pos:
                pending_pos = tok.text
        elif tok.kind == "cn":
            cn = _clean_cn(tok.text)
            if pending_en:
                en = " ".join(pending_en)
                en = re.sub(r"\s+(?:n|v|vt|vi|adj|adv|prep|conj|pron|num|art|"
                            r"int|aux|abbr)\.$", "", en, flags=re.I)
                en = _clean_en(en)
                if en and cn:
                    pairs.append({"en": en, "cn": cn,
                                  "ipa": pending_ipa, "pos": pending_pos})
                pending_en = []
                pending_ipa = ""
                pending_pos = ""
            elif not leading_cn and cn:
                leading_cn = cn

    # 中文在前、英文在后：苹果 apple
    if not pairs and pending_en and leading_cn:
        en = _clean_en(" ".join(pending_en))
        if en and leading_cn:
            pairs.append({"en": en, "cn": leading_cn,
                          "ipa": pending_ipa, "pos": pending_pos})

    return pairs


def _is_label(text: str) -> bool:
    """判断一段文字是不是「单元标题的附注」而不是「词条正文」。

    标题附注长这样：``Words`` / ``单词表`` / ``Word List``
    词条正文长这样：``apple 苹果 banana 香蕉``

    区别在于：附注很短，而且最多只有一段中文。
    """
    t = text.strip()
    if not t or len(t) > 24:
        return False
    cn_runs = CN_RUN_RE.findall(t)
    if len(cn_runs) > 1:
        return False
    ascii_words = re.findall(r"[A-Za-z][A-Za-z'’\-]*", t)
    if ascii_words and len(ascii_words) > 3:
        return False
    return True


# 行中出现的单元标记。前面必须是行首或多个空格，避免把 "unite" 误判。
_MID_UNIT_RE = re.compile(
    r"(?:^|(?<=\s\s))"
    r"((?:starter|welcome)\s+)?"
    r"(unit|module|lesson|part|section)\s*\.?\s*"
    r"([0-9]+|[一二三四五六七八九十]+)"
    r"(?=\s|$)",
    re.I | re.M,
)
_MID_UNIT_CN_RE = re.compile(
    r"(?:^|(?<=\s\s))"
    r"(第\s*[0-9一二三四五六七八九十]+\s*(?:单元|课|部分|章))"
    r"(?=\s|$)")

_GLOSSARY_BULLET_RE = re.compile(r"^\s*[▲▴△▶•▪*]\s*(.*?)\s*$")
_GLOSSARY_IPA_RE = re.compile(r"\s+(/[^/\n]{1,60}/|\[[^\]\n]{1,60}\])")
_GLOSSARY_POS_RE = re.compile(
    r"\s+(n|v|vt|vi|adj|adv|prep|conj|pron|num|art|int|aux|abbr|"
    r"interj|det|modal|a|ad)\.\s", re.I)


def _glossary_head(cell: str) -> tuple[str, str, str] | None:
    """提取词典扫描页中项目符号后的词头、音标与词性。"""
    marker = _GLOSSARY_BULLET_RE.match(cell)
    body = marker.group(1).strip() if marker else cell.strip()
    ipa = _GLOSSARY_IPA_RE.search(body)
    if not marker and not ipa:
        return None
    pos = _GLOSSARY_POS_RE.search(body)
    cuts = [m.start() for m in (ipa, pos) if m]
    if cuts:
        head = body[:min(cuts)].strip()
    else:
        head = re.split(r"\s{2,}", body, maxsplit=1)[0].strip()
        if head == body:
            head = " ".join(body.split()[:3])
    head = head.strip(" \t.,;:!?'\"()[]{}、，。；：！？")
    if not head or not re.search(r"[A-Za-z]", head):
        return None
    return head, (ipa.group(1) if ipa else ""), (pos.group(1).lower() + "." if pos else "")


def parse_glossary_text(text: str) -> list[dict]:
    """抽取教材词典版式：带 ▲ 词头、英英解释、中文释义和跨行续文。

    OCR 文本用制表符标记左右栏；各栏独立扫描，避免同一行交错时串词。
    """
    rows = [re.split(r"\t+| {4,}", line.strip()) for line in text.splitlines()]
    columns = max((len(row) for row in rows), default=0)
    out: list[dict] = []

    for column in range(columns):
        current: dict | None = None
        unit = "Unit 1"

        def finish() -> None:
            if not current:
                return
            meaning = " ".join(part for part in current["cn"] if part).strip()
            if meaning:
                out.append({
                    "unit": unit,
                    "en": current["en"],
                    "cn": re.sub(r"\s+", " ", meaning),
                    "ipa": current["ipa"],
                    "pos": current["pos"],
                })

        for row in rows:
            if column >= len(row):
                continue
            cell = row[column].strip()
            if not cell:
                continue
            unit_match = UNIT_RE.match(cell)
            if unit_match:
                unit = f"{unit_match.group(1).title()} {unit_match.group(2)}"
                continue
            header = _glossary_head(cell)
            if header:
                finish()
                en, ipa, pos = header
                current = {"en": en, "ipa": ipa, "pos": pos, "cn": []}
            if current:
                current["cn"].extend(CN_RUN_RE.findall(cell))
        finish()

    unique = []
    seen = set()
    for entry in out:
        key = (entry["en"].lower(), entry["cn"])
        if key not in seen:
            seen.add(key)
            unique.append(entry)
    return unique


def _split_by_units(text: str) -> list[tuple[str, str]]:
    """把一行按「单元标记」切成若干段。

    返回 ``[(单元名, 该段的正文), ...]``，单元名为空串表示「沿用上一段」。

    PDF 的 ``pdftotext -layout`` 会把整页表格压成几行，
    单元标题可能夹在两行中间的列里，所以要在行内也切。
    """
    s = text.strip()
    if not s:
        return []

    marks: list[tuple[int, int, str]] = []
    for m in _MID_UNIT_RE.finditer(s):
        head = m.group(1).strip().title() if m.group(1) else ""
        label = m.group(2).title()
        num = m.group(3)
        unit = f"{head} {label} {num}".strip()
        if m.group(1):
            unit = f"{head} {label} {num}".replace("  ", " ").strip()
        marks.append((m.start(), m.end(), unit))
    for m in _MID_UNIT_CN_RE.finditer(s):
        marks.append((m.start(), m.end(), m.group(1).replace(" ", "")))
    if not marks:
        return [("", s)]

    marks.sort()
    out: list[tuple[str, str]] = []
    pos = 0
    for start, end, unit in marks:
        if start > pos:
            out.append(("", s[pos:start].strip()))
        out.append((unit, ""))
        pos = end
    if pos < len(s):
        out.append(("", s[pos:].strip()))
    return [(u, t) for u, t in out if t or u]


def _split_unit_prefix(line: str) -> tuple[str, str]:
    """把行首的单元标题剥掉，返回 ``(单元名, 剩下的正文)``。

    单元名可能为空（这行不是单元标题）。
    """
    s = line.strip()
    if not s:
        return "", ""

    m = UNIT_RE.match(s)
    if m:
        head = m.group(1).title()
        label = m.group(2)
        rest = (m.group(3) or "").strip()
        unit = f"{head} {label}"
        if rest and _is_label(rest):
            unit = f"{unit} {rest}"
            rest = ""
        return unit, rest

    m = UNIT_CN_RE.match(s)
    if m:
        unit = f"第{m.group(1)}{m.group(2)}"
        rest = (m.group(3) or "").strip()
        if rest and _is_label(rest):
            unit = f"{unit} {rest}"
            rest = ""
        return unit, rest

    return "", s


def detect_unit(line: str) -> str:
    """如果这一行**整个**是单元标题，返回标题文本，否则返回空串。"""
    unit, rest = _split_unit_prefix(line)
    if unit and not rest:
        return unit
    return ""


def _is_en_only(line: str) -> str:
    """这一行是不是「只有英文」？是的话返回英文，否则空串。"""
    body = LEAD_NUM_RE.sub("", line.strip()).strip()
    if not body or NOISE_RE.match(body):
        return ""
    toks = _tokenize(body)
    if not toks:
        return ""
    if any(t.kind == "cn" for t in toks):
        return ""
    words = [_clean_en(t.text) for t in toks if t.kind == "en"]
    words = [w for w in words if w]
    if not words:
        return ""
    joined = " ".join(words)
    if len(joined) > 60:
        return ""
    return joined


def _is_cn_only(line: str) -> str:
    """这一行是不是「只有中文」？是的话返回中文，否则空串。"""
    body = LEAD_NUM_RE.sub("", line.strip()).strip()
    if not body:
        return ""
    toks = _tokenize(body)
    if not toks:
        return ""
    if any(t.kind == "en" for t in toks):
        return ""
    cn = " ".join(_clean_cn(t.text) for t in toks if t.kind == "cn")
    cn = cn.strip()
    if not cn or len(cn) > 60:
        return ""
    return cn


def parse_lines(lines, default_unit: str = "Unit 1") -> list[dict]:
    """把若干行文本解析成词条列表。

    遇到单元标题就切换当前单元；其余行按 :func:`split_entry` 解析。
    如果一行里配不出词条，但整篇里有大量「纯英文行」和「纯中文行」
    （PDF 分栏的典型情况），按出现顺序两两配对。
    """
    out: list[dict] = []
    cur_unit = default_unit
    unit = default_unit
    seen: set[tuple[str, str]] = set()

    def emit(en: str, cn: str, ipa: str = "", pos: str = "",
             unit: str | None = None) -> None:
        en = _clean_en(en)
        cn = _clean_cn(cn)
        if not en or not cn:
            return
        if len(en) == 1 and en.lower() not in ("a", "i"):
            return
        key = (en.lower(), cn)
        if key in seen:
            return
        seen.add(key)
        out.append({"unit": unit or cur_unit, "en": en, "cn": cn,
                    "ipa": ipa, "pos": pos})

    en_only: list[tuple[str, str]] = []
    cn_only: list[tuple[str, str]] = []

    for idx, line in enumerate(lines):
        if line is None:
            continue
        text = line if isinstance(line, str) else str(line)
        # 一行里可能夹着单元标题（PDF 表格的常见情况），先按单元切成若干段
        for seg_unit, seg_text in _split_by_units(text):
            if seg_unit:
                unit = seg_unit
                cur_unit = seg_unit
            if not seg_text:
                continue
            entry = split_entries(seg_text)
            if entry:
                for e in entry:
                    emit(e["en"], e["cn"], e["ipa"], e["pos"])
                continue
            en_txt = _is_en_only(seg_text)
            if en_txt:
                en_only.append((unit, en_txt))
                continue
            cn_txt = _is_cn_only(seg_text)
            if cn_txt:
                cn_only.append((unit, cn_txt))

    # 分栏兜底：英文列和中文列各成一行时，按顺序配对
    if en_only and cn_only and len(en_only) >= 3 and len(cn_only) >= 3:
        pairs = min(len(en_only), len(cn_only))
        # 数量差太大就不配了，避免错位
        if abs(len(en_only) - len(cn_only)) <= max(2, pairs // 4):
            for i in range(pairs):
                en_unit, en_txt = en_only[i]
                cn_unit, cn_txt = cn_only[i]
                # 单元不一致时以英文那行的单元为准
                emit(en_txt, cn_txt, unit=en_unit)

    return out
