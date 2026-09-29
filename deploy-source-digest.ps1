$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$sourceCore = 'C:\Projects\fullstack-agent-main\.jarvis-publish\core'
$liveCore = 'C:\Projects\JARVIS\core'
$backupRoot = 'C:\Projects\fullstack-agent-main\tmp\live-backup-source-digest-20260928'
$expected = [ordered]@{
    'source_probe.py' = 'FCB726A98FE0B173128AFCCC943FAAF2823777C4F89826DA127DB3065884F5F3'
    'document_reports.py' = '6BC601D36AD53091A51509601250372FD06009939921497AAB0F43053510BD98'
    'jarvis_mark2.py' = 'C92243C3A519C16A4FC343ED1BD10769011B2496641864B02FAC44876993D9BD'
    'action_watchdog.py' = '02B77167D3997BF06A6C7F197E9EA3083354077D919CB6913A269D99F858917C'
    'verification_engine.py' = '06293A67488FD1EB189254DA26A4FE55A167EE91D2F2C248BA342BE098853993'
    'harness_context.py' = '590CB3E8A60B23F86E9081107D1D5F7FB518C000F08A87810F8B0E8807B42CAD'
    'tests\test_source_probe.py' = '9BA253DA97799188A8AFB4BF8ABCFF3ACEADF47C4B26C50F512C231BBD75D9CA'
    'tests\test_document_reports.py' = '8B01AC19CFFAC05CE6EE04FE134CA05E296D7F645B35378816C0CC994F5E73F9'
}

if (-not (Test-Path -LiteralPath $liveCore -PathType Container)) {
    throw 'Expected live JARVIS core directory is missing.'
}
if (Test-Path -LiteralPath $backupRoot) {
    throw 'Backup directory already exists; choose a new explicit backup path.'
}
foreach ($relative in $expected.Keys) {
    $live = Join-Path $liveCore $relative
    $source = Join-Path $sourceCore $relative
    if (-not (Test-Path -LiteralPath $source -PathType Leaf) -or
        -not (Test-Path -LiteralPath $live -PathType Leaf)) {
        throw "Expected source/live file missing: $relative"
    }
    if ((Get-FileHash -LiteralPath $live -Algorithm SHA256).Hash -ne $expected[$relative]) {
        throw "Live file changed since preflight: $relative"
    }
}

New-Item -ItemType Directory -Path $backupRoot | Out-Null
foreach ($relative in $expected.Keys) {
    $live = Join-Path $liveCore $relative
    $source = Join-Path $sourceCore $relative
    $backup = Join-Path $backupRoot $relative
    $backupParent = Split-Path -Parent $backup
    if (-not (Test-Path -LiteralPath $backupParent -PathType Container)) {
        New-Item -ItemType Directory -Path $backupParent | Out-Null
    }
    Copy-Item -LiteralPath $live -Destination $backup -ErrorAction Stop
    if ((Get-FileHash -LiteralPath $backup -Algorithm SHA256).Hash -ne $expected[$relative]) {
        throw "Backup verification failed: $relative"
    }
    Copy-Item -LiteralPath $source -Destination $live -ErrorAction Stop
    if ((Get-FileHash -LiteralPath $live -Algorithm SHA256).Hash -ne
        (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash) {
        throw "Post-copy verification failed: $relative"
    }
}
Write-Output "Installed $($expected.Count) exact files with verified backup: $backupRoot"
