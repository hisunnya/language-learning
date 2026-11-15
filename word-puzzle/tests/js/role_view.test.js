/* role_view.test.js —— 换页面时不闪教师版
   <head> 里的一小段脚本在页面画出来之前，按本次会话里记下的角色设 <html> 的 class；
   auth-ui.js 在服务器答复回来后再校正，并把角色记下来给下一个页面用。 */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm');
const WEB = path.join(__dirname, '..', '..', 'web');
const html = fs.readFileSync(path.join(WEB, 'index.html'), 'utf8');
const headScript = /<script>(\(function\(\)\{var h=document\.documentElement[\s\S]*?)<\/script>/.exec(html)[1];
const authUi = fs.readFileSync(path.join(WEB, 'js', 'auth-ui.js'), 'utf8');

let passed = 0; const failures = [];
function check(name, ok, detail) { if (ok) passed++; else failures.push(name + (detail ? '：' + detail : '')); }

function makePage(cache, me, mode, page) {
  const classes = new Set(), store = Object.assign({}, cache), redirects = []; let removedHomeLinks = 0;
  const sandbox = {
    sessionStorage: { getItem: (k) => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = String(v); }, removeItem: (k) => { delete store[k]; } },
    document: {
      documentElement: { classList: { add: (...c) => c.forEach((x) => classes.add(x)), remove: (...c) => c.forEach((x) => classes.delete(x)), contains: (c) => classes.has(c) }, get lang() { return 'zh-CN'; } },
      querySelector: (sel) => (sel.indexOf('wp-base') >= 0 ? { content: '/word-puzzle' } : null),
      body: { getAttribute: (n) => (n === 'data-page' ? (page || '') : (mode || '')), classList: { add() {} } },
      querySelectorAll: (q) => (q === '.portal-nav a' ? [{ getAttribute: () => '/word-puzzle/', parentNode: { removeChild() { removedHomeLinks++; } } }, { getAttribute: () => '/word-puzzle/stats.html', parentNode: { removeChild() { removedHomeLinks += 100; } } }] : []),
      getElementById: () => null, createElement: () => ({ setAttribute() {}, appendChild() {} }),
    },
    API: { get: () => (me === 'network-error' ? Promise.reject(new Error('x')) : Promise.resolve(me)), post: () => Promise.resolve({}) },
    location: { search: '', pathname: '/word-puzzle/', replace: (u) => redirects.push(u), href: '' },
  };
  sandbox.window = sandbox; sandbox.global = sandbox;
  vm.createContext(sandbox);
  vm.runInContext(headScript, sandbox);                       // 页面画出来之前：只读缓存
  const before = Array.from(classes).sort();
  vm.runInContext(authUi, sandbox);
  return { classes, store, redirects, before, ready: sandbox.AuthUI.ready, removed: () => removedHomeLinks, landing: (u) => sandbox.AuthUI.landing(u), location: sandbox.location };
}
const sorted = (set) => Array.from(set).sort();

(async () => {
  // 1) 画出来之前
  check('没有缓存：先是「未知」，页面整页不显示', JSON.stringify(makePage({}, { auth_enabled: true, user: null }, 'public').before) === '["role-pending"]');
  check('缓存了学生：直接是学生视图，不会闪教师版', JSON.stringify(makePage({ wp_role: 'student' }, { auth_enabled: true, user: null }).before) === '["role-student"]');
  check('缓存了老师：直接是老师视图', JSON.stringify(makePage({ wp_role: 'admin' }, { auth_enabled: true, user: null }).before) === '["role-admin"]');
  check('缓存是乱的：按未知处理', JSON.stringify(makePage({ wp_role: 'hacker' }, { auth_enabled: true, user: null }).before) === '["role-pending"]');

  // 2) 服务器答复回来之后
  let p = makePage({}, { auth_enabled: true, user: { role: 'student', must_change: false, student_no: 'S1', name: '学生' } });
  await p.ready;
  check('学生：只剩 role-student，并记下来', JSON.stringify(sorted(p.classes)) === '["role-student"]' && p.store.wp_role === 'student');
  p = makePage({}, { auth_enabled: true, user: { role: 'admin', must_change: false, student_no: 'T1', name: '老师' } });
  await p.ready;
  check('老师：只剩 role-admin，并记下来', JSON.stringify(sorted(p.classes)) === '["role-admin"]' && p.store.wp_role === 'admin');
  p = makePage({ wp_role: 'admin' }, { auth_enabled: true, user: { role: 'student', must_change: false, student_no: 'S1', name: '学生' } });
  await p.ready;
  check('缓存说是老师、服务器说是学生：以服务器为准', JSON.stringify(sorted(p.classes)) === '["role-student"]' && p.store.wp_role === 'student');
  p = makePage({}, { auth_enabled: false, user: null });
  await p.ready;
  check('家庭版（没有账号）：等同老师', JSON.stringify(sorted(p.classes)) === '["role-admin"]' && p.store.wp_role === 'admin');

  // 3) 没登录
  p = makePage({ wp_role: 'admin' }, { auth_enabled: true, user: null }, '');
  await p.ready;
  check('没登录、要跳去登录页：缓存清掉，页面保持不显示（免得先闪内容）',
        !('wp_role' in p.store) && p.redirects.length === 1 && /login\.html/.test(p.redirects[0]) && !p.classes.has('role-admin') && !p.classes.has('role-student'));
  p = makePage({}, { auth_enabled: true, user: null }, 'public');
  await p.ready;
  check('登录页本身：显示出来，不跳转', !p.classes.has('role-pending') && p.redirects.length === 0);

  // 3b) 老师没有「首页」：题库工作台就是首页（学生和家庭版里没登录的访客不受影响）
  p = makePage({ wp_teacher: '1', wp_role: 'admin' }, { auth_enabled: true, user: null }, '', 'home');
  check('缓存里是登录着的老师：首页在画出来之前就跳去题库工作台', p.redirects.length === 1 && /bank\.html#banks$/.test(p.redirects[0]) && p.before.length === 0);
  p = makePage({ wp_role: 'admin' }, { auth_enabled: true, user: null }, '', 'home');
  check('只缓存了 admin 角色、不是登录着的老师（家庭版访客）：首页不跳', p.redirects.length === 0 && JSON.stringify(p.before) === '["role-admin"]');
  p = makePage({}, { auth_enabled: true, user: { role: 'admin', must_change: false, student_no: 'T1', name: '老师' } }, '', 'home');
  await p.ready;
  check('老师在首页：服务器确认后跳去题库工作台，并记住是老师', p.redirects.length === 1 && /bank\.html#banks$/.test(p.redirects[0]) && p.store.wp_teacher === '1');
  p = makePage({}, { auth_enabled: true, user: { role: 'admin', must_change: false, student_no: 'T1', name: '老师' } }, '', 'stats');
  await p.ready;
  check('老师在别的页面：不跳，但页眉里的「首页」链接被去掉（只去它一个）', p.redirects.length === 0 && p.removed() === 1);
  p = makePage({}, { auth_enabled: true, user: { role: 'student', must_change: false, student_no: 'S1', name: '学生' } }, '', 'home');
  await p.ready;
  check('学生在首页：不跳，也没有老师标记', p.redirects.length === 0 && !('wp_teacher' in p.store));
  p = makePage({ wp_teacher: '1' }, { auth_enabled: true, user: { role: 'student', must_change: false, student_no: 'S1', name: '学生' } }, 'admin');
  await p.ready;
  check('残留的老师标记遇到学生账号：被送回首页，并且标记被清掉（不会来回跳）', p.redirects.some((u) => /\/word-puzzle\/$/.test(u)) && !('wp_teacher' in p.store));
  p = makePage({ wp_teacher: '1', wp_role: 'admin' }, { auth_enabled: true, guest_mode: true, user: null }, '', 'stats');
  await p.ready;
  check('老师登录过期、变成家庭版访客：老师标记被清掉', !('wp_teacher' in p.store) && p.classes.has('role-admin'));
  p = makePage({}, { auth_enabled: true, user: { role: 'admin', must_change: false, student_no: 'T1', name: '老师' } }, '', 'stats');
  await p.ready;
  check('登录后默认去哪：老师是题库工作台，学生是首页，指定了页面就去指定的页面',
        /bank\.html#banks$/.test(p.landing({ role: 'admin' })) && p.landing({ role: 'student' }) === '/word-puzzle/' &&
        (p.location.search = '?next=%2Fword-puzzle%2Fstats.html', p.landing({ role: 'admin' }) === '/word-puzzle/stats.html'));

  // 4) 问不到服务器
  p = makePage({}, 'network-error');
  await p.ready;
  check('问不到服务器：按学生视图显示，不空白也不露出教师控件', JSON.stringify(sorted(p.classes)) === '["role-student"]');

  if (failures.length) { console.error('失败 ' + failures.length + ' 项：\n  ' + failures.join('\n  ')); process.exit(1); }
  console.log('换页面不闪教师版的行为测试：' + passed + ' 项全部通过');
})();
