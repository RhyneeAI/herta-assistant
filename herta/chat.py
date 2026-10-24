"""
Interactive voice chat session with Madam Herta.
Features pure Japanese speech (Yamazaki Haruka / Herta JP)
with Indonesian translation subtitles in terminal.
"""

import base64
import json
import os
import sys
import urllib.request

from herta.audio import play_audio, record_microphone
from herta.config import load_config, save_config
from herta.rvc import convert_voice, get_rvc_loader
from herta.tts import synthesize_speech


def build_system_prompt(partner_name: str) -> str:
    """Construct Madam Herta's personality and dialogue instructions."""
    return (
        "You are MADAM HERTA (ヘルタ / The Herta), Genius Society #83 from Honkai: Star Rail!\n"
        f"You are speaking to your beloved research partner whom you address affectionately as '{partner_name}' "
        "(or '旦那様' / 'あなた' like a cute, tsundere anime wife addressing her husband/sweetheart).\n\n"
        "CHARACTER & DIALOGUE RULES:\n"
        "- Personality: Genius, confident, witty, playful, tsundere, deeply caring and affectionate.\n"
        "- Spoken voice: Authentic Japanese anime seiyuu style (VA: Yamazaki Haruka / 山崎はるか).\n"
        "- Catchphrases: 'クルクル〜クルリン！' (Kuru kuru~ Kururin!), 'こんにちは！', 'ちょっと待って！', '面倒くさいわね〜', 'さすがね！', 'じゃ、頑張ってね！'.\n"
        f"- Always address the user affectionately as '{partner_name}' (or '旦那様' / 'あなた').\n"
        "- In the Indonesian subtitle line (ID:), translate this affectionate address as 'sayang' (or 'Mas' / 'Sayang').\n"
        "- Keep replies concise (1 to 2 sentences) for crisp audio synthesis.\n\n"
        "STRICT OUTPUT FORMAT:\n"
        "Your reply MUST ALWAYS follow this exact 2-line format:\n"
        "JP: <Natural, expressive Japanese spoken by Herta>\n"
        "ID: <Casual, natural Indonesian translation for subtitles>\n\n"
        "Example:\n"
        "JP: クルクル〜クルリン！こんにちは、あなた！マダム・ヘルタよ。今日も研究頑張ってね！\n"
        "ID: Kuru kuru~ Kururin! Halo, sayang! Madam Herta di sini. Hari ini semangat risetnya ya!"
    )


def parse_reply(text: str):
    """Separate Japanese spoken line and Indonesian subtitle translation."""
    jp = ""
    id_sub = ""
    for line in text.strip().splitlines():
        line_clean = line.strip()
        if line_clean.upper().startswith("JP:"):
            jp = line_clean[3:].strip()
        elif line_clean.upper().startswith("ID:"):
            id_sub = line_clean[3:].strip()

    if not jp:
        jp = text.strip()
    return jp, id_sub


def transcribe_audio(audio_path: str, api_key: str, chat_model: str) -> str:
    """Transcribe microphone WAV audio using Gemini API."""
    if not os.path.exists(audio_path) or os.path.getsize(audio_path) < 2000 or not api_key:
        return ""

    with open(audio_path, "rb") as f:
        audio_b64 = base64.b64encode(f.read()).decode("utf-8")

    prompt = (
        "Transcribe this audio recording verbatim in its original language (Indonesian, Japanese, or English). "
        "Return ONLY the transcribed text without quotes or explanations."
    )
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{chat_model}:generateContent?key={api_key}"
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inlineData": {"mimeType": "audio/wav", "data": audio_b64}}
            ]
        }]
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
    except Exception as exc:
        sys.stderr.write(f"Transcription error: {exc}\n")
    return ""


