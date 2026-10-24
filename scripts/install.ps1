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

# Link .venv in project root for IDE detection (Pyright/VS Code)
$ProjectVenv = Join-Path $ProjectDir ".venv"
if (-not (Test-Path $ProjectVenv)) {
    try {
        New-Item -ItemType Junction -Path $ProjectVenv -Target $VenvDir -ErrorAction SilentlyContinue | Out-Null
    } catch {}
}

$PythonExe = Join-Path $VenvDir "Scripts\python.exe"
$PipExe = Join-Path $VenvDir "Scripts\pip.exe"


# 2. Install Dependencies
Write-Host "Installing Core Python dependencies..." -ForegroundColor Yellow
& $PipExe install --upgrade pip
& $PipExe install PyQt6 Pillow edge-tts soundfile requests numpy scipy librosa
& $PipExe install -e $ProjectDir

Write-Host "Installing optional RVC voice conversion packages..." -ForegroundColor Yellow
try {
    & $PipExe install torch torchcrepe transformers praat-parselmouth faiss-cpu infer-rvc-python --no-deps
} catch {
    Write-Host "Note: Optional RVC dependencies skipped. Herta will use Fast Edge-TTS mode." -ForegroundColor Gray
}


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

# 6. Optional Initial Configuration (Partner Name & Gemini API Key)
Write-Host "`n======================================================================" -ForegroundColor Cyan
Write-Host "⚙️   INITIAL CONFIGURATION (OPTIONAL)" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Press [Enter] to keep defaults, or customize your initial settings:`n" -ForegroundColor Gray

# Prompt Partner Name
$CurrentName = "あなた"
try {
    $CfgRaw = & $PythonExe -c "from herta.config import load_config; print(load_config().get('partner_name', 'あなた'))"
    if ($CfgRaw) { $CurrentName = $CfgRaw.Trim() }
} catch {}

$InputName = Read-Host "Partner name / title Madam Herta uses to address you (Default: $CurrentName)"
if (-not [string]::IsNullOrWhiteSpace($InputName)) {
    & $PythonExe -m herta.cli config --name $InputName
}

# Prompt Gemini API Key
$HasKey = $false
try {
    $KeyStatus = & $PythonExe -c "from herta.config import load_config; print(bool(load_config().get('gemini_api_key')))"
    if ($KeyStatus -eq "True") { $HasKey = $true }
} catch {}

if ($HasKey) {
    Write-Host "Google Gemini API Key is already configured." -ForegroundColor Green
    $InputKey = Read-Host "Update Gemini API Key (Optional - press [Enter] to keep existing)"
} else {
    $InputKey = Read-Host "Enter your Google Gemini API Key (Optional - press [Enter] to skip)"
}

if (-not [string]::IsNullOrWhiteSpace($InputKey)) {
    & $PythonExe -m herta.cli config --key $InputKey
}

Write-Host "`n======================================================================" -ForegroundColor Green
Write-Host "✨ Installation Complete for Windows!" -ForegroundColor Green
Write-Host "You can now run 'herta' or 'herta chat' in PowerShell or CMD." -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green

