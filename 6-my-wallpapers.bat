@echo off
chcp 65001 >nul
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\wallpapers.ps1"
if errorlevel 1 goto end
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\launcher.ps1"
if errorlevel 1 goto end
:end
echo.
pause
