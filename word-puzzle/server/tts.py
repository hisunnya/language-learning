"""发音音频：保证**美式女声**。

两条路
------
1. ** espeak-ng（服务器端）** —— ``espeak-ng -v en-us+f3``。
   ``en-us`` 是美式英语，``+f3`` 是该音色的女声变体，
   输出跟客户端装了什么语音包无关，**永远不会读成英式或中文**。
2. **浏览器 TTS（前端兜底）** —— 见 ``web/js/game-ui.js``，
   在可用音色里挑 ``en-US`` 且是女声的那一个。

服务器端渲染的好处是所有学生听到的都一样，而且离线测试页也能带上音频。

音频文件缓存在 ``var/audio/``，同名文件只生成一次。
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUDIO_DIR = Path(os.environ.get("WP_AUDIO_DIR") or (ROOT / "var" / "audio"))

# espeak-ng 的音色：en-us = 美式英语，+f3 = 女声（Female 3）
DEFAULT_VOICE = os.environ.get("WP_TTS_VOICE", "en-us+f3")

# 允许的音色白名单：必须是 en-us 开头，且带女声变体 +fN
_ALLOWED_VOICE_RE = re.compile(r"^en-us(\+f[1-9])?$")

_lock = threading.Lock()
_espeak_path: str | None = None
_espeak_checked = False
_espeak_works = False
_last_error = ""


def _data_dirs() -> list[str]:
    """espeak-ng 语音数据目录的候选路径。

    Debian/Ubuntu 把 ``espeak-ng-data`` 装在 ``/usr/lib/<arch>/espeak-ng-data``，
    而 espeak-ng 自己的编译进去的默认路径有时对不上，
    所以这里把常见位置都找出来，合成时用 ``ESPEAK_DATA_PATH`` 指过去。
    """
    out: list[str] = []
    env = os.environ.get("ESPEAK_DATA_PATH")
    if env:
        out.append(env)
    out.extend([
        "/usr/share/espeak-ng-data",
        "/usr/lib/espeak-ng-data",
        "/usr/local/share/espeak-ng-data",
        "/usr/local/lib/espeak-ng-data",
    ])
    # 架构相关目录：/usr/lib/aarch64-linux-gnu/espeak-ng-data
    for base in ("/usr/lib", "/usr/local/lib"):
        try:
            for child in sorted(Path(base).glob("*-linux-*")):
                out.append(str(child / "espeak-ng-data"))
        except OSError:
            pass
    seen: set[str] = set()
    return [d for d in out if not (d in seen or seen.add(d))]


def _run_espeak(args: list[str], timeout: int = 20) -> subprocess.CompletedProcess:
    """跑 espeak-ng，自动带上能找到的语音数据目录。"""
    env = dict(os.environ)
    for d in _data_dirs():
        if Path(d).is_dir() and (Path(d) / "phontab").exists():
            env["ESPEAK_DATA_PATH"] = d
            break
    return subprocess.run(args, capture_output=True, timeout=timeout, env=env)


def find_espeak() -> str | None:
    """找 espeak-ng 可执行文件（进程内缓存结果）。"""
    global _espeak_path, _espeak_checked
    with _lock:
        if _espeak_checked:
            return _espeak_path
        _espeak_checked = True
        found = shutil.which("espeak-ng") or shutil.which("espeak")
        if found:
            _espeak_path = found
        return _espeak_path


def available() -> bool:
    """服务器上能不能生成音频。

    不只看文件在不在，还**实际合成一句**试试：
    只装了二进制但缺 ``espeak-ng-data``（语音数据目录）时，
    ``--version`` 照样返回 0，真合成却会失败——
    不探一下，前端就会以为服务端能用，白等一个空响应。
    """
    global _espeak_works, _last_error
    exe = find_espeak()
    if not exe:
        return False
    with _lock:
        if _espeak_works:
            return True
    ok = False
    try:
        with tempfile.TemporaryDirectory(prefix="wp-tts-") as tmp:
            out = os.path.join(tmp, "probe.wav")
            proc = _run_espeak(
                [exe, "-v", voice(), "--stdout", "-w", out, "test"],
            )
            ok = (proc.returncode == 0
                  and os.path.exists(out)
                  and os.path.getsize(out) > 44)
            if not ok:
                _last_error = (proc.stderr.decode("utf-8", "replace").strip()
                               or f"espeak-ng 退出码 {proc.returncode}")
    except (OSError, subprocess.SubprocessError) as exc:
        _last_error = str(exc)
        ok = False
    with _lock:
        _espeak_works = ok
    return ok


def voice() -> str:
    """当前使用的音色（一定是美式）。"""
    v = (DEFAULT_VOICE or "").strip()
    if not _ALLOWED_VOICE_RE.match(v):
        # 配置被改坏了就退回默认的美式女声
        return "en-us+f3"
    return v


def _slug(word: str) -> str:
    out = []
    for ch in word.strip().lower():
        if ch.isalnum() and ch.isascii():
            out.append(ch)
        elif ch in " -_":
            out.append("-")
    return "".join(out).strip("-")[:80] or "word"


def synth(word: str) -> bytes | None:
    """把单词合成成 WAV 字节；失败返回 None。

    结果按单词缓存到 ``var/audio/``。
    """
    global _last_error, _espeak_works
    exe = find_espeak()
    if not exe:
        return None
    word = (word or "").strip()
    if not word:
        return None

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    name = _slug(word)
    # 加音色的哈希前缀，换音色后缓存自动失效
    key = hashlib.sha1(f"{voice()}|{word}".encode("utf-8")).hexdigest()[:8]
    target = AUDIO_DIR / f"{name}.{key}.wav"

    if target.exists() and target.stat().st_size > 44:
        return target.read_bytes()

    try:
        proc = _run_espeak(
            [exe, "-v", voice(), "--stdout", "-w", str(target), word],
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0 or not target.exists():
        # espeak-ng 存在但跑不起来（缺库 / 缺 espeak-ng-data）——记下来，
        # 让 /api/meta 能报出真实原因，别让前端以为只是「没装」。
        _last_error = (proc.stderr.decode("utf-8", "replace").strip()
                       or f"espeak-ng 退出码 {proc.returncode}")
        with _lock:
            _espeak_works = False
        return None
    try:
        data = target.read_bytes()
    except OSError:
        return None
    return data or None


def cache_path(word: str) -> Path | None:
    """某个词对应的缓存文件路径（不存在返回 None）。"""
    if not word:
        return None
    name = _slug(word)
    key = hashlib.sha1(f"{voice()}|{word.strip()}".encode("utf-8")).hexdigest()[:8]
    target = AUDIO_DIR / f"{name}.{key}.wav"
    return target if target.exists() else None


def describe() -> dict:
    """给前端 /api/meta 用的状态描述。"""
    exe = find_espeak()
    ok = available()
    return {
        "tts_available": ok,
        "tts_voice": voice() if ok else "",
        "tts_engine": Path(exe).name if exe else "",
        "tts_error": "" if ok else (_last_error or (
            "未安装 espeak-ng" if not exe else "espeak-ng 无法运行")),
    }
