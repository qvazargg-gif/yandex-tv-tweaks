# Шаг 1: только смотрит. Модель, Android, кто домашний экран, все пакеты, память + бэкап состояния.
. "$PSScriptRoot\common.ps1"
Connect-TV

$stamp = Get-Date -Format 'yyyyMMdd-HHmm'
$out = Join-Path $Data "inspect-$stamp"
New-Item -ItemType Directory -Force $out | Out-Null

$rep = @('===== УСТРОЙСТВО =====')
foreach ($p in 'ro.product.manufacturer', 'ro.product.model', 'ro.build.version.release', 'ro.build.fingerprint') {
    $rep += "$p = $(Sh "getprop $p")"
}
$rep += '', '===== ДОМАШНИЙ ЭКРАН (кнопка Home) ====='
$rep += Sh 'cmd package resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.HOME'
$rep += '', '===== ЭТО ЯНДЕКС ТВ? ====='
$rep += $(if (Sh 'pm path com.yandex.tv.home') { 'да, com.yandex.tv.home найден' } else { 'НЕТ - эти скрипты рассчитаны на Яндекс ТВ, дальше осторожно' })
$rep += '', '===== УЖЕ ОТКЛЮЧЁННЫЕ ====='
$rep += Sh 'pm list packages -d'
$rep += '', '===== УСТАНОВЛЕННЫЕ ПОЛЬЗОВАТЕЛЕМ ====='
$rep += Sh 'pm list packages -3'
$rep += '', '===== СИСТЕМНЫЕ ====='
$rep += Sh 'pm list packages -s -f'
$rep += '', '===== ПАМЯТЬ ====='
$rep += ((& $Adb -s $Target shell 'dumpsys meminfo' 2>$null | Select-Object -First 70) -join "`n")

$rep | Set-Content (Join-Path $out 'report.txt') -Encoding UTF8
Sh 'pm list packages -e' | Set-Content (Join-Path $out 'backup-enabled.txt') -Encoding UTF8
Sh 'pm list packages -d' | Set-Content (Join-Path $out 'backup-disabled.txt') -Encoding UTF8
Shot "inspect-$stamp.png"

Write-Host ''
Write-Host "Готово, на ТВ ничего не менялось. Отчёт: $out\report.txt" -ForegroundColor Green
Invoke-Item $out
