"""
Startup and boot voice greeting module for Madam Herta.
Plays pre-rendered authentic Yamazaki Haruka voiceline according to local time
and shows desktop notification with Indonesian subtitle translation.
"""

import datetime
import json
import os

from herta.audio import play_audio
from herta.config import AUDIO_DIR, load_config
from herta.notifier import show_notification
from herta.reminders import get_active_reminders


def get_time_slot_key() -> str:
    """Determine audio key based on current local hour."""
    hour = datetime.datetime.now().hour
    if 5 <= hour < 12:
        return "herta_morning"
    elif 12 <= hour < 18:
        return "herta_afternoon"
    else:
        return "herta_evening"


def trigger_greeting():
    """Execute startup voice greeting."""
    cfg = load_config()
    partner_name = cfg.get("partner_name", "あなた")
    sub_lang = cfg.get("subtitle_language", "id")
    key = get_time_slot_key()

    audio_file = os.path.join(AUDIO_DIR, f"{key}.wav")
    meta_file = os.path.join(AUDIO_DIR, "voicelines.json")

    jp_text = f"クルクル〜クルリン！こんにちは、{partner_name}！マダム・ヘルタよ。"
    sub_text = f"Kuru kuru~ Kururin! Halo, {partner_name}! Madam Herta di sini."
    flag = "🇮🇩"

    if os.path.exists(meta_file):
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                meta = json.load(f)
                if key in meta:
                    jp_text = meta[key].get("jp", jp_text).replace("リンネ", partner_name)
                    if sub_lang == "en":
                        sub_text = meta[key].get("en", "").replace("Rinne", partner_name)
                        flag = "🇬🇧"
                    else:
                        sub_text = meta[key].get("id", "").replace("Rinne", partner_name)
                        flag = "🇮🇩"
        except Exception:
            pass

    # Append active priority reminder if due today
    active_rems = get_active_reminders()
    if active_rems:
        top_rem = active_rems[0].get("title", "")
        if sub_lang == "en":
            sub_text += f"\n📌 Priority Reminder: {top_rem}"
        else:
            sub_text += f"\n📌 Pengingat Prioritas: {top_rem}"

    # Display notification banner with subtitles and Herta icon
    show_notification(f"Madam Herta: {jp_text}", f"{flag} {sub_text}")

    # Play authentic Yamazaki Haruka audio
    if os.path.exists(audio_file):
        play_audio(audio_file, timeout=15)
