# YouTube для ТВ без рекламы: SmartTube (официальный релиз с GitHub автора, github.com/yuliskov/SmartTube).
# Если версия устарела - поменяй $url на свежий *_universal.apk со страницы релизов.
. "$PSScriptRoot\common.ps1"
$url = 'https://github.com/yuliskov/SmartTube/releases/download/32.68s/SmartTube_stable_32.68_universal.apk'
$apk = Join-Path $Tools 'SmartTube.apk'
if (-not (Download $url $apk)) { exit 1 }
Connect-TV
if (-not (Install-Apk $apk)) { Write-Host 'Установка не прошла.' -ForegroundColor Red; exit 1 }
$pkg = Find-Package @('org.smarttube.stable', 'com.teamsmart.videomanager.tv', 'com.liskovsoft.smarttubetv.beta')
Sh "monkey -p $pkg -c android.intent.category.LEANBACK_LAUNCHER 1" | Out-Null
Start-Sleep 8
Shot 'smarttube.png'
Write-Host ''
Write-Host "Готово: SmartTube ($pkg) стоит и попадёт в док нового экрана." -ForegroundColor Green
Write-Host 'Если пишет "Unable to resolve host www.youtube.com" - YouTube недоступен в твоей сети,' -ForegroundColor Yellow
Write-Host 'нужен твой VPN (см. vpn-*.bat в README).' -ForegroundColor Yellow
