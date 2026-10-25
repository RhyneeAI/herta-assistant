# <img src="assets/images/herta_avatar_64.png" width="32" height="32" valign="middle" /> Madam Herta Assistant (ヘルタ)

Authentic **Madam Herta** (Genius Society #83 from *Honkai: Star Rail*) AI Assistant ecosystem for **Linux** and **Windows**.

Features 100% authentic Japanese spoken voice using **Yamazaki Haruka (山崎はるか)** RVC v2 weights, paired with clean subtitle translations in Indonesian and English across your desktop, notifications, and interactive floating mascot.

---

## ✨ Features

* **Authentic Japanese Voice (山崎はるか / Herta JP)**:
  Trained on official voicelines from *Honkai: Star Rail* via RVC v2 (Retrieval-based Voice Conversion) for genuine anime seiyuu cadence, tone, and emotional inflection.
* **Authentic In-Game "Kuru Kuru~ Kururin~" Voice Samples**:
  Direct in-game battle & talent audio clips (くるくる～――っと！, くるりん～っと！, くるりんっ！) from *Honkai: Star Rail* integrated into greetings, mascot pokes, wake-ups, and dedicated Kuru Kuru interactive triggers.
* **Desktop Mascot & System Tray GUI (`herta gui`)**:
  Interactive desktop companion combining a frameless, transparent, draggable anime mascot (with animated Kuru Kuru spinning GIF, mini action toolbar, and live subtitle speech bubbles) and an unobtrusive system tray applet with quick controls. Includes an interactive `🌀 Kuru Kuru!` button, voice replays (`🔊`), and quick suggestion chips.
* **Subtitles in Indonesian & English**:
  Every response displays the Japanese line alongside an Indonesian (`id`) or English (`en`) translation subtitle.
* **Proactive Companion & Wife Mode (Sweet Wife & Yandere)**:
  Periodically and spontaneously checks in on you (customizable, default: every 20–45 minutes). Switchable between **Sweet Wife** (doting tsundere) and **Yandere** (sweetly possessive and obsessive).
* **Boot & Login Greeting**:
  Plays time-contextual voicelines (morning, afternoon, evening) with native desktop notifications when your computer starts or logs in.
* **Sleep & Wake Monitor**:
  * **Going to Sleep**: Plays a bedtime voiceline (*"Mou neru no, anata? Kuru kuru~ Oyasumi, mata ashita ne!"*).
  * **Waking Up**: Greets you on resume (*"Kuru kuru~ Kururin! Okaeri, anata!"*).
* **Cross-Platform**:
  Full native compatibility for both **Linux** (systemd, PipeWire/PulseAudio, notify-send) and **Windows 10/11** (Win32 power broadcast, winsound, PowerShell toast notifications).

---

## 📋 Requirements & Prerequisites

Before installing, ensure your environment meets the following requirements:

### 1. Python Environment
* **Python Version**: Python `>= 3.10` (Recommended: **Python 3.10 – 3.12** for full local RVC v2 neural voice conversion compatibility, or **Python 3.10 – 3.14+** for standard Edge-TTS Japanese voice & Desktop GUI).
* **System PATH**: Ensure *"Add python.exe to PATH"* is checked when installing Python on Windows.

### 2. Python Packages
Dependencies are separated into two tiers:
* **Core & Desktop GUI (Required)** — Lightweight and runs out of the box across all platforms:
  * `PyQt6` (Desktop Mascot & System Tray UI)
  * `Pillow` (Herta GIF animations & transparent sprite rendering)
  * `edge-tts` (Real-time Japanese voice synthesis)
  * `soundfile` & `numpy` (Audio playback & waveform processing)
  * `requests` (Gemini API communication)
* **RVC Neural Voice Conversion (Optional)** — Authentic Yamazaki Haruka RVC v2 inference:
  * `torch`, `torchaudio`, `torchcrepe`, `transformers`, `praat-parselmouth`, `infer-rvc-python`, `faiss-cpu`, `scipy`, `librosa`.
  * *Note:* If RVC packages are omitted or fail to compile on your system, Madam Herta automatically engages a *graceful fallback* to the high-clarity Japanese Edge-TTS voice (`ja-JP-NanamiNeural`) with zero lag.

### 3. System Tools (Recommended)
* **Windows**: `ffmpeg` (recommended for general audio conversions), Visual C++ Build Tools (only if compiling native Cython packages like `pyworld`).
* **Linux**: `ffmpeg`, `libasound2-dev`, `python3-venv`, `notify-send`.

---

## 🚀 Installation Guide

### Option 1: Automated Installer (Recommended)

#### 🔹 On Windows (10 / 11):
1. Open PowerShell and navigate to the project directory.
2. Run the installer script:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\install.ps1
```
*(Alternatively, simply double-click `scripts\install.bat`)*

The installer will:
* Create a dedicated Python virtual environment in `%USERPROFILE%\.herta-env`.
* Install all required dependencies and register the package in editable mode.
* Download the Yamazaki Haruka RVC model files into `%APPDATA%\HertaAssistant\models`.
* Create the global `herta.cmd` launcher in your user PATH.
* Setup Windows Startup shortcuts for boot greeting and background sleep/wake monitor.
* **Initial Setup Prompt (Optional)**: Prompt you to set your partner name / title (default: `"あなた"` / *Anata*) and your Google Gemini API Key (press Enter to skip or keep defaults).

#### 🔹 On Linux:
```bash
cd herta-assistant
chmod +x scripts/install.sh
./scripts/install.sh
```

The installer will automatically set up the virtual environment, install dependencies, register the `herta` CLI in `~/.local/bin`, prompt for initial partner name and Gemini API key, and enable the `herta-sleep-monitor.service` systemd user service.

---

### Option 2: Manual Installation (Step-by-Step)

If you prefer to manage your virtual environment manually:

```bash
# 1. Navigate to the project directory
cd herta-assistant

# 2. Create Python virtual environment
python -m venv .venv

# 3. Activate the virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Windows (CMD):
.venv\Scripts\activate.bat
# Linux:
source .venv/bin/activate

# 4. Upgrade pip & install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 5. Install herta-assistant in editable mode
pip install -e .

# 6. (Optional) Configure partner name and Gemini API key
herta config --name "あなた" --key "YOUR_GEMINI_API_KEY"

# 7. Launch Madam Herta Desktop Mascot
herta gui
```

---

## 💻 Usage & Commands

### CLI Command Reference

| Command | Option / Flag | Description |
| :--- | :--- | :--- |
| `herta gui` | *None* | Launch Madam Herta Desktop Mascot & System Tray GUI. |
| `herta` or `herta chat` | `[--fast]` | Start live voice chat session in terminal. `--fast` uses instant Edge-TTS. |
| `herta alarm` | `[list]` | View all currently scheduled alarms and active countdown timers. |
| `herta alarm add` | `<time> [label]` | Set a daily scheduled alarm (e.g. `herta alarm add 07:00 "Bangun Pagi"`). |
| `herta alarm timer` | `<minutes> [label]` | Set a countdown timer (e.g. `herta alarm timer 25 "Pomodoro Break"`). |
| `herta alarm delete` | `<id>` | Delete an alarm or timer by its unique ID. |
| `herta alarm test` | *None* | Test Madam Herta wake-up voice and pop-up dialog immediately. |
| `herta greet` | *None* | Trigger time-aware login/startup voice greeting (morning, afternoon, evening). |
| `herta sleep` | *None* | Manually trigger bedtime / going-to-sleep voiceline. |
| `herta wake` | *None* | Manually trigger resume / wake-up voiceline. |
| `herta nudge` | *None* | Ask Madam Herta to say something sweet, tease you, or check in on you right now. |
| `herta companion` | `[--now]`<br>`[--interval <m>]` | Run companion loop in foreground. `--now` fires an interaction immediately. |
| `herta monitor` | *None* | Run background power listener (sleep/wake events), companion daemon, and alarm scheduler. |
| `herta service on` | *None* | Enable and start background daemon (`systemd` on Linux, Startup on Windows). |
| `herta service off` | *None* | Stop and disable background service. |
| `herta service restart` | *None* | Restart background service to reload changes. |
| `herta service status` | *None* | Check whether background service is currently running. |
| `herta config` | *See below* | View or update configuration values directly via CLI. |

### CLI Configuration Flags (`herta config`)

```bash
herta config [OPTIONS]
```

| Option | Argument Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `--name` | `string` | `"あなた"` | Set the partner name or title Herta uses to address you. |
| `--key` | `string` | `""` | Set or update your Google Gemini API key. |
| `--rvc` | `on` \| `off` | `on` | Enable or disable high-fidelity RVC Yamazaki Haruka voice transformation. |
| `--romance` | `on` \| `off` | `on` | Enable or disable affectionate anime wife mode (intimate Japanese inflections). |
| `--style` | `sweet_wife` \| `yandere` | `sweet_wife` | Choose romance persona style: `sweet_wife` (affectionate tsundere) or `yandere` (obsessive & possessive). |
| `--lang` | `id` \| `en` | `id` | Choose subtitle translation language: `id` (Indonesian, default) or `en` (English). |
| `--companion-min` | `integer` | `20` | Minimum wait interval (in minutes) for spontaneous companion check-ins. |
| `--companion-max` | `integer` | `45` | Maximum wait interval (in minutes) for spontaneous companion check-ins. |
| `--telegram-token` | `string` | `""` | Optional Telegram Bot Token to forward alarm alerts directly to your phone. |
| `--telegram-chat-id` | `string` | `""` | Optional Telegram Chat ID to receive phone alarm alerts. |


---

## ⚙️ Configuration Reference (`config.json`)

Configuration settings are stored in JSON format and loaded automatically at startup:
* **Linux**: `~/.config/herta/config.json`
* **Windows**: `%APPDATA%\HertaAssistant\config.json`

### Example `config.json`

```json
{
  "partner_name": "あなた",
  "gemini_api_key": "YOUR_GEMINI_API_KEY",
  "rvc_enabled": true,
  "rvc_model_path": "/mnt/games/rvc_models/model.pth",
  "rvc_index_path": "/mnt/games/rvc_models/model.index",
  "tts_voice": "ja-JP-NanamiNeural",
  "gemini_chat_model": "gemini-3.5-flash",
  "gemini_tts_model": "gemini-2.5-flash-preview-tts",
  "romance_mode": true,
  "romance_address_style": "sweet_wife",
  "subtitle_language": "id",
  "companion_min_minutes": 20,
  "companion_max_minutes": 45
}
```

### Key Descriptions & Parameters

| Key | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `partner_name` | `string` | `"あなた"` | How Madam Herta addresses you in conversation and notifications. When set to `"あなた"` (*Anata*), it conveys an intimate, affectionate tone like an anime wife addressing her husband, accompanied by the Indonesian subtitle translation *"Sayang"* (or *"Darling"* in English). You can also customize it to your name (e.g. `"Rinne"`) or title (e.g. `"夫"` / *Danna-sama*). |
| `gemini_api_key` | `string` | `""` | Google Gemini API Key used for dynamic chat reasoning, spontaneous dialogue generation, and fallback intelligence. Can also be set via the `GEMINI_API_KEY` environment variable or legacy `~/.gemini_api_key`. |
| `rvc_enabled` | `boolean` | `true` | When `true`, all speech synthesis is converted through Retrieval-based Voice Conversion (RVC v2) using Yamazaki Haruka's official Herta voice weights. When `false`, uses raw Edge-TTS for ultra-fast response without neural pitch modeling. |
| `rvc_model_path` | `string` | Path | Absolute path to the trained RVC `.pth` checkpoint file. Defaults to `/mnt/games/rvc_models/model.pth` on Linux or `%APPDATA%\HertaAssistant\models\model.pth` on Windows. |
| `rvc_index_path` | `string` | Path | Absolute path to the trained RVC `.index` feature retrieval index file. Enhances acoustic timbre matching and prevents voice distortion. |
| `tts_voice` | `string` | `"ja-JP-NanamiNeural"` | The base Microsoft Edge-TTS voice synthesized before RVC voice conversion. Pre-tuned with custom pitch (+8Hz) and rate (+2%) for lively Japanese intonation. |
| `gemini_chat_model` | `string` | `"gemini-3.5-flash"` | The Gemini model identifier used for conversational LLM chat turns and generating spontaneous companion dialogues. |
| `gemini_tts_model` | `string` | `"gemini-2.5-flash-preview-tts"` | Fallback cloud TTS model used if local neural TTS synthesis is unreachable. |
| `romance_mode` | `boolean` | `true` | When `true`, engages Madam Herta's intimate anime wife persona. Prompts inject affectionate phrasing, playful tsundere teasing, loving pauses (`...`, `〜`), and sweet Japanese particles (`よ`, `ね`, `わ`). |
| `romance_address_style` | `string` | `"sweet_wife"` | Preset addressing style for the romance engine. Options: `"sweet_wife"` (loving, doting, tsundere anime wife) or `"yandere"` (obsessively loving, sweetly possessive, clingy, subtle chilling possessiveness). |
| `subtitle_language` | `string` | `"id"` | Subtitle translation language displayed in terminal and desktop notification banners. Options: `"id"` (Indonesian, default) or `"en"` (English). Spoken voice always remains 100% Japanese. |
| `companion_min_minutes` | `integer` | `20` | Lower bound of the randomized spontaneous companion timer in minutes. Prevents check-ins from firing too frequently. |
| `companion_max_minutes` | `integer` | `45` | Upper bound of the randomized spontaneous companion timer in minutes. Ensures Herta spontaneously checks in before you stay idle or overworked for too long. |

---

## ⚙️ In-Chat Commands

While in a `herta chat` session:
* **Press `[ENTER]`**: Record your microphone input.
* **Type text**: Send typed messages directly.
* **`name <new_name>`**: Change your partner name on the fly.
* **`style <sweet_wife|yandere>`**: Switch romance style dynamically.
* **`lang <id|en>`**: Switch subtitle language on the fly.
* **`rvc on` / `rvc off`**: Toggle between high-fidelity Yamazaki Haruka voice and instant Fast TTS.
* **`exit`**: End the conversation.

---

## 📁 Project Directory Structure

```text
herta-assistant/
├── assets/
│   ├── audio/              # Pre-rendered voicelines (morning, afternoon, sleep, wake)
│   └── images/             # Authentic avatar icons and Kuru Kuru animated GIFs
├── herta/
│   ├── __init__.py
│   ├── audio.py            # Cross-platform audio playback & mic recording
│   ├── chat.py             # Interactive live voice chat engine
│   ├── cli.py              # Unified command-line interface entrypoint
│   ├── companion.py        # Proactive companion loop & spontaneous interactions
│   ├── config.py           # Configuration manager (Linux & Windows paths)
│   ├── greeting.py         # Startup / boot greeting handler
│   ├── gui.py              # Desktop Mascot & System Tray GUI (PyQt6)
│   ├── notifier.py         # Cross-platform desktop toast notification banners
│   ├── power_monitor.py    # Sleep and wake listener (DBus / Win32)
│   ├── rvc.py              # RVC v2 Yamazaki Haruka inference wrapper
│   ├── service.py          # Background service controller
│   └── tts.py              # Japanese TTS generator (Edge-TTS & Gemini)
├── scripts/
│   ├── download_models.py  # Automatic Hugging Face RVC model downloader
│   ├── install.bat         # Windows double-click installer
│   ├── install.ps1         # Windows PowerShell installer
│   └── install.sh          # Linux Bash installer
├── pyproject.toml          # Python package specification
├── README.md               # Documentation
└── requirements.txt        # Python package dependencies
```

---

## 🔑 Configuration & Storage Paths

* **Linux**:
  * Config: `~/.config/herta/config.json`
  * Cache & Models: `~/.config/herta/models/`
* **Windows**:
  * Config: `%APPDATA%\HertaAssistant\config.json`
  * Cache & Models: `%APPDATA%\HertaAssistant\models\`
