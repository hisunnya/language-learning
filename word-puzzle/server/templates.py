"""给老师下载的模板：词表（题库工作台上传用）和学生名单（账号管理导入用）。

表头用的正是解析时认的列名（materials.py 的 EN_KEYS / CN_KEYS…，roster.py 的 ALIASES），按模板填就一定能识别。
中文界面下载中文表头，英文界面下载英文表头，两种服务器都认。每个 Excel 模板还带一页填写说明。
"""
from __future__ import annotations

import csv
import io

from . import xlsx

WORDLIST = {
    "zh": {
        "header": ["单元", "英文", "中文", "音标", "词性"],
        "rows": [["Unit 1", "apple", "苹果", "/ˈæpəl/", "n."],
                 ["", "take care of", "照顾；照看", "", "phr."],
                 ["Unit 2", "eradicate", "根除；消灭", "", "v."],
                 ["", "staple food", "主食", "", "phr."]],
        "notes_title": "填写说明",
        "notes": [
            "词表模板 · 填写说明",
            "1. 每行一个单词或短语。「英文」「中文」两列必须填；「音标」「词性」可以空着。",
            "2. 「单元」写这个词属于哪个单元（例如 Unit 1）。同一个单元只在第一行写也可以，下面空着就算和上一行同一个单元。",
            "3. 一个词有几个意思，在「中文」里用「；」隔开。",
            "4. 不要改表头、不要合并单元格；第一行之后只写词，不写标题或说明。",
            "5. 示例行可以直接删掉或改成自己的内容。",
            "6. 保存成 Excel（.xlsx）或 CSV（UTF-8）后，在「题库工作台 → 新建题库 → 上传新词表」里上传。",
        ],
    },
    "en": {
        "header": ["unit", "english", "chinese", "ipa", "pos"],
        "rows": [["Unit 1", "apple", "苹果", "/ˈæpəl/", "n."],
                 ["", "take care of", "照顾；照看", "", "phr."],
                 ["Unit 2", "eradicate", "根除；消灭", "", "v."],
                 ["", "staple food", "主食", "", "phr."]],
        "notes_title": "Notes",
        "notes": [
            "Word list template · how to fill it in",
            "1. One word or phrase per row. The english and chinese columns are required; ipa and pos may stay empty.",
            "2. unit is the unit the word belongs to (e.g. Unit 1). You may write it only on the first row of a unit; an empty cell means the same unit as the row above.",
            "3. Separate several meanings in the chinese column with ；",
            "4. Do not change the header or merge cells; below the first row write only words, no titles or notes.",
            "5. Delete the sample rows or overwrite them with your own.",
            "6. Save as Excel (.xlsx) or CSV (UTF-8) and upload it under Word banks → New word bank → Upload a new list.",
        ],
    },
}

ROSTER = {
    "zh": {
        "header": ["学号", "姓名", "班级", "学院", "院系", "初始密码", "标签"],
        "rows": [["2026001", "张三", "一班", "外国语学院", "英语系", "", "大学英语BI"],
                 ["2026002", "李四", "一班", "外国语学院", "英语系", "", "大学英语BI, 测试"]],
        "notes_title": "填写说明",
        "notes": [
            "学生名单模板 · 填写说明",
            "1. 每行一个学生。「学号」「姓名」必须填，学号同时是登录名。",
            "2. 「班级」「学院」「院系」可以空着；积分榜按班级分，建议填上班级。",
            "3. 「初始密码」空着就自动生成（导入后可以下载初始密码表）；学生第一次登录要先改密码。",
            "4. 「标签」决定学生能看到哪些题库：题库和学生有同一个标签就能看到；多个标签用逗号隔开。",
            "5. 手机号等其他列不会被保存。学号一列已经设成文本格式，长学号不会变成科学计数法。",
            "6. 保存成 Excel（.xlsx）或 CSV 后，在「账号管理 → 导入名单」里上传。",
        ],
    },
    "en": {
        "header": ["student_no", "name", "class", "college", "department", "password", "tags"],
        "rows": [["2026001", "Zhang San", "Class 1", "School of Foreign Languages", "English", "", "College English BI"],
                 ["2026002", "Li Si", "Class 1", "School of Foreign Languages", "English", "", "College English BI, Test"]],
        "notes_title": "Notes",
        "notes": [
            "Student roster template · how to fill it in",
            "1. One student per row. student_no and name are required; the student number is also the sign-in name.",
            "2. class, college and department may stay empty; leaderboards are per class, so filling in the class is recommended.",
            "3. Leave password empty to generate one (you can download the initial passwords after the import); students change it at the first sign-in.",
            "4. tags decide which word banks a student sees: a student sees a bank that has one of the same tags. Separate several tags with commas.",
            "5. Other columns such as phone numbers are not stored. The student_no column is formatted as text so long numbers stay intact.",
            "6. Save as Excel (.xlsx) or CSV and upload it under Accounts → Import roster.",
        ],
    },
}

KINDS = {"wordlist": WORDLIST, "roster": ROSTER}
NAMES = {("wordlist", "zh"): "词表模板", ("wordlist", "en"): "word-list-template",
         ("roster", "zh"): "学生名单模板", ("roster", "en"): "roster-template"}


def build(kind: str, fmt: str, lang: str = "zh") -> tuple[str, bytes, str]:
    """返回 (文件名, 内容, Content-Type)。kind：wordlist / roster；fmt：xlsx / csv。"""
    if kind not in KINDS or fmt not in ("xlsx", "csv"):
        raise KeyError(kind)
    lang = "en" if lang == "en" else "zh"
    spec = KINDS[kind][lang]
    rows = [spec["header"]] + spec["rows"]
    name = "%s.%s" % (NAMES[(kind, lang)], fmt)
    if fmt == "csv":
        buf = io.StringIO()
        csv.writer(buf, lineterminator="\r\n").writerows(rows)
        return name, ("﻿" + buf.getvalue()).encode("utf-8"), "text/csv; charset=utf-8"
    data = xlsx.build([(("词表" if kind == "wordlist" else "名单") if lang == "zh" else ("Words" if kind == "wordlist" else "Roster"), rows),
                       (spec["notes_title"], [[line] for line in spec["notes"]])],
                      text_columns=1 if kind == "roster" else 0)
    return name, data, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
