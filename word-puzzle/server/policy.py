"""谁能做什么（动作级）。所有「需要权限」的判断都从这里过；「能看到哪些学生 / 题库」这种按数据划分的范围在 server/tenancy.py。

角色：
* 超级管理员（role=admin）：什么都能做，包括加老师、把题库 / 学生共享或分配给别的老师、恢复删除、看审计记录。
* 老师（role=teacher）：能用所有管理功能，但只对自己名下的学生、题库、词表生效（范围由 tenancy 决定）。
* 学生：只能做自己的事。
"""
from __future__ import annotations

# 动作名：<对象>.<操作>。调用处用字符串，新增动作只要在这里登记。
ADMIN_ONLY = {               # 老师和超级管理员都能做（范围由 tenancy 限制）
    "admin",                 # 泛指「管理功能」（账号、名单、访问记录、导出等）
    "bank.create", "bank.edit", "bank.delete", "bank.tags",
    "material.upload", "material.read", "material.delete",
    "user.manage", "visits.read",
    "records.read_all",      # 看名下所有人的成绩 / 进度
}
SUPER_ONLY = {               # 只有超级管理员
    "tenants.manage",        # 加老师、共享 / 分配、恢复删除、看审计记录、看已删除的
}
STAFF_ROLES = ("admin", "teacher")


def allow(user: dict | None, action: str, resource: dict | None = None) -> bool:
    """user 为 None = 没登录。resource 例如 {"bank_id": 3} / {"class_name": "一班"} / {"subject": "chemistry"}。"""
    if not user:
        return False
    role = user.get("role")
    if role == "admin":
        return True
    if role == "teacher":
        return action not in SUPER_ONLY
    return action not in ADMIN_ONLY and action not in SUPER_ONLY
