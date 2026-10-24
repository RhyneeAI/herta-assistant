# 💎 Madam Herta Assistant (ヘルタ)

Authentic **Madam Herta** (Genius Society #83 from *Honkai: Star Rail*) AI Assistant ecosystem for **Linux** and **Windows**.

Features 100% authentic Japanese spoken voice using **Yamazaki Haruka (山崎はるか)** RVC v2 weights, paired with clean Indonesian subtitle translations in your terminal and desktop notifications.

---

## ✨ Features

* **Authentic Japanese Voice (山崎はるか / Herta JP)**:
  Trained on official voicelines from Honkai: Star Rail via RVC v2 (Retrieval-based Voice Conversion) for genuine anime seiyuu cadence and tone.
* **Indonesian Subtitles**:
  Every response displays the Japanese line alongside an Indonesian translation subtitle.
* **Proactive Companion & Wife Mode**:
  Periodically and spontaneously checks in on you (every 45–90 minutes), asking if you're tired, reminding you to drink water, acting bored and demanding attention, or sharing sweet tsundere praise (*"Nee, anata~ Watashi chotto taikutsu nandakedo!"*).
* **Boot & Login Greeting**:
  Plays time-contextual voicelines (morning, afternoon, evening) when your computer starts or logs in.
* **Sleep & Wake Monitor**:
  * **Going to Sleep**: Plays a bedtime voiceline (*"Mou neru no, Rinne? Kuru kuru~ Oyasumi, mata ashita ne!"*).
  * **Waking Up**: Greets you on resume (*"Kuru kuru~ Kururin! Okaeri, Rinne!"*).
* **Cross-Platform**:
  Full native compatibility for both **Linux** (systemd, PipeWire/PulseAudio, notify-send) and **Windows 10/11** (Win32 power broadcast, winsound, PowerShell toast notifications).

---

## 🚀 Quick Installation

### On Linux

Clone or copy the directory, then run the installer:

```bash
cd herta-assistant
chmod +x scripts/install.sh
./scripts/install.sh
```

The installer will:
1. Create or use Python virtual environment.
2. Install dependencies and register the `herta` command in `~/.local/bin`.
3. Link or download the Yamazaki Haruka RVC model weights.
4. Enable the `herta-sleep-monitor.service` systemd user service.
5. Setup the desktop autostart login greeting.

---

### On Windows (10 / 11)

1. Open PowerShell as Administrator or standard user.
2. Navigate to the folder and run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\install.ps1
```
*(Alternatively, simply double-click `scripts\install.bat`)*

The installer will:
1. Create a Python virtual environment in `%USERPROFILE%\.herta-env`.
2. Install all required dependencies.
3. Automatically download the Yamazaki Haruka model files into `%APPDATA%\HertaAssistant\models`.
4. Create the `herta.cmd` launcher in your user PATH.
5. Create Windows Startup shortcuts for the login greeting and background sleep monitor.

---

## 💻 Usage & Commands

| Command | Description |
| :--- | :--- |
| `herta` or `herta chat` | Start interactive live voice chat session |
| `herta chat --fast` | Chat in Fast Mode (Instant Japanese TTS without RVC) |
| `herta greet` | Trigger the startup / login voice greeting |
| `herta sleep` | Manually trigger the bedtime voiceline |
| `herta wake` | Manually trigger the wake-up voiceline |
| `herta nudge` or `herta companion --now` | Trigger a spontaneous companion interaction right now |
| `herta companion` | Run the standalone companion loop in foreground |
| `herta monitor` | Run background sleep/wake power monitor + companion daemon |
| `herta service status` | Inspect whether background monitor daemon is active |
| `herta service on` | Start and enable background service at boot |
| `herta service off` | Stop and disable background service |
| `herta service restart` | Restart background service |
| `herta config` | View current configuration settings |
| `herta config --name <name>` | Change your registered partner name |
| `herta config --key <api_key>` | Set or update your Google Gemini API key |

---

## ⚙️ In-Chat Commands

While in a `herta chat` session:
* **Press `[ENTER]`**: Record your microphone input.
* **Type text**: Send typed messages directly.
* **`name <new_name>`**: Change your partner name on the fly.
* **`rvc on` / `rvc off`**: Toggle between high-fidelity Yamazaki Haruka voice and instant Fast TTS.
* **`exit`**: End the conversation.

---

## 📁 Project Directory Structure

```text
herta-assistant/
├── assets/
│   └── audio/              # Pre-rendered voicelines (morning, afternoon, sleep, wake)
├── herta/
│   ├── __init__.py
│   ├── audio.py            # Cross-platform audio playback & mic recording
│   ├── chat.py             # Interactive live voice chat engine
│   ├── cli.py              # Unified command-line interface entrypoint
│   ├── config.py           # Configuration manager (Linux & Windows paths)
│   ├── greeting.py         # Startup / boot greeting handler
│   ├── notifier.py         # Cross-platform desktop toast notification banners
│   ├── power_monitor.py    # Sleep and wake listener (DBus / Win32)
│   ├── rvc.py              # RVC v2 Yamazaki Haruka inference wrapper
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
