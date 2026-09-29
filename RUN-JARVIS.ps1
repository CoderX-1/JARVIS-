param(
    [switch]$NoBrowser,
    [switch]$Desktop,
    [switch]$InteractiveRelaunch
)

$ErrorActionPreference = "Stop"
if ($Desktop) { $NoBrowser = $true }

$root = $PSScriptRoot
$components = Join-Path $root "components"
$backtalk = Join-Path $components "backtalk"
$barehands = Join-Path $components "barehands"
$visualizer = Join-Path $components "ai-visualizer"
$config = Join-Path $root "config"
$core = Join-Path $root "core"
$runtime = Join-Path $root "runtime"
$logs = Join-Path $runtime "logs"
$models = Join-Path $root "models"
$backtalkPython = Join-Path $backtalk ".venv\Scripts\python.exe"
$florencePython = Join-Path $runtime "florence-venv\Scripts\python.exe"
$florenceWorker = Join-Path $core "florence_worker.py"
$florenceModel = Join-Path $models "florence-2-base-ft"
$started = @()
$launcherMutex = $null
$ownsLauncherMutex = $false

function Test-InteractiveDesktop {
    if (-not ("JarvisDesktopContext" -as [type])) {
        Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;

public static class JarvisDesktopContext
{
    private delegate bool EnumWindowsProc(IntPtr hwnd, IntPtr lParam);

    [DllImport("user32.dll")]
    private static extern IntPtr GetForegroundWindow();

    [DllImport("user32.dll")]
    private static extern bool EnumWindows(EnumWindowsProc callback, IntPtr lParam);

    public static bool IsVisibleDesktop()
    {
        if (GetForegroundWindow() != IntPtr.Zero) return true;
        var count = 0;
        EnumWindows((hwnd, lParam) => { count++; return true; }, IntPtr.Zero);
        return count > 0;
    }
}
'@
    }
    return [JarvisDesktopContext]::IsVisibleDesktop()
}

function Restart-InInteractiveDesktop {
    if ($InteractiveRelaunch) {
        throw "JARVIS cannot access the logged-in Windows desktop after interactive relaunch."
    }
    $arguments = @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-WindowStyle', 'Hidden',
        '-File', ('"' + $PSCommandPath + '"'), '-InteractiveRelaunch'
    )
    if ($NoBrowser) { $arguments += '-NoBrowser' }
    if ($Desktop) { $arguments += '-Desktop' }
    $shell = New-Object -ComObject Shell.Application
    $shell.ShellExecute(
        'powershell.exe', ($arguments -join ' '), $root, '', 0
    )
}

# A process can have the same numeric session ID as Explorer while still being
# attached to an isolated window station/desktop. In that state Win32 audio and
# global keys may work, but GetForegroundWindow and EnumWindows return nothing,
# making Vision/UI State Graph falsely report "no foreground window". Relaunch
# through Explorer before starting any child process so every JARVIS component
# inherits the logged-in user's visible desktop.
if (-not (Test-InteractiveDesktop)) {
    Restart-InInteractiveDesktop
    return
}

function Import-DotEnv {
    param([Parameter(Mandatory = $true)][string]$Path,
          [string[]]$AllowedNames = @())
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Missing private environment file: $Path"
    }
    foreach ($line in Get-Content -LiteralPath $Path) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("#") -or
            -not $trimmed.Contains("=")) { continue }
        $name, $value = $trimmed.Split("=", 2)
        $name = $name.Trim()
        $value = $value.Trim().Trim('"').Trim("'")
        if ($name -match '^[A-Za-z_][A-Za-z0-9_]*$' -and
                ($AllowedNames.Count -eq 0 -or $AllowedNames -contains $name)) {
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
}

function Test-LocalPort {
    param([Parameter(Mandatory = $true)][int]$Port)
    $client = [Net.Sockets.TcpClient]::new()
    try {
        $client.Connect("127.0.0.1", $Port)
        return $client.Connected
    }
    catch { return $false }
    finally { $client.Dispose() }
}

function Wait-LocalPort {
    param([Parameter(Mandatory = $true)][int]$Port, [int]$Seconds = 20)
    $timer = [Diagnostics.Stopwatch]::StartNew()
    while ($timer.Elapsed.TotalSeconds -lt $Seconds) {
        if (Test-LocalPort $Port) { return $true }
        Start-Sleep -Milliseconds 250
    }
    return $false
}

