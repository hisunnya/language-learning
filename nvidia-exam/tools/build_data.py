#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把采集到的原始资料整理成网站用的题库与指南数据。

输入（都在 raw-files/ 里，是 2026-11-27 采集的公开资料）：

* ``nvidia_cert_data.json`` —— 8 项认证的题目、选项、答案、解析、社区讨论帖与学习指南索引；
* ``学习指南汇总.md``     —— 570 篇学习指南正文（按认证分章）。

输出：

* ``data/bank.json`` / ``data/bank.js`` —— 网站用的题库（两种格式内容必须一致，tests 会校验）；
* ``data/guides.json`` / ``data/guides.js`` —— 学习指南索引；
* ``docs/guides/<CODE>.md`` —— 按认证拆开的学习指南正文，方便只读自己考的那一科；
* ``docs/采集说明.md`` —— 采集过程与口径说明（从 raw-files 复制，抹掉邮箱）。

跑法：

    cd nvidia-exam && python3 tools/build_data.py

仓库是公开的：脚本里会把正文里的邮箱地址抹掉（`[邮箱已隐去]`），
免得把第三方的私人邮箱带进 git 历史。
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
RAW = BASE / "raw-files"
DATA = BASE / "data"
DOCS = BASE / "docs"

LETTERS = "ABCDEFGHIJKLMNOP"

# ---------------------------------------------------------------- 官方考纲

