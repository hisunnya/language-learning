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
  - `chore(open-webui): bump image to 0.12.4`
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

Two mechanisms are already in use; follow the one that fits the page:

| Mechanism | Where | How it works |
|---|---|---|
| i18n table | `gemma/webapp/frontend/index.html` | A `i18n = { zh: {...}, en: {...} }` object; `applyLang()` walks a list of element ids and writes `textContent`. |
| `data-i18n` attributes | `gemma/datatransfer/static/` | `<tag data-i18n="key">`; a single `applyLang()` swaps every marked node. |
| `data-lang` blocks | `gemma/lora/material-guide.html` | Two parallel blocks, one per language, shown or hidden by a body class. |

Whichever mechanism is used, **the language toggle belongs in the header**,
next to the palette picker.

### 3.2 Multiple colour palettes

- At least **three** palettes, each a named set of CSS custom properties on
  `[data-theme="…"]`, not hard-coded colours scattered through the stylesheet.
- The palette is remembered across reloads (`localStorage`).
- The active palette is marked in the picker (`aria-pressed` / `.active`).
- Every palette needs a name in both languages, and the name should read as
  the two colours it combines (e.g. `翡翠 / 云白` — `Jade / Cloud`).

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
<button type="button" class="theme-chip" data-theme-val="sage"
        data-tooltip-zh="松柏绿" data-tooltip-en="Sage"
        aria-label="松柏绿配色">
  <span class="swatch" style="--swatch-main: #186851; --swatch-bg: #f9fbfa;"></span>
</button>
````

### 3.4 Reference implementations

| Page | Bilingual | Palettes | Picker |
|---|---|---|---|
| `gemma/webapp/frontend/index.html` | i18n table | 3 | top-right, square swatches |
| `gemma/datatransfer/static/index.html` | `data-i18n` | 5 | top-right, square swatches |
| `gemma/lora/material-guide.html` | `data-lang` blocks | 3 | top-right, square swatches |

`gemma/datatransfer/static/` is the most complete example of the picker style.

### 3.5 Adding a new page

A new user-facing page is not done until all of this is in place. Walk the
list in order:

1. **Pick the bilingual mechanism** (§3.1) and put the strings in both
   languages. No hard-coded user-visible text in the markup.
2. **Define at least three palettes** on `[data-theme="…"]` (§3.2), each with
   its own `--bg` / `--accent` / `--line` / … set. Move every hard-coded
   colour out of the stylesheet and into a variable.
3. **Build the picker** (§3.3): small squares in the top-right of the header,
   each split diagonally into that palette's own two colours, each with a
   bilingual tooltip.
4. **Persist both choices** in `localStorage`, and mark the active palette
   with `aria-pressed` (or `.active`).
5. **Test it** (§3.6).

### 3.6 Tests

The frontend test (`gemma/webapp/frontend/test_frontend.cjs`) must fail when a
button ends up without visible text — a button with no id is never filled in
by `applyLang()` and renders as an empty box. Keep that check, and extend the
same idea to new pages: every control either carries an id with a non-empty
label or has static text.

The same applies to the palette style. Each page's test asserts that:

- every palette swatch carries **both** of its colours (`--swatch-main` and
  `--swatch-bg`), so no swatch is indistinguishable from another;
- the split is a hard-stop diagonal gradient (`0 50%` → `50% 100%`);
- the swatch is a **square** (`border-radius: 4px`), not a circle;
- every palette defines its own variable set, so the palettes are really
  different;
- the choice is persisted in `localStorage`.

A regression here must fail the suite rather than ship.

---

## 4. Tests

- Every behaviour change comes with a test. The suites are plain
  `unittest` (Python) and `node:test`/`assert` (JavaScript) — no new
  frameworks without a reason.
- Run the suite before committing. A change that cannot be verified on this
  machine must say so explicitly instead of claiming success.
- Verification means the real path, not only unit tests: a unit test with mock
  data cannot catch a changed upstream dataset or an unreachable registry.

