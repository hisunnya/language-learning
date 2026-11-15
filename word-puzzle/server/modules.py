"""学科 / 功能模块的登记表：以后把化学、物理、每日话题、无线电考试也放到学生版里（走 Tailscale）时，
只要在这里加一项并把页面放进去，就自动有同一套登录、访问记录和成绩接口，不用再改后端。

约定（给将来接入的模块）：
* 页面：静态文件，放在 ``/<path>/`` 下，页头用共享的 ``/shared/module-header.js``；
  要访问记录就引入 ``/word-puzzle/js/tracker.js``（它只认 wp-base 元标签，不依赖词境的任何页面脚本）。
* 登录：向 ``/word-puzzle/api/auth/me`` 问当前用户（同一个 Cookie，同一套账号）。
* 成绩 / 进度：``POST /api/records``，``{"subject": 模块 id, "kind": "quiz", "payload": {...}}``，
  ``GET /api/records?subject=…`` 取（学生只看得到自己的，老师看全部）。
* 权限：``server/policy.py`` 的 ``allow(user, action, resource)``，资源里写 ``subject``，将来按学科给老师分权限。
"""
from __future__ import annotations

MODULES = [
    {"id": "lexica", "zh": "词境", "en": "Lexica", "path": "/word-puzzle/", "enabled": True},
    {"id": "topics", "zh": "每日话题", "en": "Daily Topics", "path": "/topics/", "enabled": False},
    {"id": "ham", "zh": "无线电执照", "en": "Ham Exam", "path": "/ham/", "enabled": False},
    {"id": "chemistry", "zh": "化学探秘", "en": "Chem Quest", "path": "/chemistry/", "enabled": False},
    {"id": "physics", "zh": "物理探秘", "en": "Phys Quest", "path": "/physics/", "enabled": False},
]


def enabled_ids() -> set[str]:
    return {m["id"] for m in MODULES if m["enabled"]}


def listing() -> list[dict]:
    return [dict(m) for m in MODULES]
