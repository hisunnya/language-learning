"""语音识别（排排坐的朗读评分用）：本机离线模型 faster-whisper，不把录音发给任何第三方。

后端本身只用 Python 标准库；识别在单独的虚拟环境里跑（和 Edge 语音一样），每次起一个子进程：
``<WP_ASR_PYTHON> tools/asr_worker.py --model base.en --models-dir … 录音.wav`` → 打印 ``{"text": "…"}``。
子进程跑完就退出，模型占的内存（几百 MB）随之释放，2 核 2G 的服务器也扛得住；同一时间只跑一个（见 recordings.py 的队列）。

评分只看「转出来的词和标准句子对上多少」：学生不用读得多标准，能让系统转成正确的单词就行。
没装识别（WP_ASR_PYTHON 不存在）时 available() 为 False，录音照收、照给「提交朗读」的分，只是没有奖励分。
"""
from __future__ import annotations

import difflib
import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKER = ROOT / "tools" / "asr_worker.py"
_last_error = ""


def python() -> str:
    return os.environ.get("WP_ASR_PYTHON", "/opt/word-puzzle-family/asr-venv/bin/python")


def model() -> str:
    return os.environ.get("WP_ASR_MODEL", "base.en")


def models_dir() -> str:
    return os.environ.get("WP_ASR_MODELS_DIR", "/opt/word-puzzle-family/asr-models")


def available() -> bool:
    """装了识别的虚拟环境、而且模型已经下载好（安装时下载；服务运行时不联网）。"""
    models = Path(models_dir())
    return os.access(python(), os.X_OK) and WORKER.exists() and models.is_dir() and any(models.iterdir())


def transcribe(wav: str | Path, timeout: int = 180) -> str | None:
    """返回识别出的英文（可能是空串 = 没听到话）；识别本身出错返回 None。"""
    global _last_error
    if not available():
        _last_error = "没有安装语音识别"
        return None
    try:
        env = dict(os.environ, HF_HUB_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1", HF_HOME=models_dir())
        proc = subprocess.run([python(), str(WORKER), "--model", model(), "--models-dir", models_dir(), "--offline", "--", str(wav)],
                              capture_output=True, timeout=timeout, env=env)
    except (OSError, subprocess.SubprocessError) as exc:
        _last_error = str(exc)
        return None
    if proc.returncode != 0:
        _last_error = proc.stderr.decode("utf-8", "replace").strip()[-500:] or "识别退出码 %d" % proc.returncode
        return None
    try:
        return str(json.loads(proc.stdout.decode("utf-8").strip().splitlines()[-1]).get("text", "")).strip()
    except (ValueError, IndexError) as exc:
        _last_error = "识别输出看不懂：%s" % exc
        return None


def last_error() -> str:
    return _last_error


# ------------------------------------------------------------------ 比对

_NUM = {"0": "zero", "1": "one", "2": "two", "3": "three", "4": "four", "5": "five", "6": "six", "7": "seven",
        "8": "eight", "9": "nine", "10": "ten"}


def words(text: str) -> list[str]:
    """比对用的词：小写，弯引号换直引号，去掉标点（单词里的 ' 和 - 保留），单个数字换成英文。"""
    text = (text or "").lower().replace("’", "'").replace("‘", "'")
    out = []
    for w in re.findall(r"[a-z0-9]+(?:['-][a-z0-9]+)*", text):
        out.append(_NUM.get(w, w))
    return out


def accuracy(reference: str, heard: str) -> float:
    """标准句子里有多少比例的词，按顺序在识别结果里出现了（0..1）。多读的词不扣分。"""
    ref, got = words(reference), words(heard)
    if not ref:
        return 0.0
    matcher = difflib.SequenceMatcher(a=ref, b=got, autojunk=False)
    same = sum(block.size for block in matcher.get_matching_blocks())
    return round(same / len(ref), 3)


def missing(reference: str, heard: str) -> list[int]:
    """标准句子里没对上的词的位置（页面上可以标出来）。"""
    ref, got = words(reference), words(heard)
    matcher = difflib.SequenceMatcher(a=ref, b=got, autojunk=False)
    hit = set()
    for block in matcher.get_matching_blocks():
        hit.update(range(block.a, block.a + block.size))
    return [i for i in range(len(ref)) if i not in hit]
