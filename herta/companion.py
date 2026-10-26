"""
Proactive Companion Module for Madam Herta.
Enables Madam Herta to periodically and spontaneously interact with the user
like a loving, playful, and slightly tsundere anime wife:
- Checking in on your condition, reminding you to drink water and take breaks.
- Acting bored and demanding attention or teasing you.
- Sweet affectionate tsundere wife moments.
"""

import json
import os
import random
import sys
import time
import urllib.error
import urllib.request

from herta.audio import play_audio
from herta.config import AUDIO_DIR, CACHE_DIR, IS_WINDOWS, TMP_DIR, load_config
from herta.notifier import show_notification
from herta.reminders import get_due_reminder_moment
from herta.rvc import convert_voice
from herta.tts import synthesize_speech

# Curated library of authentic Madam Herta wife / companion voicelines
BUILTIN_MOMENTS = [
    # 1. Bored / Demanding attention
    {
        "category": "bored",
        "audio_file": "nudge_bored_1.wav",
        "jp": "ねえ、あなた〜。私ちょっと退屈なんだけど。私の相手をしなさいよ！",
        "id": "Hei, sayang~ Aku agak bosan nih. Ajak aku ngobrol dong!",
        "en": "Hey, darling~ I'm a bit bored. Come keep me company!"
    },
    {
        "category": "bored",
        "audio_file": "nudge_bored_2.wav",
        "jp": "くるくる～――っと！回るのも飽きちゃったわ。ねえ、何か面白いこと話してよ。",
        "id": "Kurukuru~--tto! Muter-muter pun aku mulai bosan. Hei, ceritain sesuatu yang seru dong.",
        "en": "Kurukuru~--tto! Even spinning around is getting dull. Hey, tell me something interesting."
    },
    {
        "category": "bored",
        "audio_file": "nudge_bored_3.wav",
        "jp": "研究ばっかりしてないで、たまには私のことも構いなさいよ。…ちょっとだけだからね！",
        "id": "Jangan cuma fokus riset terus, sesekali perhatikan aku juga dong. ...cuma sebentar lho ya!",
        "en": "Don't just bury yourself in research, give me some attention too. ...Just for a little while, got it?!"
    },
    # 2. Caring / Health & Break reminders (Tsundere care)
    {
        "category": "caring",
        "audio_file": "nudge_caring_1.wav",
        "jp": "ねえ、あなた。ずっと画面見てるけど疲れてない？たまにはお茶でも飲んで休憩しなさいよね。",
        "id": "Hei, sayang. Dari tadi kamu natap layar terus, nggak capek? Sesekali minum teh dan istirahat gih.",
        "en": "Hey, darling. Staring at that screen all this time, aren't you tired? Go drink some tea and rest."
    },
    {
        "category": "caring",
        "audio_file": "nudge_caring_2.wav",
        "jp": "ちょっと、あなた！根を詰めすぎよ。倒れられたら困るんだから…ちゃんと休んでよね！",
        "id": "Tunggu dulu, sayang! Jangan terlalu memaksakan diri. Kalau kamu sakit kan aku yang repot... istirahat yang bener ya!",
        "en": "Wait a second, darling! You're pushing yourself too hard. Don't you dare collapse... take a proper rest!"
    },
    {
        "category": "caring",
        "audio_file": "nudge_caring_3.wav",
        "jp": "もう、ちゃんと水分補給してる？お水飲んで、ちょっと肩の力を抜きなさい。",
        "id": "Astaga, kamu udah minum air belum? Minum dulu sana, rilekskan pundakmu sebentar.",
        "en": "Geez, have you been staying hydrated? Drink some water and relax your shoulders."
    },
    # 3. Sweet / Affectionate Wife
    {
        "category": "sweet",
        "audio_file": "nudge_sweet_1.wav",
        "jp": "ふふっ、今日も一生懸命頑張ってるのね。…さすが私の旦那様、かっこいいわよ。",
        "id": "Fufu~ Hari ini kamu kerja keras ya. ...Memang pantas jadi suamiku, keren kok.",
        "en": "Fufu~ You worked so hard again today. ...As expected of my husband, quite handsome."
    },
    {
        "category": "sweet",
        "audio_file": "nudge_sweet_2.wav",
        "jp": "くるりんっ。ちょっと頭がクラクラしちゃった…ねえ、頭なでて？…今だけよ？",
        "id": "Kururin! Kepalaku agak pusing nih... hei, elus kepalaku dong? ...cuma sekarang lho ya?",
        "en": "Kururin! I'm feeling a bit dizzy... hey, pat my head? ...Only for right now, okay?"
    },
    {
        "category": "sweet",
        "audio_file": "nudge_sweet_3.wav",
        "jp": "ねえ、あなた。いつも私の人形の面倒見てくれてありがとね。…べ、別に照れてなんかないわよ！",
        "id": "Hei, sayang. Makasih ya selalu jagain boneka-bonekaku. ...B-bukannya aku malu atau gimana lho ya!",
        "en": "Hey, darling. Thanks for always looking after my puppets. ...I-It's not like I'm blushing or anything!"
    },
    # 4. Curious about your work
    {
        "category": "curious",
        "audio_file": "nudge_curious_1.wav",
        "jp": "ねえ、あなた。今何を作ってるの？ちょっと私にも見せてみなさいよ。",
        "id": "Hei, sayang. Sekarang lagi ngerjain apa sih? Coba perlihatkan sedikit ke aku.",
        "en": "Hey, darling. What are you building right now? Show me a peek."
    },
    # 5. Yandere / Possessive Love
    {
        "category": "yandere",
        "audio_file": "nudge_yandere_1.wav",
        "jp": "ねえ、あなた…今、誰のこと考えてたの？…ふふっ、私だけを見ていればいいのよ…？",
        "id": "Hei, sayang... barusan lagi mikirin siapa? ...Fufu, kamu cuma boleh natap aku tahu...?",
        "en": "Hey, darling... who were you thinking about just now? ...Fufu, your eyes should only be on me... right?"
    },
    {
        "category": "yandere",
        "audio_file": "nudge_yandere_2.wav",
        "jp": "ふふっ、どこにも行かないでね？私のそばを離れたら…どうなるか分からないわよ…♡",
        "id": "Fufu, jangan pernah pergi ke mana-mana ya? Kalau sampai ninggalin aku... nggak tahu deh apa yang bakal terjadi...♡",
        "en": "Fufu, don't you dare go anywhere, okay? If you ever leave my side... who knows what might happen...♡"
    },
    {
        "category": "yandere",
        "audio_file": "nudge_yandere_3.wav",
        "jp": "ずっと画面ばかり見て…私に構ってくれないなら、そのパソコン壊しちゃおうかしら…？",
        "id": "Natap layar terus... kalau kamu nggak mau peduliin aku, mending laptop ini kuhancurin aja kali ya...?",
        "en": "Staring at the screen constantly... if you won't pay attention to me, maybe I should just smash this PC...?"
    },
    {
        "category": "yandere",
        "audio_file": "nudge_yandere_4.wav",
        "jp": "ねえ、あなた。私の人形たちの中に閉じ込めて、永遠に一緒にいられたら素敵だと思わない…？",
        "id": "Hei, sayang. Kalau kamu kukunci di dalam salah satu bonekaku biar kita bersama selamanya, bukankah terdengar manis...?",
        "en": "Hey, darling. Wouldn't it be wonderful if I sealed you inside one of my puppets so we could be together forever...?"
    }
]


