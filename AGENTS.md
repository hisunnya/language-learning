# AGENTS.md

Repository-wide conventions for coding agents. These rules apply to every file
in this repository, on every machine, and to every pull request.

The point of this file is that a rule written here travels with the code: it is
versioned in git, so it reaches every developer machine and every agent session
— unlike a per-machine scratch note.

---

## 1. Git

### Commit messages are written in English

Both the subject and the body. This is the only English-language artefact in
the repository — see §2 for everything else.

- **Subject**: imperative mood, ≤ 72 characters, prefixed with a scope when it
  helps identify the area.
  - `fix(webapp): label the three unlabelled refresh buttons`
  - `feat(hub): add the obsidian palette`
  - `docs: explain that the deploy directory is separate from the repo`
- **Body**: state the root cause first, then the change, then how it was
  verified. A reviewer should not have to re-derive why the change was needed.
- Never write Chinese in a commit message, even in the body.
- Before pushing, `git rebase origin/main` — the remote often has commits that
  landed in the meantime.

### Identity: the owner's personal address, never a company one

This is a **personal** repository and it is public: the author and committer e-mail of
every commit is published with the history. Commits must carry the owner's personal
address (the one in `git config user.email`; see `AGENTS.local.md`), never a company or
any other private address. Before the first commit on a machine check
`git config user.email`; if it is wrong, fix it *before* committing. The hygiene test
fails on any e-mail address in tracked files and unless all commits share exactly one
identity (and, on the owner's machine, unless it avoids every pattern in the git-ignored
`.private-patterns`). Rewriting published history needs the owner's explicit agreement
(it requires a force-push); it has been done twice on the owner's request — to remove a
company address, then to switch to the personal one.

### Branches and reverts

- One logical change per commit. Do not mix a refactor with a behaviour change.
- Never rewrite published history (`rebase` of an already-pushed branch needs
  explicit agreement).

---

## 2. Language of the code and the docs

| Artefact | Language |
|---|---|
| Commit message | **English** (§1) |
| Documentation (`.md`) | Chinese, matching the existing files |
| Code comments | Chinese, matching the surrounding code |
| User-facing UI strings | **Both Chinese and English** (§3) |
| Identifiers, log keys, API payloads | English, unchanged |

Do not "helpfully" translate the existing Chinese docs or comments into
English. The repository is Chinese-first for prose; only commit messages are
English.

---

## 3. Frontend pages

Every user-facing page in this repository ships with **all three** of the
following. A page that is missing one of them is unfinished, not "a simpler
page".

This applies to **every** page — the ones that exist today and any page added
later. A new page is not "a simplified version"; it carries the same bilingual
support, the same palette picker and the same tests as the existing ones.

### 3.1 Bilingual Chinese / English

Every user-visible string exists in both languages and the user can switch
between them at runtime.

- No hard-coded user-visible text in the markup that is not translatable.
- The choice is remembered across reloads (`localStorage`).
- The current language is reflected on the element (`<html lang="…">`).

Two mechanisms are in use; follow the one that fits the page:

| Mechanism | Where | How it works |
|---|---|---|
| `data-i18n` attributes | `hub/index.html` | `<tag data-i18n="key">`; a single `applyLang()` swaps every marked node. |
| i18n table | (available for new pages that prefer it) | An `i18n = { zh: {...}, en: {...} }` object; `applyLang()` walks a list of element ids and writes `textContent`. |
| `data-module-zh/en` + `WPI18N` | `word-puzzle/web/*.html` | Static text carries `data-module-zh` / `data-module-en` (the shared header swaps it). Text drawn by scripts uses `WPI18N.t('key', {n})` with the entries in `web/js/i18n-lexica.js`, and redraws on the `portal-lang-change` event. The offline single-file page embeds the same files and has its own toggle. |

Whichever mechanism is used, **the language toggle belongs in the header**,
next to the palette picker.

The hub's i18n table lives in `hub/js/hub.js` as `I18N = { zh: {...}, en: {...} }`.
**Both dictionaries must carry exactly the same keys** — a key present in one
language and missing in the other is a bug, and the hub test enforces it.

### 3.2 Multiple colour palettes

- At least **three** palettes, each a named set of CSS custom properties on
  `[data-theme="…"]`, not hard-coded colours scattered through the stylesheet.