function Wait-ListenerOwner {
    param([Parameter(Mandatory = $true)][int]$Port, [int]$Seconds = 20)
    $timer = [Diagnostics.Stopwatch]::StartNew()
    while ($timer.Elapsed.TotalSeconds -lt $Seconds) {
        $listener = Get-NetTCPConnection -State Listen -LocalPort $Port `
            -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($listener -and $listener.OwningProcess) {
            return [int]$listener.OwningProcess
        }
        Start-Sleep -Milliseconds 100
    }
    return $null
}

foreach ($path in @($backtalk, $barehands, $visualizer)) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Missing JARVIS component: $path"
    }
}
if (-not (Test-Path -LiteralPath $backtalkPython)) {
    throw "Missing JARVIS voice runtime: $backtalkPython"
}

New-Item -ItemType Directory -Force -Path $logs, (Join-Path $runtime "signals"),
    $models | Out-Null
$envFile = Join-Path $root ".env"
# The sign-in process inherits only Supabase's public project configuration,
# never model-provider API keys loaded for the voice process later.
Import-DotEnv $envFile -AllowedNames @("SUPABASE_URL", "SUPABASE_ANON_KEY",
    "JARVIS_AUTH_REQUIRED")

# Auth is deliberately opt-in until the Supabase project/user is configured
# and the owner has passed a live login test. Once enabled, cancel/failure
# stops startup before the microphone, face, or agent services are launched.
if ($Desktop -and $env:JARVIS_AUTH_REQUIRED -eq "1") {
    $authPython = Join-Path $runtime "desktop-venv\Scripts\python.exe"
    $authGate = Join-Path $root "desktop\auth_gate.py"
    if (-not (Test-Path -LiteralPath $authPython) -or
            -not (Test-Path -LiteralPath $authGate)) {
        throw "JARVIS sign-in runtime is missing; no services were started."
    }
    $inheritedProviderSecrets = @{}
    foreach ($secretName in @("OPENAI_API_KEY", "GEMINI_API_KEY", "AI_API_KEY",
            "FISH_API_KEY", "FISH_AUDIO_API_KEY", "ELEVENLABS_API_KEY",
            "BRAVE_SEARCH_API_KEY")) {
        $secretValue = [Environment]::GetEnvironmentVariable($secretName, "Process")
        if ($null -ne $secretValue) {
            $inheritedProviderSecrets[$secretName] = $secretValue
            [Environment]::SetEnvironmentVariable($secretName, $null, "Process")
        }
    }
    try {
        & $authPython $authGate
        if ($LASTEXITCODE -ne 0) {
            throw "JARVIS sign-in was cancelled or failed; no services were started."
        }
    }
    finally {
        foreach ($secretName in $inheritedProviderSecrets.Keys) {
            [Environment]::SetEnvironmentVariable(
                $secretName, $inheritedProviderSecrets[$secretName], "Process")
        }
    }
}
Remove-Item Env:\SUPABASE_ANON_KEY -ErrorAction SilentlyContinue
Import-DotEnv $envFile
Remove-Item Env:\SUPABASE_ANON_KEY -ErrorAction SilentlyContinue

$env:BACKTALK_CONFIG = Join-Path $config "backtalk.json"
$env:BAREHANDS_CONFIG = Join-Path $config "barehands.json"
$env:AI_VISUALIZER_CONFIG = Join-Path $config "ai-visualizer.json"
$env:BACKTALK_LOG = Join-Path $logs "backtalk.log"
$env:HF_HOME = Join-Path $models "huggingface"
$env:JARVIS_FLORENCE_ENABLED = "0"

# A freshly installed winget portable FFmpeg may not yet be visible in the
# Explorer process PATH. Fish Audio playback needs the executable, so resolve
# it from the per-user winget package location before starting Backtalk.
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    $wingetPackages = Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Packages'
    if (Test-Path -LiteralPath $wingetPackages) {
        $ffmpeg = Get-ChildItem -LiteralPath $wingetPackages -Filter 'ffmpeg.exe' `
            -Recurse -File -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($ffmpeg) {
            $env:PATH = $ffmpeg.DirectoryName + [IO.Path]::PathSeparator + $env:PATH
        }
    }
}

