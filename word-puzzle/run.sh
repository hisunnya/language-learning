#!/usr/bin/env bash
# 本地开发：一条命令把整个站点跑起来。
#
#   ./run.sh              # http://127.0.0.1:8000
#   ./run.sh 9000         # 换端口
#
# 依赖：只需要 Python 3.8+（标准库），不需要 pip install。
set -euo pipefail

cd "$(dirname "$0")"

PORT="${1:-${WP_PORT:-8000}}"
HOST="${WP_HOST:-127.0.0.1}"
PY="${PYTHON:-python3}"

if ! command -v "$PY" >/dev/null 2>&1; then
  echo "找不到 $PY，请先安装 Python 3.8+" >&2
  exit 1
fi

if [ ! -f data/pep_curriculum.json ]; then
  echo "内置词库缺失，正在生成……"
  "$PY" tools/build_seed_data.py
fi

if [[ -z "${WP_EDGE_TTS:-}" && -x "$PWD/var/tts-venv/bin/edge-tts" ]]; then
  export WP_EDGE_TTS="$PWD/var/tts-venv/bin/edge-tts"
fi

echo
echo "  word-puzzle 开发服务器"
echo "  地址：http://${HOST}:${PORT}/"
echo "  停止：Ctrl-C"
echo
exec "$PY" -m server.app --host "$HOST" --port "$PORT"
