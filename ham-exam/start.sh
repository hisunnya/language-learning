#!/usr/bin/env bash
# 一键启动本地服务
cd "$(dirname "$0")" || exit 1
PORT="${1:-8080}"
echo "─────────────────────────────────────────────"
echo "  业余无线电操作证 · 模拟考试系统"
echo "  请在浏览器打开： http://127.0.0.1:${PORT}"
echo "  按 Ctrl+C 停止"
echo "─────────────────────────────────────────────"
if command -v python3 >/dev/null 2>&1; then
  python3 -m http.server "$PORT"
elif command -v python >/dev/null 2>&1; then
  python -m SimpleHTTPServer "$PORT"
elif command -v npx >/dev/null 2>&1; then
  npx --yes serve -l "$PORT" .
else
  echo "未找到 python3 / python / npx，直接双击 index.html 也能使用。"
  exit 1
fi