# 每一项认证的官方信息（题量、时长、及格线、考纲知识域与权重）。
# 权重来自采集到的学习指南里引用的 NVIDIA 公开考试大纲；没有公布权重的那一科
# （NCP-OUSD）按题库里各知识域的题量分布折算，并在 blueprint 里注明。
BLUEPRINTS = {
    "nca-aiio": {
        "code": "NCA-AIIO",
        "name": "NVIDIA Certified Associate: AI Infrastructure and Operations",
        "nameZh": "NVIDIA 认证助理：AI 基础设施与运维",
        "shortZh": "AI 基础设施与运维",
        "shortEn": "AI Infrastructure and Operations",
        "level": "NCA",
        "track": "AI 基础设施",
        "official": {"questions": 50, "durationMin": 60, "passPct": 70},
        "blueprint": "official",
        "domains": [
            ("essential-ai-knowledge", "Essential AI Knowledge", "AI 基础知识", 38),
            ("ai-infrastructure", "AI Infrastructure", "AI 基础设施", 40),
            ("ai-operations", "AI Operations", "AI 运维", 22),
        ],
    },
    "nca-genl": {
        "code": "NCA-GENL",
        "name": "NVIDIA Certified Associate: Generative AI Large Language Models",
        "nameZh": "NVIDIA 认证助理：生成式 AI 大语言模型",
        "shortZh": "生成式 AI 大语言模型",
        "shortEn": "Generative AI Large Language Models",
        "level": "NCA",
        "track": "生成式 AI",
        "official": {"questions": 50, "durationMin": 60, "passPct": 70},
        "blueprint": "official",
        "domains": [
            ("core-ml-knowledge", "Core Machine Learning and AI Knowledge", "核心机器学习与 AI 知识", 30),
            ("software-development", "Software Development", "软件开发", 24),
            ("experimentation", "Experimentation", "实验", 22),
            ("data-analysis", "Data Analysis and Visualization", "数据分析与可视化", 14),
            ("trustworthy-ai", "Trustworthy AI", "可信 AI", 10),
        ],
    },
    "nca-genm": {
        "code": "NCA-GENM",
        "name": "NVIDIA Certified Associate: Generative AI Multimodal",
        "nameZh": "NVIDIA 认证助理：生成式 AI 多模态",
        "shortZh": "生成式 AI 多模态",
        "shortEn": "Generative AI Multimodal",
        "level": "NCA",
        "track": "生成式 AI",
        "official": {"questions": 60, "durationMin": 60, "passPct": 70},
        "blueprint": "official",
        "domains": [
            ("experimentation", "Experimentation", "实验", 25),
            ("core-ml-knowledge", "Core Machine Learning and AI Knowledge", "核心机器学习与 AI 知识", 20),
            ("multimodal-data", "Multimodal Data", "多模态数据", 15),
            ("software-development", "Software Development", "软件开发", 15),
            ("data-analysis", "Data Analysis and Visualization", "数据分析与可视化", 10),
            ("performance-optimization", "Performance Optimization", "性能优化", 10),
            ("trustworthy-ai", "Trustworthy AI", "可信 AI", 5),
        ],
    },
    "ncp-aai": {
        "code": "NCP-AAI",
        "name": "NVIDIA Certified Professional: Agentic AI",
        "nameZh": "NVIDIA 认证专家：智能体 AI",
        "shortZh": "智能体 AI",
        "shortEn": "Agentic AI",
        "level": "NCP",
        "track": "Agentic AI",
        "official": {"questions": 50, "durationMin": 60, "passPct": 70},
        # 采集到的官方考纲只列了 9 个域（合计 93%），按最大余数法归一到 100%
        "blueprint": "partial",
        "domains": [
            ("agent-architecture", "Agent Architecture and Design", "智能体架构与设计", 15),
            ("agent-development", "Agent Development", "智能体开发", 15),
            ("evaluation-tuning", "Evaluation and Tuning", "评估与调优", 13),
            ("deployment-scaling", "Deployment and Scaling", "部署与扩缩", 13),
            ("cognition-memory", "Cognition, Planning, and Memory", "认知、规划与记忆", 10),
            ("knowledge-integration", "Knowledge Integration and Data Handling", "知识整合与数据处理", 10),
            ("nvidia-platform", "NVIDIA Platform Implementation", "NVIDIA 平台落地", 7),
            ("operations-monitoring", "Operations, Monitoring, and Maintenance", "运行、监控与维护", 5),
            ("security-ethics", "Security, Ethics, and Compliance", "安全、伦理与合规", 5),
        ],
    },
    "ncp-aii": {
        "code": "NCP-AII",
        "name": "NVIDIA Certified Professional: AI Infrastructure",
        "nameZh": "NVIDIA 认证专家：AI 基础设施",
        "shortZh": "AI 基础设施",
        "shortEn": "AI Infrastructure",
        "level": "NCP",
        "track": "AI 基础设施",
        "official": {"questions": 75, "durationMin": 120, "passPct": 70},
        "blueprint": "official",
        "domains": [
            ("system-bringup", "System and Server Bring-up", "系统与服务器上线", 31),
            ("physical-layer", "Physical Layer Management", "物理层管理", 5),
            ("control-plane", "Control Plane Installation and Configuration", "控制平面安装与配置", 19),
            ("cluster-verification", "Cluster Test and Verification", "集群测试与验证", 33),
            ("troubleshooting", "Troubleshoot and Optimize", "故障排查与优化", 12),
        ],
    },
    "ncp-ain": {
        "code": "NCP-AIN",
        "name": "NVIDIA Certified Professional: AI Networking",
        "nameZh": "NVIDIA 认证专家：AI 网络",
        "shortZh": "AI 网络",
        "shortEn": "AI Networking",
        "level": "NCP",
        "track": "AI 网络",
        "official": {"questions": 75, "durationMin": 120, "passPct": 70},
        "blueprint": "official",
        "domains": [
            ("dc-design", "AI Data Center Design and Optimization", "AI 数据中心设计与优化", 5),
            ("spectrum-networking", "NVIDIA Spectrum Networking", "NVIDIA Spectrum 网络", 30),
            ("infiniband-networking", "NVIDIA InfiniBand Networking", "NVIDIA InfiniBand 网络", 30),
            ("kubernetes-integration", "Kubernetes Integration", "Kubernetes 集成", 5),
            ("troubleshooting-tools", "Troubleshooting Tools", "排障工具", 20),
            ("automation-config", "Automation and Configuration", "自动化与配置", 10),
        ],
    },
    "ncp-aio": {
        "code": "NCP-AIO",
        "name": "NVIDIA Certified Professional: AI Operations",
        "nameZh": "NVIDIA 认证专家：AI 运维",
        "shortZh": "AI 运维",
        "shortEn": "AI Operations",
        "level": "NCP",
        "track": "AI 运维",
        "official": {"questions": 30, "durationMin": 120, "passPct": 70,
                    "note": "官方形式是 30 道选择题加 3 场动手实验，实验部分与题目部分各占结果的一半"},
        "blueprint": "official",
        "domains": [
            ("installation-deployment", "Installation and Deployment", "安装与部署", 31),
            ("administration", "Administration", "管理", 23),
            ("workload-management", "Workload Management", "工作负载管理", 23),
            ("troubleshooting-optimization", "Troubleshooting and Optimization", "故障排查与优化", 23),
        ],
    },
    "ncp-ousd": {
        "code": "NCP-OUSD",
        "name": "NVIDIA Certified Professional: OpenUSD Development",
        "nameZh": "NVIDIA 认证专家：OpenUSD 开发",
        "shortZh": "OpenUSD 开发",
        "shortEn": "OpenUSD Development",
        "level": "NCP",
        "track": "OpenUSD / 3D",
        "official": {"questions": 65, "durationMin": 90, "passPct": 70},
        # NVIDIA 没有公布这一科的域权重，按题库里各域的题量分布折算
        "blueprint": "bank",
        "domains": [
            ("composition", "Composition", "组合", None),
            ("content-aggregation", "Content Aggregation", "内容聚合", None),
            ("customizing-usd", "Customizing USD", "定制 USD", None),
            ("data-exchange", "Data Exchange", "数据交换", None),
            ("data-modeling", "Data Modeling", "数据建模", None),
            ("debugging", "Debugging and Troubleshooting", "调试与排障", None),
            ("pipeline-development", "Pipeline Development", "流水线开发", None),
            ("visualization", "Visualization", "可视化", None),
        ],
    },
}

