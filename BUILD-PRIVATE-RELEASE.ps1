param(
    [string]$LiveRoot = 'C:\Projects\JARVIS',
    [string]$Output = (Join-Path ([Environment]::GetFolderPath('UserProfile')) 'Downloads\JARVIS-private-release.zip')
)

$ErrorActionPreference = 'Stop'
$python = Get-Command python -ErrorAction Stop
& $python.Source -c 'import cryptography; import sys; assert sys.version_info[:2] == (3, 12)'
if ($LASTEXITCODE -ne 0) {
    throw 'Builder requires Python 3.12 with cryptography installed on this PC.'
}
& $python.Source (Join-Path $PSScriptRoot 'tools\private_release.py') build `
    --source $PSScriptRoot `
    --env (Join-Path $LiveRoot '.env') `
    --config (Join-Path $LiveRoot 'config') `
    --models (Join-Path $LiveRoot 'models') `
    --output $Output
if ($LASTEXITCODE -ne 0) { throw 'Private release was not created.' }
Write-Host 'Release ZIP is private. Do not upload it to GitHub or a public file-sharing link.'
