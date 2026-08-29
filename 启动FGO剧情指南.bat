@echo off
chcp 65001 >nul
title FGO 剧情追剧指南
where node >nul 2>nul
if errorlevel 1 (
  echo [错误] 未检测到 Node.js，请先安装：https://nodejs.org
  pause
  exit /b 1
)
echo 正在启动本地服务器...
node "%~dp0server.js"
pause
