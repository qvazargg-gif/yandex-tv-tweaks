@echo off
chcp 65001 >nul
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\vpn-connect.ps1"
if errorlevel 1 goto end
:end
echo.
pause
