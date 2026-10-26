"""
Reminder management module for Madam Herta Assistant.
Provides task-aware reminders, contextual prompt injection for LLM dialogues,
and spontaneous partner nudges for critical deadlines.
"""

import datetime
import json
import os
from typing import List, Optional

from herta.config import CONFIG_DIR

REMINDERS_FILE = os.path.join(CONFIG_DIR, "reminders.json")


def load_reminders() -> List[dict]:
    """Load active reminders from the configuration directory."""
    if not os.path.exists(REMINDERS_FILE):
        return []
    try:
        with open(REMINDERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_reminders(reminders: List[dict]):
    """Persist reminders list to the configuration directory."""
    try:
        with open(REMINDERS_FILE, "w", encoding="utf-8") as f:
            json.dump(reminders, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def get_active_reminders() -> List[dict]:
    """Retrieve all active reminders that are due on or before today."""
    today_str = datetime.date.today().isoformat()
    reminders = load_reminders()
    active = []
    for r in reminders:
        due = r.get("due", "")
        if not due or due <= today_str:
            active.append(r)
    return active


def add_reminder(
    title: str,
    due: str = "",
    priority: str = "P1",
    reason: str = "",
    jp: str = "",
    id_sub: str = "",
    en_sub: str = ""
) -> dict:
    """Register a new reminder."""
    reminders = load_reminders()
    reminder_id = f"rem_{int(datetime.datetime.now().timestamp())}"
    item = {
        "id": reminder_id,
        "title": title,
        "due": due or datetime.date.today().isoformat(),
        "priority": priority,
        "reason": reason,
        "jp": jp,
        "id": id_sub,
        "en": en_sub
    }
    reminders.append(item)
    save_reminders(reminders)
    return item


def complete_reminder(reminder_id_or_title: str) -> bool:
    """Mark a reminder as completed and remove it from active list."""
    reminders = load_reminders()
    target_lower = reminder_id_or_title.lower()
    updated = [
        r for r in reminders
        if r.get("id") != reminder_id_or_title and target_lower not in r.get("title", "").lower()
    ]
    if len(updated) != len(reminders):
        save_reminders(updated)
        return True
    return False


def format_reminder_prompt_context(partner_name: str) -> str:
    """Format active reminders into a concise system prompt context for Gemini."""
    active = get_active_reminders()
    if not active:
        return ""

    lines = [
        "\nACTIVE REMINDERS & PRIORITIES FOR YOUR PARTNER / HUSBAND:",
        f"You are watching over '{partner_name}'. Keep these important tasks in mind and remind him:"
    ]
    for idx, r in enumerate(active, 1):
        title = r.get("title", "")
        reason = r.get("reason", "")
        extra = f" (Context: {reason})" if reason else ""
        lines.append(f"{idx}. {title}{extra}")
    lines.append(
        "If he asks about his tasks, or if he is chatting casually, naturally and playfully "
        "bring up these reminders so he doesn't forget.\n"
    )
    return "\n".join(lines)


def get_due_reminder_moment(partner_name: str, subtitle_lang: str = "id") -> Optional[dict]:
    """Retrieve a spontaneous reminder moment dictionary if an urgent reminder exists."""
    active = get_active_reminders()
    if not active:
        return None

    # Pick highest priority reminder
    r = active[0]
    title = r.get("title", "")
    reason = r.get("reason", "")

    jp = r.get("jp") or f"ねえ、{partner_name}！「{title}」のこと、忘れてないでしょうね？ちゃんと今日終わらせなさいよ！"
    id_text = r.get("id") or f"Hei, {partner_name}! Jangan sampai lupa sama '{title}' ya! Selesaikan hari ini gih!"
    en_text = r.get("en") or f"Hey, {partner_name}! You haven't forgotten about '{title}', right? Make sure you finish it today!"

    flag = "🇬🇧" if subtitle_lang == "en" else "🇮🇩"
    sub_text = en_text if subtitle_lang == "en" else id_text

    return {
        "jp": jp,
        "sub": sub_text,
        "flag": flag,
        "title": title
    }
