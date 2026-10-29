# Передаёт подписку (или одну ссылку vless://, vmess://, ss://...) из vpn-subscription.txt в v2rayNG -
# без ввода текста пультом. Файл vpn-subscription.txt личный и в git не попадает.
. "$PSScriptRoot\common.ps1"
$file = Join-Path $Root 'vpn-subscription.txt'
$sub = if (Test-Path $file) { (Get-Content $file -Encoding UTF8 | Where-Object { $_ -and -not $_.StartsWith('#') } | Select-Object -First 1) } else { '' }
if (-not $sub) {
    "# Вставь на следующую строку ссылку на подписку или конфиг от своего VPN-сервиса и сохрани файл" | Set-Content $file -Encoding UTF8
    Write-Host 'Открываю vpn-subscription.txt - вставь туда ссылку, сохрани и запусти снова.' -ForegroundColor Yellow
    Start-Process notepad.exe $file; exit 1
}
Connect-TV
$pkg = Find-Package @('com.v2ray.ang.fdroid', 'com.v2ray.ang')
if (-not $pkg) { Write-Host 'v2rayNG не найден - сначала vpn-1-install.bat' -ForegroundColor Red; exit 1 }
$enc = [Uri]::EscapeDataString($sub.Trim())
$hostPart = if ($sub -match '^https?://') { 'install-sub' } else { 'install-config' }
Sh "am start -a android.intent.action.VIEW -d 'v2rayng://${hostPart}?url=$enc' $pkg" | Out-Null
Start-Sleep 8
Shot 'vpn-import.png'
Write-Host 'Готово. Если список серверов пустой: в v2rayNG меню (три точки) -> "Обновить подписку".' -ForegroundColor Green
Write-Host 'Подключиться: vpn-3-connect.bat (нажимает кнопку запуска за тебя).' -ForegroundColor Green
