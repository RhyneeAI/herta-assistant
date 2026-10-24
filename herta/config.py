"""
Configuration management for Madam Herta Assistant.
Cross-platform support for Linux and Windows operating systems.
"""

import json
import os
import sys

IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    APPDATA = os.environ.get("APPDATA", os.path.expanduser("~\\AppData\\Roaming"))
    LOCALAPPDATA = os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
    CONFIG_DIR = os.path.join(APPDATA, "HertaAssistant")
    CACHE_DIR = os.path.join(LOCALAPPDATA, "HertaAssistant", "cache")
    TMP_DIR = os.path.join(LOCALAPPDATA, "Temp", "HertaAssistant")
else:
    CONFIG_DIR = os.path.expanduser("~/.config/herta")
    CACHE_DIR = os.path.expanduser("~/.cache/herta")
    TMP_DIR = "/mnt/games/tmp" if os.path.exists("/mnt/games") else "/tmp/herta"

os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(TMP_DIR, exist_ok=True)

CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(PACKAGE_DIR, "assets")
AUDIO_DIR = os.path.join(ASSETS_DIR, "audio")

# Default settings (Partner name defaults to affectionate 'あなた' / Sayang)
DEFAULT_CONFIG = {
    "partner_name": "あなた",
    "gemini_api_key": "",
    "rvc_enabled": True,
    "rvc_model_path": "/mnt/games/rvc_models/model.pth" if not IS_WINDOWS else os.path.join(CONFIG_DIR, "models", "model.pth"),
    "rvc_index_path": "/mnt/games/rvc_models/model.index" if not IS_WINDOWS else os.path.join(CONFIG_DIR, "models", "model.index"),
    "tts_voice": "ja-JP-NanamiNeural",
    "gemini_chat_model": "gemini-3.5-flash",
    "gemini_tts_model": "gemini-2.5-flash-preview-tts"
}


def load_config() -> dict:
    """Load configuration dictionary, creating defaults if not present."""
    cfg = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                cfg.update(saved)
        except Exception:
            pass
    else:
        save_config(cfg)

    # Check for legacy Gemini API key files
    if not cfg.get("gemini_api_key"):
        legacy_key_file = os.path.expanduser("~/.gemini_api_key")
        if os.path.exists(legacy_key_file):
            try:
                with open(legacy_key_file, "r", encoding="utf-8") as f:
                    cfg["gemini_api_key"] = f.read().strip()
            except Exception:
                pass
        if not cfg.get("gemini_api_key"):
            cfg["gemini_api_key"] = os.environ.get("GEMINI_API_KEY", "")

    return cfg


def save_config(cfg: dict):
    """Save configuration dictionary to disk."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception as exc:
        sys.stderr.write(f"Failed to save config: {exc}\n")
