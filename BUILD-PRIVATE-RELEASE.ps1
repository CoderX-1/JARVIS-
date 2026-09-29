param(
    [string]$LiveRoot = 'C:\Projects\JARVIS',
    [string]$Output = (Join-Path $PSScriptRoot '.jarvis-private\JARVIS-private-release.zip'),
    [switch]$PasswordlessInstall
)

$ErrorActionPreference = 'Stop'
$python = Get-Command python -ErrorAction Stop
& $python.Source -c 'import cryptography; import sys; assert sys.version_info[:2] == (3, 12)'
if ($LASTEXITCODE -ne 0) {
    throw 'Builder requires Python 3.12 with cryptography installed on this PC.'
}
$privateFolder = Join-Path $PSScriptRoot '.jarvis-private'
New-Item -ItemType Directory -Force -Path $privateFolder | Out-Null
$buildArgs = @(
    'build',
    '--source', $PSScriptRoot,
    '--env', (Join-Path $LiveRoot '.env'),
    '--config', (Join-Path $LiveRoot 'config'),
    '--models', (Join-Path $LiveRoot 'models'),
    '--output', $Output
)
if ($PasswordlessInstall) {
    $buildArgs += '--passwordless-install'
} else {
    $buildArgs += @('--generate-passphrase-file',
        (Join-Path $privateFolder 'teacher-install-private-release.password.txt'))
}
& $python.Source (Join-Path $PSScriptRoot 'tools\private_release.py') @buildArgs
if ($LASTEXITCODE -ne 0) { throw 'Private release was not created.' }
if ($PasswordlessInstall) {
    Write-Warning 'The ZIP contains its own unlock passphrase. Anyone who obtains it can recover the API keys.'
} else {
    Write-Host 'Send only the ZIP to the trusted laptop. Keep the password file separately.'
}
