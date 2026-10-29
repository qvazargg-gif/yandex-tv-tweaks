# Заставка "Ретро-аркада" (входит в лаунчер). Старые настройки заставки сохраняются, restore.bat их вернёт.
. "$PSScriptRoot\common.ps1"
Connect-TV
$ours = 'com.mihir.tvhome/.Screensaver'
$before = Join-Path $Data 'screensaver-before.txt'
if (-not (Sh 'dumpsys package com.mihir.tvhome | grep -i Screensaver')) {
    Write-Host 'Сначала поставь новый экран: 3-launcher.bat' -ForegroundColor Red; exit 1
}
if (-not (Test-Path $before)) {
    @("screensaver_enabled=$(Sh 'settings get secure screensaver_enabled')"
      "screensaver_components=$(Sh 'settings get secure screensaver_components')"
      "screensaver_default_component=$(Sh 'settings get secure screensaver_default_component')") |
        Set-Content $before -Encoding UTF8
}
Sh 'settings put secure screensaver_enabled 1' | Out-Null
Sh "settings put secure screensaver_components $ours" | Out-Null
Sh "settings put secure screensaver_default_component $ours" | Out-Null
$ms = Sh 'settings get system screen_off_timeout'
if ($ms -match '^\d+$') { Write-Host "Заставка включится после $([math]::Round([int64]$ms / 60000, 1)) мин без действий (меняется в настройках ТВ)." }
Write-Host 'Показываю заставку для проверки...' -ForegroundColor Cyan
Sh 'am start -n com.android.systemui/.Somnambulator' | Out-Null
Start-Sleep 10
Shot 'screensaver.png'
Write-Host 'Готово. Любая кнопка на пульте - выход из заставки.' -ForegroundColor Green
