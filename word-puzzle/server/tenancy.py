"""多位老师：底层一份数据，上层按老师划分「谁能看到、谁能管什么」。

角色
----
* **超级管理员**（``role='admin'``）：什么都看得到（包括别的老师的、已删除的），能加老师、把题库 / 学生共享或分配给任何老师、恢复删除。
* **老师**（``role='teacher'``）：只看得到、只管得了自己名下的学生（``teacher_students``）、题库（自己建的 ``banks.owner_id``、
  别人共享过来的 ``teacher_banks``、所有人共用的内置题库 ``owner_id IS NULL``）、自己上传的词表，以及这些学生的成绩和访问记录。
* **学生**：看得到的题库 = 某位老师给他和这个题库打了同一个标签（标签按老师分开，见 db.py 的 user_tags / bank_tags）。
* **家庭版访客**（内网入口、不登录）：内置题库 + 超级管理员的题库；成绩只有没登录时按设备记的那些。
* 没有账号体系的家庭版（``auth is None``）：等同超级管理员，标签记在 teacher_id = 0 下。

删除一律是软删除：打上 ``deleted_at``，老师和学生都看不到，超级管理员能看到并恢复。
老师「删除」别人共享过来的题库 / 也挂在别的老师名下的学生，只是从自己名下移走，不影响别人。

SQL 片段都只拼常量和 ``?`` 占位符，参数另外传，不拼用户输入。
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass

from .db import Database

ALL, SUPER, TEACHER, STUDENT, GUEST, NOBODY = "all", "super", "teacher", "student", "guest", "nobody"


@dataclass(frozen=True)
class Scope:
    kind: str
    user_id: int | None = None

    @property
    def staff(self) -> bool:            # 能用管理功能
        return self.kind in (ALL, SUPER, TEACHER)

    @property
    def everything(self) -> bool:       # 什么都看得到
        return self.kind in (ALL, SUPER)

    @property
    def tag_teacher(self) -> int:       # 这个人打的标签记在谁名下
        return int(self.user_id) if self.kind in (SUPER, TEACHER) and self.user_id else 0


def scope_for(auth_enabled: bool, user: dict | None, guest: bool) -> Scope:
    if not auth_enabled:
        return Scope(ALL)
    if user:
        role = user.get("role")
        if role == "admin":
            return Scope(SUPER, user["id"])
        if role == "teacher":
            return Scope(TEACHER, user["id"])
        return Scope(STUDENT, user["id"])
    return Scope(GUEST) if guest else Scope(NOBODY)


# ------------------------------------------------------------------ 题库

def bank_where(scope: Scope, include_deleted: bool = False) -> tuple[str, tuple]:
    """这个人能看到的题库（给 ``SELECT … FROM banks b WHERE …`` 用）。"""
    alive = "1=1" if include_deleted and scope.everything else "b.deleted_at=0"
    if scope.everything:
        return alive, ()
    if scope.kind == TEACHER:
        return (alive + " AND (b.owner_id IS NULL OR b.owner_id=? OR b.id IN "
                "(SELECT bank_id FROM teacher_banks WHERE teacher_id=?))", (scope.user_id, scope.user_id))
    if scope.kind == STUDENT:
        return (alive + " AND EXISTS (SELECT 1 FROM bank_tags bt JOIN user_tags ut "
                "ON ut.tag=bt.tag AND ut.teacher_id=bt.teacher_id "
                "WHERE bt.bank_id=b.id AND ut.user_id=? "
                "AND (bt.teacher_id=0 OR bt.teacher_id IN (SELECT id FROM users WHERE deleted_at=0 AND disabled=0)))",
                (scope.user_id,))
    if scope.kind == GUEST:
        return alive + " AND (b.owner_id IS NULL OR b.owner_id IN (SELECT id FROM users WHERE role='admin'))", ()
    return "0", ()


def list_banks(db: Database, scope: Scope, include_deleted: bool = False) -> list[dict]:
    where, args = bank_where(scope, include_deleted)
    tag_teacher = scope.tag_teacher if scope.staff else -1      # 学生、访客不需要看到标签
    banks = db.list_banks(where, args, tag_teacher=tag_teacher)
    if scope.kind == TEACHER:
        for b in banks:
            b["relation"] = relation_to_bank(db, scope, b)
    return banks


def bank_visible(db: Database, scope: Scope, bank: dict | None) -> bool:
    if not bank:
        return False
    where, args = bank_where(scope)             # 删掉的谁都打不开（超管在「已删除」里恢复）
    return db.one("SELECT 1 FROM banks b WHERE b.id=? AND " + where, (bank["id"], *args)) is not None


def relation_to_bank(db: Database, scope: Scope, bank: dict) -> str:
    """owner = 自己建的 / 超管、shared = 共享给自己的、system = 内置（所有人共用）、'' = 跟自己没关系。"""
    if scope.everything:
        return "owner"
    if scope.kind != TEACHER:
        return ""
    if bank.get("owner_id") == scope.user_id:
        return "owner"
    if db.one("SELECT 1 FROM teacher_banks WHERE teacher_id=? AND bank_id=?", (scope.user_id, bank["id"])):
        return "shared"
    if bank.get("owner_id") is None:
        return "system"
    return ""


def can_tag_bank(db: Database, scope: Scope, bank: dict | None) -> bool:
    """能不能给这个题库打（自己的）标签：自己建的、共享过来的、内置的都行。"""
    return bool(bank) and not bank.get("deleted_at") and relation_to_bank(db, scope, bank) in ("owner", "shared", "system")


def can_edit_bank(db: Database, scope: Scope, bank: dict | None) -> bool:
    """能不能改题库本身（分类）：自己建的才行；内置题库和共享过来的只有超管能改。"""
    return bool(bank) and relation_to_bank(db, scope, bank) == "owner"


# ------------------------------------------------------------------ 学生

def student_where(scope: Scope, col: str = "u.id", include_deleted: bool = False) -> tuple[str, tuple]:
    """这个人管得了的账号（给 ``… FROM users u WHERE …`` 用）。超管：所有人；老师：自己名下没删除的学生。"""
    if scope.everything:
        return ("1=1" if include_deleted else "u.deleted_at=0"), ()
    if scope.kind == TEACHER:
        return ("u.deleted_at=0 AND u.role='student' AND " + col +
                " IN (SELECT student_id FROM teacher_students WHERE teacher_id=?)"), (scope.user_id,)
    return "0", ()


def can_manage_user(db: Database, scope: Scope, user: dict | None) -> bool:
    if not user:
        return False
    if scope.everything:
        return True
    if scope.kind != TEACHER or user.get("role") != "student" or user.get("deleted_at"):
        return False
    return db.one("SELECT 1 FROM teacher_students WHERE teacher_id=? AND student_id=?",
                  (scope.user_id, user["id"])) is not None


def people_where(scope: Scope, col: str) -> tuple[str, tuple]:
    """成绩 / 访问记录 / 登录记录按人过滤：超管看全部；老师看自己名下的学生和自己；学生只看自己；访客只看没登录的。"""
    if scope.everything:
        return "1=1", ()
    if scope.kind == TEACHER:
        return ("(" + col + "=? OR " + col + " IN (SELECT ts.student_id FROM teacher_students ts "
                "JOIN users su ON su.id=ts.student_id WHERE ts.teacher_id=? AND su.deleted_at=0))"), (scope.user_id, scope.user_id)
    if scope.kind == STUDENT:
        return col + "=?", (scope.user_id,)
    if scope.kind == GUEST:
        return col + " IS NULL", ()
    return "0", ()


# ------------------------------------------------------------------ 词表

def material_where(scope: Scope, include_deleted: bool = False) -> tuple[str, tuple]:
    if scope.everything:
        return ("1=1" if include_deleted else "deleted_at=0"), ()
    if scope.kind == TEACHER:
        return "deleted_at=0 AND owner_id=?", (scope.user_id,)
    return "0", ()


def material_visible(db: Database, scope: Scope, mid: int) -> bool:
    where, args = material_where(scope)
    return db.one("SELECT 1 FROM materials WHERE id=? AND " + where, (mid, *args)) is not None


# ------------------------------------------------------------------ 审计

def audit(db: Database, actor: int | None, action: str, target_type: str = "", target_id: int | None = None,
          now: float | None = None, **detail) -> None:
    db.execute("INSERT INTO audit_log(ts, actor_id, action, target_type, target_id, detail) VALUES (?,?,?,?,?,?)",
               (int(now or time.time()), actor, action, target_type, target_id, json.dumps(detail, ensure_ascii=False)))


def audit_rows(db: Database, limit: int = 200) -> list[dict]:
    rows = db.query("SELECT a.*, u.name AS actor_name, u.student_no AS actor_no FROM audit_log a "
                    "LEFT JOIN users u ON u.id=a.actor_id ORDER BY a.id DESC LIMIT ?", (limit,))
    out = []
    for r in rows:
        d = dict(r)
        try:
            d["detail"] = json.loads(d["detail"] or "{}")
        except ValueError:
            d["detail"] = {}
        out.append(d)
    return out


# ------------------------------------------------------------------ 关系：共享、分配、移走

def link_student(db: Database, teacher_id: int, student_id: int, actor: int | None, now: float | None = None) -> bool:
    cur = db.execute("INSERT OR IGNORE INTO teacher_students(teacher_id, student_id, added_at, added_by) VALUES (?,?,?,?)",
                     (teacher_id, student_id, int(now or time.time()), actor))
    return cur.rowcount > 0


def unlink_student(db: Database, teacher_id: int, student_id: int) -> None:
    """从这位老师名下移走：连同这位老师给他打的标签（否则他还看得到这位老师开放的题库）。"""
    with db._tx() as conn:
        conn.execute("DELETE FROM teacher_students WHERE teacher_id=? AND student_id=?", (teacher_id, student_id))
        conn.execute("DELETE FROM user_tags WHERE teacher_id=? AND user_id=?", (teacher_id, student_id))


def student_teachers(db: Database, student_id: int) -> list[int]:
    return [r["teacher_id"] for r in db.query(
        "SELECT ts.teacher_id FROM teacher_students ts JOIN users t ON t.id=ts.teacher_id "
        "WHERE ts.student_id=? AND t.deleted_at=0 ORDER BY ts.teacher_id", (student_id,))]


def link_bank(db: Database, teacher_id: int, bank_id: int, actor: int | None, now: float | None = None) -> bool:
    cur = db.execute("INSERT OR IGNORE INTO teacher_banks(teacher_id, bank_id, added_at, added_by) VALUES (?,?,?,?)",
                     (teacher_id, bank_id, int(now or time.time()), actor))
    return cur.rowcount > 0


def unlink_bank(db: Database, teacher_id: int, bank_id: int) -> None:
    """不再共享给这位老师：连同这位老师在这个题库上打的标签（否则他的学生还看得到）。"""
    with db._tx() as conn:
        conn.execute("DELETE FROM teacher_banks WHERE teacher_id=? AND bank_id=?", (teacher_id, bank_id))
        conn.execute("DELETE FROM bank_tags WHERE teacher_id=? AND bank_id=?", (teacher_id, bank_id))


def move_bank(db: Database, bank_id: int, teacher_id: int) -> None:
    """分配（转给）：题库归这位老师所有。原来的主人如果是老师，失去这个题库（连同他的标签）；共享关系里多余的那一行去掉。"""
    bank = db.get_bank(bank_id)
    old = bank.get("owner_id") if bank else None
    with db._tx() as conn:
        conn.execute("UPDATE banks SET owner_id=? WHERE id=?", (teacher_id, bank_id))
        conn.execute("DELETE FROM teacher_banks WHERE teacher_id=? AND bank_id=?", (teacher_id, bank_id))
        if old and old != teacher_id:
            role = conn.execute("SELECT role FROM users WHERE id=?", (old,)).fetchone()
            if role and role[0] == "teacher":
                conn.execute("DELETE FROM bank_tags WHERE teacher_id=? AND bank_id=?", (old, bank_id))


def move_student(db: Database, student_id: int, teacher_id: int, actor: int | None) -> None:
    """分配（转给）：只挂在这位老师名下。原来的老师都移走（连同他们打的标签）。"""
    for old in student_teachers(db, student_id):
        if old != teacher_id:
            unlink_student(db, old, student_id)
    link_student(db, teacher_id, student_id, actor)


# ------------------------------------------------------------------ 软删除和恢复

def soft_delete(db: Database, table: str, row_id: int, actor: int | None, now: float | None = None) -> None:
    assert table in ("banks", "users", "materials")
    db.execute("UPDATE %s SET deleted_at=?, deleted_by=? WHERE id=?" % table, (int(now or time.time()), actor, row_id))
    if table == "users":
        db.execute("DELETE FROM sessions WHERE user_id=?", (row_id,))          # 马上退出登录


def restore(db: Database, table: str, row_id: int) -> bool:
    assert table in ("banks", "users", "materials")
    cur = db.execute("UPDATE %s SET deleted_at=0, deleted_by=NULL WHERE id=? AND deleted_at<>0" % table, (row_id,))
    return cur.rowcount > 0


def deleted_rows(db: Database) -> dict:
    """超管看「已删除」：谁、什么时候删的。"""
    def rows(sql):
        return [dict(r) for r in db.query(sql)]
    return {
        "users": rows("SELECT u.id, u.student_no, u.name, u.class_name, u.role, u.deleted_at, d.name AS deleted_by_name "
                      "FROM users u LEFT JOIN users d ON d.id=u.deleted_by WHERE u.deleted_at<>0 ORDER BY u.deleted_at DESC"),
        "banks": rows("SELECT b.id, b.title, b.category, b.word_count, b.deleted_at, o.name AS owner_name, d.name AS deleted_by_name "
                      "FROM banks b LEFT JOIN users o ON o.id=b.owner_id LEFT JOIN users d ON d.id=b.deleted_by "
                      "WHERE b.deleted_at<>0 ORDER BY b.deleted_at DESC"),
        "materials": rows("SELECT m.id, m.name, m.word_count, m.deleted_at, o.name AS owner_name, d.name AS deleted_by_name "
                          "FROM materials m LEFT JOIN users o ON o.id=m.owner_id LEFT JOIN users d ON d.id=m.deleted_by "
                          "WHERE m.deleted_at<>0 ORDER BY m.deleted_at DESC"),
    }


def delete_bank_for(db: Database, scope: Scope, bank: dict) -> str:
    """老师 / 超管点「删除」：返回做了什么（deleted / unshared）。不允许的抛 PermissionError。"""
    if scope.everything:
        soft_delete(db, "banks", bank["id"], scope.user_id)
        return "deleted"
    relation = relation_to_bank(db, scope, bank)
    if relation == "owner":
        soft_delete(db, "banks", bank["id"], scope.user_id)
        return "deleted"
    if relation == "shared":
        unlink_bank(db, scope.user_id, bank["id"])
        return "unshared"
    raise PermissionError("内置题库不能删除" if relation == "system" else "没有这个题库")


def delete_student_for(db: Database, scope: Scope, user: dict) -> str:
    """老师删学生：也挂在别的老师名下的，只从自己名下移走（unlinked）；只属于自己的，软删除（deleted）。超管直接软删除。"""
    if scope.everything:
        soft_delete(db, "users", user["id"], scope.user_id)
        return "deleted"
    others = [t for t in student_teachers(db, user["id"]) if t != scope.user_id]
    if others:
        unlink_student(db, scope.user_id, user["id"])
        return "unlinked"
    soft_delete(db, "users", user["id"], scope.user_id)
    return "deleted"