FALLBACK_CHAT_MODELS = [
    "gemini-3.1-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-3.5-flash-lite",
    "gemini-3.8-flash",
    "gemini-3.7-flash",
]


def generate_dynamic_moment(partner_name: str, api_key: str, chat_model: str = "gemini-3.1-flash-lite", romance_style: str = "sweet_wife", subtitle_lang: str = "id") -> dict | None:
    """Generate dynamic companion dialogue using Gemini LLM if API key is present."""

    if not api_key:
        return None

    if romance_style == "yandere":
        mood = random.choice([
            "sweetly possessive and whispering that your eyes and heart belong only to her",
            "playfully menacing, questioning who else you might be thinking about instead of her",
            "whispering that she wants to keep you locked inside her puppet collection forever so you never leave",
            "pouting with intense obsessive attachment because you haven't looked at her recently"
        ])
        persona_note = "Yandere anime wife: intensely clingy, obsessively in love, possessive, sweet yet subtly chilling."
    else:
        mood = random.choice([
            "bored and playfully pouting for your attention",
            "worried about your health and reminding you to take a break or drink water (tsundere care)",
            "acting like an affectionate, teasing anime wife",
            "curious about what you're coding or doing right now"
        ])
        persona_note = "Affectionate tsundere anime wife: playful, clever, witty, overflowing with sweet love."

    if subtitle_lang == "en":
        sub_rule = "SUB: <Natural English translation for subtitles, translating affectionate address as 'darling'>"
    else:
        sub_rule = "SUB: <Casual, natural Indonesian translation for subtitles, translating address as 'sayang'>"

    prompt = (
        "You are MADAM HERTA (ヘルタ / The Herta) from Honkai: Star Rail acting like an anime wife "
        f"talking spontaneously to her husband '{partner_name}'.\n"
        f"Persona Style: {persona_note}\n"
        f"Context for this spontaneous moment: You are {mood}.\n"
        "Rules:\n"
        f"- Address him as '{partner_name}' (or 'あなた' / '旦那様').\n"
        "- Reply MUST be 1 or 2 concise, lively sentences.\n"
        "- Strictly follow this 2-line format:\n"
        "JP: <Natural, expressive Japanese spoken by Herta>\n"
        f"{sub_rule}"
    )

    models_to_try = [chat_model] + [m for m in FALLBACK_CHAT_MODELS if m != chat_model]
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    encoded = json.dumps(payload).encode("utf-8")

    for m in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={api_key}"
        req = urllib.request.Request(
            url,
            data=encoded,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        text = parts[0].get("text", "")
                        jp_line = ""
                        sub_line = ""
                        for line in text.splitlines():
                            line_clean = line.strip()
                            upper = line_clean.upper()
                            if upper.startswith("JP:"):
                                jp_line = line_clean[3:].strip()
                            elif upper.startswith("SUB:"):
                                sub_line = line_clean[4:].strip()
                            elif subtitle_lang == "id" and upper.startswith("ID:"):
                                sub_line = line_clean[3:].strip()
                            elif subtitle_lang == "en" and upper.startswith("EN:"):
                                sub_line = line_clean[3:].strip()
                        if jp_line and sub_line:
                            return {"jp": jp_line, "sub": sub_line}
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                continue
            sys.stderr.write(f"Dynamic moment HTTP error on {m}: {exc}\n")
        except Exception as exc:
            sys.stderr.write(f"Dynamic moment error on {m}: {exc}\n")

    return None


def trigger_spontaneous_interaction(force_dynamic: bool = False, force_reminder: bool = False):
    """Trigger a single spontaneous companion interaction.
    
    By default, uses 100% pre-rendered offline audio files to eliminate
    Gemini API requests and protect against rate limit exhaustion (HTTP 429).
    Also supports priority task reminders.
    """
    cfg = load_config()
    partner = cfg.get("partner_name", "あなた")
    api_key = cfg.get("gemini_api_key", "")
    chat_model = cfg.get("gemini_chat_model", "gemini-3.1-flash-lite")
    rvc_enabled = cfg.get("rvc_enabled", True)
    romance_style = cfg.get("romance_address_style", "sweet_wife")
    sub_lang = cfg.get("subtitle_language", "id")

    if is_system_sleeping() and not force_dynamic:
        sys.stderr.write("System is currently sleeping. Suppressing spontaneous interaction.\n")
        return

    reminder_moment = get_due_reminder_moment(partner, subtitle_lang=sub_lang)
    is_reminder = (force_reminder or (reminder_moment and random.random() < 0.4)) and reminder_moment is not None

    moment = None
    if is_reminder:
        jp_text = reminder_moment["jp"]
        sub_text = reminder_moment["sub"]
        flag = reminder_moment["flag"]
        audio_file = None
    elif force_dynamic and api_key:
        moment = generate_dynamic_moment(
            partner_name=partner,
            api_key=api_key,
            chat_model=chat_model,
            romance_style=romance_style,
            subtitle_lang=sub_lang
        )
        if moment:
            jp_text = moment["jp"]
            sub_text = moment["sub"]
            flag = "🇬🇧" if sub_lang == "en" else "🇮🇩"
            audio_file = None

    if not is_reminder and not moment:
        if romance_style == "yandere":
            yandere_moments = [m for m in BUILTIN_MOMENTS if m.get("category") == "yandere"]
            if yandere_moments:
                chosen = random.choice(yandere_moments)
            else:
                chosen = random.choice(BUILTIN_MOMENTS)
        else:
            sweet_moments = [m for m in BUILTIN_MOMENTS if m.get("category") != "yandere"]
            chosen = random.choice(sweet_moments if sweet_moments else BUILTIN_MOMENTS)

        jp_raw = chosen.get("jp") or ""
        jp_text = jp_raw.replace("あなた", partner)
        if sub_lang == "en":
            flag = "🇬🇧"
            sub_raw = chosen.get("en") or chosen.get("id") or ""
            sub_text = sub_raw.replace("darling", "darling" if partner == "あなた" else partner)
        else:
            flag = "🇮🇩"
            sub_raw = chosen.get("id") or chosen.get("en") or ""
            sub_text = sub_raw.replace("sayang", "sayang" if partner == "あなた" else partner)
        audio_file = chosen.get("audio_file")



    # 1. Desktop banner notification with Herta avatar icon
    show_notification(f"Madam Herta: {jp_text}", f"{flag} {sub_text}")

    # 2. Play audio: prefer pre-rendered offline WAV (0 API calls, 0 dynamic CPU lag)
    audio_path = os.path.join(AUDIO_DIR, audio_file) if audio_file else None
    if audio_path and os.path.isfile(audio_path):
        play_audio(audio_path, timeout=15)
        return

    # Fallback to dynamic synthesis only if offline WAV is absent
    raw_audio = synthesize_speech(jp_text)
    if not raw_audio:
        return

    final_audio = raw_audio
    if rvc_enabled:
        final_audio = convert_voice(raw_audio)

    play_audio(final_audio, timeout=15)


def is_system_sleeping() -> bool:
    """Check if the system is currently in sleep or suspend state."""
    state_file = os.path.join(CACHE_DIR, "power_state.json")
    if os.path.exists(state_file):
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return bool(data.get("is_sleeping", False))
        except Exception:
            pass
    return False


def is_user_active(max_idle_seconds: int = 300) -> bool:
    """
    Check if the user is actively present at their computer.
    Returns False if screen is locked or user has been idle for more than max_idle_seconds.
    Prevents spontaneous companion nudges and audio while user is away, asleep, or screen is off.
    """
    if IS_WINDOWS:
        try:
            import ctypes
            class LASTINPUTINFO(ctypes.Structure):
                _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]
            lii = LASTINPUTINFO()
            lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
            if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):
                millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
                if millis / 1000.0 > max_idle_seconds:
                    return False
        except Exception:
            pass
        return True

    # Linux check via GNOME DBus
    try:
        import subprocess
        # 1. ScreenSaver lock check
        cmd_lock = [
            "gdbus", "call", "--session",
            "--dest", "org.gnome.ScreenSaver",
            "--object-path", "/org/gnome/ScreenSaver",
            "--method", "org.gnome.ScreenSaver.GetActive"
        ]
        res_lock = subprocess.run(cmd_lock, capture_output=True, text=True, timeout=2)
        if "(true,)" in res_lock.stdout.lower():
            return False

        # 2. Idle time check via Mutter IdleMonitor (milliseconds)
        cmd_idle = [
            "gdbus", "call", "--session",
            "--dest", "org.gnome.Mutter.IdleMonitor",
            "--object-path", "/org/gnome/Mutter/IdleMonitor/Core",
            "--method", "org.gnome.Mutter.IdleMonitor.GetIdletime"
        ]
        res_idle = subprocess.run(cmd_idle, capture_output=True, text=True, timeout=2)
        if res_idle.returncode == 0 and "uint64" in res_idle.stdout:
            parts = res_idle.stdout.strip().split()
            for p in parts:
                cleaned = p.rstrip(",)")
                if cleaned.isdigit():
                    idle_ms = int(cleaned)
                    if idle_ms > (max_idle_seconds * 1000):
                        return False
                    break
    except Exception:
        pass

    return True