# 采集数据里出现的知识域写法 → 上表的知识域 id
DOMAIN_ALIASES = {
    "essential ai knowledge": "essential-ai-knowledge",
    "essential ai knowledge（ai 基础知识）": "essential-ai-knowledge",
    "ai knowledge": "essential-ai-knowledge",
    "ai infrastructure": "ai-infrastructure",
    "ai operations": "ai-operations",
    "core machine learning and ai knowledge": "core-ml-knowledge",
    "software development": "software-development",
    "experimentation": "experimentation",
    "data analysis and visualization": "data-analysis",
    "data analysis": "data-analysis",
    "trustworthy ai": "trustworthy-ai",
    "multimodal data": "multimodal-data",
    "performance optimization": "performance-optimization",
    "agent architecture and design": "agent-architecture",
    "agent development": "agent-development",
    "evaluation and tuning": "evaluation-tuning",
    "deployment and scaling": "deployment-scaling",
    "cognition, planning, and memory": "cognition-memory",
    "knowledge integration and data handling": "knowledge-integration",
    "nvidia platform implementation": "nvidia-platform",
    "operations, monitoring, and maintenance": "operations-monitoring",
    "security, ethics, and compliance": "security-ethics",
    "system and server bring-up": "system-bringup",
    "physical layer management": "physical-layer",
    "control plane installation and configuration": "control-plane",
    "cluster test and verification": "cluster-verification",
    "troubleshoot and optimize": "troubleshooting",
    "ai data center design and optimization": "dc-design",
    "nvidia spectrum networking": "spectrum-networking",
    "spectrum-x configuration, optimization, security, and troubleshooting": "spectrum-networking",
    "nvidia infiniband networking": "infiniband-networking",
    "infiniband configuration, optimization, security, and troubleshooting": "infiniband-networking",
    "kubernetes integration": "kubernetes-integration",
    "troubleshooting tools": "troubleshooting-tools",
    "automation and configuration": "automation-config",
    "installation and deployment": "installation-deployment",
    "administration": "administration",
    "workload management": "workload-management",
    "troubleshooting and optimization": "troubleshooting-optimization",
    "composition": "composition",
    "content aggregation": "content-aggregation",
    "customizing usd": "customizing-usd",
    "data exchange": "data-exchange",
    "data modeling": "data-modeling",
    "debugging and troubleshooting": "debugging",
    "pipeline development": "pipeline-development",
    "visualization": "visualization",
}

