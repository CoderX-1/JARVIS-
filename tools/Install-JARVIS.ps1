param(
    [string]$Destination = (Join-Path $env:LOCALAPPDATA 'Programs\JARVIS')
)

$ErrorActionPreference = 'Stop'
$bundle = Join-Path $PSScriptRoot 'JARVIS-private-release.zip'
if (-not (Test-Path -LiteralPath $bundle)) {
    $sibling = Join-Path (Split-Path -Parent $PSScriptRoot) 'JARVIS-private-release.zip'
    if (Test-Path -LiteralPath $sibling) { $bundle = $sibling }
}
if (-not (Test-Path -LiteralPath $bundle)) {
    $bundle = Read-Host 'Full path to the private release ZIP'
}
if (-not (Test-Path -LiteralPath $bundle)) { throw 'Private release ZIP not found.' }

$python = $null
$pyLauncher = Get-Command py -ErrorAction SilentlyContinue
if ($pyLauncher) {
    & $pyLauncher.Source -3.12 -c 'import sys,struct; assert sys.version_info[:2] == (3, 12) and struct.calcsize(chr(80)) == 8'
    if ($LASTEXITCODE -eq 0) { $python = @($pyLauncher.Source, '-3.12') }
}
if (-not $python) {
    $candidate = Get-Command python -ErrorAction SilentlyContinue
    if ($candidate) {
        & $candidate.Source -c 'import sys,struct; assert sys.version_info[:2] == (3, 12) and struct.calcsize(chr(80)) == 8'
        if ($LASTEXITCODE -eq 0) { $python = @($candidate.Source) }
    }
}
if (-not $python) {
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $winget) {
        throw 'Python 3.12 x64 is missing and winget is unavailable. Install Python 3.12 x64 from python.org, then rerun. No JARVIS files were installed.'
    }
    Write-Host 'Installing Python 3.12 x64 for this Windows user via winget...'
    & $winget.Source install --id Python.Python.3.12 --exact --source winget --scope user --silent --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) { throw 'Python installation failed; no JARVIS files were installed.' }
    $installedPython = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'
    if (-not (Test-Path -LiteralPath $installedPython)) {
        throw 'Python installer finished but Python 3.12 was not found. Reopen PowerShell and rerun.'
    }
    & $installedPython -c 'import sys,struct; assert sys.version_info[:2] == (3, 12) and struct.calcsize(chr(80)) == 8'
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.12 x64 validation failed.' }
    $python = @($installedPython)
}
$pythonArgs = @($python | Select-Object -Skip 1)

Write-Host 'JARVIS private installer: Python 3.12 found.'
Write-Host 'It will decrypt your configuration locally, then download Python dependencies.'
Write-Host 'Internet and several GB of free disk space are required.'
$destinationPath = [IO.Path]::GetFullPath($Destination)
if (Test-Path -LiteralPath $destinationPath) {
    throw "Installation folder already exists; no files were overwritten: $destinationPath"
}
$destinationParent = Split-Path -Parent $destinationPath
if (-not (Test-Path -LiteralPath $destinationParent)) {
    New-Item -ItemType Directory -Force -Path $destinationParent | Out-Null
}

$tempVenv = Join-Path $env:TEMP ('jarvis-setup-' + [guid]::NewGuid().ToString('N'))
& $python[0] @pythonArgs -m venv $tempVenv
if ($LASTEXITCODE -ne 0) { throw 'Setup Python environment failed.' }
$setupPython = Join-Path $tempVenv 'Scripts\python.exe'
& $setupPython -m pip install --disable-pip-version-check 'cryptography>=45,<48'
if ($LASTEXITCODE -ne 0) { throw 'Encryption support could not be installed; no JARVIS files were installed.' }

$installCode = Join-Path $PSScriptRoot 'app\tools\private_release.py'
if (-not (Test-Path -LiteralPath $installCode)) {
    throw 'Extract the entire private release ZIP, then run this script from the extracted folder.'
}
& $setupPython $installCode unpack --bundle $bundle --destination $destinationPath
if ($LASTEXITCODE -ne 0) { throw 'Private release verification or passphrase failed.' }

