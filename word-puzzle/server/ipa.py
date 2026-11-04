"""美式音标（American English IPA）。

为什么不用 ECDICT
-----------------
ECDICT 的 ``phonetic`` 字段是**英式**音标（``/ˈɒrɪndʒ/``、``/ˈdɔː/``、``/ˈtiːtʃə/``），
跟本项目要求的「美语」不符。

本模块改用 **CMU Pronouncing Dictionary**（CMUdict）：

* 收录 13.5 万条**美式**发音，是英语发音的标准参考；
* 原始格式是 ARPAbet（美式音素集），本模块负责转成国际音标；
* 自带大量英式/美式差异词条（``schedule`` = 美 ``SK EH1 JH UW0 L``，
  英式则是 ``SH EH1 JH UW0 L``），能直接体现「美语」。

音标对照表见 ``data/raw/us_ipa.tsv``（每行 ``word<TAB>/ipa/``），
由 ``tools/build_ipa_table.py`` 生成。

用法::

    from server import ipa
    ipa.lookup("schedule")      # '/skˈɛdʒʊl/'
    ipa.lookup("colour")        # '/ˈkʌlər/'  (自动转美式拼写)
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IPA_TABLE = ROOT / "data" / "raw" / "us_ipa.tsv"

# ---------------------------------------------------------------- ARPAbet → IPA

# 元音
_VOWELS = {
    "AA": "ɑ", "AE": "æ", "AH": "ʌ", "AO": "ɔ", "AW": "aʊ", "AY": "aɪ",
    "EH": "ɛ", "ER": "ɝ", "EY": "eɪ", "IH": "ɪ", "IY": "i", "OW": "oʊ",
    "OY": "ɔɪ", "UH": "ʊ", "UW": "u",
}
# 辅音
_CONSONANTS = {
    "B": "b", "CH": "tʃ", "D": "d", "DH": "ð", "F": "f", "G": "ɡ", "HH": "h",
    "JH": "dʒ", "K": "k", "L": "l", "M": "m", "N": "n", "NG": "ŋ", "P": "p",
    "R": "ɹ", "S": "s", "SH": "ʃ", "T": "t", "TH": "θ", "V": "v", "W": "w",
    "Y": "j", "Z": "z", "ZH": "ʒ",
}

_PHONEME_RE = re.compile(r"^([A-Z]+)([0-2])?$")


def arpabet_to_ipa(arpabet: str) -> str:
    """把 CMUdict 的一行 ARPAbet 转成国际音标。

    ``"S K EH1 JH UH0 L"`` → ``"skˈɛdʒʊl"``

    重音标记：``1`` → 主重音 ``ˈ``，``2`` → 次重音 ``ˌ``，``0`` → 不标。
    美式特有的弱读音素：``AH0`` → ``ə``，``ER0`` → ``ɚ``。
    """
    out: list[str] = []
    for token in arpabet.split():
        m = _PHONEME_RE.match(token)
        if not m:
            continue
        ph, stress = m.group(1), m.group(2)
        if ph == "AH" and stress == "0":
            sym = "ə"
        elif ph == "ER":
            sym = "ɝ" if stress == "1" else "ɚ"
        else:
            sym = _VOWELS.get(ph) or _CONSONANTS.get(ph)
        if sym is None:
            continue
        if stress == "1":
            out.append("ˈ")
        elif stress == "2":
            out.append("ˌ")
        out.append(sym)
    return "".join(out)


# ---------------------------------------------------------------- 英式 → 美式拼写

# 人教版教材用英式拼写（colour / organise / centre ...），
# 而 CMUdict 收录的是美式拼写。查表前先做一次拼写归一，
# 这样 "colourful" 也能查到美式音标 /ˈkʌlərfəl/。
_BRITISH_TO_AMERICAN = {
    "colour": "color", "colourful": "colorful", "colours": "colors",
    "favourite": "favorite", "favourites": "favorites",
    "flavour": "flavor", "flavours": "flavors", "flavourful": "flavorful",
    "honour": "honor", "honours": "honors", "honourable": "honorable",
    "labour": "labor", "neighbour": "neighbor", "neighbours": "neighbors",
    "neighbourhood": "neighborhood",
    "behaviour": "behavior", "behaviours": "behaviors",
    "centre": "center", "centres": "centers", "centred": "centered",
    "theatre": "theater", "theatres": "theaters",
    "metre": "meter", "metres": "meters", "litre": "liter",
    "kilometre": "kilometer", "kilometres": "kilometers",
    "centimetre": "centimeter", "millimetre": "millimeter",
    "programme": "program", "programmes": "programs",
    "practise": "practice", "practises": "practices",
    "organise": "organize", "organises": "organizes", "organised": "organized",
    "organising": "organizing", "organisation": "organization",
    "organisations": "organizations", "organised": "organized",
    "recognise": "recognize", "recognises": "recognizes",
    "recognised": "recognized", "realise": "realize", "realised": "realized",
    "specialise": "specialize", "specialised": "specialized",
    "apologise": "apologize", "apologised": "apologized",
    "criticise": "criticize", "criticised": "criticized",
    "civilisation": "civilization", "civilisations": "civilizations",
    "commercialise": "commercialize", "commercialised": "commercialized",
    "commercialisation": "commercialization",
    "civilise": "civilize", "civilised": "civilized",
    "emphasise": "emphasize", "emphasised": "emphasized",
    "memorise": "memorize", "memorised": "memorized",
    "minimise": "minimize", "maximise": "maximize",
    "modernise": "modernize", "modernised": "modernized",
    "normalise": "normalize", "organise": "organize",
    "popularise": "popularize", "prioritise": "prioritize",
    "standardise": "standardize", "summarise": "summarize",
    "symbolise": "symbolize", "utilise": "utilize",
    "visualise": "visualize", "advertise": "advertise",
    "enterprise": "enterprise",
    "enrol": "enroll", "enrolment": "enrollment",
    "fulfil": "fulfill", "instalment": "installment",
    "skilful": "skillful", "wilful": "willful",
    "defence": "defense", "offence": "offense", "preence": "pretense",
    "licence": "license", "practise": "practice",
    "rumour": "rumor", "rumours": "rumors", "armour": "armor",
    "harbour": "harbor", "harbours": "harbors", "savour": "savor",
    "savoury": "savory", "rigour": "rigor", "vigour": "vigor",
    "splendour": "splendor", "tumour": "tumor", "odour": "odor",
    "aluminium": "aluminum", "grey": "gray", "tyre": "tire",
    "storey": "story", "jewellery": "jewelry", "travelling": "traveling",
    "travelled": "traveled", "cancelled": "canceled", "labelling": "labeling",
    "modelling": "modeling", "signalling": "signaling",
    "fuelled": "fueled", "totally": "totally",
    "programme": "program", "dialogue": "dialog",
    "analogue": "analog", "catalogue": "catalog",
    "fibre": "fiber", "fibres": "fibers", "litre": "liter",
    "sabre": "saber", "sombre": "somber", "spectre": "specter",
    "theatre": "theater", "manoeuvre": "maneuver",
    "practised": "practiced", "specialised": "specialized",
    "travelling": "traveling", "whilst": "while",
    "whilst": "while", "amongst": "among", "towards": "toward",
}


def to_american_spelling(word: str) -> str:
    """把英式拼写换成美式拼写（逐词替换，保留原拼写不变时的结果）。"""
    parts = word.split()
    out = []
    for part in parts:
        low = part.lower()
        if low in _BRITISH_TO_AMERICAN:
            repl = _BRITISH_TO_AMERICAN[low]
            # 保留首字母大小写
            if part[:1].isupper():
                repl = repl[:1].upper() + repl[1:]
            out.append(repl)
        else:
            out.append(part)
    return " ".join(out)


# ---------------------------------------------------------------- 查表

_TABLE: dict[str, str] | None = None


def load_table(path: Path | None = None) -> dict[str, str]:
    """载入音标对照表（进程内缓存）。"""
    global _TABLE
    if _TABLE is not None and path is None:
        return _TABLE
    target = Path(path) if path else IPA_TABLE
    table: dict[str, str] = {}
    if target.exists():
        with target.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.rstrip("\n")
                if not line or "\t" not in line:
                    continue
                word, ph = line.split("\t", 1)
                word = word.strip().lower()
                ph = ph.strip()
                if word and ph:
                    table.setdefault(word, ph)
    if path is None:
        _TABLE = table
    return table


def _strip_decoration(word: str) -> str:
    """去掉词尾的括号注释、标点等装饰，只留下词本身。

    教材里常见的形式::

        crisis ( pl. crises )      → crisis
        bacterium ( pl. -ria/-ria/) → bacterium
        NASA abbr. National ...     → nasa abbr national
        analyse (NAmE -ze]          → analyse
    """
    w = word.strip()
    # 先去成对的括号（可能不配对，如 ``analyse (NAmE -ze]``）
    w = re.sub(r"[（(][^）)]*[)）]?", " ", w)
    w = re.sub(r"[\[【][^\]】]*[\]】]?", " ", w)
    w = w.strip(".,;:!?\"'()[]{}")
    w = re.sub(r"[^A-Za-z'\- ]", " ", w)
    # 归一化连字符两侧空格：``Three- Body`` → ``Three-Body``
    w = re.sub(r"\s*-\s*", "-", w)
    return " ".join(w.split()).lower()


def _segment(word: str, table: dict[str, str]) -> list[str] | None:
    """把复合词拆成 CMUdict 里有的部分。

    ``schoolbag`` → ``["school", "bag"]``
    """
    parts: list[str] = []
    i = 0
    n = len(word)
    while i < n:
        j = n
        while j > i + 1:
            if word[i:j].lower() in table:
                break
            j -= 1
        else:
            return None
        parts.append(word[i:j])
        i = j
    return parts


def lookup(word: str, table: dict[str, str] | None = None) -> str:
    """查一个词的**美式**音标，查不到返回空串。

    依次尝试：

    1. 手工表（教材专有名词 / 带注释条目）；
    2. 原词直接查；
    3. 去掉装饰字符后再查；
    4. 英式拼写转美式拼写后查（``colour`` → ``color``）；
    5. 多词短语：每个词分别查，拼成整体音标；
    6. 复合词拆分后拼成整体音标（``schoolbag`` → ``school`` + ``bag``）。
    """
    if not word:
        return ""
    table = load_table() if table is None else table
    key = word.strip().lower()
    if not key:
        return ""

    # 1) 手工表（原文匹配 → 去装饰匹配）
    if key in _MANUAL:
        return _MANUAL[key]
    clean0 = _strip_decoration(word)
    if clean0 and clean0 in _MANUAL:
        return _MANUAL[clean0]

    # 2) 占位符（sb. / sth. 等教材常用缩写）
    if key in _PLACEHOLDERS:
        return "/" + _PLACEHOLDERS[key] + "/"
    if clean0 and clean0 in _PLACEHOLDERS:
        return "/" + _PLACEHOLDERS[clean0] + "/"

    # 3) 直接查
    if key in table:
        return table[key]

    # 4) 去掉装饰
    clean = clean0
    if clean and clean != key and clean in table:
        return table[clean]

    # 5) 英式 → 美式拼写
    amer = to_american_spelling(clean or key)
    if amer and amer != clean and amer in table:
        return table[amer]

    # 6) 短语：逐词查
    if " " in (clean or key):
        parts = (clean or key).split()
        ph = _lookup_phrase(parts, table)
        if ph:
            return ph

    # 7) 复合词拆分（schoolbag → school + bag；ice-skate → ice + skate）
    if clean and "-" not in clean and len(clean) > 3:
        # 先按连字符拆，拆不出来再尝试整体二分
        target = clean
    elif clean and "-" in clean:
        target = clean.replace("-", " ")
    else:
        return ""

    seg = _segment(target, table) if "-" not in clean else \
        [p for p in clean.split("-") if p]
    if not seg:
        return ""
    found = []
    for part in seg:
        ph = (table.get(part.lower())
              or table.get(to_american_spelling(part))
              or _MANUAL.get(part.lower()))
        if not ph:
            return ""
        found.append(ph.strip("/"))
    return "/" + "".join(found) + "/"


# 教材里常见的占位符（sb. = somebody, sth. = something）
_PLACEHOLDERS = {
    "sb": "səmbədi", "sb's": "səmbədiz", "sth": "sʌmθɪŋ",
    "sth's": "sʌmθɪŋz", "somebody": "sʌmbədi", "something": "sʌmθɪŋ",
    "everyone": "ɛvriwʌn", "anyone": "ɛniwʌn", "somewhere": "sʌmwɛr",
    "anywhere": "ɛniwɛr", "nothing": "nʌθɪŋ", "everything": "ɛvriθɪŋ",
}

# 教材里收录、但 CMUdict 没有的词（专有名词、英式拼写、带注释的条目）。
# 音标一律按**美式**标注。
_MANUAL = {
    "analyse (NAmE -ze]": "/ˈænəlaɪz/",
    "categorise": "/ˈkætəɡəraɪz/",
    "fertiliser": "/ˈfɜːrtəlaɪzɚ/",
    "gramme": "/ɡræm",
    "sulphuric pool": "/sʌlˈfjʊɹɪk puːl",
    "chilli=chili": "/ˈtʃɪli",
    "good/bad-tempered": "/ɡʊd bæd ˈtɛmpɚd",
    "aquarium": "/əˈkwɛɹiəm",
    "bacterium": "/bækˈtɪɹiəm",
    "crisis": "/ˈkɹaɪsɪs",
    "criterion": "/kɹaɪˈtɪɹiən",
    "criterion ( pl. criteria /-ri/ )": "/kɹaɪˈtɪɹiən",
    "shelf ( pl. shelves  )": "/ʃɛlf",
    "the Arctic /'a:ktrk/ Circle": "/ˈɑɹktɪk ˈsɚkl",
    "Rapa  River": "/ˈɹɑpə ˈɹɪvɚ",
    "resume ( BrE CV)": "/ɹˈɛzəmeɪ",
    "IV needle": "/ˌaɪ viː ˈnidəl",
    "stadium (pl. stadiums or stadia)": "/ˈsteɪdiəm",
    "bagpipes (pl.)": "/ˈbæɡpaɪps",
    "genius ( pl. geniuses)": "/ˈdʒiniəs",
    "keep（……）in mind": "/kip ɪn maɪnd",
    "the Naadam Festival “": "/ðə nəˈɑdəm ˈfɛstɪvəl",
    "the Wenhai Scholarship “": "/ðə wənˈhaɪ ˈskɜːlɚʃɪp",
    "cm abbr.（centimetre or centimeter）": "/ˈsɛntɪmiːtɚ",
    "NASA abbr. National Aeronautics and Space Administration": "/ˈnæsə",
    "GPS abbr. global positioning system": "/ˌdʒi piː ˈɛs",
    "LED abbr( light- emitting diode )": "/ˌɛl ˈdiː",
    "the USSR abbr. the Union of Soviet Socialist Republics": "/juː ɛs ɛs ˈɑɹ",
    "SARS   abbr.": "/sɑɹz",
    "botanical adi.": "/bəˈtænɪkəl",
    "namaste interj.": "/nəˈmɑsteɪ",
    "cheers interj.": "/tʃɪɚz",
    "the haka": "/ˈhɑkə",
    "duck-billed platypus": "/ˈdʌk bɪld ˈplætɪpəs",
    "manuka honey": "/məˈnuːkə ˈhʌni",
    "the OB-GYN department": "/ˌoʊ biː ˈdʒiː aɪ ɛn ˈdi pɑɹtmənt",
    "coverage /'kvard3/": "/ˈkʌvɚdʒ",
    "rigid /'rd3yd/": "/ˈɹɪdʒɪd",
    "maths": "/mæθs",
    "PE": "/ˌpiː ˈiː",
    "healthily": "/ˈhɛlθəli",
    "café": "/kæˈfeɪ",
    "vr.": "/ˈviː ˈɑɹ",
    "tive off": "/taɪv ɔf",
    "iower": "/ˈaɪəwɚ",
    "cinquain": "/sɪŋˈkweɪn",
    "chilli": "/ˈtʃɪli",
    "fertiliser ( NAmE -izer )": "/ˈfɜːrtəlaɪzɚ",
    "aquarium ( pl. aquariums or aquaria /-ria/ )": "/əˈkwɛɹiəm",
    "ginkgo": "/ˈɡɪŋkoʊ",
}

# 专有名词（地名 / 人名）CMUdict 未收录，按**英语化读音**（anglicized）标注。
_PROPER_NOUNS = {
    "malee": "/məˈli/",
    "gongbao chicken": "/ˈɡɔŋbaʊ ˈtʃɪkɪn/",
    "dongpo pork": "/ˈdʊŋpoʊ pɔɹk/",
    "mount huangshan": "/ˈmaʊnt ˈhwɑŋʃɑn/",
    "world war ii": "/ˈwɝld wɔɹ ˈtuː ˈaɪ/",
    "guest-greeting pine": "/ɡɛst ˈɡɹiːtɪŋ paɪn/",
    "guoqiao rice noodles": "/ˌɡwoʊˈtʃaʊ ˈraɪs ˈnoʊdlz/",
    "mogao caves": "/moʊˈɡaʊ keɪvz/",
    "mount qomolangma": "/ˈmaʊnt ˌtʃoʊmoʊˈlɑŋmə/",
    "taklimakan desert": "/ˌtɑːkliːməˈkɑːn ˈdɛzɚt/",
    "lake baikal": "/leɪk baɪˈkɑːl/",
    "türkiye": "/ˈtɝːki.eɪ",
    "the three-body problem": "/ðə θɹiː ˈbɑdi ˈprɑbləm",
    "aswan dam": "/əˈswɑːn dæm/",
    "coming-of-age day": "/ˈkʌmɪŋ əv eɪdʒ deɪ/",
    "la tomatina": "/ˌlɑː təˈmɑːtiːnə/",
    "huangguoshu waterfall": "/ˌhwɑŋɡwɔˈʃuː ˈwɔːtɚfɔːl/",
    "typhoon goni": "/taɪˈfuːn ˈɡoʊni/",
    "elon musk": "/ˈɛlən mʌsk/",
    "sarek national park": "/ˈsɑːrɛk ˈnæʃənəl pɑɹk/",
    "giotto di bondone": "/ˈdʒoʊtoʊ di bɔnˈdoʊni/",
    "giverny": "/ˈʒivɚni/",
    "svalbard": "/ˈsvɑːlbɑːd/",
    "ernest shacklton": "/ˈɜːrnɪst ˈʃækltən/",
    "perce blackborow": "/pɜːs ˈblækbəroʊ/",
    "thomas orde-lees": "/ˈtɑːməs ˈɔɹdi liːz",
    "gladys claffern": "/ˈɡlædis ˈklæfɚn/",
    "zac sunderland": "/zæk ˈsʌndɚlænd/",
}

# 统一小写键，便于与 lookup() 的 key（word.strip().lower()）对齐
_MANUAL.update({k.lower(): v for k, v in _PROPER_NOUNS.items()})
_MANUAL = {k.lower(): v for k, v in _MANUAL.items()}


def _lookup_phrase(words: list[str], table: dict[str, str]) -> str:
    """短语逐词查音标；占位符（sb. / sth.）用固定读音。"""
    found: list[str] = []
    for part in words:
        low = part.lower().strip(".")
        # "sb's" → 先试原样，再去掉所有格
        cands = [low]
        if low.endswith("'s") or low.endswith("’s"):
            cands.append(low[:-2])
        cands.append(to_american_spelling(low))
        ph = ""
        for c in cands:
            ph = table.get(c) or _MANUAL.get(c) or _PLACEHOLDERS.get(c)
            if ph:
                break
        if not ph:
            return ""
        found.append(ph.strip("/"))
    return "/" + " ".join(found) + "/"


def available() -> bool:
    """音标表是否已就绪。"""
    return bool(load_table())
