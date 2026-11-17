"""多位老师的页面：老师用同一套管理界面（数据只有自己的）、账号页能删学生和整个班、题库列表区分共享和内置、超管专属的「老师与分配」页。"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"


def read(name):
    return (WEB / name).read_text(encoding="utf-8")


class TestTeacherIsStaffInThePages(unittest.TestCase):
    def test_auth_ui_treats_teachers_as_staff_and_only_the_super_admin_gets_the_teachers_page(self):
        ui = read("js/auth-ui.js")
        self.assertIn("function isStaffRole(role) { return role === 'admin' || role === 'teacher'; }", ui)
        self.assertIn("isSuper: function", ui)
        self.assertIn("tenantsNavLink", ui)
        self.assertIn("if (nav && isSuper && !document.getElementById('tenantsNavLink'))", ui)
        self.assertIn("if (mode === 'super' && info.user.role !== 'admin')", ui)

    def test_every_page_loads_the_new_auth_script(self):
        for page in WEB.glob("*.html"):
            html = page.read_text(encoding="utf-8")
            if "auth-ui.js" in html:
                self.assertIn("auth-ui.js?v=20261117-requests", html, page.name + "：老旧缓存会把老师当成学生")

    def test_accounts_page_loads_users_for_teachers_too(self):
        self.assertIn("info.user.role === 'admin' || info.user.role === 'teacher'", read("js/page-admin.js"))


class TestAccountsPage(unittest.TestCase):
    def test_delete_a_student_and_a_whole_class(self):
        html, code = read("admin.html"), read("js/page-admin.js")
        self.assertIn('id="btnBulkDelete"', html)
        self.assertIn("data-act=\"delete\"", code)
        self.assertEqual(code.count("'/api/admin/users/delete'"), 2, "单个删除和删除整个列表都走同一个接口")
        self.assertIn("deleteDone", code)

    def test_the_super_admin_sees_which_teachers_hold_each_student(self):
        html, code = read("admin.html"), read("js/page-admin.js")
        self.assertIn('<th id="thTeachers" hidden', html)
        self.assertIn("superView = !!res.super;", code)
        self.assertIn("teachersCell(u)", code)

    def test_the_import_report_mentions_automatically_shared_students(self):
        self.assertIn("importShared", read("js/page-admin.js"))

    def test_share_requests_are_shown_and_decided_on_the_accounts_page(self):
        html, code = read("admin.html"), read("js/page-admin.js")
        self.assertIn('id="reqCard"', html)
        self.assertIn("importRequested", code)
        self.assertIn("'/api/admin/share-requests/' + r.id + '/decide'", code)
        self.assertIn("window.confirm(question)", code, "批准前要确认（对方能看成绩和访问记录）")

    def test_students_shared_with_me_have_no_reset_disable_or_unlock_button(self):
        code = read("js/page-admin.js")
        self.assertIn("var mine = u.can_manage !== false;", code)
        self.assertIn("if (mine && u.locked)", code)
        self.assertIn("if (mine) actions += '<button class=\"btn sm ' + (u.disabled", code)
        self.assertIn("managedBy", code)

    def test_the_super_admin_can_set_a_teachers_group(self):
        html, code = read("tenants.html"), read("js/page-tenants.js")
        self.assertIn('data-module-zh="教研组"', html)
        self.assertIn("'/api/admin/teachers/' + u.id + '/group'", code)


class TestWorkbench(unittest.TestCase):
    def test_built_in_banks_have_no_delete_or_category_button_and_shared_ones_are_removed_not_deleted(self):
        code = read("js/page-bank.js")
        self.assertIn("var canEdit = rel === 'owner', canDelete = rel !== 'system';", code)
        self.assertIn("bank_removeShared", code)
        self.assertIn("res.done === 'unshared'", code)


class TestTenantsPage(unittest.TestCase):
    HTML = read("tenants.html")
    CODE = read("js/page-tenants.js")

    def test_the_page_is_super_only_and_follows_the_house_style(self):
        self.assertIn('<body data-auth="super">', self.HTML)
        self.assertIn("sessionStorage.getItem('wp_role')", self.HTML, "画出来之前就按缓存的角色设好样式")
        self.assertIn('id="portalHeaderControls"', self.HTML, "页眉里有语言和配色")
        self.assertIn("/shared/module-header.js", self.HTML)

    def test_four_tabs(self):
        for name in ("Teachers", "Assign", "Deleted", "Audit"):
            self.assertRegex(self.HTML, r'id="tab%s"[^>]*aria-controls="panel%s"' % (name, name))
            self.assertRegex(self.HTML, r'<section id="panel%s" role="tabpanel"' % name)

    def test_it_uses_only_the_super_endpoints_it_needs(self):
        for endpoint in ("'/api/admin/teachers'", "'/api/admin/assign'", "'/api/admin/deleted'", "'/api/admin/restore'",
                         "'/api/admin/audit?limit=300'"):
            self.assertIn(endpoint, self.CODE)
        self.assertIn("if (!AuthUI.isSuper()) return;", self.CODE)

    def test_every_audit_action_has_a_translation(self):
        backend = "\n".join((ROOT / "server" / n).read_text(encoding="utf-8") for n in ("app.py", "tenancy.py", "auth.py"))
        actions = set(re.findall(r'"((?:teacher|bank|student|material|user|share)\.[a-z_]+)"', backend))
        actions |= {"%s.%s" % (k, m) for k in ("bank", "student") for m in ("share", "move", "unshare")}
        actions |= {"%s.restore" % k for k in ("user", "bank", "material")}
        actions |= {"bank.delete", "bank.unshare_self", "student.delete", "student.unlink_self"}
        actions |= {"share.request", "share.approve", "share.reject"}
        keys = dict(re.findall(r"'((?:teacher|bank|student|material|user|share)\.[a-z_]+)': '(ten_act_[a-z_]+)'", self.CODE))
        self.assertEqual(actions - set(keys), set(), "审计里会出现、页面上却没有译文的动作")

    def test_initial_passwords_are_only_shown_once_and_escaped(self):
        self.assertIn("esc(res.password)", self.CODE)
        self.assertNotIn("localStorage", self.CODE, "密码不能存在浏览器里")


if __name__ == "__main__":
    unittest.main()