$voiceRoot = Join-Path $destinationPath 'components\backtalk'
$voiceVenv = Join-Path $voiceRoot '.venv'
& $python[0] @pythonArgs -m venv $voiceVenv
if ($LASTEXITCODE -ne 0) { throw 'Voice environment setup failed.' }
$voicePython = Join-Path $voiceVenv 'Scripts\python.exe'
& $voicePython -m pip install --disable-pip-version-check -e $voiceRoot
if ($LASTEXITCODE -ne 0) { throw 'Voice dependency install failed; see the error above.' }
& $voicePython -m pip install --disable-pip-version-check -r (Join-Path $destinationPath 'core\requirements-vision.txt') -r (Join-Path $destinationPath 'core\requirements-artifacts.txt')
if ($LASTEXITCODE -ne 0) { throw 'Vision or report dependency install failed; see the error above.' }
# Browser automation uses the system's detected default Chromium browser
# executable, so a separate Playwright Chromium download is unnecessary.

$desktopVenv = Join-Path $destinationPath 'runtime\desktop-venv'
New-Item -ItemType Directory -Force -Path (Join-Path $destinationPath 'runtime') | Out-Null
& $python[0] @pythonArgs -m venv $desktopVenv
if ($LASTEXITCODE -ne 0) { throw 'Desktop environment setup failed.' }
$desktopPython = Join-Path $desktopVenv 'Scripts\python.exe'
& $desktopPython -m pip install --disable-pip-version-check 'pywebview>=5,<7'
if ($LASTEXITCODE -ne 0) { throw 'Desktop WebView dependency install failed.' }

$florenceVenv = Join-Path $destinationPath 'runtime\florence-venv'
& $python[0] @pythonArgs -m venv $florenceVenv
if ($LASTEXITCODE -ne 0) { throw 'Florence environment setup failed.' }
$florencePython = Join-Path $florenceVenv 'Scripts\python.exe'
& $florencePython -m pip install --disable-pip-version-check -r (Join-Path $destinationPath 'core\requirements-florence.txt')
if ($LASTEXITCODE -ne 0) { throw 'Florence dependency install failed; see the error above.' }

& $voicePython -c 'import faster_whisper, sounddevice, playwright, reportlab, winocr'
if ($LASTEXITCODE -ne 0) { throw 'Voice/vision/report import smoke test failed.' }
& $desktopPython -c 'import webview'
if ($LASTEXITCODE -ne 0) { throw 'Desktop import smoke test failed.' }
function Test-WebView2Runtime {
    $client = '{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}'
    foreach ($registryPath in @(
        ('HKLM:\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\' + $client),
        ('HKCU:\Software\Microsoft\EdgeUpdate\Clients\' + $client))) {
        $item = Get-ItemProperty -LiteralPath $registryPath -Name pv -ErrorAction SilentlyContinue
        if ($item -and $item.pv -and $item.pv -ne '0.0.0.0') { return $true }
    }
    return $false
}
$winget = Get-Command winget -ErrorAction SilentlyContinue
if (-not (Test-WebView2Runtime)) {
    if (-not $winget) { throw 'Microsoft Edge WebView2 Runtime is missing and winget is unavailable.' }
    Write-Host 'Installing Microsoft Edge WebView2 Runtime...'
    & $winget.Source install --id Microsoft.EdgeWebView2Runtime --exact --source winget --scope user --silent --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0 -or -not (Test-WebView2Runtime)) {
        throw 'WebView2 Runtime installation was not verified; the desktop cockpit may not open.'
    }
}
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    if (-not $winget) { throw 'FFmpeg is required for Fish Audio playback, but winget is unavailable.' }
    Write-Host 'Installing FFmpeg for Fish Audio playback...'
    & $winget.Source install --id Gyan.FFmpeg --exact --source winget --scope user --silent --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) { throw 'FFmpeg installation failed; Fish Audio voice cannot be verified.' }
}
$ffmpegCommand = Get-Command ffmpeg -ErrorAction SilentlyContinue
if (-not $ffmpegCommand) {
    $packages = Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Packages'
    if (Test-Path -LiteralPath $packages) {
        $ffmpegCommand = Get-ChildItem -LiteralPath $packages -Filter 'ffmpeg.exe' -Recurse -File -ErrorAction SilentlyContinue | Select-Object -First 1
    }
}
if (-not $ffmpegCommand) { throw 'FFmpeg executable not found after installation; Fish Audio voice cannot be verified.' }
& $florencePython -c 'import torch, transformers, timm, einops'
if ($LASTEXITCODE -ne 0) { throw 'Florence import smoke test failed.' }
Write-Host "JARVIS installed: $destinationPath"
Write-Host 'Before class: run START-JARVIS-DESKTOP.bat, sign in, and test mic, TTS, PDF, PPTX, browser, and app opening on this laptop.'
Write-Host 'Do not upload or share this private ZIP publicly; installed API keys remain accessible to the laptop owner/admin.'
