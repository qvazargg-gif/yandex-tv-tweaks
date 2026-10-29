# Шаг 3: собрать новый домашний экран (лаунчер + заставку) и поставить на ТВ вместо Яндекса.
# Первый запуск скачает JDK 17 и Android SDK (~500 МБ) в папку tools\. Это означает согласие
# с лицензией Android SDK от Google. Вернуть всё: restore.bat
. "$PSScriptRoot\common.ps1"

$build = Join-Path $Tools 'build'
$jdk   = Join-Path $build 'jdk'
$sdk   = Join-Path $build 'android-sdk'
$src   = Join-Path $Root 'launcher'
$out   = Join-Path $Data 'launcher-build'
$ks    = Join-Path $Data 'launcher.keystore'   # свой ключ подписи, создаётся при первой сборке
$myWp  = Join-Path $Data 'wallpapers'          # свои обои (my-wallpapers.bat), иначе - из launcher\assets
function Check($what) { if ($LASTEXITCODE -ne 0) { Write-Host "Ошибка на шаге: $what (код $LASTEXITCODE)" -ForegroundColor Red; exit 1 } }
New-Item -ItemType Directory -Force $build | Out-Null

# ---------- JDK 17 ----------
if (-not (Test-Path "$jdk\bin\javac.exe")) {
    Write-Host 'Скачиваю JDK 17 (~190 МБ)...' -ForegroundColor Cyan
    $zip = "$build\jdk.zip"; $tmp = "$build\jdk-tmp"
    Invoke-WebRequest 'https://api.adoptium.net/v3/binary/latest/17/ga/windows/x64/jdk/hotspot/normal/eclipse' -OutFile $zip
    Expand-Archive $zip $tmp -Force
    Move-Item (Get-ChildItem $tmp -Directory | Select-Object -First 1).FullName $jdk
    Remove-Item $tmp, $zip -Recurse -Force
}
$env:JAVA_HOME = $jdk
$env:Path = "$jdk\bin;$env:Path"

# ---------- Android SDK ----------
$sdkm = "$sdk\cmdline-tools\latest\bin\sdkmanager.bat"
if (-not (Test-Path $sdkm)) {
    Write-Host 'Скачиваю Android command-line tools (~150 МБ)...' -ForegroundColor Cyan
    $zip = "$build\cmdline.zip"; $tmp = "$build\cmdline-tmp"
    Invoke-WebRequest 'https://dl.google.com/android/repository/commandlinetools-win-11076708_latest.zip' -OutFile $zip
    Expand-Archive $zip $tmp -Force
    New-Item -ItemType Directory -Force "$sdk\cmdline-tools" | Out-Null
    Move-Item "$tmp\cmdline-tools" "$sdk\cmdline-tools\latest"
    Remove-Item $tmp, $zip -Recurse -Force
}
$BT  = "$sdk\build-tools\34.0.0"
$JAR = "$sdk\platforms\android-34\android.jar"
if (-not (Test-Path $JAR) -or -not (Test-Path "$BT\aapt2.exe")) {
    Write-Host 'Ставлю Android platform 34 и build-tools 34 (~120 МБ)...' -ForegroundColor Cyan
    ("y`n" * 20) | & $sdkm "--sdk_root=$sdk" --licenses | Out-Null
    & $sdkm "--sdk_root=$sdk" "platforms;android-34" "build-tools;34.0.0"
    Check 'sdkmanager'
}

