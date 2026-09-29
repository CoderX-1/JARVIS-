param(
    [string]$Destination = (Join-Path $env:LOCALAPPDATA 'Programs\JARVIS')
)

$ErrorActionPreference = 'Stop'
$bundle = Join-Path $PSScriptRoot 'JARVIS-private-release.zip'
if (-not (Test-Path -LiteralPath $bundle)) {
    # When run from the extracted release ZIP, use that ZIP's path supplied by
    # the user. The builder prints the file path; no API key is entered here.
    $bundle = Read-Host 'Full path to the private release ZIP'
}
if (-not (Test-Path -LiteralPath $bundle)) { throw 'Private release ZIP not found.' }

$python = $null
$pyLauncher = Get-Command py -ErrorAction SilentlyContinue
if ($pyLauncher) {
    & $pyLauncher.Source -3.12 -c 'import sys; assert sys.version_info[:2] == (3, 12)'
    if ($LASTEXITCODE -eq 0) { $python = @($pyLauncher.Source, '-3.12') }
}
if (-not $python) {
    $candidate = Get-Command python -ErrorAction SilentlyContinue
    if ($candidate) {
        & $candidate.Source -c 'import sys; assert sys.version_info[:2] == (3, 12)'
        if ($LASTEXITCODE -eq 0) { $python = @($candidate.Source) }
    }
}
if (-not $python) {
    throw 'Python 3.12 x64 is required. Install it from python.org, then rerun this installer. No JARVIS files were installed.'
}
$pythonArgs = @($python | Select-Object -Skip 1)

Write-Host 'JARVIS private installer: Python 3.12 found.'
Write-Host 'It will decrypt your configuration locally, then download Python dependencies.'
Write-Host 'Internet and several GB of free disk space are required.'
$destinationPath = [IO.Path]::GetFullPath($Destination)
if (Test-Path -LiteralPath $destinationPath) {
    throw "Installation folder already exists; no files were overwritten: $destinationPath"
}
if (-not (Test-Path -LiteralPath (Split-Path -Parent $destinationPath))) {
    throw 'Installation parent folder does not exist.'
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
& $voicePython -m playwright install chromium
if ($LASTEXITCODE -ne 0) { throw 'Browser engine install failed; see the error above.' }

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
& $florencePython -c 'import torch, transformers, timm, einops'
if ($LASTEXITCODE -ne 0) { throw 'Florence import smoke test failed.' }
Write-Host "JARVIS installed: $destinationPath"
Write-Host 'Before class: run START-JARVIS-DESKTOP.bat, sign in, and test mic, TTS, PDF, PPTX, browser, and app opening on this laptop.'
Write-Host 'Do not upload or share this private ZIP publicly; installed API keys remain accessible to the laptop owner/admin.'
