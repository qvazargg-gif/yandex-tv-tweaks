@echo off
chcp 65001 >nul
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\vpn-autostart.ps1" -Mode on
if errorlevel 1 goto end
:end
echo.
pause