# Use the app-owned runtime. A clean installation must not depend on a
# machine-wide Python command still being on PATH after setup.
$python = $backtalkPython

function Start-DesktopCockpit {
    $desktopApp = Join-Path $root "desktop\board_app.py"
    $pythonw = Join-Path $runtime "desktop-venv\Scripts\pythonw.exe"
    if (-not (Test-Path -LiteralPath $desktopApp)) {
        throw "Missing desktop app: $desktopApp"
    }
    if (-not (Test-Path -LiteralPath $pythonw)) {
        throw "Missing Board cockpit runtime: $pythonw. Install pywebview in runtime\desktop-venv first."
    }
    # UI attaches to the existing local bridge. Provider keys stay in the
    # voice process and are never inherited by this new WebView2 window.
    foreach ($secretName in @("OPENAI_API_KEY", "GEMINI_API_KEY",
            "AI_API_KEY", "FISH_API_KEY", "FISH_AUDIO_API_KEY",
            "ELEVENLABS_API_KEY")) {
        [Environment]::SetEnvironmentVariable($secretName, $null, "Process")
    }
    return Start-Process $pythonw -ArgumentList ('"' + $desktopApp + '"') -WorkingDirectory (Join-Path $root "desktop") -PassThru -RedirectStandardError (Join-Path $logs "desktop-error.log") -RedirectStandardOutput (Join-Path $logs "desktop.log")
}