# ---------- Сборка APK (без Gradle) ----------
Write-Host 'Собираю лаунчер...' -ForegroundColor Cyan
if (Test-Path $out) { Remove-Item $out -Recurse -Force }
New-Item -ItemType Directory -Force "$out\gen", "$out\classes", "$out\dex" | Out-Null
$wpDir = if ((Test-Path $myWp) -and (Get-ChildItem $myWp -Filter *.jpg)) { $myWp } else { "$src\assets\wallpapers" }
Write-Host "Обои из: $wpDir"
Push-Location $src
try {
    & "$BT\aapt2.exe" compile --dir res -o "$out\res.zip"; Check 'aapt2 compile'
    # Обои кладём в APK сами (ниже): aapt2 на Windows пишет пути с "\", и Android их не видит
    & "$BT\aapt2.exe" link -o "$out\base.apk" -I $JAR --manifest AndroidManifest.xml --java "$out\gen" `
        --min-sdk-version 30 --target-sdk-version 30 "$out\res.zip"; Check 'aapt2 link'
    $javaFiles = Get-ChildItem src, "$out\gen" -Recurse -Filter *.java | ForEach-Object FullName
    & javac -encoding UTF-8 -nowarn -Xlint:-options --release 11 -classpath $JAR -d "$out\classes" @javaFiles; Check 'javac'
    $classFiles = Get-ChildItem "$out\classes" -Recurse -Filter *.class | ForEach-Object FullName
    & "$BT\d8.bat" --min-api 30 --lib $JAR --output "$out\dex" @classFiles; Check 'd8'

    Copy-Item "$out\base.apk" "$out\unsigned.apk"
    Add-Type -AssemblyName System.IO.Compression, System.IO.Compression.FileSystem
    $z = [IO.Compression.ZipFile]::Open("$out\unsigned.apk", 'Update')
    [void][IO.Compression.ZipFileExtensions]::CreateEntryFromFile($z, "$out\dex\classes.dex", 'classes.dex')
    foreach ($f in Get-ChildItem $wpDir -Filter *.jpg) {
        [void][IO.Compression.ZipFileExtensions]::CreateEntryFromFile($z, $f.FullName, "assets/wallpapers/$($f.Name)", 'NoCompression')
    }
    $z.Dispose()

    & "$BT\zipalign.exe" -f 4 "$out\unsigned.apk" "$out\aligned.apk"; Check 'zipalign'
    if (Test-Path $ks) {
        & keytool -list -keystore $ks -storepass android 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) { Remove-Item $ks -Force }
    }
    if (-not (Test-Path $ks)) {
        & keytool -genkeypair -keystore $ks -storepass android -keypass android -alias tvhome `
            -keyalg RSA -keysize 2048 -validity 10000 -dname "CN=tvhome" 2>&1 | Out-Null
        Check 'keytool'
    }
    & "$BT\apksigner.bat" sign --ks $ks --ks-pass pass:android --out "$out\tvhome.apk" "$out\aligned.apk"; Check 'apksigner'
} finally { Pop-Location }
$apk = "$out\tvhome.apk"
Write-Host "Собрано: $([math]::Round((Get-Item $apk).Length / 1MB, 1)) МБ" -ForegroundColor Green

# ---------- Установка ----------
Connect-TV
if (-not (Install-Apk $apk)) { Write-Host 'Установка не прошла.' -ForegroundColor Red; exit 1 }
Sh 'pm grant com.mihir.tvhome android.permission.ACCESS_FINE_LOCATION' | Out-Null
Sh 'cmd package set-home-activity --user 0 com.mihir.tvhome/.MainActivity' | Out-Null

# Домашний экран Яндекса - обратимо отключаем, чтобы не перехватывал Home и не висел в памяти
if (Sh 'pm path com.yandex.tv.home') {
    $r = Sh 'pm disable-user --user 0 com.yandex.tv.home'
    if ($r -match 'disabled') { Add-ToLog 'com.yandex.tv.home'; Write-Host 'Домашний экран Яндекса отключён (restore.bat вернёт).' }
}
Sh 'cmd package set-home-activity --user 0 com.mihir.tvhome/.MainActivity' | Out-Null
Sh 'am force-stop com.android.tv.settings' | Out-Null
Sh 'am force-stop com.mihir.tvhome' | Out-Null
Sh 'input keyevent KEYCODE_HOME' | Out-Null
Start-Sleep 5
Shot 'launcher-home.png'

# ---------- Проверка кнопки Home изнутри приложения ----------
Sh 'am start -a android.settings.SETTINGS' | Out-Null
Start-Sleep 4
Sh 'input keyevent KEYCODE_HOME' | Out-Null
Start-Sleep 4
Shot 'launcher-home-from-app.png'
if ((Top-Activity) -match 'com.mihir.tvhome') {
    Write-Host 'Готово: кнопка Home ведёт на новый экран.' -ForegroundColor Green
} else {
    Write-Host "Кнопка Home открыла что-то другое: $(Top-Activity)" -ForegroundColor Yellow
    Write-Host 'Скриншоты в data\screenshots. Вернуть как было: restore.bat' -ForegroundColor Yellow
}