# 采集来源 → 页面上的中英文名字（app.js 里的 i18n 键用同样的 id）
SOURCES = {
    "examtopics": ("ExamTopics 题目页", "ExamTopics question pages"),
    "discussion": ("ExamTopics 社区讨论帖", "ExamTopics community threads"),
    "exam4success": ("exam4success 免费题库", "exam4success free bank"),
    "seekexams": ("seekexams 免费题库", "seekexams free bank"),
    "examtopicshub": ("examtopicshub 免费题库", "examtopicshub free bank"),
    "examstrack": ("examstrack 免费题库", "examstrack free bank"),
    "solution2pass": ("solution2pass 免费题库", "solution2pass free bank"),
    "github": ("GitHub 开源题库", "GitHub open-source bank"),
    "seed": ("自编题（按官方考纲）", "Self-written from the blueprint"),
}

GENERAL_DOMAIN = ("general", "General Practice", "综合练习")

# ---------------------------------------------------------------- 隐私处理

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")
PHONE_RE = re.compile(r"(?<![0-9])1[3-9][0-9]{9}(?![0-9])")


def redact(text: str) -> str:
    """抹掉正文里的邮箱与手机号：仓库在 GitHub 上是公开的。"""
    text = EMAIL_RE.sub("[邮箱已隐去]", text)
    return PHONE_RE.sub("[号码已隐去]", text)


# ---------------------------------------------------------------- 题目整理


def pick_domain(raw: str | None, domain_ids: set[str]) -> str:
    """把采集数据里的知识域写法对上官方考纲的知识域 id。"""
    if not raw:
        return ""
    key = raw.strip().lower()
    alias = DOMAIN_ALIASES.get(key)
    if alias and alias in domain_ids:
        return alias
    return ""


def letters_to_indexes(answer: str | None, count: int) -> list[int]:
    """'C' → [2]，'A,D' → [0,3]。"""
    out = []
    for ch in (answer or "").upper():
        if ch in LETTERS[:count] and (LETTERS.index(ch) not in out):
            out.append(LETTERS.index(ch))
    return out


def best_comment(question: dict) -> str:
    """社区讨论帖里赞数最高的一条回答，当作原站没有解析时的补充说明。"""
    best = ""
    best_votes = -1
    for thread in question.get("threads") or []:
        for comment in thread.get("comments") or []:
            votes = comment.get("upvotes") or 0
            text = (comment.get("text") or "").strip()
            if text and votes > best_votes:
                best_votes = votes
                best = text
    return best


def build_question(raw: dict, seq: int, domain_ids: set[str]) -> dict:
    options = raw.get("options") or []
    texts = [o.get("text") or "" for o in options]
    texts_zh = [(o.get("text_zh") or o.get("text") or "") for o in options]
    correct = [i for i, o in enumerate(options) if o.get("correct")]
    if not correct:
        correct = letters_to_indexes(raw.get("answer"), len(texts))

    domain = pick_domain(raw.get("domain"), domain_ids) or pick_domain(raw.get("topic"), domain_ids)
    answer_letters = ", ".join(LETTERS[i] for i in correct)

    source = raw.get("source") or "examtopics"
    if source not in SOURCES:
        source = "examtopics"

    # 解析：原站有就用原站的；没有就用社区讨论里赞数最高的那条；再没有就写清楚出处
    explanation = (raw.get("explanation") or "").strip()
    explanation_zh = (raw.get("explanation_zh") or "").strip()
    comment = best_comment(raw)
    if not explanation and comment:
        explanation = comment
    if not explanation:
        explanation = (
            "The published answer key for this item is %s. The source page carries no written "
            "explanation, so read the community discussion linked below." % answer_letters
        )
    if not explanation_zh:
        answer_text = (raw.get("answer_text_zh") or "").strip()
        if answer_text:
            explanation_zh = "参考答案：%s（%s）。原题未附中文解析，可在「来源」里看社区讨论。" % (
                answer_letters, answer_text)
        else:
            explanation_zh = "参考答案：%s。原题未附中文解析，可在「来源」里看社区讨论。" % answer_letters

    return {
        "id": seq,
        "domain": domain or GENERAL_DOMAIN[0],
        "topic": (raw.get("topic") or "").strip(),
        "q": (raw.get("stem") or "").strip(),
        "qZh": (raw.get("stem_zh") or "").strip(),
        "o": texts,
        "oZh": texts_zh,
        "a": correct,
        "multi": len(correct) > 1,
        "e": explanation,
        "eZh": explanation_zh,
        "src": source,
        "url": (raw.get("url") or "").strip(),
        "discussion": (raw.get("discussion") or "").strip(),
    }


