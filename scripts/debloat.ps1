# Шаг 2: обратимо отключить мусор по списку config\debloat-list.txt (спрашивает про спорные группы).
. "$PSScriptRoot\common.ps1"
Connect-TV

$stamp = Get-Date -Format 'yyyyMMdd-HHmm'
Sh 'pm list packages -e' | Set-Content (Join-Path $Data "backup-enabled-before-debloat-$stamp.txt") -Encoding UTF8
Sh 'pm list packages -d' | Set-Content (Join-Path $Data "backup-disabled-before-debloat-$stamp.txt") -Encoding UTF8

$listFile = Join-Path $Root 'config\debloat-list.txt'
$enabled = $true
foreach ($raw in Get-Content $listFile -Encoding UTF8) {
    $line = $raw.Trim()
    if (-not $line -or $line.StartsWith('#')) { continue }
    if ($line -eq '[safe]') { $enabled = $true; Write-Host ''; Write-Host 'Мусор и телеметрия:' -ForegroundColor Cyan; continue }
    if ($line -match '^\[ask:(.+)\]$') {
        Write-Host ''
        $a = Read-Host "$($Matches[1]) [y = да / n = нет]"
        $enabled = $a.Trim() -match '^(y|yes|д|да|l)$'
        continue
    }
    if (-not $enabled) { continue }
    $pkg, $desc = ($line -split '\|', 2) | ForEach-Object { $_.Trim() }
    if (-not (Sh "pm path $pkg")) { Write-Host "  - нет на ТВ: $desc" -ForegroundColor DarkGray; continue }
    $r = Sh "pm disable-user --user 0 $pkg"
    if ($r -match 'disabled') { Write-Host "  + отключено: $desc" -ForegroundColor Green; Add-ToLog $pkg }
    else { Write-Host "  ! система не дала: $desc" -ForegroundColor Yellow }
}

Sh 'input keyevent KEYCODE_HOME' | Out-Null
Start-Sleep 4
Shot "after-debloat-$stamp.png"
Write-Host ''
Write-Host 'Готово. Проверь, что открываются твои приложения и HDMI. Если что-то сломалось - restore.bat' -ForegroundColor Green
