@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PORT=8080
echo ---------------------------------------------
echo   业余无线电操作证 - 模拟考试系统
echo   请在浏览器打开： http://127.0.0.1:%PORT%
echo   按 Ctrl+C 停止
echo ---------------------------------------------
python -m http.server %PORT%