def seed_questions(exam_id: str, domains: list[dict]) -> list[dict]:
    """自编种子题（按官方考纲写的）：知识域 id 换成新考纲里的写法。"""
    seed_file = DATA / "seed.json"
    if not seed_file.is_file():
        return []
    seed = json.loads(seed_file.read_text(encoding="utf-8"))
    out = []
    for exam in seed.get("exams", []):
        if exam.get("id") != exam_id:
            continue
        rename = {"ai-knowledge": "essential-ai-knowledge"}
        for q in exam.get("questions", []):
            item = dict(q)
            item["domain"] = rename.get(item.get("domain"), item.get("domain"))
            item["src"] = "seed"
            item["topic"] = ""
            item["url"] = ""
            item["discussion"] = ""
            out.append(item)
    return out


def distribute_weights(domains: list[dict], counts: dict[str, int]) -> None:
    """官方没公布权重的那一科：按题库里各知识域的题量折算，合计 100。"""
    total = sum(counts.get(d["id"], 0) for d in domains)
    if not total:
        for d in domains:
            d["weight"] = 0
        return
    rest = 100
    for d in domains[:-1]:
        w = round(100 * counts.get(d["id"], 0) / total)
        d["weight"] = w
        rest -= w
    domains[-1]["weight"] = rest


def normalize_weights(domains: list[dict]) -> None:
    """考纲只列了一部分域（合计不到 100%）：按最大余数法归一到 100。"""
    total = sum(d["weight"] or 0 for d in domains)
    if not total:
        return
    exact = [(d["id"], 100 * (d["weight"] or 0) / total) for d in domains]
    floors = {gid: int(value) for gid, value in exact}
    rest = 100 - sum(floors.values())
    order = sorted(exact, key=lambda item: item[1] - floors[item[0]], reverse=True)
    for gid, _ in order[:rest]:
        floors[gid] += 1
    for d in domains:
        d["weight"] = floors[d["id"]]


# ---------------------------------------------------------------- 指南


GUIDE_META_RE = re.compile(
    r"^>\s*来源：(?P<meta>.+)$",
    re.M,
)
REPO_RE = re.compile(r"`(?P<repo>[^`]+)`")
FILE_RE = re.compile(r"`(?P<file>[^`]+)`")
URL_RE = re.compile(r"\[原文链接\]\((?P<url>[^)]+)\)")
LANG_RE = re.compile(r"语言：(?P<lang>[^·]+)")
CERT_RE = re.compile(r"^##\s+(?P<code>(?:NCA|NCP)-[A-Z]+)\s+·\s*(?P<name>.+)$")
GROUP_RE = re.compile(r"^###\s+(?P<group>.+?)（(?P<n>\d+)\s*篇）\s*$")
GUIDE_RE = re.compile(r"^####\s+(?P<title>.+?)\s*$")


def starts_guide(lines: list[str], index: int) -> bool:
    """`####` 标题后面紧跟「> 来源：…」的才是新的一篇指南，否则只是正文里的小标题。"""
    for line in lines[index + 1: index + 4]:
        if not line.strip():
            continue
        return bool(GUIDE_META_RE.match(line))
    return False