- The palette is remembered across reloads (`localStorage`).
- The active palette is marked in the picker (`aria-pressed` / `.active`).
- Every palette needs a name in both languages, and the name should read as
  the two colours it combines (e.g. `靛蓝 · 雪白` — `Indigo · Snow`).
- **Every palette defines the complete same set of variables.** A palette that
  is missing `--accent-soft` or `--line` is not a palette, it is a broken page.
  The hub test compares the variable sets and fails on a difference.

### 3.3 The palette picker

This is a specific house style. Follow it exactly:

- **Position**: top-right of the header, next to the language toggle.
- **Shape**: small **squares** (rounded corners are fine, a circle is not).
- **Contents**: each square is **split diagonally** into the two dominant
  colours of that palette — the accent (top-right half) and the page
  background (bottom-left half).
- A tooltip names the palette in the current language.
- The selected square is visually marked (outline / ring).

The same style applies to every page in the repository, so the picker looks
and behaves the same wherever the user meets it. Do not invent a second
picker style.

The diagonal split is a `linear-gradient` with a hard stop — no images, no
extra markup:

````css
.swatch {
  width: 16px;
  height: 16px;
  border-radius: 4px;
  border: 1px solid var(--line);
  /* bottom-left = background, top-right = accent */
  background: linear-gradient(to top right,
    var(--swatch-bg) 0 50%,
    var(--swatch-main) 50% 100%);
}
````

Each swatch carries the two colours of its **own** palette inline, because the
picker must show what each palette looks like, not what the current one looks
like:

````html
<button type="button" class="theme-chip" data-theme-val="indigo"
        data-tooltip-zh="靛蓝 · 雪白" data-tooltip-en="Indigo · Snow"
        aria-label="靛蓝雪白配色" aria-pressed="true">
  <span class="swatch" style="--swatch-main:#4F46E5; --swatch-bg:#F4F6FB;"></span>
</button>
````

### 3.4 Reference implementations

`hub/index.html` is the **canonical reference implementation** — it is the only
page in the repository that implements all of §3 today, and the hub test
(`hub/tests/test_hub.py`) is what keeps it that way.

| Page | Bilingual | Palettes | Picker | Status |
|---|---|---|---|---|
| `hub/index.html` | `data-i18n` | 5 | top-right, square swatches | ✅ reference |
| `word-puzzle/web/*.html` | `data-module-zh/en` + `WPI18N` | 5 (shared header) | top-right, square swatches (shared header) | ✅ every page, including the game and the offline page |
| `topic-app/topic-app/index.html` | — | 3 (different picker) | — | ⚠️ to be brought up to §3 |
| `ham-exam/index.html` | — | — | — | ⚠️ to be brought up to §3 |
| `word-puzzle/web/{login,change-password,admin,tenants,leaderboard}.html` | `data-module-zh/en` | 5 (shared header) | top-right, square swatches (shared header) | ✅ new pages follow §3 |
| `hub/privacy.html` | `data-module-zh/en` (shared header) | 5 (shared header) | top-right, square swatches (shared header) | ✅ |
| `miniprogram/` (WeChat) | `utils/i18n.js` | 5 (same names) | top-right, square swatches (tap, name shown below) | ✅ adapted, see 3.4.1 |

The two ⚠️ pages predate this convention. When you touch one of them, bring
it along: the target style is `hub/`, not the reverse. Do not "fix" the hub to
match the older pages.

Note that `topic-app` already has three colour themes, but its picker is a
row of three stacked colour bars with a text label — that is **not** the house
style. Converting it means replacing the picker with diagonal-split squares
and moving the theme variables onto `[data-theme="…"]`.

#### 3.4.1 The WeChat mini program

`miniprogram/` is not a web page, so §3 is adapted rather than copied:

- Language: `utils/i18n.js` (`zh` / `en` tables with identical keys and
  placeholders), toggle in the header next to the palettes, remembered in
  `wx` storage (`wp_lang`). WXML contains no visible text of its own.
- Palettes: the same five as the hub, as `.theme-<key>` blocks in `app.wxss`
  with an identical variable set; the page root and every overlay carry the
  class. The navigation bar and the page background are outside WXML and are
  set from `utils/prefs.js`. Choice remembered as `wp_theme`.
