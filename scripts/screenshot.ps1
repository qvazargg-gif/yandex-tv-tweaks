# Снимок экрана ТВ + что открыто + последние падения. Ничего не меняет.
. "$PSScriptRoot\common.ps1"
Connect-TV
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
Shot "shot-$stamp.png"
@("Открыто: $(Top-Activity)", 'Падения:', (Sh "logcat -d -t 600 | grep -E 'FATAL|ANR in|has died' | tail -n 30")) |
    Set-Content (Join-Path $Shots "shot-$stamp.txt") -Encoding UTF8
Write-Host "Снимок: data\screenshots\shot-$stamp.png" -ForegroundColor Green
Invoke-Item $Shots