def parse_guides(markdown: str) -> dict[str, dict]:
    """把《学习指南汇总.md》拆成 {code: {name, groups: [{group, guides: [...]}]}}。"""
    lines = markdown.split("\n")
    certs: dict[str, dict] = {}
    cur_cert = None
    cur_group = None
    cur_guide = None

    def flush_guide():
        nonlocal cur_guide
        if cur_guide is not None and cur_cert is not None:
            cur_cert["groups"][-1]["guides"].append(cur_guide)
            cur_guide = None

    for i, line in enumerate(lines):
        m = CERT_RE.match(line)
        if m:
            flush_guide()
            cur_cert = {"code": m.group("code"), "name": m.group("name").strip(), "groups": []}
            certs[m.group("code")] = cur_cert
            cur_group = None
            continue
        if cur_cert is None:
            continue
        m = GROUP_RE.match(line)
        if m:
            flush_guide()
            cur_group = {"group": m.group("group").strip(), "guides": []}
            cur_cert["groups"].append(cur_group)
            continue
        m = GUIDE_RE.match(line)
        if m and starts_guide(lines, i):
            flush_guide()
            if cur_group is None:
                cur_group = {"group": "", "guides": []}
                cur_cert["groups"].append(cur_group)
            cur_guide = {"title": m.group("title").strip(), "meta": "", "body": []}
            continue
        if cur_guide is not None:
            if cur_guide["meta"] == "" and line.startswith(">"):
                cur_guide["meta"] = line
            else:
                cur_guide["body"].append(line)

    flush_guide()
    return certs


def guide_meta(meta: str) -> dict:
    code_spans = FILE_RE.findall(meta)
    url = URL_RE.search(meta)
    lang = LANG_RE.search(meta)
    out = {
        "repo": code_spans[0] if code_spans else "",
        "file": code_spans[1] if len(code_spans) > 1 else "",
        "url": "",
        "lang": "en",
        "translated": False,
    }
    if url:
        out["url"] = url.group("url")
    if lang:
        text = lang.group("lang").strip()
        out["lang"] = "zh" if text.startswith("中文") else "en"
        out["translated"] = "中译" in text
    return out


# ---------------------------------------------------------------- 主流程


def write_js(path: Path, name: str, payload: dict, comment: str) -> None:
    path.write_text(
        "/* %s\n   由 tools/build_data.py 生成，请勿手工改动。 */\nwindow.%s = %s;\n"
        % (comment, name, json.dumps(payload, ensure_ascii=False)),
        encoding="utf-8",
    )


