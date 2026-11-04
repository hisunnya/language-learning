#!/usr/bin/env python3
"""生成美式音标对照表 ``data/raw/us_ipa.tsv``。

数据来源
--------
**CMU Pronouncing Dictionary**（cmusphinx/cmudict）——
卡内基梅隆大学的标准美式发音词典，收录 13.5 万条词条，
原始格式是 ARPAbet 音素，本脚本转成国际音标。

为什么不用 ECDICT：ECDICT 的 ``phonetic`` 字段是**英式**音标，
跟本项目要求的「美语」不符。

下载（只需一次）::

    curl -L -o /tmp/cmudict.dict \
      https://raw.githubusercontent.com/cmusphinx/cmudict/master/cmudict.dict

生成::

    python3 tools/build_ipa_table.py --cmudict /tmp/cmudict.dict

产物每行 ``word<TAB>/ipa/``，供 ``server/ipa.py`` 运行时查表。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from server.ipa import arpabet_to_ipa  # noqa: E402

OUT = ROOT / "data" / "raw" / "us_ipa.tsv"

_VARIANT_RE = re.compile(r"\(\d+\)$")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cmudict", default="/tmp/cmudict.dict",
                    help="cmudict.dict 路径")
    args = ap.parse_args()

    src = Path(args.cmudict)
    if not src.exists():
        sys.stderr.write(
            f"!! 找不到 {src}\n"
            "   请先下载：\n"
            "     curl -L -o /tmp/cmudict.dict "
            "https://raw.githubusercontent.com/cmusphinx/cmudict/master/cmudict.dict\n")
        return 1

    table: dict[str, str] = {}
    with src.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith(";;;"):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            word = _VARIANT_RE.sub("", parts[0])   # 去掉 read(2) 里的变体标记
            if word in table:
                continue
            ipa = arpabet_to_ipa(" ".join(parts[1:]))
            if ipa:
                table[word] = "/" + ipa + "/"

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as fh:
        for word in sorted(table):
            fh.write(f"{word}\t{table[word]}\n")

    print(f"已写出 {OUT}")
    print(f"  词条 {len(table)}  大小 {OUT.stat().st_size / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
