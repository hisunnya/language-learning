"""学科 / 功能模块的登记表：化学、物理、每日话题、无线电考试也用同一套登录、访问记录和成绩接口。

约定（给将来接入的模块）：
* 页面：静态文件，放在 ``/<path>/`` 下，页头用共享的 ``/shared/module-header.js``；
  要访问记录就引入 ``/word-puzzle/js/tracker.js``（它只认 wp-base 元标签，不依赖词境的任何页面脚本）。
* 登录：向 ``/word-puzzle/api/auth/me`` 问当前用户（同一个 Cookie，同一套账号）。
* 成绩 / 进度：``POST /api/records``，``{"subject": 模块 id, "kind": "quiz", "payload": {...}}``，
  ``GET /api/records?subject=…`` 取（学生只看得到自己的，老师看全部）。
* 权限：``server/policy.py`` 的 ``allow(user, action, resource)``，资源里写 ``subject``，将来按学科给老师分权限。

``enabled`` 现在是「这个学科的成绩可以存进数据库」的开关：四个静态模块从 2026-11-22 起
也开始往 ``/api/records`` 上报练习小结和访问记录，所以总后台（``/backends/``）才不是空的。
"""
from __future__ import annotations

MODULES = [
    {"id": "lexica", "zh": "词境", "en": "Lexica", "path": "/word-puzzle/", "enabled": True},
    {"id": "topics", "zh": "每日话题", "en": "Daily Topics", "path": "/topics/", "enabled": True},
    {"id": "ham", "zh": "无线电执照", "en": "Ham Exam", "path": "/ham/", "enabled": True},
    {"id": "chemistry", "zh": "化学探秘", "en": "Chem Quest", "path": "/chemistry/", "enabled": True},
    {"id": "physics", "zh": "物理探秘", "en": "Phys Quest", "path": "/physics/", "enabled": True},
    {"id": "nvidia", "zh": "NVIDIA 认证", "en": "NVIDIA Exam", "path": "/nvidia-exam/", "enabled": True},
]


def enabled_ids() -> set[str]:
    return {m["id"] for m in MODULES if m["enabled"]}


def listing() -> list[dict]:
    return [dict(m) for m in MODULES]