def main() -> None:
    raw = json.loads((RAW / "nvidia_cert_data.json").read_text(encoding="utf-8"))
    seed = json.loads((DATA / "seed.json").read_text(encoding="utf-8")) if (DATA / "seed.json").is_file() else {}
    guide_md = (RAW / "学习指南汇总.md").read_text(encoding="utf-8")

    guide_certs = parse_guides(guide_md)
    guide_meta_index: dict[tuple[str, str], dict] = {}
    guide_file_index: dict[tuple[str, str, str], dict] = {}
    for cert in raw:
        for g in cert.get("guides", []):
            guide_meta_index[(cert["code"], g.get("title", "").strip())] = g
            guide_file_index[(cert["code"], g.get("repo", ""), g.get("file", ""))] = g

    exams = []
    for cert in raw:
        slug = cert["slug"]
        blueprint = BLUEPRINTS.get(slug)
        if not blueprint:
            raise SystemExit("没有为 %s 准备考纲" % cert["code"])
        domains = [
            {"id": d[0], "en": d[1], "zh": d[2], "weight": d[3]}
            for d in blueprint["domains"]
        ]
        domain_ids = {d["id"] for d in domains}

        questions = []
        for raw_q in cert.get("questions", []):
            questions.append(build_question(raw_q, len(questions) + 1, domain_ids))
        seed_qs = seed_questions(slug, domains)
        for q in seed_qs:
            q["id"] = len(questions) + 1
            questions.append(q)

        counts: dict[str, int] = {}
        for q in questions:
            counts[q["domain"]] = counts.get(q["domain"], 0) + 1
        if blueprint["blueprint"] == "bank":
            distribute_weights(domains, counts)
        elif blueprint["blueprint"] == "partial":
            normalize_weights(domains)
        # 落在考纲之外（采集数据没写知识域）的题目归到「综合练习」，权重为 0
        if counts.get(GENERAL_DOMAIN[0]):
            domains.append({"id": GENERAL_DOMAIN[0], "en": GENERAL_DOMAIN[1], "zh": GENERAL_DOMAIN[2], "weight": 0})
        used = sum(d["weight"] for d in domains)
        if used != 100:
            raise SystemExit("%s 的知识域权重合计是 %d，不是 100" % (cert["code"], used))

        official = dict(blueprint["official"])
        duration = official.get("durationMin") or 60
        count = official.get("questions") or 50
        exams.append({
            "id": slug,
            "code": blueprint["code"],
            "name": blueprint["name"],
            "nameZh": blueprint["nameZh"],
            "shortZh": blueprint["shortZh"],
            "shortEn": blueprint["shortEn"],
            "level": blueprint["level"],
            "track": blueprint["track"],
            "durationMinPerQuestion": round(duration / float(count), 2),
            "passPct": official.get("passPct") or 70,
            "official": official,
            "blueprint": blueprint["blueprint"],
            "bankTotal": cert.get("total_questions"),
            "collected": len(questions),
            "domains": domains,
            "questions": questions,
        })

    bank = {
        "version": "2026-11-27",
        "note": "题库来自 ExamTopics 等公开免费题库与 GitHub 开源备考仓库（采集过程见 docs/采集说明.md），"
                "仅用于学习自测，不是官方真题。",
        "sources": [
            {"id": sid, "zh": zh, "en": en}
            for sid, (zh, en) in SOURCES.items()
        ],
        "exams": exams,
    }
    (DATA / "bank.json").write_text(
        json.dumps(bank, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    write_js(DATA / "bank.js", "NVIDIA_BANK", bank, "题库数据。由 tools/build_data.py 生成，与 bank.json 内容一致。")

    # ---- 指南索引 + 按认证拆分的正文
    guides = []
    guide_dir = DOCS / "guides"
    guide_dir.mkdir(parents=True, exist_ok=True)
    for cert in raw:
        code = cert["code"]
        parsed = guide_certs.get(code, {"name": cert.get("cn", ""), "groups": []})
        items = []
        body_parts = ["# %s · %s\n" % (code, parsed["name"]), ""]
        for group in parsed["groups"]:
            body_parts.append("## %s\n" % group["group"])
            body_parts.append("")
            for g in group["guides"]:
                meta = guide_meta(g["meta"])
                extra = guide_meta_index.get((code, g["title"])) or guide_file_index.get(
                    (code, meta["repo"], meta["file"])) or {}
                item = {
                    "title": g["title"],
                    "group": group["group"],
                    "kind": extra.get("kind") or "note",
                    "lang": meta["lang"],
                    "translated": meta["translated"],
                    "repo": meta["repo"],
                    "file": meta["file"],
                    "url": meta["url"],
                    "chars": extra.get("chars") or 0,
                }
                items.append(item)
                body_parts.append("### %s\n" % g["title"])
                body_parts.append("")
                body_parts.append(g["meta"].strip())
                body_parts.append("")
                body_parts.extend(g["body"])
                body_parts.append("")
            body_parts.append("")
        text = redact("\n".join(body_parts))
        (guide_dir / ("%s.md" % code)).write_text(text, encoding="utf-8")
        guides.append({
            "code": code,
            "slug": cert["slug"],
            "name": cert.get("cn", ""),
            "count": len(items),
            "guides": items,
        })

    guide_payload = {
        "version": "2026-11-27",
        "note": "学习指南索引：来自 GitHub 上的公开备考仓库，正文见 docs/guides/<代码>.md。",
        "certs": guides,
    }
    (DATA / "guides.json").write_text(
        json.dumps(guide_payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    write_js(DATA / "guides.js", "NVIDIA_GUIDES", guide_payload,
             "学习指南索引。由 tools/build_data.py 生成，与 guides.json 内容一致。")

    # ---- 采集说明
    DOCS.mkdir(parents=True, exist_ok=True)
    notes = (RAW / "采集说明.md").read_text(encoding="utf-8")
    (DOCS / "采集说明.md").write_text(redact(notes), encoding="utf-8")

    total_q = sum(len(e["questions"]) for e in exams)
    total_g = sum(g["count"] for g in guides)
    print("题库：%d 项认证 / %d 道题" % (len(exams), total_q))
    for e in exams:
        print("  %-10s %4d 题 / %2d 个知识域 / 指南 %d 篇"
              % (e["code"], len(e["questions"]), len(e["domains"]),
                 next((g["count"] for g in guides if g["code"] == e["code"]), 0)))
    print("学习指南：%d 篇，已拆成 %d 个文件" % (total_g, len(guides)))


if __name__ == "__main__":
    main()
