"""
Madam Herta Alarm & Timer Assistant Engine.
Provides persistent alarms, countdown timers, wake-up audio triggers,
interactive pop-up dialogs, natural language intent parsing,
and optional Telegram phone bridge notifications.
"""

import datetime
import json
import os
import re
import sys
import threading
import time
import urllib.request
import urllib.parse

from herta.audio import play_audio
from herta.config import AUDIO_DIR, CONFIG_DIR, load_config
from herta.notifier import show_notification

ALARM_FILE = os.path.join(CONFIG_DIR, "alarms.json")
_alarm_lock = threading.Lock()
_active_alarm_players = {}


def load_alarms() -> list:
    """Load persistent alarms and timers from JSON."""
    with _alarm_lock:
        if os.path.exists(ALARM_FILE):
            try:
                with open(ALARM_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []


def save_alarms(alarms: list):
    """Save persistent alarms and timers to JSON."""
    with _alarm_lock:
        try:
            with open(ALARM_FILE, "w", encoding="utf-8") as f:
                json.dump(alarms, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            sys.stderr.write(f"Failed to save alarms: {exc}\n")


def parse_time_string(time_str: str) -> str:
    """
    Normalize various time string inputs to standard 'HH:MM' (24-hour).
    Supports: '7', '07:00', '7:30', '7.30', '7am', '7:30pm', '19:30'.
    """
    clean = time_str.strip().lower().replace(".", ":")

    # Match 12-hour format with am/pm (e.g. '7am', '7:30pm', '11:45 pm')
    am_pm_match = re.match(r"^(\d{1,2})(?::(\d{2}))?\s*(am|pm)$", clean)
    if am_pm_match:
        hour = int(am_pm_match.group(1))
        minute = int(am_pm_match.group(2) or 0)
        period = am_pm_match.group(3)
        if period == "pm" and hour != 12:
            hour += 12
        elif period == "am" and hour == 12:
            hour = 0
        return f"{hour:02d}:{minute:02d}"

    # Match standard HH:MM or H:MM
    standard_match = re.match(r"^(\d{1,2}):(\d{2})$", clean)
    if standard_match:
        hour = int(standard_match.group(1))
        minute = int(standard_match.group(2))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return f"{hour:02d}:{minute:02d}"

    # Match single hour number '7' -> '07:00'
    single_hour = re.match(r"^(\d{1,2})$", clean)
    if single_hour:
        hour = int(single_hour.group(1))
        if 0 <= hour <= 23:
            return f"{hour:02d}:00"

    raise ValueError(f"Invalid time format: '{time_str}'. Use HH:MM format (e.g., 07:00, 14:30).")


def add_alarm(
    time_str: str,
    label: str = "Alarm",
    days: list = None,
    sound: str = "herta_morning.wav",
    once: bool = False
) -> dict:
    """Register a new scheduled daily or one-shot alarm."""
    normalized_time = parse_time_string(time_str)
    alarms = load_alarms()

    alarm_id = f"alm_{int(time.time() * 1000)}"
    entry = {
        "id": alarm_id,
        "type": "alarm",
        "time": normalized_time,
        "label": label.strip() or "Alarm Madam Herta",
        "days": days if days is not None else ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "once": once,
        "enabled": True,
        "sound": sound,
        "last_triggered": "",
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    alarms.append(entry)
    save_alarms(alarms)
    return entry


def add_timer(
    minutes: float,
    label: str = "Timer",
    sound: str = "herta_morning.wav"
) -> dict:
    """Register a countdown timer."""
    if minutes <= 0:
        raise ValueError("Timer duration must be greater than 0 minutes.")

    target_ts = time.time() + (minutes * 60)
    target_dt = datetime.datetime.fromtimestamp(target_ts)
    alarms = load_alarms()

    alarm_id = f"tmr_{int(time.time() * 1000)}"
    entry = {
        "id": alarm_id,
        "type": "timer",
        "duration_minutes": minutes,
        "target_timestamp": target_ts,
        "target_time_str": target_dt.strftime("%H:%M:%S"),
        "label": label.strip() or f"Timer {minutes} menit",
        "enabled": True,
        "sound": sound,
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    alarms.append(entry)
    save_alarms(alarms)
    return entry


def delete_alarm(alarm_id: str) -> bool:
    """Remove alarm or timer by ID."""
    alarms = load_alarms()
    new_alarms = [a for a in alarms if a.get("id") != alarm_id]
    if len(new_alarms) != len(alarms):
        save_alarms(new_alarms)
        return True
    return False


def toggle_alarm(alarm_id: str, enabled: bool) -> bool:
    """Enable or disable alarm."""
    alarms = load_alarms()
    found = False
    for a in alarms:
        if a.get("id") == alarm_id:
            a["enabled"] = enabled
            found = True
            break
    if found:
        save_alarms(alarms)
    return found


def snooze_alarm(alarm_id: str, minutes: int = 5) -> dict:
    """Snooze an existing alarm by creating a temporary timer."""
    alarms = load_alarms()
    orig_label = "Snooze Alarm"
    for a in alarms:
        if a.get("id") == alarm_id:
            orig_label = a.get("label", orig_label)
            break

    return add_timer(
        minutes=float(minutes),
        label=f"[Snooze {minutes}m] {orig_label}",
        sound="herta_morning.wav"
    )


def send_telegram_alert(alarm: dict):
    """Optional bridge to send alarm alert to Telegram on user's phone."""
    cfg = load_config()
    token = cfg.get("telegram_bot_token", "").strip()
    chat_id = cfg.get("telegram_chat_id", "").strip()
    partner = cfg.get("partner_name", "あなた")

    if not token or not chat_id:
        return

    label = alarm.get("label", "Alarm")
    time_info = alarm.get("time") or alarm.get("target_time_str") or "Sekarang"

    text = (
        f"💎 [MADAM HERTA ALARM WAKE-UP]\n\n"
        f"⏰ Waktunya: {label} ({time_info})\n"
        f"ねえ、{partner}！起きて！(Bangun, {partner}!)\n\n"
        f"くるくる～――っと！二度寝したら許さないんだからね！✨"
    )

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": text
    }).encode("utf-8")

    try:
        req = urllib.request.Request(url, data=payload, method="POST")
        with urllib.request.urlopen(req, timeout=8):
            pass
    except Exception as exc:
        sys.stderr.write(f"Telegram notification error: {exc}\n")


def show_alarm_popup(alarm: dict, stop_event: threading.Event):
    """Display an interactive top-most GUI dialog with Dismiss and Snooze buttons."""
    try:
        import tkinter as tk
        from tkinter import ttk

        root = tk.Tk()
        root.title("⏰ Madam Herta Alarm")
        root.geometry("420x280")
        root.resizable(False, False)
        root.attributes("-topmost", True)
        root.configure(bg="#111827")

        label_title = tk.Label(
            root,
            text="💎 MADAM HERTA ALARM 💎",
            font=("Segoe UI", 14, "bold"),
            fg="#c084fc",
            bg="#111827"
        )
        label_title.pack(pady=(16, 6))

        time_val = alarm.get("time") or alarm.get("target_time_str") or "Waktunya!"
        label_time = tk.Label(
            root,
            text=f"⏰ {time_val}",
            font=("Segoe UI", 24, "bold"),
            fg="#f43f5e",
            bg="#111827"
        )
        label_time.pack(pady=(0, 4))

        label_desc = tk.Label(
            root,
            text=alarm.get("label", "Alarm Madam Herta"),
            font=("Segoe UI", 12),
            fg="#f3f4f6",
            bg="#111827"
        )
        label_desc.pack(pady=(0, 8))

        label_msg = tk.Label(
            root,
            text="くるくる～――っと！ねえ、起きて！\n(Kururin~ Bangun! Jangan tidur lagi!)",
            font=("Segoe UI", 10, "italic"),
            fg="#a855f7",
            bg="#111827"
        )
        label_msg.pack(pady=(0, 16))

        btn_frame = tk.Frame(root, bg="#111827")
        btn_frame.pack(pady=(0, 16))

        def on_dismiss():
            stop_event.set()
            root.destroy()

        def on_snooze():
            stop_event.set()
            snooze_alarm(alarm.get("id", ""), minutes=5)
            root.destroy()

        btn_dismiss = tk.Button(
            btn_frame,
            text="💖 Matikan Alarm",
            font=("Segoe UI", 11, "bold"),
            bg="#9333ea",
            fg="white",
            activebackground="#7e22ce",
            activeforeground="white",
            padx=14,
            pady=6,
            relief="flat",
            command=on_dismiss
        )
        btn_dismiss.pack(side=tk.LEFT, padx=8)

        btn_snooze = tk.Button(
            btn_frame,
            text="⏰ Snooze 5 Menit",
            font=("Segoe UI", 11),
            bg="#374151",
            fg="#e5e7eb",
            activebackground="#4b5563",
            activeforeground="white",
            padx=12,
            pady=6,
            relief="flat",
            command=on_snooze
        )
        btn_snooze.pack(side=tk.LEFT, padx=8)

        # Auto-close after 5 minutes if unhandled
        root.after(300000, on_dismiss)
        root.mainloop()
    except Exception as exc:
        sys.stderr.write(f"Alarm popup error: {exc}\n")


def play_alarm_audio_loop(sound_file: str, stop_event: threading.Event):
    """Play intro sample then loop alarm voiceline until dismissed or stop_event is set."""
    sound_path = os.path.join(AUDIO_DIR, sound_file) if sound_file else None
    if not sound_path or not os.path.exists(sound_path):
        sound_path = os.path.join(AUDIO_DIR, "herta_morning.wav")

    intro_path = os.path.join(AUDIO_DIR, "kuru_kururin.wav")

    # 1. Play quick authentic in-game kuru intro sound
    if os.path.exists(intro_path) and not stop_event.is_set():
        play_audio(intro_path, timeout=5)

    # 2. Loop wake-up voiceline up to 5 times (or until user dismisses)
    loops = 0
    while not stop_event.is_set() and loops < 5:
        if os.path.exists(sound_path):
            play_audio(sound_path, timeout=15)
        loops += 1
        # Small pause between loops
        for _ in range(20):
            if stop_event.is_set():
                break
            time.sleep(0.1)


def trigger_alarm(alarm: dict):
    """Execute alarm alert: audio, desktop banner toast, interactive dialog, and Telegram."""
    label = alarm.get("label", "Alarm Madam Herta")
    time_info = alarm.get("time") or alarm.get("target_time_str") or "Sekarang"
    cfg = load_config()
    partner = cfg.get("partner_name", "あなた")

    print(f"\n⏰ [MADAM HERTA ALARM TRIGGERED] {time_info} - {label}")

    # 1. Desktop Notification Banner
    show_notification(
        f"⏰ MADAM HERTA ALARM! ({time_info})",
        f"ねえ、{partner}！起きて！{label} の時間よ！✨"
    )

    # 2. Telegram Alert
    threading.Thread(target=send_telegram_alert, args=(alarm,), daemon=True).start()

    # 3. Audio & Interactive Dialog
    stop_event = threading.Event()
    sound = alarm.get("sound", "herta_morning.wav")

    audio_thread = threading.Thread(
        target=play_alarm_audio_loop,
        args=(sound, stop_event),
        daemon=True
    )
    audio_thread.start()

    # Show popup on main desktop
    show_alarm_popup(alarm, stop_event)


def check_and_trigger_due_alarms():
    """Check all registered alarms and timers, triggering any that are due."""
    alarms = load_alarms()
    if not alarms:
        return

    now = datetime.datetime.now()
    current_time_str = now.strftime("%H:%M")
    current_minute_key = now.strftime("%Y-%m-%d %H:%M")
    current_weekday = now.strftime("%a")  # e.g., 'Mon', 'Tue'
    now_ts = time.time()

    updated = False
    due_list = []

    for item in alarms:
        if not item.get("enabled", True):
            continue

        item_type = item.get("type", "alarm")

        # 1. Check countdown timer
        if item_type == "timer":
            target_ts = float(item.get("target_timestamp", 0))
            if now_ts >= target_ts:
                due_list.append(item)
                item["enabled"] = False  # Timers run once
                updated = True

        # 2. Check daily or one-shot scheduled alarm
        elif item_type == "alarm":
            alarm_time = item.get("time", "")
            if alarm_time == current_time_str:
                days = item.get("days", [])
                if not days or current_weekday in days:
                    if item.get("last_triggered") != current_minute_key:
                        item["last_triggered"] = current_minute_key
                        due_list.append(item)
                        if item.get("once", False):
                            item["enabled"] = False
                        updated = True

    if updated:
        # Clean up expired timers
        active_alarms = [a for a in alarms if not (a.get("type") == "timer" and not a.get("enabled"))]
        save_alarms(active_alarms)

    for due_alarm in due_list:
        threading.Thread(target=trigger_alarm, args=(due_alarm,), daemon=True).start()


def run_alarm_scheduler_loop(interval_sec: int = 5, stop_event: threading.Event = None):
    """Background monitoring loop to check alarms periodically."""
    print("⏰ Madam Herta Alarm Scheduler ACTIVE.")
    while stop_event is None or not stop_event.is_set():
        try:
            check_and_trigger_due_alarms()
        except Exception as exc:
            sys.stderr.write(f"Alarm scheduler error: {exc}\n")

        for _ in range(interval_sec * 2):
            if stop_event is not None and stop_event.is_set():
                break
            time.sleep(0.5)


def parse_alarm_intent(text: str) -> dict | None:
    """
    Parse user natural language or action tags to extract alarm/timer intent.
    Supports:
    - [ACTION:SET_ALARM time="07:00" label="Bangun"]
    - [ACTION:SET_TIMER minutes=15 label="Rehat"]
    - "bangunin aku jam 7 pagi"
    - "pasang alarm jam 06:30"
    - "set timer 20 menit"
    - "alarm 07:00"
    """
    if not text:
        return None

    clean = text.strip()

    # 1. Structured action tags from LLM
    act_alarm = re.search(r'\[ACTION:SET_ALARM\s+time=["\']([^"\']+)["\'](?:\s+label=["\']([^"\']*)["\'])?\]', clean, re.IGNORECASE)
    if act_alarm:
        t_str = act_alarm.group(1)
        lbl = act_alarm.group(2) or "Alarm"
        return {"action": "add_alarm", "time": t_str, "label": lbl}

    act_timer = re.search(r'\[ACTION:SET_TIMER\s+minutes=["\']?(\d+(?:\.\d+)?)["\']?(?:\s+label=["\']([^"\']*)["\'])?\]', clean, re.IGNORECASE)
    if act_timer:
        m_val = float(act_timer.group(1))
        lbl = act_timer.group(2) or f"Timer {m_val} menit"
        return {"action": "add_timer", "minutes": m_val, "label": lbl}

    # 2. Natural language: Timer (e.g., "pasang timer 25 menit", "timer 10 menit", "timer 5m")
    timer_pattern = re.search(r'(?:pasang\s+|set\s+)?timer\s+(\d+(?:\.\d+)?)\s*(?:menit|m|min)?(?:\s+(?:untuk|buat)\s+(.+))?', clean, re.IGNORECASE)
    if timer_pattern:
        minutes = float(timer_pattern.group(1))
        label = timer_pattern.group(2) or f"Timer {minutes} menit"
        return {"action": "add_timer", "minutes": minutes, "label": label.strip()}

    # 3. Natural language: Alarm (e.g., "bangunin aku jam 07:00", "pasang alarm jam 7 pagi", "set alarm 06:30")
    alarm_pattern = re.search(r'(?:bangunin\s+(?:aku\s+)?(?:jam\s+)?|pasang\s+alarm\s+(?:jam\s+)?|set\s+alarm\s+(?:jam\s+)?|alarm\s+)(\d{1,2}(?:[:.]\d{2})?\s*(?:am|pm|pagi|siang|sore|malam)?)(?:\s+(?:untuk|buat)\s+(.+))?', clean, re.IGNORECASE)
    if alarm_pattern:
        raw_time = alarm_pattern.group(1).strip()
        label = alarm_pattern.group(2) or "Alarm"

        # Handle Indonesian time modifiers (pagi, siang, sore, malam)
        lower_time = raw_time.lower()
        if "malam" in lower_time or "sore" in lower_time:
            num_part = re.sub(r"[^\d:.]", "", lower_time).replace(".", ":")
            try:
                parts = num_part.split(":")
                h = int(parts[0])
                m = int(parts[1]) if len(parts) > 1 else 0
                if h < 12:
                    h += 12
                raw_time = f"{h:02d}:{m:02d}"
            except Exception:
                pass
        elif "pagi" in lower_time:
            num_part = re.sub(r"[^\d:.]", "", lower_time).replace(".", ":")
            try:
                parts = num_part.split(":")
                h = int(parts[0])
                m = int(parts[1]) if len(parts) > 1 else 0
                raw_time = f"{h:02d}:{m:02d}"
            except Exception:
                pass

        try:
            parsed = parse_time_string(raw_time)
            return {"action": "add_alarm", "time": parsed, "label": label.strip()}
        except Exception:
            pass

    return None
