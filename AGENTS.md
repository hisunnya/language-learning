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
| `word-puzzle/web/*.html` | — | — | — | ⚠️ to be brought up to §3 |
| `topic-app/topic-app/index.html` | — | 3 (different picker) | — | ⚠️ to be brought up to §3 |
| `ham-exam/index.html` | — | — | — | ⚠️ to be brought up to §3 |

The three ⚠️ pages predate this convention. When you touch one of them, bring
it along: the target style is `hub/`, not the reverse. Do not "fix" the hub to
match the older pages.

Note that `topic-app` already has three colour themes, but its picker is a
row of three stacked colour bars with a text label — that is **not** the house
style. Converting it means replacing the picker with diagonal-split squares
and moving the theme variables onto `[data-theme="…"]`.

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
- Run the suite before committing. A change that cannot be verified on this
  machine must say so explicitly instead of claiming success.
- Verification means the real path, not only unit tests: a unit test with mock
  data cannot catch a changed upstream dataset or an unreachable registry.

```bash
cd word-puzzle && python3 -m unittest discover -s tests -v   # 后端用例
cd hub        && python3 -m unittest discover -s tests -v   # 样式规范用例
cd word-puzzle && python3 tools/check_js.py                  # JS 语法体检
```

---

## 5. Repository layout

```
language-learning/
├── AGENTS.md               # 本文件
├── README.md               # 仓库总说明（中文）
├── hub/                    # 总主页「语林 Lingua Grove」—— 三个工具的入口
├── word-puzzle/            # 词境 Lexica —— 英语词汇游戏（网站版）
├── topic-app/              # 每日话题 Daily Topics —— 初中生家庭讨论
└── ham-exam/               # 无线电执照 Ham Exam —— 业余无线电模拟考试
```

- **The deployment directory is not the git working tree.** A `git pull` does
  not change what the running service serves; the code has to be copied to the
  server and the service restarted.
- Directory names are lowercase, because production is Ubuntu and paths are
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
| Portal (hub) | 语林 | Lingua Grove | `hub/` |

The vocabulary game was called 「单词消消乐」 while it was a single file. That
was a working name, not a product name — the product covers word and language
games generally, so it is 「词境 Lexica」 now. Use the product names above in
titles, headers, README and the hub.

### 5.2 Deployment layout on the server

| Path | Holds |
|---|---|
| `/srv/word-puzzle` | 词境 Lexica 的后端代码（`word-puzzle/deploy/install.sh` 装的） |
| `/var/lib/word-puzzle` | 词境的 SQLite 数据库和离线页 |
| `/var/www/topic-app` | 每日话题（纯静态） |
| `/var/www/ham-exam` | 无线电执照（纯静态） |
| `/var/www/lingua-grove` | 总主页（纯静态） |

`word-puzzle/deploy/install.sh` is the only installer in the repository. The
other three are static trees copied into `/var/www/`; `hub/deploy/` and
`topic-app/部署说明.md` describe their nginx blocks.

---

## 6. Servers and network

### 6.1 The home network

The household LAN is **10.0.0.0/20**.

- **Both domestic and foreign sites are reachable directly.** There is no
  corporate proxy and no whitelist to work around — do not set `HTTP_PROXY`,
  `HTTPS_PROXY` or `NO_PROXY` here, and do not try to reach things "through"
  a gateway.
- A script that downloads from the internet therefore just works. Bind an
  explicit timeout to every outbound call anyway, and make big downloads
  resumable so a dropped connection does not cost the whole file.
- When a download fails, report **which URL failed and how** ("GitHub reset
  after 90 s" is an answer; "it timed out" is not).

### 6.2 The production server

**10.1.1.93** — PVE (Proxmox VE) host.

- nginx is **already installed and configured**. Add sites as
  `/etc/nginx/sites-available/<name>` plus a symlink into
  `sites-enabled/`, then `nginx -t && systemctl reload nginx`.
- PVE means the machine also runs a few **virtual machines**. When something
  on the host misbehaves, check whether it is actually a guest VM before
  blaming the host.
- Apart from the VMs, treat it as an ordinary **Ubuntu server**: systemd
  units, `apt`, the standard directory layout, `nginx` for static sites.
- Deploy by copying files in and reloading — `git pull` on the server is not
  part of the flow.

### 6.3 Where the work happens

Development happens on a workstation inside the home network; deployment is a
copy to 10.1.1.93 plus a service reload. A change that has only been verified
on the workstation has **not** been verified in production — say so.

---

## 7. Vocabulary and pronunciation

The vocabulary game teaches **American English**, read by a **female** voice.
This is a product requirement, not a preference.

- **Phonemes**: `word-puzzle/server/ipa.py` is the single source of truth.
  The table is generated from the CMU Pronouncing Dictionary (US
  pronunciations) and converted from ARPAbet to IPA. **Never use ECDICT's
  `phonetic` column** — it holds British transcriptions.
- **Spoken audio**: espeak-ng `-v en-us+f3`. `en-us` is American English and
  `+f3` is the female variant of that voice. `+fN` is female, `+mN` is male —
  verified by measuring the fundamental frequency (`en-us+f3` ≈ 208 Hz,
  `en-us` ≈ 101 Hz).
- The voice whitelist accepts only `en-us` and `en-us+f1..f9`. A misconfigured
  value falls back to `en-us+f3`, so the site **cannot** read in British or
  Chinese.
- The browser TTS fallback must pick an `en-US` locale and prefer a
  female-named local voice.

See `/memories/repo/word-puzzle-website.md` for the implementation details.