---

## 5. Repository layout

- **The deployment directory is not the git working tree.** A `git pull` does
  not change what the running service serves; the code must be copied to
  `/opt/prelude-forge/gemma` and the service restarted. See
  `gemma/webapp/DEPLOYMENT.md`.
- Directory names are lowercase, because production is Ubuntu and paths are
  case-sensitive there. `Gemma/` became `gemma/` for this reason.
- Model and product names keep their own capitalisation (`Gemma 4 31B`,
  `Gemma4Config`) — those are names, not paths.

---

## 6. Servers and network

### 6.1 The three GPU servers

| Host | GPU | Role | Network |
|---|---|---|---|
| `aiinfraservice-dev-k8s-worker-3` (RTX 4090 x8, `10.200.200.74`) | 8×RTX 4090 24GB | GPU 0-3: Gemma production inference; GPU 4-7: training / benchmark / CosyVoice | **光环新网托管机房** — direct access to domestic (China-compliant) internet, **no corporate proxy** |
| `s133m0000022` (V100 DGX-1) | 8×V100 32GB, NVLink | GPU 0-3: Qwen-Turbo; GPU 4-7: M.O.G.-SEC-27B | **公司内网** — internet only through the `s133m0000025` proxy |
| `s133m0000023` (V100 x8) | 8×V100 32GB | WeMM-Embedding, Qwen3-VL embedding | **公司内网** — internet only through the `s133m0000025` proxy |

The development host `c133vl000001` (aarch64, no GPU) also reaches the internet
through the `s133m0000025` proxy.

### 6.2 The corporate proxy

```bash
export HTTP_PROXY=http://s133it4ada025.cn133.corpintra.net:3128
export HTTPS_PROXY=http://s133it4ada025.cn133.corpintra.net:3128
export NO_PROXY=localhost,127.0.0.1,::1,.cn133.corpintra.net,.corpintra.net
```

- `s133it4ada025.cn133.corpintra.net:3128` — the proxy host (resolves to
  `53.89.34.206`). It is named after the machine `s133m0000025`.
- It is the **only** way out to the internet for the company-internal V100
  machines and for the development host.
- It reaches **domestic** sites directly and **foreign** sites through a
  **whitelist** (see §6.3).

`NO_PROXY` matters: Python's `httpx`/`aiohttp` do not understand CIDR
notation, so container names and internal domains must be listed by name.
`platform/open-webui/README.md` carries a worked example of a `NO_PROXY` that
also has to include `.corpdir.net` (the LDAP server is not under
`.corpintra.net`).

### 6.3 Foreign sites are whitelist-gated — ask, do not work around it

On the proxy, foreign sites are reachable **only if they are on the
whitelist**. A site that is not on it fails to connect.

**When something foreign cannot be reached from `s133m0000022`,
`s133m0000023` or the development host, tell the user which host or URL is
blocked and ask them to add it to the whitelist.** Do not:

- retry in a loop hoping it is a transient failure;
- silently switch to a mirror and present the result as if the original
  source had worked;
- claim the data was fetched when it came from somewhere else — record the
  actual source instead.

The 4090 machine is the exception: it reaches domestic internet directly, so
Hugging Face and similar are reachable there only when the site is
domestic-accessible or mirrored. Use the ModelScope (魔搭) path in
`infra/benchmark/` for datasets, and mirror endpoints such as
`https://hf-mirror.com` where the official host is not.

### 6.4 Consequences for tooling

- Any script that downloads from the internet must work on **both** network
  models. Prefer a source that is reachable from the 4090 machine (domestic
  mirror) as the primary path, and the proxy as the fallback, not the other
  way round.
- Bind an explicit timeout to every outbound call. The proxy resets
  long-running transfers (image pulls over 1 GB were reset mid-transfer), so
  a download must be resumable or retryable.
- When a download fails, report **which** of the two paths failed and why.
  "It timed out" is not an answer; "HF via the proxy resets after 90 s while
  ModelScope returns 200" is.

