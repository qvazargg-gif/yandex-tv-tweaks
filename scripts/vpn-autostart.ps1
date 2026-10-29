# Постоянный VPN Android: v2rayNG сам подключается при включении ТВ (к выбранному серверу).
param([string]$Mode = 'on')
. "$PSScriptRoot\common.ps1"
Connect-TV
if ($Mode -eq 'off') {
    Sh 'settings delete secure always_on_vpn_app' | Out-Null
    Sh 'settings delete secure always_on_vpn_lockdown' | Out-Null
    Write-Host 'Автозапуск VPN выключен.' -ForegroundColor Green; exit 0
}
$pkg = Find-Package @('com.v2ray.ang.fdroid', 'com.v2ray.ang')
if (-not $pkg) { Write-Host 'v2rayNG не найден.' -ForegroundColor Red; exit 1 }
Sh "settings put secure always_on_vpn_app $pkg" | Out-Null
Sh 'settings put secure always_on_vpn_lockdown 0' | Out-Null   # если VPN не поднялся - интернет всё равно работает
Write-Host 'Готово. Проверь: выключи ТВ из розетки на 10 секунд, включи, подожди минуту и открой SmartTube.' -ForegroundColor Green
Write-Host 'Если Кинопоиск/Rutube перестали работать через VPN - выключи: vpn-autostart-off.bat' -ForegroundColor Yellow
