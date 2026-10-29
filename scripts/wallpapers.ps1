# Свои обои: картинки из папки my-wallpapers обрезаются под 16:9, ужимаются до 1920x1080
# и кладутся в data\wallpapers. Потом запускается сборка лаунчера.
. "$PSScriptRoot\common.ps1"
$srcDir = Join-Path $Root 'my-wallpapers'
$dst = Join-Path $Data 'wallpapers'
New-Item -ItemType Directory -Force $srcDir, $dst | Out-Null
$files = @(Get-ChildItem $srcDir -File | Where-Object { $_.Extension -match '^\.(jpe?g|png|bmp)$' } | Sort-Object Name | Select-Object -First 20)
if ($files.Count -eq 0) {
    Write-Host 'В папке my-wallpapers нет картинок (jpg/png). Положи их туда и запусти снова.' -ForegroundColor Yellow
    Write-Host 'Чтобы вернуть встроенные обои - удали папку data\wallpapers и запусти 3-launcher.bat.' -ForegroundColor Yellow
    Invoke-Item $srcDir; exit 1
}
Add-Type -AssemblyName System.Drawing
$codec = [Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq 'image/jpeg' }
$ep = New-Object Drawing.Imaging.EncoderParameters 1
$ep.Param[0] = New-Object Drawing.Imaging.EncoderParameter ([Drawing.Imaging.Encoder]::Quality, [long]90)
Get-ChildItem $dst -File | Remove-Item -Force
$i = 0
foreach ($f in $files) {
    try {
        $img = [Drawing.Image]::FromFile($f.FullName)
        if ($img.PropertyIdList -contains 0x0112) {
            switch ($img.GetPropertyItem(0x0112).Value[0]) {
                3 { $img.RotateFlip('Rotate180FlipNone') }
                6 { $img.RotateFlip('Rotate90FlipNone') }
                8 { $img.RotateFlip('Rotate270FlipNone') }
            }
        }
        $tw, $th = 1920, 1080
        $scale = [Math]::Max($tw / $img.Width, $th / $img.Height)
        $cw = [int]($tw / $scale); $ch = [int]($th / $scale)
        $cx = [int](($img.Width - $cw) / 2); $cy = [int](($img.Height - $ch) / 2)
        $bmp = New-Object Drawing.Bitmap $tw, $th
        $g = [Drawing.Graphics]::FromImage($bmp)
        $g.InterpolationMode = 'HighQualityBicubic'; $g.PixelOffsetMode = 'HighQuality'
        $g.DrawImage($img, (New-Object Drawing.Rectangle 0, 0, $tw, $th), (New-Object Drawing.Rectangle $cx, $cy, $cw, $ch), 'Pixel')
        $i++
        $bmp.Save((Join-Path $dst ('{0:D2}.jpg' -f $i)), $codec, $ep)
        $g.Dispose(); $bmp.Dispose(); $img.Dispose()
        $warn = if ($scale -gt 1.5) { '  (маленькая картинка, может быть мыльной)' } else { '' }
        Write-Host ("  + {0}{1}" -f $f.Name, $warn) -ForegroundColor Green
    } catch { Write-Host "  ! не открылась: $($f.Name)" -ForegroundColor Yellow }
}
if ($i -eq 0) { Remove-Item $dst -Recurse -Force; exit 1 }
Write-Host "Готово: $i обоев. Дальше пересборка лаунчера." -ForegroundColor Cyan
