# Общие функции: скачивание adb, поиск и подключение телевизора, команды и скриншоты.
# Подключается к другим скриптам через:  . "$PSScriptRoot\common.ps1"

$ErrorActionPreference = 'Continue'
$ProgressPreference    = 'SilentlyContinue'   # без этого скачивание в PowerShell очень медленное
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$Root    = Split-Path -Parent $PSScriptRoot
$Tools   = Join-Path $Root 'tools'
$Data    = Join-Path $Root 'data'          # IP, бэкапы, скриншоты - всё личное, в git не попадает
$Shots   = Join-Path $Data 'screenshots'
$Adb     = Join-Path $Tools 'platform-tools\adb.exe'
$IpFile  = Join-Path $Data 'tv-ip.txt'
$LogFile = Join-Path $Data 'disabled-by-me.txt'
$Target  = $null
New-Item -ItemType Directory -Force $Tools, $Data, $Shots | Out-Null

function Ensure-Adb {
    if (Test-Path $Adb) { return }
    Write-Host 'Скачиваю Android platform-tools (adb, ~10 МБ)...' -ForegroundColor Cyan
    $zip = Join-Path $Tools 'platform-tools.zip'
    Invoke-WebRequest 'https://dl.google.com/android/repository/platform-tools-latest-windows.zip' -OutFile $zip
    Expand-Archive $zip -DestinationPath $Tools -Force
    Remove-Item $zip
}

function Find-TvOnNetwork {
    Write-Host 'Ищу телевизор в сети (порт ADB 5555)...' -ForegroundColor Cyan
    $found = @()
    $locals = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
        Where-Object { $_.IPAddress -match '^(192\.168\.|10\.|172\.(1[6-9]|2\d|3[01])\.)' }
    foreach ($l in $locals) {
        $prefix = ($l.IPAddress -split '\.')[0..2] -join '.'
        $tasks = @{}
        foreach ($i in 1..254) {
            $c = New-Object Net.Sockets.TcpClient
            $tasks["$prefix.$i"] = @($c, $c.ConnectAsync("$prefix.$i", 5555))
        }
        Start-Sleep -Milliseconds 2000
        foreach ($k in $tasks.Keys) {
            if ($tasks[$k][1].Status -eq 'RanToCompletion') { $found += $k }
            $tasks[$k][0].Dispose()
        }
    }
    return $found
}

function Connect-TV {
    Ensure-Adb
    $dev = & $Adb devices 2>$null | Select-String ':5555\s+device$' | Select-Object -First 1
    if ($dev) { $script:Target = ($dev.Line -split '\s+')[0]; return }

    $ip = if (Test-Path $IpFile) { (Get-Content $IpFile -Raw).Trim() } else { '' }
    if (-not $ip) {
        $found = @(Find-TvOnNetwork)
        if ($found.Count -eq 1) { $ip = $found[0]; Write-Host "Нашёл: $ip" -ForegroundColor Green }
        else {
            if ($found.Count -gt 1) { Write-Host "Нашёл несколько: $($found -join ', ')" -ForegroundColor Yellow }
            Write-Host 'IP телевизора: Настройки -> Об устройстве -> Статус -> IP-адрес'
            $ip = Read-Host 'Введи IP телевизора'
        }
    }
    $script:Target = "${ip}:5555"
    & $Adb connect $script:Target | Out-Host
    Write-Host 'Если на ТВ появилось "Разрешить отладку?" - отметь "Всегда" и нажми "Разрешить".' -ForegroundColor Yellow
    for ($t = 0; $t -lt 30; $t++) {
        if ((& $Adb -s $script:Target get-state 2>&1 | Out-String).Trim() -eq 'device') { break }
        Start-Sleep 2
        if ($t % 5 -eq 4) { & $Adb connect $script:Target | Out-Null }
    }
    if ((& $Adb -s $script:Target get-state 2>&1 | Out-String).Trim() -ne 'device') {
        Write-Host 'Не удалось подключиться. Проверь: на ТВ включена "Отладка по USB" (и "по сети", если есть),' -ForegroundColor Red
        Write-Host 'ТВ и компьютер в одной Wi-Fi сети. Если IP поменялся - удали data\tv-ip.txt.' -ForegroundColor Red
        exit 1
    }
    $ip | Set-Content $IpFile
    Write-Host "Подключено: $script:Target" -ForegroundColor Green
}

function Sh([string]$cmd) { (& $Adb -s $script:Target shell $cmd 2>&1 | Out-String).Trim() }

function Shot([string]$name) {
    Sh 'screencap -p /sdcard/tv-shot.png' | Out-Null
    & $Adb -s $script:Target pull /sdcard/tv-shot.png (Join-Path $Shots $name) 2>&1 | Out-Null
    Sh 'rm /sdcard/tv-shot.png' | Out-Null
}

function Top-Activity { Sh "dumpsys activity activities | grep -E 'mResumedActivity|topResumedActivity' | head -n 1" }

function Find-Package([string[]]$names) {
    foreach ($p in $names) { if (Sh "pm path $p") { return $p } }
    return $null
}

function Add-ToLog([string]$pkg) {
    $done = @(); if (Test-Path $LogFile) { $done = @(Get-Content $LogFile | Where-Object { $_ }) }
    if ($done -notcontains $pkg) { $done += $pkg }
    $done | Set-Content $LogFile -Encoding UTF8
}

function Download([string]$url, [string]$file, [string]$sha256 = '') {
    if (-not (Test-Path $file)) {
        Write-Host "Скачиваю $(Split-Path -Leaf $file)..." -ForegroundColor Cyan
        try { Invoke-WebRequest $url -OutFile $file -UserAgent 'Mozilla/5.0' -ErrorAction Stop }
        catch { Write-Host "Не скачалось: $($_.Exception.Message)" -ForegroundColor Red; return $false }
    }
    if ($sha256) {
        $h = (Get-FileHash $file -Algorithm SHA256).Hash.ToLower()
        if ($h -ne $sha256.ToLower()) {
            Write-Host "Контрольная сумма не совпала, файл удалён." -ForegroundColor Red
            Remove-Item $file -Force; return $false
        }
    }
    return $true
}

function Install-Apk([string]$apk) {
    Write-Host "Ставлю $(Split-Path -Leaf $apk) на телевизор..." -ForegroundColor Cyan
    $r = (& $Adb -s $script:Target install -r $apk 2>&1 | Out-String).Trim()
    Write-Host $r
    return ($r -match 'Success')
}
