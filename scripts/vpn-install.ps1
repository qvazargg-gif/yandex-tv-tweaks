# Ставит v2rayNG (официальный релиз с GitHub, github.com/2dust/v2rayNG) и проверяет контрольную сумму.
# Сам VPN-сервер/подписку ты берёшь у своего VPN-сервиса.
. "$PSScriptRoot\common.ps1"
$url = 'https://github.com/2dust/v2rayNG/releases/download/2.3.11/v2rayNG_2.3.11-fdroid_universal.apk'
$sha = '7d92b7d64ef1d4c74ac5dc07a22e2080cace8459440b1f99ace878963e41e662'
$apk = Join-Path $Tools 'v2rayNG.apk'
if (-not (Download $url $apk $sha)) { exit 1 }
Connect-TV
if (-not (Install-Apk $apk)) { Write-Host 'Установка не прошла.' -ForegroundColor Red; exit 1 }
Write-Host 'Готово. Дальше: впиши ссылку на подписку в vpn-subscription.txt и запусти vpn-2-import.bat' -ForegroundColor Green
