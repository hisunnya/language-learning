"""谁能做什么：所有「需要权限」的判断都从这里过，以后加「多个老师、各管各的班级 / 题库 / 学科」只改这一个文件。

现在的规则很简单：老师（role=admin）什么都能做，学生只能做自己的事。
将来的规则（见 docs/路线图.md）：老师带一组「范围」——班级、题库、学科——``allow`` 按资源里的
``class_name`` / ``bank_id`` / ``subject`` 去对照；调用处已经把资源传进来了，不用再改调用处。
"""
from __future__ import annotations

# 动作名：<对象>.<操作>。调用处用字符串，新增动作只要在这里登记。
ADMIN_ONLY = {
    "admin",                 # 泛指「管理功能」（账号、名单、访问记录、导出等）
    "bank.create", "bank.edit", "bank.delete", "bank.tags",
    "material.upload", "material.read", "material.delete",
    "user.manage", "visits.read",
    "records.read_all",      # 看所有人的成绩 / 进度
}


def allow(user: dict | None, action: str, resource: dict | None = None) -> bool:
    """user 为 None = 没登录。resource 例如 {"bank_id": 3} / {"class_name": "一班"} / {"subject": "chemistry"}。"""
    if not user:
        return False
    if user.get("role") == "admin":
        return True            # 将来：在这里按 teacher_scopes 对照 resource
    return action not in ADMIN_ONLY
