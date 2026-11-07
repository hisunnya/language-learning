#!/usr/bin/env bash
# Check and install all Debian/Ubuntu packages needed by the app and its full feature set.
set -euo pipefail

PACKAGES=(
  python3
  python3-venv
  rsync
  nginx
  systemd
  passwd
  poppler-utils
  tesseract-ocr
  tesseract-ocr-eng
  tesseract-ocr-chi-sim
  espeak-ng
)

missing=()
for package in "${PACKAGES[@]}"; do
  status="$(dpkg-query -W -f='${db:Status-Status}' "$package" 2>/dev/null || true)"
  if [[ "$status" == "installed" ]]; then
    printf '  OK      %s\n' "$package"
  else
    printf '  MISSING %s\n' "$package"
    missing+=("$package")
  fi
done

if [[ ${#missing[@]} -gt 0 ]]; then
  if [[ $(id -u) -ne 0 ]]; then
    printf '\n请使用 sudo 运行此脚本以安装缺少的包。\n' >&2
    exit 1
  fi
  if ! command -v apt-get >/dev/null 2>&1; then
    printf '错误：当前系统没有 apt-get，无法自动安装依赖。\n' >&2
    exit 1
  fi

  printf '\n安装缺少的包：%s\n' "${missing[*]}"
  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "${missing[@]}"
else
  printf '\n所有系统包都已安装，跳过安装。\n'
fi

for command_name in python3 nginx systemctl useradd pdftotext pdftoppm tesseract espeak-ng; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    printf '错误：安装后仍找不到命令 %s。\n' "$command_name" >&2
    exit 1
  fi
done

python3 - <<'PY'
import http.server
import sqlite3
import xml.etree.ElementTree
import zipfile
import zlib
PY

printf '依赖检查通过。\n'