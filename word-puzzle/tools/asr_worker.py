#!/usr/bin/env python3
"""语音识别子进程：在装了 faster-whisper 的虚拟环境里运行（不是后端用的系统 Python）。

    <venv>/bin/python tools/asr_worker.py --model base.en --models-dir /opt/…/asr-models -- 录音.wav
    → {"text": "Her success speaks for itself ..."}

* 只认英语（language="en"）；不给「标准答案」当提示词 —— 否则模型会把含糊的读音往答案上猜，分数就不真实了。
* vad_filter：先切掉没有人声的部分，录了一段安静（或只有杂音）时得到空字符串，而不是模型编出来的话。
* 模型第一次用时下载到 --models-dir；国内服务器连不上下载站时，从工作站把这个目录整个拷过去（见部署说明）。
"""
from __future__ import annotations

import argparse
import json
import os
import sys


def load(path: str):
    """16 kHz 单声道 WAV（服务器先用 ffmpeg 转好）自己读成采样数组交给模型，不经过 PyAV：
    PyAV 新版本改过接口（faster-whisper 1.2 + av 19 会报 metadata_errors 错），自己读最稳。其他格式才交给 faster-whisper 自己解码。"""
    import wave
    import numpy as np
    try:
        with wave.open(path, "rb") as w:
            if w.getnchannels() == 1 and w.getsampwidth() == 2 and w.getframerate() == 16000:
                return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    except (wave.Error, EOFError):
        pass
    return path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="base.en")
    ap.add_argument("--models-dir", default="")
    ap.add_argument("--threads", type=int, default=int(os.environ.get("WP_ASR_THREADS", "2")))
    ap.add_argument("--offline", action="store_true", help="只用已经下载好的模型，不联网")
    ap.add_argument("wav")
    args = ap.parse_args()
    from faster_whisper import WhisperModel          # 只在识别的虚拟环境里有
    model = WhisperModel(args.model, device="cpu", compute_type="int8", cpu_threads=args.threads,
                         download_root=args.models_dir or None, local_files_only=args.offline)
    segments, _info = model.transcribe(load(args.wav), language="en", beam_size=1, vad_filter=True,
                                       condition_on_previous_text=False)
    text = " ".join(seg.text.strip() for seg in segments).strip()
    print(json.dumps({"text": text}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
