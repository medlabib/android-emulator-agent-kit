param(
  [int]$Api = 35,
  [string]$Avd = "Pixel_Play_API_$Api"
)
$ErrorActionPreference = "Stop"
$Sdk = $env:ANDROID_SDK_ROOT
if (-not $Sdk) { $Sdk = $env:ANDROID_HOME }
if (-not $Sdk) { $Sdk = Join-Path $env:LOCALAPPDATA "Android\Sdk" }
$SdkManager = Join-Path $Sdk "cmdline-tools\latest\bin\sdkmanager.bat"
$AvdManager = Join-Path $Sdk "cmdline-tools\latest\bin\avdmanager.bat"
if (-not (Test-Path $SdkManager) -or -not (Test-Path $AvdManager)) {
  throw "Install Android SDK Command-line Tools (latest) in Android Studio SDK Manager."
}
$Image = "system-images;android-$Api;google_apis_playstore;x86_64"
& $SdkManager "platform-tools" "emulator" "platforms;android-$Api" $Image
if ($LASTEXITCODE -ne 0) { throw "sdkmanager failed" }
$Existing = (& $AvdManager list avd | Out-String)
if ($Existing -notmatch "Name:\s+$([regex]::Escape($Avd))\b") {
  "no" | & $AvdManager create avd --name $Avd --package $Image --device "pixel_7"
  if ($LASTEXITCODE -ne 0) { throw "avdmanager failed" }
}
$Config = Join-Path $env:USERPROFILE ".android\avd\$Avd.avd\config.ini"
if (Test-Path $Config) {
  $Lines = Get-Content $Config | Where-Object { $_ -notmatch '^hw\.camera\.(back|front)=' }
  $Lines += @("hw.camera.back=webcam0", "hw.camera.front=webcam0")
  Set-Content -Path $Config -Value $Lines
}
Write-Host "Created/verified AVD: $Avd"
Write-Host "Start with: emulator -avd `"$Avd`""
Write-Host "If webcam0 is unavailable, choose Emulated camera in Device Manager."