- Picker: small squares split along the diagonal (a hard 50 % stop, not the
  `0 50%` two-position syntax, which older WebViews may not parse). There is no
  hover on a phone, so the active palette's name is printed under the picker
  instead of a tooltip.
- `miniprogram/tests/` checks all of this; WXML rendering itself still has to
  be looked at once in WeChat DevTools.

### 3.5 Adding a new page

A new user-facing page is not done until all of this is in place. Walk the
list in order:

1. **Pick the bilingual mechanism** (§3.1) and put the strings in both
   languages. No hard-coded user-visible text in the markup.
2. **Define at least three palettes** on `[data-theme="…"]` (§3.2), each with
   its own complete `--bg` / `--accent` / `--line` / … set. Move every
   hard-coded colour out of the stylesheet and into a variable.
3. **Build the picker** (§3.3): small squares in the top-right of the header,
   each split diagonally into that palette's own two colours, each with a
   bilingual tooltip.
4. **Persist both choices** in `localStorage`, and mark the active palette
   with `aria-pressed` (or `.active`).
5. **Test it** (§3.6).

### 3.6 Tests

`hub/tests/test_hub.py` is the style guard for the whole repository. Run it
after touching any page's markup, styles or scripts:

```bash
cd hub && python3 -m unittest discover -s tests -v
```

It fails when:

- a button ends up without visible text — a button with no id is never filled
  in by `applyLang()` and renders as an empty box;
- a visible string is not covered by a `data-i18n` key, or a key exists in one
  language but not the other;
- a palette swatch carries only one of its two colours (`--swatch-main` and
  `--swatch-bg`), so no swatch is indistinguishable from another;
- the split is not a hard-stop diagonal gradient (`0 50%` → `50% 100%`);
- the swatch is not a square (`border-radius: 4px`);
- a palette does not define the complete variable set, so the palettes are not
  really different;
- the choice is not persisted in `localStorage`.

A regression here must fail the suite rather than ship.

---

## 4. Tests

- Every behaviour change comes with a test. The suites are plain
  `unittest` (Python) — no new frameworks without a reason. There is **no
  Node.js on the target host**, so JavaScript is checked with
  `word-puzzle/tools/check_js.py`, not `node --check`.
- The pure-computation layer `word-puzzle/web/js/game-core.js` has a
  behaviour test at `word-puzzle/tests/js/game_core.test.js`, driven by
  `word-puzzle/tests/test_game_core.py`. It runs under `node` where node is
  available and **skips** where it is not, so the target host stays
  dependency-free. A change to the scoring or matching rules belongs there.
- `miniprogram/utils/game-core.js` is a port of the website core. The two are
  kept honest by `word-puzzle/tests/js/core_parity.test.js` (same seed, same
  random sequence of picks / ticks / pauses / replays, state and events
  compared at every step) and `word-puzzle/tests/test_bank_levels.py`
  (`bank.py` and `miniprogram/utils/bank.js` must cut identical levels). Change
  one copy and the other has to follow, or these fail.
- The mini program has its own suite (`miniprogram/tests/`) and a fake `wx`
  runtime (`tests/js/harness.js`) with a controllable clock and timers.
- **Asset versions are computed, not typed.** Pages load JS / CSS with `?v=<first 8 hex of the
  file's content hash>`; the public entrance lets browsers keep versioned files for an hour and
  WeChat caches hard, so a file changed without a new `?v=` keeps running old code on students'
  phones. After editing any file under `word-puzzle/web/js`, `web/css` or `hub/shared`, run
  `python3 word-puzzle/tools/bump_assets.py` (rewrites every page); `tests/test_asset_versions.py`
  fails when a page does not match.
- Run the suite before committing. A change that cannot be verified on this
  machine must say so explicitly instead of claiming success.
- Verification means the real path, not only unit tests: a unit test with mock
  data cannot catch a changed upstream dataset or an unreachable registry.

```bash
cd word-puzzle && python3 -m unittest discover -s tests -v   # 后端用例
cd hub        && python3 -m unittest discover -s tests -v   # 样式规范用例
cd word-puzzle && python3 tools/check_js.py                  # JS 语法体检
cd chemistry  && python3 -m unittest discover -s tests -v   # 化学探秘
cd physics    && python3 -m unittest discover -s tests -v   # 物理探秘
cd miniprogram && python3 -m unittest discover -s tests -v  # 小程序
```

