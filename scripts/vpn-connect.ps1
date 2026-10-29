# Нажимает в v2rayNG то, до чего не дотянуться пультом: вкладка подписки -> первый сервер -> запуск.
# Координаты под экран 1920x1080 и v2rayNG 2.3.x. Снимок после каждого шага - в data\screenshots.
. "$PSScriptRoot\common.ps1"
Connect-TV
$pkg = Find-Package @('com.v2ray.ang.fdroid', 'com.v2ray.ang')
if (-not $pkg) { Write-Host 'v2rayNG не найден.' -ForegroundColor Red; exit 1 }
Sh "monkey -p $pkg 1" | Out-Null; Start-Sleep 4
Sh 'input tap 356 175' | Out-Null; Start-Sleep 2     # вкладка подписки
Sh 'input tap 600 300' | Out-Null; Start-Sleep 2     # первый сервер
Shot 'vpn-1-server.png'
Sh 'input tap 1816 950' | Out-Null; Start-Sleep 4    # кнопка запуска
Shot 'vpn-2-start.png'
Write-Host 'Если на ТВ появилось "Запрос на подключение" - нажми на пульте "ОК".' -ForegroundColor Yellow
Read-Host 'Потом нажми здесь Enter'
Start-Sleep 3
Shot 'vpn-3-after.png'
Write-Host 'Готово. Чтобы VPN включался сам при старте ТВ: vpn-4-autostart-on.bat' -ForegroundColor Green
