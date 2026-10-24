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

from herta.audio import play_audio
from herta.config import AUDIO_DIR, TMP_DIR, load_config
from herta.notifier import show_notification
from herta.rvc import convert_voice
from herta.tts import synthesize_speech

# Curated library of authentic Madam Herta wife / companion voicelines
BUILTIN_MOMENTS = [
    # 1. Bored / Demanding attention
    {
        "category": "bored",
        "jp": "ねえ、あなた〜。私ちょっと退屈なんだけど。私の相手をしなさいよ！",
        "id": "Hei, sayang~ Aku agak bosan nih. Ajak aku ngobrol dong!"
    },
    {
        "category": "bored",
        "jp": "クルクル〜回るのも飽きちゃったわ。ねえ、何か面白いこと話してよ。",
        "id": "Kuru kuru~ Muter-muter pun aku mulai bosan. Hei, ceritain sesuatu yang seru dong."
    },
    {
        "category": "bored",
        "jp": "研究ばっかりしてないで、たまには私のことも構いなさいよ。…ちょっとだけだからね！",
        "id": "Jangan cuma fokus riset terus, sesekali perhatikan aku juga dong. ...cuma sebentar lho ya!"
    },
    # 2. Caring / Health & Break reminders (Tsundere care)
    {
        "category": "caring",
        "jp": "ねえ、あなた。ずっと画面見てるけど疲れてない？たまにはお茶でも飲んで休憩しなさいよね。",
        "id": "Hei, sayang. Dari tadi kamu natap layar terus, nggak capek? Sesekali minum teh dan istirahat gih."
    },
    {
        "category": "caring",
        "jp": "ちょっと、あなた！根を詰めすぎよ。倒れられたら困るんだから…ちゃんと休んでよね！",
        "id": "Tunggu dulu, sayang! Jangan terlalu memaksakan diri. Kalau kamu sakit kan aku yang repot... istirahat yang bener ya!"
    },
    {
        "category": "caring",
        "jp": "もう、ちゃんと水分補給してる？お水飲んで、ちょっと肩の力を抜きなさい。",
        "id": "Astaga, kamu udah minum air belum? Minum dulu sana, rilekskan pundakmu sebentar."
    },
    # 3. Sweet / Affectionate Wife
    {
        "category": "sweet",
        "jp": "ふふっ、今日も一生懸命頑張ってるのね。…さすが私の旦那様、かっこいいわよ。",
        "id": "Fufu~ Hari ini kamu kerja keras ya. ...Memang pantas jadi suamiku, keren kok."
    },
    {
        "category": "sweet",
        "jp": "クルクル〜ちょっと頭がクラクラしちゃった…ねえ、頭なでて？…今だけよ？",
        "id": "Kuru kuru~ Kepalaku agak pusing nih... hei, elus kepalaku dong? ...cuma sekarang lho ya?"
    },
    {
        "category": "sweet",
        "jp": "ねえ、あなた。いつも私の人形の面倒見てくれてありがとね。…べ、別に照れてなんかないわよ！",
        "id": "Hei, sayang. Makasih ya selalu jagain boneka-bonekaku. ...B-bukannya aku malu atau gimana lho ya!"
    },
    # 4. Curious about your work
    {
        "category": "curious",
        "jp": "ねえ、あなた。今何を作ってるの？ちょっと私にも見せてみなさいよ。",
        "id": "Hei, sayang. Sekarang lagi ngerjain apa sih? Coba perlihatkan sedikit ke aku."
    }
]


def generate_dynamic_moment(partner_name: str, api_key: str, chat_model: str) -> dict:
    """Generate dynamic companion dialogue using Gemini LLM if API key is present."""
    if not api_key:
        return None

    import urllib.request
    mood = random.choice([
        "bored and playfully pouting for your attention",
        "worried about your health and reminding you to take a break or drink water (tsundere care)",
        "acting like an affectionate, teasing anime wife",
        "curious about what you're coding or doing right now"
    ])

    prompt = (
        "You are MADAM HERTA (ヘルタ / The Herta) from Honkai: Star Rail acting like an affectionate, "
        f"playful, tsundere anime wife talking spontaneously to her husband '{partner_name}'.\n"
        f"Context for this spontaneous interaction: You are {mood}.\n"
        "Rules:\n"
        f"- Address him as '{partner_name}' (or 'あなた' / '旦那様').\n"
        "- Reply MUST be 1 or 2 concise, lively sentences.\n"
        "- Strictly follow this 2-line format:\n"
        "JP: <Natural, expressive Japanese spoken by Herta>\n"
        "ID: <Casual, natural Indonesian translation for subtitles, translating address as 'sayang'>"
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{chat_model}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
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
                    id_line = ""
                    for line in text.splitlines():
                        line_clean = line.strip()
                        if line_clean.upper().startswith("JP:"):
                            jp_line = line_clean[3:].strip()
                        elif line_clean.upper().startswith("ID:"):
                            id_line = line_clean[3:].strip()
                    if jp_line and id_line:
                        return {"jp": jp_line, "id": id_line}
    except Exception as exc:
        sys.stderr.write(f"Dynamic moment generation error: {exc}\n")

    return None


def trigger_spontaneous_interaction():
    """Trigger a single spontaneous companion interaction right now."""
    cfg = load_config()
    partner = cfg.get("partner_name", "あなた")
    api_key = cfg.get("gemini_api_key", "")
    chat_model = cfg.get("gemini_chat_model", "gemini-3.5-flash")
    rvc_enabled = cfg.get("rvc_enabled", True)

    moment = None
    # 50% chance to try dynamic generation if API key exists, otherwise pick from curated library
    if api_key and random.random() < 0.5:
        moment = generate_dynamic_moment(partner, api_key, chat_model)

    if not moment:
        chosen = random.choice(BUILTIN_MOMENTS)
        moment = {
            "jp": chosen["jp"].replace("あなた", partner),
            "id": chosen["id"].replace("sayang", "sayang" if partner == "あなた" else partner)
        }

    jp_text = moment["jp"]
    id_text = moment["id"]

    # 1. Desktop banner notification
    show_notification(f"💎 Madam Herta: {jp_text}", f"🇮🇩 {id_text}")

    # 2. Synthesize audio
    raw_audio = synthesize_speech(jp_text)
    if not raw_audio:
        return

    final_audio = raw_audio
    if rvc_enabled:
        final_audio = convert_voice(raw_audio)

    # 3. Play audio
    play_audio(final_audio, timeout=15)


def run_companion_loop(min_interval_minutes: int = 20, max_interval_minutes: int = 45):
    """
    Run continuous background companion loop.
    Periodically checks in on the user with randomized natural intervals.
    """
    print(f"💎 Madam Herta Companion Mode ACTIVE.")
    print(f"Spontaneous check-in default range: {min_interval_minutes} to {max_interval_minutes} minutes.")

    while True:
        cfg = load_config()
        min_m = int(cfg.get("companion_min_minutes", min_interval_minutes))
        max_m = int(cfg.get("companion_max_minutes", max_interval_minutes))
        if min_m > max_m:
            min_m, max_m = max_m, min_m
        wait_seconds = random.randint(max(1, min_m) * 60, max(1, max_m) * 60)
        time.sleep(wait_seconds)
        try:
            trigger_spontaneous_interaction()
        except Exception as exc:
            sys.stderr.write(f"Companion loop error: {exc}\n")
