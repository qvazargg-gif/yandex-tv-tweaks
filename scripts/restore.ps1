# Вернуть всё как было: включить отключённые пакеты, домашний экран и заставку Яндекса, выключить автозапуск VPN.
# Лаунчер, SmartTube и v2rayNG остаются установленными - удалить их можно в Настройки -> Приложения.
. "$PSScriptRoot\common.ps1"
Connect-TV
$pkgs = @(); if (Test-Path $LogFile) { $pkgs = @(Get-Content $LogFile | Where-Object { $_ }) }
if ($pkgs -notcontains 'com.yandex.tv.home') { $pkgs += 'com.yandex.tv.home' }
foreach ($pkg in $pkgs) { Write-Host "  $pkg -> $(Sh "pm enable $pkg")" }
Sh 'cmd package set-home-activity --user 0 com.yandex.tv.home/.HomeActivity' | Out-Null

$ssFile = Join-Path $Data 'screensaver-before.txt'
if (Test-Path $ssFile) {
    foreach ($line in Get-Content $ssFile) {
        $k, $v = $line -split '=', 2
        if (-not $k) { continue }
        if ($v -and $v -ne 'null') { Sh "settings put secure $k $v" | Out-Null } else { Sh "settings delete secure $k" | Out-Null }
    }
    Remove-Item $ssFile
    Write-Host '  заставка возвращена'
}
Sh 'settings delete secure always_on_vpn_app' | Out-Null
Sh 'settings delete secure always_on_vpn_lockdown' | Out-Null
Sh 'input keyevent KEYCODE_HOME' | Out-Null
Remove-Item $LogFile -ErrorAction SilentlyContinue
Write-Host ''
Write-Host 'Всё включено обратно. Можно перезагрузить телевизор.' -ForegroundColor Green