---

## 5. Repository layout

```
language-learning/
├── AGENTS.md               # 本文件
├── README.md               # 仓库总说明（中文）
├── hub/                    # 网站主页「词境 Lexica」（原「语林」）—— 五个模块的入口、隐私说明、全站页脚
├── word-puzzle/            # 词境 Lexica —— 英语词汇游戏（网站版）
├── topic-app/              # 每日话题 Daily Topics —— 初中生家庭讨论
├── ham-exam/               # 无线电执照 Ham Exam —— 业余无线电模拟考试
├── chemistry/              # 化学探秘 Chem Quest —— 分龄化学练习
└── physics/                # 物理探秘 Phys Quest —— 分龄物理练习
```

- **The deployment directory is not the git working tree.** A `git pull` does
  not change what the running service serves; the code has to be copied to the
  server and the service restarted.
- Directory names are lowercase, because production is Linux (Debian) and paths are
  case-sensitive there.
- **Product names are names, not paths.** The product is 「词境 Lexica」; the
  directory is still `word-puzzle/` because renaming it would break the
  systemd unit, the nginx site and the paths already deployed on the server.
  Do not "helpfully" rename the directory.

### 5.1 Product names

| Product | 中文名 | English | Directory |
|---|---|---|---|
| Vocabulary game | 词境 | Lexica | `word-puzzle/` |
| Daily discussion | 每日话题 | Daily Topics | `topic-app/` |
| Radio exam | 无线电执照 | Ham Exam | `ham-exam/` |
| Chemistry learning | 化学探秘 | Chem Quest | `chemistry/` |
| Physics learning | 物理探秘 | Phys Quest | `physics/` |
| Vocabulary mini program | 词境 · 单词消消乐 | Lexica (WeChat) | `miniprogram/` |
| Site / homepage (hub) | 词境 | Lexica | `hub/` |

The whole site is called 「词境 Lexica」 (the name of the ICP filing); the homepage was called 「语林
Lingua Grove」 until 2026-11-21. The vocabulary module keeps the same name — the repetition is intended.

The vocabulary game was called 「单词消消乐」 while it was a single file. That
was a working name, not a product name — the product covers word and language
games generally, so it is 「词境 Lexica」 now. Use the product names above in
titles, headers, README and the hub.

### 5.2 Deployment layout on the server

**Architecture (one backend, two fronts, one database).** There is a single Lexica backend,
in the container `lexica` (the *student edition*, 学生版). It has two nginx entrances: the
public one (Funnel → 127.0.0.1:8081) requires login for everything; the LAN one
(`WP_LAN_ADDR`, `<container-ip>:8082`, also reached through the host's nginx at
`http://<host>/word-puzzle/`) lets visitors play without login and records their
visits and scores by device — the *home edition* (家庭版, formerly "局域网版") — and asks for a
teacher login only when a management function is used, with the same accounts because it
is the same database. nginx marks the entrance with `X-Wp-Entry` (cleared on the public
side); the backend honours it only from a loopback peer with `WP_LAN_GUEST=1`.
**The container serves the whole site** (2026-11-21): `/` is the homepage (`hub/`), plus `/privacy.html`,
`/topics/`, `/ham/`, `/chemistry/`, `/physics/` (static, no login) and `/word-puzzle/` (login). The LAN entrance
shows exactly the same as the public one (`WP_LAN_GUEST` defaults to 0 now; the guest code stays for the coming
public `/words/` entrance), and the host's port 80 forwards everything to it (`hub/deploy/site-proxy.conf`).
`deploy-all` packs `word-puzzle hub topic-app/topic-app ham-exam chemistry physics` into the container.
**Public Lexica `/words/`** (2026-11-21): the same code and backend as `/word-puzzle/`, without login, for the ICP
check and the public. `tools/build_public_web.py` generates `web-public/` at install time from `web/` (only index,
play, practice, stats; `/word-puzzle/` → `/words/`; fixed student view). nginx sends `/words/api/…` to the backend's
`/pub/api/…` (reachable only from loopback, and `/word-puzzle/api/…` cannot produce it); the backend then ignores the
session cookie, uses `tenancy.PUBLIC` (built-in banks of 初中 / 高中 only) and allows only `Handler.PUBLIC_ROUTES` —
no login, management, offline pages, leaderboard or uploads. Scores are stored with `mode='public'` against the
browser's device number and each device sees only its own; audio is synthesised only for words of public banks;
scores and audio are rate-limited per address, the API as a whole in nginx. The homepage card links to `/words/`.
**Every page carries the site footer** `/shared/site-footer.js` (ICP filing number, linked to beian.miit.gov.cn,
an optional public-security filing number, and the link to `/privacy.html`, plus a one-time notice); the number
is set in one place at the top of that file. Login-required pages and the coming site back office (`/backends/`)
are not linked from the homepage.
The database lives **outside the container** (a host directory, backups on another disk,
both bind-mounted; paths in `AGENTS.local.md`); the container stays stateless. The old
separate home backend on the host is retired. Other subjects plug in through
`server/modules.py`, `/api/records` and `server/policy.py`; see `docs/路线图.md`.