try {
    # Keep the launcher itself single-instance for its entire lifetime.  The
    # voice process also owns port 8791 as a last line of defence, but that
    # guard is reached only after the face/hands/vision workers have started.
    # Two launchers racing through that startup window used to make the second
    # voice process exit with "ANOTHER VOICE LINE", which the launcher then
    # misreported as a crash.  A named OS mutex closes that race without a
    # stale pid/lock file after a crash or force-close.
    $launcherMutex = [Threading.Mutex]::new($false, "Local\JARVIS-Launcher-v1")
    try {
        $ownsLauncherMutex = $launcherMutex.WaitOne(0)
    }
    catch [Threading.AbandonedMutexException] {
        # The previous launcher died without cleanup. Windows has already
        # transferred ownership to us, so recovery is safe and automatic.
        $ownsLauncherMutex = $true
    }

    if (-not $ownsLauncherMutex) {
        Write-Host "JARVIS is already starting or running. Reusing the existing instance." -ForegroundColor Yellow
        if ($Desktop) {
            Start-DesktopCockpit | Out-Null
            Write-Host "Board cockpit attached to the existing JARVIS session." -ForegroundColor Cyan
        }
        if (-not $NoBrowser -and (Test-LocalPort 8790)) {
            Start-Process "http://127.0.0.1:8790/"
        }
        return
    }

    # Also cover a voice line started directly (outside this launcher). Do not
    # start a second keyboard hook or microphone owner.
    if (Test-LocalPort 8791) {
        Write-Host "JARVIS voice is already running. No duplicate was started." -ForegroundColor Yellow
        if ($Desktop) {
            Start-DesktopCockpit | Out-Null
            Write-Host "Board cockpit attached to the existing JARVIS session." -ForegroundColor Cyan
        }
        if (-not $NoBrowser -and (Test-LocalPort 8790)) {
            Start-Process "http://127.0.0.1:8790/"
        }
        return
    }

    Write-Host ""
    Write-Host "Starting JARVIS from $root" -ForegroundColor Cyan

    if (-not (Test-LocalPort 8790)) {
        $started += Start-Process $python -ArgumentList "server.py", "--no-open" -WorkingDirectory $visualizer -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logs "visualizer.log") -RedirectStandardError (Join-Path $logs "visualizer-error.log")
    }
    if (-not (Test-LocalPort 8794)) {
        $started += Start-Process $python -ArgumentList "server.py", "--no-open" -WorkingDirectory $barehands -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logs "barehands.log") -RedirectStandardError (Join-Path $logs "barehands-error.log")
    }
    if (-not (Test-LocalPort 8795) -and
        (Test-Path -LiteralPath $florencePython) -and
        (Test-Path -LiteralPath $florenceWorker) -and
        (Test-Path -LiteralPath (Join-Path $florenceModel "model.safetensors"))) {
        $started += Start-Process $florencePython -ArgumentList "-B", $florenceWorker, "--model-dir", $florenceModel, "--port", "8795" -WorkingDirectory $core -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logs "florence.log") -RedirectStandardError (Join-Path $logs "florence-error.log")
    }

    if ((Wait-LocalPort 8790) -and -not $NoBrowser) {
        Start-Process "http://127.0.0.1:8790/"
    }
    elseif (-not (Test-LocalPort 8790)) {
        Write-Warning "JARVIS face did not start on port 8790."
    }

    if ((Wait-LocalPort 8794) -and -not $NoBrowser) {
        Start-Process "http://127.0.0.1:8794/stage.html"
    }
    elseif (-not (Test-LocalPort 8794)) {
        Write-Warning "JARVIS hands did not start on port 8794."
    }

    if (Wait-LocalPort 8795 -Seconds 35) {
        $env:JARVIS_FLORENCE_ENABLED = "1"
        Write-Host "Local Florence semantic vision is ready." -ForegroundColor Green
    }
    else {
        Write-Warning "Local Florence semantic vision is unavailable; deterministic vision remains active."
    }

    Write-Host ""
    Write-Host "JARVIS is ready." -ForegroundColor Green
    Write-Host "Hold HOME, speak, then release."
    Write-Host "Close this window to stop the voice, face, hands, and local vision worker."
    Write-Host ""

    # Launch through the venv, then attach supervision to the process that
    # actually owns Backtalk's single-instance listener. Windows venv/uv
    # launchers can be redirector processes: stopping only the returned PID
    # leaves the real Python child alive with the microphone and HOME hook.
    $voiceBootstrap = Start-Process $backtalkPython -ArgumentList "-m", "backtalk.main" -WorkingDirectory $backtalk -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logs "backtalk-console.log") -RedirectStandardError (Join-Path $logs "backtalk-console-error.log")
    $started += $voiceBootstrap
    $voiceOwnerId = Wait-ListenerOwner 8791 -Seconds 20
    if (-not $voiceOwnerId) {
        if (-not $voiceBootstrap.HasExited) {
            Stop-Process -Id $voiceBootstrap.Id -ErrorAction SilentlyContinue
        }
        throw "JARVIS voice did not claim its single-instance listener. See runtime logs."
    }
    $voice = Get-Process -Id $voiceOwnerId -ErrorAction Stop
    if ($voice.Id -ne $voiceBootstrap.Id) {
        $started += $voice
    }
    if ($Desktop) {
        $started += Start-DesktopCockpit
        Write-Host "Desktop cockpit opened. Closing this launcher stops JARVIS." -ForegroundColor Cyan
    }
    $voice.WaitForExit()
    $voice.Refresh()
    $voiceExitCode = $null
    try { $voiceExitCode = $voice.ExitCode } catch {}
    if ($null -eq $voiceExitCode) {
        throw "JARVIS voice exited unexpectedly (exit code unavailable). See runtime logs."
    }
    if ($voiceExitCode -ne 0) {
        throw "JARVIS voice process exited with code $voiceExitCode. See runtime logs."
    }
}
finally {
    Remove-Item Env:\OPENAI_API_KEY -ErrorAction SilentlyContinue
    Remove-Item Env:\GEMINI_API_KEY -ErrorAction SilentlyContinue
    Remove-Item Env:\ELEVENLABS_API_KEY -ErrorAction SilentlyContinue
    Remove-Item Env:\FISH_API_KEY -ErrorAction SilentlyContinue
    Remove-Item Env:\FISH_AUDIO_API_KEY -ErrorAction SilentlyContinue
    Remove-Item Env:\JARVIS_FLORENCE_ENABLED -ErrorAction SilentlyContinue
    # Children were appended after their launchers. Stop in reverse order so
    # a redirector cannot orphan the real microphone-owning Python process.
    for ($i = $started.Count - 1; $i -ge 0; $i--) {
        $process = $started[$i]
        if ($process -and -not $process.HasExited) {
            Stop-Process -Id $process.Id -ErrorAction SilentlyContinue
        }
    }
    if ($ownsLauncherMutex -and $launcherMutex) {
        try { $launcherMutex.ReleaseMutex() } catch {}
    }
    if ($launcherMutex) {
        $launcherMutex.Dispose()
    }
}