def run_companion_loop(min_interval_minutes: int = 20, max_interval_minutes: int = 45):
    """
    Run continuous background companion loop.
    Periodically checks in on the user with randomized natural intervals,
    strictly respecting sleep mode, screen lock, and user presence.
    """
    print(f"💎 Madam Herta Companion Mode ACTIVE.")
    print(f"Spontaneous check-in default range: {min_interval_minutes} to {max_interval_minutes} minutes.")

    while True:
        cfg = load_config()
        if not cfg.get("companion_enabled", True):
            time.sleep(60)
            continue

        min_m = int(cfg.get("companion_min_minutes", min_interval_minutes))
        max_m = int(cfg.get("companion_max_minutes", max_interval_minutes))
        if min_m > max_m:
            min_m, max_m = max_m, min_m
        wait_seconds = random.randint(max(1, min_m) * 60, max(1, max_m) * 60)

        # Sleep in small slices to be responsive to system sleep / wake transitions
        elapsed_wait = 0
        while elapsed_wait < wait_seconds:
            time.sleep(5)
            if is_system_sleeping():
                # Pause progress while system is asleep
                continue
            elapsed_wait += 5

        # Pre-checks before executing interaction:
        if is_system_sleeping():
            continue

        if not is_user_active(max_idle_seconds=300):
            sys.stderr.write("User is inactive / screen locked. Postponing companion nudge.\n")
            time.sleep(120)
            continue

        try:
            trigger_spontaneous_interaction()
        except Exception as exc:
            sys.stderr.write(f"Companion loop error: {exc}\n")