**Teachers as tenants (one database, visibility by relation).** Roles are `admin` (the
*super administrator*: sees and manages everything, including other teachers' work and
deleted rows), `teacher` and `student`. All rows live in the same tables; what a person
sees is decided in one place, `word-puzzle/server/tenancy.py` (`Scope`, `bank_where`,
`student_where`, `people_where`, `material_where`) — add a new list endpoint through it,
never with its own ad-hoc filter.

- A teacher sees the students linked to them (`teacher_students`), the banks they own
  (`banks.owner_id`), banks shared with them (`teacher_banks`) and the built-in banks
  (`owner_id IS NULL`, usable by every teacher, editable only by the super administrator),
  their own uploaded materials, and the scores / visits of their students.
- Tags are **per teacher** (`user_tags.teacher_id`, `bank_tags.teacher_id`): a student sees a
  bank only when one teacher gave both the same tag. Removing a student or a bank from a
  teacher also removes that teacher's tags on it.
- Importing a student number that already belongs to another teacher does **not** link it:
  `tenancy.claim_student` files a row in `share_requests` (audit `share.request`) and the
  importer gets no data, no tags and no password reset for it. The teacher responsible for the
  student (the first one linked, `tenancy.primary_teacher`) or the super administrator approves
  or rejects on the accounts page (`share.approve` / `share.reject`). Direct links without a
  request happen only when the super administrator imports, when the student has no teacher
  at all, or when both teachers have the same `users.teacher_group` (set by the super
  administrator; audit `student.auto_share` with the reason). Reason: anyone who knows a
  student number could otherwise take over the account of a student from another school.
- Reset password, disable and unlock (also via a roster import with "reset existing") are
  allowed only for the responsible teacher and the super administrator
  (`tenancy.can_manage_account`, error code `not_primary`); other teachers a student is shared
  with can read scores and visits and use their own tags.
- **Deletes are soft** (`deleted_at` / `deleted_by` on users, banks, materials): hidden from
  teachers and students, restorable by the super administrator on `tenants.html`. A
  teacher "deleting" something that is only shared with them just unlinks it. The hard
  `Database.delete_bank` is for internal rebuilds of the built-in banks only.
- Sharing, moving, deleting, restoring and adding teachers go to `audit_log`.
- The LAN guest (home edition, not logged in) sees the built-in banks and the super
  administrator's banks.
- The leaderboard (`server/leaderboard.py`, `leaderboard.html`) shows names and points only.
  Without settings a student sees their own class (classmates = same class name AND a shared
  teacher), a teacher the classes of their own students, the super administrator everyone.
  The super administrator can set an overall board (`app_settings` key `leaderboard`: the
  classes and an optional title, edited on `tenants.html`, audit `leaderboard.config`); then
  every signed-in student and teacher sees those classes' students together, deliberately
  across teachers, with the class next to each name.


| Path | Holds |
|---|---|
| `/srv/word-puzzle` | 词境 Lexica 的后端代码（`word-puzzle/deploy/install.sh` 装的） |
| `/var/lib/word-puzzle` | 词境的 SQLite 数据库和离线页 |
| `/var/www/topic-app` | 每日话题（纯静态） |
| `/var/www/ham-exam` | 无线电执照（纯静态） |
| `/var/www/chemistry` | 化学探秘（纯静态） |
| `/var/www/physics` | 物理探秘（纯静态） |
| `/var/www/lingua-grove` | 总主页（纯静态） |