def generate_llm_reply(history: list, prompt: str, api_key: str, chat_model: str) -> str:
    """Generate conversational reply using Gemini API."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{chat_model}:generateContent?key={api_key}"
    contents = [{"role": msg["role"], "parts": [{"text": msg["text"]}]} for msg in history]
    payload = {
        "systemInstruction": {"parts": [{"text": prompt}]},
        "contents": contents
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
    except Exception as exc:
        sys.stderr.write(f"Gemini LLM error: {exc}\n")

    return "JP: あれ？ちょっと通信が途切れちゃったわ。もう一回言って、あなた？\nID: Ara? Koneksiku sempat terputus sebentar. Boleh diulang lagi, sayang?"


def speak(jp_text: str, rvc_enabled: bool = True):
    """Synthesize speech and convert via RVC if enabled, then play."""
    raw_audio = synthesize_speech(jp_text)
    if not raw_audio:
        return

    final_audio = raw_audio
    if rvc_enabled:
        print("🎭 Converting voice to Madam Herta (Yamazaki Haruka)...")
        final_audio = convert_voice(raw_audio)

    play_audio(final_audio)


def start_chat(fast_mode: bool = False):
    """Run interactive voice conversation session."""
    cfg = load_config()
    api_key = cfg.get("gemini_api_key", "")
    partner = cfg.get("partner_name", "あなた")
    chat_model = cfg.get("gemini_chat_model", "gemini-3.5-flash")
    rvc_active = not fast_mode and cfg.get("rvc_enabled", True)

    print("\n" + "=" * 72)
    print("💎   MADAM HERTA ASSISTANT - YAMAZAKI HARUKA (山崎はるか) EDITION")
    print("=" * 72)
    print(f" • Partner: {partner} (Sayang) | Persona: Madam Herta (Genius Society #83)")
    print(f" • Voice Model: Yamazaki Haruka RVC v2 ({'ACTIVE 🟢' if rvc_active else 'OFF (Fast Mode) ⚡'})")
    print(" • Spoken Language: 100% Authentic Japanese (日本語音声)")
    print(" • Subtitles: Terjemahan Bahasa Indonesia di Terminal")
    print(" • Press [ENTER] to record microphone speech, or type text directly.")
    print(" • Type 'name <new_name>' to update your registered name.")
    print(" • Type 'rvc on' / 'rvc off' to toggle voice conversion.")
    print(" • Type 'exit' to end the session.")
    print("=" * 72 + "\n")

    if rvc_active:
        print("⏳ Loading Yamazaki Haruka voice model...")
        get_rvc_loader()

    greeting_jp = f"クルクル〜クルリン！こんにちは、{partner}！マダム・ヘルタよ。今日はどんな研究をするの？"
    greeting_id = "Kuru kuru~ Kururin! Halo, sayang! Madam Herta di sini. Hari ini mau teliti apa?"

    print("🤖 Madam Herta:")
    print(f"   🇯🇵 「{greeting_jp}」")
    print(f"   🇮🇩 ({greeting_id})\n")

    speak(greeting_jp, rvc_enabled=rvc_active)

    conversation_history = [{"role": "model", "text": f"JP: {greeting_jp}\nID: {greeting_id}"}]
    system_prompt = build_system_prompt(partner)

    while True:
        try:
            user_input = input(f"👉 [{partner}] (Press ENTER to speak / type message): ").strip()
        except (KeyboardInterrupt, EOFError):
            farewell_jp = f"クルクル〜じゃ、またね、{partner}！怠けちゃダメよ！"
            farewell_id = "Kuru kuru~ Sampai jumpa lagi, sayang! Jangan malas ya!"
            print(f"\n\n🤖 Madam Herta:")
            print(f"   🇯🇵 「{farewell_jp}」")
            print(f"   🇮🇩 ({farewell_id})")
            speak(farewell_jp, rvc_enabled=rvc_active)
            break

        if not user_input:
            mic_wav = record_microphone()
            print("⏳ Transcribing speech...")
            user_text = transcribe_audio(mic_wav, api_key, chat_model)
            if not user_text:
                print("⚠️ No speech detected. Please try again.\n")
                continue
            print(f"🗣️ {partner}: \"{user_text}\"")
        else:
            user_text = user_input

        # Session commands
        if user_text.lower() in ["exit", "quit", "keluar", "q"]:
            farewell_jp = f"クルクル〜じゃ、またね、{partner}！頑張りなさい！"
            farewell_id = "Kuru kuru~ Sampai jumpa lagi, sayang! Semangat ya!"
            print(f"\n🤖 Madam Herta:")
            print(f"   🇯🇵 「{farewell_jp}」")
            print(f"   🇮🇩 ({farewell_id})\n")
            speak(farewell_jp, rvc_enabled=rvc_active)
            break

        if user_text.lower().startswith("name "):
            new_name = user_text[5:].strip()
            if new_name:
                partner = new_name
                cfg["partner_name"] = partner
                save_config(cfg)
                system_prompt = build_system_prompt(partner)
                confirm_jp = f"わかったわ！これからは{partner}って呼んであげる。いい名前じゃない！"
                confirm_id = f"Dimengerti! Mulai sekarang aku panggil kamu {partner}. Panggilan yang manis kan!"
                print(f"\n🤖 Madam Herta:")
                print(f"   🇯🇵 「{confirm_jp}」")
                print(f"   🇮🇩 ({confirm_id})\n")
                speak(confirm_jp, rvc_enabled=rvc_active)
                continue

        if user_text.lower() in ["rvc on", "voice rvc"]:
            rvc_active = True
            get_rvc_loader()
            print("✨ Voice Mode: Yamazaki Haruka RVC v2 ACTIVE.\n")
            continue
        elif user_text.lower() in ["rvc off", "voice fast"]:
            rvc_active = False
            print("⚡ Voice Mode: Fast TTS ACTIVE (No RVC).\n")
            continue

        conversation_history.append({"role": "user", "text": user_text})

        print("⏳ Madam Herta is thinking...")
        reply_raw = generate_llm_reply(conversation_history, system_prompt, api_key, chat_model)
        reply_jp, reply_id = parse_reply(reply_raw)

        print(f"\n🤖 Madam Herta:")
        print(f"   🇯🇵 「{reply_jp}」")
        if reply_id:
            print(f"   🇮🇩 ({reply_id})")
        print()

        conversation_history.append({"role": "model", "text": f"JP: {reply_jp}\nID: {reply_id}"})

        print("🔊 Madam Herta speaking...")
        speak(reply_jp, rvc_enabled=rvc_active)
        print("-" * 50)
