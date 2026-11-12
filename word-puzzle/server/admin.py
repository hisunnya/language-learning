"""家庭版 / 班级版的管理命令行：在服务器上用，不经过网络。

    python3 -m server.admin create-admin 20260001 --name 张老师
    python3 -m server.admin import 名单.xlsx --out 初始密码.csv     # 文件名写 - 表示从标准输入读
    python3 -m server.admin reset-password 2026001
    python3 -m server.admin unlock 2026001
    python3 -m server.admin disable 2026001        # enable 同理
    python3 -m server.admin list --class-name 计算机1班

数据库位置：--db 或环境变量 WP_DB。
"""
from __future__ import annotations

import argparse
import csv
import getpass
import os
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    __package__ = "server"

from server import auth as auth_mod        # noqa: E402
from server import roster                   # noqa: E402
from server.db import Database              # noqa: E402


def _cell(value) -> str:
    """以 = + - @ 开头的单元格在 Excel 里会被当成公式（名单是外来内容），前面补一个单引号。"""
    value = str(value)
    return "'" + value if value[:1] in ("=", "+", "-", "@") else value


def write_credentials(path: str, credentials: list[dict]) -> None:
    """初始密码清单：UTF-8 带 BOM，Excel 直接打开不乱码。文件里是明文，发完请删除。"""
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["学号", "姓名", "班级", "初始密码"])
        for c in credentials:
            writer.writerow([_cell(c["student_no"]), _cell(c["name"]), _cell(c["class_name"]),
                             _cell(c["password"])])
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="词境 家庭版账号管理")
    ap.add_argument("--db", default=os.environ.get("WP_DB", ""), help="数据库文件（默认读 WP_DB）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("create-admin", help="创建管理员账号")
    p.add_argument("student_no")
    p.add_argument("--name", required=True)
    p.add_argument("--password", help="不给就会提示输入（推荐，避免留在命令历史里）")

    p = sub.add_parser("import", help="导入学生名单（csv / xlsx）")
    p.add_argument("file")
    p.add_argument("--out", default="初始密码.csv", help="初始密码清单的保存位置")
    p.add_argument("--reset-existing", action="store_true", help="已存在的学号也重置密码")

    for name in ("reset-password", "unlock", "disable", "enable"):
        p = sub.add_parser(name)
        p.add_argument("student_no")

    p = sub.add_parser("list", help="列出账号")
    p.add_argument("--class-name", default="")
    p.add_argument("--college", default="")
    p.add_argument("--department", default="")

    args = ap.parse_args(argv)
    if not args.db:
        ap.error("请用 --db 或环境变量 WP_DB 指定数据库文件")
    db = Database(args.db)
    svc = auth_mod.AuthService(db)
    try:
        if args.cmd == "create-admin":
            password = args.password
            if not password:
                password = getpass.getpass("管理员密码: ")
                if getpass.getpass("再输一遍: ") != password:
                    print("两次输入不一致", file=sys.stderr)
                    return 1
            problem = auth_mod.password_problem(password, args.student_no)
            if problem:
                print(problem, file=sys.stderr)
                return 1
            user, _ = svc.create_user(args.student_no, args.name, password=password,
                                      role="admin", must_change=False)
            print("已创建管理员 %s（%s）" % (user["student_no"], user["name"]))
            return 0

        if args.cmd == "import":
            data = sys.stdin.buffer.read() if args.file == "-" else Path(args.file).read_bytes()
            table = roster.parse_roster(args.file, data)
            report = svc.import_roster(table["rows"], reset_existing=args.reset_existing)
            if table["ignored_columns"]:
                print("注意：这些列不会被保存：" + "、".join(table["ignored_columns"]))
            print("新建 %d，更新 %d，跳过 %d" % (report["created"], report["updated"], report["skipped"]))
            for e in report["errors"]:
                print("  第 %s 行 %s：%s" % (e["row"], e["student_no"] or "-", e["reason"]))
            if report["credentials"]:
                write_credentials(args.out, report["credentials"])
                print("初始密码清单已写到 %s（明文，发完请删除）" % args.out)
            return 0 if not report["errors"] else 2

        if args.cmd == "list":
            for u in svc.list_users(class_name=args.class_name, college=args.college,
                                    department=args.department):
                flags = "".join([" [管理员]" if u["role"] == "admin" else "",
                                 " [停用]" if u["disabled"] else "", " [锁定]" if u["locked"] else "",
                                 " [待改密码]" if u["must_change"] else ""])
                print("%s\t%s\t%s\t%s%s" % (u["student_no"], u["name"], u["class_name"],
                                            u["college"], flags))
            return 0

        user = svc.get_by_student_no(args.student_no)
        if not user:
            print("没有学号 %s" % args.student_no, file=sys.stderr)
            return 1
        if args.cmd == "reset-password":
            print("新的初始密码：%s（登录后必须修改）" % svc.reset_password(user["id"]))
        elif args.cmd == "unlock":
            svc.unlock(user["id"])
            print("已解锁")
        else:
            svc.set_disabled(user["id"], args.cmd == "disable")
            print("已停用" if args.cmd == "disable" else "已启用")
        return 0
    except (auth_mod.AuthError, roster.RosterError, OSError) as exc:
        print(getattr(exc, "message", str(exc)), file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