`word-puzzle/deploy/install.sh` installs the Lexica backend and systemd service.
`hub/deploy/install.sh` publishes the hub and its four static project trees
(topics, ham exam, chemistry, physics) and configures the shared nginx entry. The root
`deploy-all-<timestamp>.sh` runs both installers from the repo checkout on the
target host: on production the flow is `git pull`, then run the script, which
copies the files into the paths above.

The **student edition** (学生版) of Lexica (login required, `WP_AUTH=1`) is a
separate instance of the same code and is *not* part of `deploy-all`:
`word-puzzle/deploy/family/install.sh` installs it under `/srv/word-puzzle-family`,
`/var/lib/word-puzzle-family`, systemd unit `word-puzzle-family`, backend on
127.0.0.1:8766 and nginx on 127.0.0.1:8081, and never touches the home edition or
Tailscale. Install it in its own container or VM, not on the PVE host
(`word-puzzle/deploy/family/部署说明.md`).
Container: unprivileged LXC, hostname `lexica`, static address on `vmbr0` (the concrete
id and addresses are in `AGENTS.local.md`; pick a free id with `qm list; pct list`).

### 5.3 Environments: workstation, development VM, home test, cloud production

| Environment | Where | Used for |
|---|---|---|
| Workstation + development VM (6.2.1) | macOS, Ubuntu arm64 | unit tests, rehearsing the installers |
| **Test** | the home PVE (6.2) | staging: the same code and the same installer, with a daily copy of the production data |
| **Production** | one Debian 13 server of a cloud provider in mainland China (Beijing), see 6.4 | the real student edition: backend, database and backups on one machine, nginx in front on 80 / 443 |

`word-puzzle/deploy/cloud/` installs the production server (`部署说明.md` there is the runbook):
`install.sh` reuses `deploy/family/install.sh` (with `WP_CLOUD=1`) for the backend, database, systemd units,
backup and watchdog, and adds the public nginx entrance (`render-nginx.sh`); `harden.sh` limits SSH to keys and
installs fail2ban; `enable-tls.sh` issues the Let's Encrypt certificate once the domain is filed (备案) and resolves
to the server. The site content of the public entrance is generated from the family nginx config, so the two never
drift apart. The home edition (LAN, no login) is retired; the Funnel setup of the home container is left as it is.
`migrate-data.sh` swaps a consistent database backup into the cloud (check by default, `--apply` to do it: snapshot of
the old database first, stop, swap, health check, row counts must match, automatic rollback on any failure) and
`sync-from-home.sh` drives it from the workstation (`rehearse` leaves the home service running, `cutover --yes` stops it
first and restarts it if the cutover fails). The database is replaced as a whole: accounts created on the cloud before the
cutover are discarded, the home accounts come over. Live databases are only opened by the service account, never by root
(a root-owned `-shm` next to a WAL database stops the service from opening it).

- The domain and server address are private values (6): `AGENTS.local.md`, never a tracked file.
- Before there is a certificate the site is reachable only from the server itself (SSH tunnel): login cookies are
  `Secure`, and clear text over the public internet is not acceptable. Serving the public before the filing is
  approved is not done.
- Never run frp, proxies, VPNs or reverse tunnels on the cloud server (the provider forbids traffic penetration and
  illegal proxying and shuts such instances down), and never put the database back on a home machine.
- Code is pushed to the server from the workstation (`scp` of a tarball), not pulled from GitHub there (6.4).

**Every commit ships a new `deploy-all-<YYYYMMDD_HHMMSS>.sh`.** Rename the
previous one with `git mv` to the new timestamp (never keep two side by side),
keep its file checks, smoke checks and printed URLs in step with the code — a
new module is added to all three — and commit it together with the change.

---

## 6. Servers and network

**Private facts are not in this file.** The repository is public, so addresses, host
names, user names, the container id, the Funnel URL and the like live in
`AGENTS.local.md` (git-ignored, on the developer machine — read it first if it exists)
and, on the servers, in the git-ignored `deploy.local.env`
(`deploy.local.env.example` shows the keys). Never write them into a tracked file, a
commit message, a PR description or a test; `word-puzzle/tests/test_repo_hygiene.py`
fails on private-looking addresses, tailnet host names and e-mail addresses.

