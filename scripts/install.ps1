# ==============================================================================
# Madam Herta Assistant - Windows One-Click PowerShell Installer
# ==============================================================================

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir
$VenvDir = Join-Path $env:USERPROFILE ".herta-env"
$BinDir = Join-Path $env:USERPROFILE "bin"

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "💎   INSTALLING MADAM HERTA ASSISTANT (WINDOWS)" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

# 1. Create Python Virtual Environment
if (-not (Test-Path $VenvDir)) {
    Write-Host "Creating Python virtual environment in $VenvDir..." -ForegroundColor Yellow
    python -m venv $VenvDir
}

$PythonExe = Join-Path $VenvDir "Scripts\python.exe"
$PipExe = Join-Path $VenvDir "Scripts\pip.exe"

# 2. Install Dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
& $PipExe install --upgrade pip
& $PipExe install -r (Join-Path $ProjectDir "requirements.txt")
& $PipExe install -e $ProjectDir

# 3. Download Models
Write-Host "Checking / Downloading voice models..." -ForegroundColor Yellow
& $PythonExe (Join-Path $ScriptDir "download_models.py")

# 4. Create herta.cmd Launcher
if (-not (Test-Path $BinDir)) {
    New-Item -ItemType Directory -Path $BinDir | Out-Null
}

$CmdLauncher = Join-Path $BinDir "herta.cmd"
"@echo off`n`"$PythonExe`" -m herta.cli %*" | Set-Content -Path $CmdLauncher -Encoding ASCII

# Ensure User PATH contains $BinDir
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($UserPath -notlike "*$BinDir*") {
    Write-Host "Adding $BinDir to User PATH..." -ForegroundColor Yellow
    [Environment]::SetEnvironmentVariable("Path", "$UserPath;$BinDir", "User")
    $env:Path += ";$BinDir"
}

# 5. Create Windows Startup Shortcuts
$StartupDir = [Environment]::GetFolderPath("Startup")
$WScriptShell = New-Object -ComObject WScript.Shell

# Boot Greeting Shortcut
$GreetingShortcutPath = Join-Path $StartupDir "HertaGreeting.lnk"
$GreetingShortcut = $WScriptShell.CreateShortcut($GreetingShortcutPath)
$GreetingShortcut.TargetPath = $PythonExe
$GreetingShortcut.Arguments = "-m herta.cli greet"
$GreetingShortcut.WindowStyle = 7 # Minimized
$GreetingShortcut.Save()

# Background Sleep Monitor Shortcut (vbs runner to hide console)
$MonitorVbsPath = Join-Path $ProjectDir "scripts\herta_monitor_background.vbs"
"CreateObject(`"Wscript.Shell`").Run `"`"`"$PythonExe`"`" -m herta.cli monitor`", 0, False" | Set-Content -Path $MonitorVbsPath -Encoding ASCII

$MonitorShortcutPath = Join-Path $StartupDir "HertaSleepMonitor.lnk"
$MonitorShortcut = $WScriptShell.CreateShortcut($MonitorShortcutPath)
$MonitorShortcut.TargetPath = "wscript.exe"
$MonitorShortcut.Arguments = "`"$MonitorVbsPath`""
$MonitorShortcut.Save()

Write-Host "`n======================================================================" -ForegroundColor Green
Write-Host "✨ Installation Complete for Windows!" -ForegroundColor Green
Write-Host "You can now run 'herta' or 'herta chat' in PowerShell or CMD." -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green
