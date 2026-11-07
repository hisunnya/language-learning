"""美式女声合成：优先 Edge Neural TTS，失败时回退本地 eSpeak。"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUDIO_DIR = Path(os.environ.get("WP_AUDIO_DIR") or (ROOT / "var" / "audio"))

# edge-tts 使用微软在线神经语音；上传或内置单词只在被朗读时发送。
DEFAULT_VOICE = os.environ.get("WP_TTS_VOICE", "en-US-AriaNeural")
FALLBACK_VOICE = "en-us+f3"
_ALLOWED_VOICES = {"en-US-AriaNeural"}

_lock = threading.Lock()
_edge_path: str | None = None
_edge_checked = False
_edge_retry_after = 0.0
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


def find_edge_tts() -> str | None:
    """查找 edge-tts 命令；部署时通常由 WP_EDGE_TTS 指向专用 venv。"""
    global _edge_path, _edge_checked
    with _lock:
        if _edge_checked:
            return _edge_path
        _edge_checked = True
        configured = os.environ.get("WP_EDGE_TTS", "")
        if configured:
            _edge_path = (configured if Path(configured).is_file()
                          and os.access(configured, os.X_OK)
                          else shutil.which(configured))
        else:
            _edge_path = shutil.which("edge-tts")
        return _edge_path


def available() -> bool:
    """服务器上是否有可用的在线或本地合成器。"""
    global _espeak_works, _last_error
    if find_edge_tts():
        return True
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
                [exe, "-v", FALLBACK_VOICE, "--stdout", "-w", out, "test"],
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
    """当前神经语音音色（固定美式女声）。"""
    v = (DEFAULT_VOICE or "").strip()
    if v not in _ALLOWED_VOICES:
        return "en-US-AriaNeural"
    return v


def _slug(word: str) -> str:
    out = []
    for ch in word.strip().lower():
        if ch.isalnum() and ch.isascii():
            out.append(ch)
        elif ch in " -_":
            out.append("-")
    return "".join(out).strip("-")[:80] or "word"


def _cache_file(word: str, engine: str, voice_name: str, suffix: str) -> Path:
    name = _slug(word)
    key = hashlib.sha1(f"{engine}|{voice_name}|{word}".encode("utf-8")).hexdigest()[:8]
    return AUDIO_DIR / f"{name}.{key}.{suffix}"


def _synth_edge(word: str, exe: str) -> bytes | None:
    """调用神经网络音色生成 MP3；网络故障时短暂冷却再尝试。"""
    global _edge_retry_after, _last_error
    if time.monotonic() < _edge_retry_after:
        return None
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    target = _cache_file(word, "edge-tts", voice(), "mp3")
    if target.exists() and target.stat().st_size > 64:
        return target.read_bytes()

    fd, temp_name = tempfile.mkstemp(prefix="wp-tts-", suffix=".mp3",
                                     dir=AUDIO_DIR)
    os.close(fd)
    os.unlink(temp_name)
    try:
        proc = subprocess.run(
            [exe, "--voice", voice(), "--text", word,
             "--write-media", temp_name, "--no-progress"],
            capture_output=True, timeout=30,
        )
        temp = Path(temp_name)
        if proc.returncode != 0 or not temp.exists() or temp.stat().st_size <= 64:
            _last_error = (proc.stderr.decode("utf-8", "replace").strip()
                           or f"edge-tts 退出码 {proc.returncode}")
            _edge_retry_after = time.monotonic() + 60
            return None
        os.replace(temp_name, target)
        return target.read_bytes()
    except (OSError, subprocess.SubprocessError) as exc:
        _last_error = str(exc)
        _edge_retry_after = time.monotonic() + 60
        return None
    finally:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass


def _synth_espeak(word: str, exe: str | None = None) -> bytes | None:
    """本地 eSpeak 美式女声兜底，返回 WAV 字节。"""
    global _last_error, _espeak_works
    exe = exe or find_espeak()
    if not exe:
        return None
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    target = _cache_file(word, "espeak-ng", FALLBACK_VOICE, "wav")
    if target.exists() and target.stat().st_size > 44:
        return target.read_bytes()

    try:
        proc = _run_espeak(
            [exe, "-v", FALLBACK_VOICE, "--stdout", "-w", str(target), word],
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


def synth(word: str) -> bytes | None:
    """合成单词音频并缓存；优先 MP3 神经语音，失败时使用 WAV 兜底。"""
    word = (word or "").strip()
    if not word:
        return None
    edge = find_edge_tts()
    if edge:
        data = _synth_edge(word, edge)
        if data:
            return data
    return _synth_espeak(word)


def content_type(data: bytes) -> str:
    """返回合成音频对应的 HTTP MIME 类型。"""
    return "audio/wav" if data.startswith(b"RIFF") else "audio/mpeg"


def cache_path(word: str) -> Path | None:
    """某个词对应的缓存文件路径（不存在返回 None）。"""
    if not word:
        return None
    candidates = (
        _cache_file(word.strip(), "edge-tts", voice(), "mp3"),
        _cache_file(word.strip(), "espeak-ng", FALLBACK_VOICE, "wav"),
    )
    return next((target for target in candidates if target.exists()), None)


def describe() -> dict:
    """给前端 /api/meta 用的状态描述。"""
    edge = find_edge_tts()
    exe = find_espeak()
    ok = available()
    return {
        "tts_available": ok,
        "tts_voice": voice() if edge else (FALLBACK_VOICE if ok else ""),
        "tts_engine": "edge-tts" if edge else (Path(exe).name if exe else ""),
        "tts_remote": bool(edge),
        "tts_error": "" if ok else (_last_error or (
            "未安装 edge-tts 或 espeak-ng" if not exe else "espeak-ng 无法运行")),
    }