### 6.1 The home network

- **Both domestic and foreign sites are reachable directly from the servers.** There is
  no corporate proxy and no whitelist to work around — do not set `HTTP_PROXY`,
  `HTTPS_PROXY` or `NO_PROXY` there, and do not try to reach things "through" a gateway.
- A script that downloads from the internet therefore just works. Bind an
  explicit timeout to every outbound call anyway, and make big downloads
  resumable so a dropped connection does not cost the whole file.
- When a download fails, report **which URL failed and how** ("GitHub reset
  after 90 s" is an answer; "it timed out" is not).
- **The home broadband is behind carrier-grade NAT** (the ISP no longer hands out
  public IPs, IPv6 is not used), so router port forwarding cannot work. Public access
  goes through **Tailscale Funnel** (`https://<name>.<tailnet>.ts.net`, HTTPS
  certificate handled by Tailscale, no domain needed); it was tested from the company
  network and from a phone on mobile data. Funnel's bandwidth is limited and its
  reachability from China is not guaranteed.

### 6.2 The production server

A PVE (Proxmox VE) host on the home network.

It runs **Debian 13 (trixie)**, not Ubuntu — PVE is built on Debian. Anything
that names a distribution must use `debian`/`trixie` there: the nginx.org apt
repository is `https://nginx.org/packages/debian trixie nginx`, and an
`ubuntu` URL returns 404. The host also runs Docker and LXC next to the VMs;
do not restart those services as a side effect of a deploy.

- nginx is **already installed and configured** — **1.30.6 (stable)**, the same
  version as the development VM (6.2.1). Both are meant to stay on the
  nginx.org stable line; upgrade them together so a config that passes on the
  VM means the same thing in production. Site configs go in `conf.d/`; the
  nginx.org package has no `sites-enabled/`. Put site configs in
  `/etc/nginx/conf.d/<name>.conf`, then run
  `nginx -t && systemctl reload nginx`. Create `conf.d/` if it is missing.
- PVE means the machine also runs a few **virtual machines**. When something
  on the host misbehaves, check whether it is actually a guest VM before
  blaming the host.
- Apart from the VMs, treat it as an ordinary **Debian server**: systemd
  units, `apt`, the standard directory layout, `nginx` for static sites.
  Scripts must stay Debian/Ubuntu-neutral (`apt-get`, `www-data`, Python
  `venv` for pip packages — system pip is externally managed).
- Deploy is `git pull` in the checkout (`/root/language-learning`), then
  `sudo bash deploy-all-<timestamp>.sh`: the script reads its target from
  `deploy.local.env`, copies the files into the deployment paths and reloads. The
  checkout itself is never what nginx serves.

### 6.2.1 The development VM

An Ubuntu 26.04 arm64 VM used as the test target for the deploy scripts. It is
reachable over SSH with passwordless `sudo`, so `sudo bash deploy-all-<timestamp>.sh`
(with its own `deploy.local.env`) runs there for real. Never grant passwordless
`sudo` on the production host.

### 6.4 The cloud production server (mainland China)

Unlike the home network (6.1), a server in a mainland data centre does **not** reach everything directly:

- **GitHub is slow and unreliable** (a single request took about 8 s when measured): push code from the workstation
  or the development VM, never `git pull` on the server.
- `apt` uses the provider's mirror and PyPI answers in about a second, so installing dependencies works as usual.
- **Edge TTS works from there** (measured: `en-US-AriaNeural`, about 2–3 s for the first synthesis of a word, about 13 KB
  per clip, then served from the cache). Edge Neural TTS stays mandatory (7); espeak-ng remains the fallback only.
- The instance is a lightweight-server plan whose bandwidth peak is a ceiling, not a promise. Traffic is not limited.
- A website for the public on a mainland server needs the ICP filing; until it is approved the provider blocks the
  domain on 80 / 443, so the certificate cannot be issued yet (`enable-tls.sh` explains this when it fails).
- SSH: key only (`harden.sh`), the provider firewall allows 22 / 80 / 443 and nothing else.
- Backups: the daily database backup lands in a directory on the same machine, so it protects against mistakes, not
  against losing the machine. The provider snapshot and the daily pull to the test environment (started from home,
  read-only, because the home broadband is behind NAT) cover that.

### 6.3 Where the work happens

Development happens on a macOS workstation and on the development VM
(6.2.1) in parallel; deployment is a copy to the production host plus a service reload.
The scripts need root, systemd and nginx, so they cannot run on macOS: verify
them on the development VM. A change that has only been verified on the
workstation or the development VM has **not** been verified in production —
say so.

---

## 7. Vocabulary and pronunciation

The vocabulary game teaches **American English**, read by a **female** voice.
This is a product requirement, not a preference.

- **Phonemes**: `word-puzzle/server/ipa.py` is the single source of truth.
  The table is generated from the CMU Pronouncing Dictionary (US
  pronunciations) and converted from ARPAbet to IPA. **Never use ECDICT's
  `phonetic` column** — it holds British transcriptions.
- **Spoken audio**: prefer Edge Neural TTS `en-US-AriaNeural` for natural
  American female speech. Only the English word requested for playback is sent
  to the online voice service during play; generated audio is cached. When
  building an offline page, all English words in the selected bank are sent for
  synthesis and embedded in the HTML. On network or install failure, use local
  espeak-ng `-v en-us+f3` consistently for the whole offline page.
- Teaching abbreviations are spoken as whole words (`word-puzzle/server/tts.py`
  `speakable()`): `sb.` → somebody, `sth.` → something, `etc.` → et cetera, `e.g.` →
  for example, `i.e.` → that is, `vs` → versus; `…` / `...` placeholders become a
  gap and ` / ` alternatives become "or". Cards still show the original text; the
  audio cache and the offline pages are keyed so the card text finds the clip. Add
  new abbreviations there, with a test.
- The browser TTS fallback must pick an `en-US` locale and prefer a
  female-named local voice.

See `/memories/repo/word-puzzle-website.md` for the implementation details.

---

## 8. Public exposure and student data

**This repository is public on GitHub.** Code and documentation may be public; data may
not. Never commit rosters, databases, backups, credentials lists, phone numbers or keys
(`.gitignore` blocks the usual names and `word-puzzle/tests/test_repo_hygiene.py` fails on
tracked data files, phone-like numbers and key-like strings). Use the GitHub no-reply
address as `git config user.email` — the commit author address is published with the
history. See `docs/路线图.md` §5.

Anything reachable through Funnel is **public**: the `*.ts.net` name appears in
certificate-transparency logs, and within a minute of turning Funnel on, scanners
were requesting `/.env`, `/AGENTS.md`, `/CLAUDE.md`, `/config.js` (observed).

- Never point Funnel at a directory listing or a throw-away file server
  (`python3 -m http.server` serves every file in its working directory, dotfiles
  included — a test that ran it in `/root` exposed `/root` until it was stopped).
  Funnel points only at the family nginx (127.0.0.1:8081), which sits in front of a
  backend that requires login for every API call.
- Funnel **does** pass the visitor's address: it arrives in `X-Forwarded-For` (verified on
  2026-11-15: the address recorded for a request through Funnel equalled the sender's
  public IP). nginx copies it into `X-Wp-Edge-Xff`; the backend records the last address
  of that chain after skipping `WP_TRUSTED_PROXIES`. A per-IP rate limit is therefore
  possible later; today login is protected by per-account lockout (5 failures → 15 min)
  and per-student / site-wide attempt limits in the backend.
- The student edition stores what the roster provides (student number, name, class,
  college, department) and everything the site observes: game results and a
  permanent **access log** (`page_views`, `login_events`) with account, IP address,
  device, browser, pages visited and time on page. Nothing is deleted
  automatically and there is no "keep as little as possible" rule — more detail is
  better. The login page deliberately carries no recording notice (owner's decision, 2026-11-20). The roster importer
  still drops phone-number columns (they are not needed), and passwords are stored
  as scrypt hashes, never in the log. Initial passwords are shared with the
  students by the administrator and every account must change its password at the
  first login (`must_change`).
- Browser-facing text that comes from a roster (names, classes) is untrusted:
  escape it on output, and prefix `= + - @` cells in every CSV export.
- Client-supplied `Host` / `X-Forwarded-Host` must not decide any link the
  server generates: set `WP_PUBLIC_HOME_URL`, and let nginx overwrite the headers.
