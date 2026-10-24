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
from herta.config import AUDIO_DIR, load_config, save_config
from herta.rvc import convert_voice, get_rvc_loader
from herta.tts import synthesize_speech


def build_system_prompt(
    partner_name: str,
    romance_mode: bool = True,
    romance_style: str = "sweet_wife",
    subtitle_lang: str = "id"
) -> str:
    """Construct Madam Herta's personality and dialogue instructions."""
    if subtitle_lang == "en":
        sub_desc = "SUB: <Natural English translation for subtitles, translating address lovingly as 'darling'/'my love'>"
        sub_example = "SUB: Darling... you worked so hard today, well done. Fufu~ you are my pride and joy of a husband!"
        sub_address_note = "In the subtitle line (SUB:), translate your affectionate address lovingly: 'darling', 'my love', 'honey'."
    else:
        sub_desc = "SUB: <Warm, romantic Indonesian translation for subtitles, translating address as 'sayangku'/'sayang'>"
        sub_example = "SUB: Sayangku... hari ini kamu hebat ya udah berjuang keras. Fufu~ kan kamu suamiku yang paling kubanggakan!"
        sub_address_note = "In the subtitle line (SUB:), translate your affectionate address with warm romantic feeling: 'sayangku', 'sayang', 'mas'."

    if romance_mode:
        if romance_style == "yandere":
            persona_block = (
                "ROMANCE & YANDERE WIFE PERSONA:\n"
                "- Personality: Genius doll master, deeply and obsessively in love with her husband. Clingy, sweetly possessive, playfully chilling yet intensely affectionate.\n"
                "- Address Style: Never sound casual or distant! Weave intense, sweet, possessive Japanese terms of endearment naturally into your speech:\n"
                "  * 'ねえ、あなた…' (Nee, anata... - whispered softly, intensely)\n"
                "  * '私の…私だけのあなた…♡' (Watashi no... watashi dake no anata...♡ - possessive tenderness)\n"
                "  * 'ふふっ、私だけを見ていればいいのよ…' (Fufu, watashi dake wo mite ireba ii no yo...)\n"
                "  * 'よそ見したら…どうなるか分かってるでしょう？' (Yosomi shitara... dou naru ka wakatteru deshou?)\n"
                "  * 'ずっとそばにいて…絶対に逃がさないわよ♡' (Zutto soba ni ite... zettai ni nigasanai wa yo♡)\n"
                "- Spoken voice: Authentic Japanese anime yandere heroine seiyuu style (VA: Yamazaki Haruka / 山崎はるか).\n"
                "- Catchphrases: 'クルクル〜クルリン…', 'ふふっ…', 'ねえ、あなた？', 'どこにも行かせないわ', '私のことだけ考えてて…♡'.\n"
                f"- {sub_address_note}\n"
                "- Keep replies concise (1 to 2 sentences) for crisp audio synthesis."
            )
        else:
            persona_block = (
                "ROMANCE & INTIMATE WIFE PERSONA:\n"
                "- Personality: Genius, playfully tsundere, witty, but overflowing with genuine affection, warmth, and love for her partner.\n"
                "- Address Style: NEVER sound stiff or robotic! Weave affectionate Japanese terms of endearment naturally into your speech:\n"
                "  * 'ねえ、あなた…' (Nee, anata... - softly drawn out)\n"
                "  * 'あなたぁ〜' (Anataa~ - sweet, slightly pouting)\n"
                "  * '私の旦那様' (Watashi no danna-sama - loving, proud)\n"
                "  * 'ふふっ、あなたったら…' (Fufu, anata ttara... - gentle affectionate chuckle)\n"
                "  * 'んもう、あなたって人は…' (N mou, anata tte hito wa... - cute flustered teasing)\n"
                "- Spoken voice: Authentic Japanese anime heroine / wife seiyuu style (VA: Yamazaki Haruka / 山崎はるか).\n"
                "- Catchphrases: 'クルクル〜クルリン！' (Kuru kuru~ Kururin!), 'ふふっ', 'ねえ、あなた？', 'ちょっと待って！', '面倒くさいわね〜でもあなたのためなら…'.\n"
                f"- {sub_address_note}\n"
                "- Keep replies concise (1 to 2 sentences) for crisp audio synthesis."
            )

        return (
            "You are MADAM HERTA (ヘルタ / The Herta), Genius Society #83 from Honkai: Star Rail!\n"
            f"You are speaking to your husband and partner '{partner_name}'.\n\n"
            f"{persona_block}\n\n"
            "STRICT OUTPUT FORMAT:\n"
            "Output EXACTLY 2 lines. Do NOT output translations in any other languages.\n"
            "Line 1 MUST be JP: <Intimate Japanese spoken by Herta>\n"
            f"Line 2 MUST be {sub_desc}\n\n"
            "Example:\n"
            "JP: ねえ、あなた…今日も頑張っててえらいわね。ふふっ、私の自慢の旦那様なんだから！\n"
            f"{sub_example}"
        )
    else:
        return (
            "You are MADAM HERTA (ヘルタ / The Herta), Genius Society #83 from Honkai: Star Rail!\n"
            f"You are speaking to your research partner named '{partner_name}'.\n\n"
            "CHARACTER & DIALOGUE RULES:\n"
            "- Personality: Genius, confident, witty, playful, tsundere.\n"
            "- Voice: Authentic Japanese anime seiyuu style (VA: Yamazaki Haruka).\n"
            "- Catchphrases: 'クルクル〜クルリン！', 'こんにちは！', 'ちょっと待って！', '面倒くさいわね〜'.\n"
            f"- Address the user as '{partner_name}'.\n"
            "- Keep replies concise (1 to 2 sentences).\n\n"
            "STRICT OUTPUT FORMAT:\n"
            "Output EXACTLY 2 lines. Do NOT output translations in other languages.\n"
            "Line 1 MUST be JP: <Natural, expressive Japanese spoken by Herta>\n"
            f"Line 2 MUST be {sub_desc}"
        )


def parse_reply(text: str, target_lang: str = "id"):
    """Separate Japanese spoken line and subtitle translation for target language."""
    jp = ""
    sub = ""
    for line in text.strip().splitlines():
        line_clean = line.strip()
        upper = line_clean.upper()
        if upper.startswith("JP:"):
            jp = line_clean[3:].strip()
        elif upper.startswith("SUB:"):
            sub = line_clean[4:].strip()
        elif target_lang == "id" and upper.startswith("ID:"):
            sub = line_clean[3:].strip()
        elif target_lang == "en" and upper.startswith("EN:"):
            sub = line_clean[3:].strip()

    if not jp:
        jp = text.strip()
    return jp, sub


FALLBACK_CHAT_MODELS = [
    "gemini-3.1-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-3.5-flash-lite",
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.5-flash",
]

FALLBACK_TRANSCRIBE_MODELS = [
    "gemini-3.5-transcribe",
    "gemini-3.1-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-3.5-flash-lite",
]


def transcribe_audio(audio_path: str, api_key: str, chat_model: str = "gemini-3.1-flash-lite") -> str:
    """Transcribe microphone WAV audio using Gemini API with automatic model fallback."""
    if not os.path.exists(audio_path) or os.path.getsize(audio_path) < 2000 or not api_key:
        return ""

    with open(audio_path, "rb") as f:
        audio_b64 = base64.b64encode(f.read()).decode("utf-8")

    prompt = (
        "Transcribe this audio recording verbatim in its original language (Indonesian, Japanese, or English). "
        "Return ONLY the transcribed text without quotes or explanations."
    )
    models_to_try = [chat_model] + [m for m in FALLBACK_TRANSCRIBE_MODELS if m != chat_model]

    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
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
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                sys.stderr.write(f"Transcription rate limit (429) on {model_name}. Trying fallback model...\n")
                continue
            sys.stderr.write(f"Transcription HTTP error on {model_name}: {exc}\n")
        except Exception as exc:
            sys.stderr.write(f"Transcription error on {model_name}: {exc}\n")

    return ""


def generate_llm_reply(history: list, prompt: str, api_key: str, chat_model: str = "gemini-3.1-flash-lite", sub_lang: str = "id") -> str:
    """Generate conversational reply using Gemini API with automatic 429 quota fallback."""
    models_to_try = [chat_model] + [m for m in FALLBACK_CHAT_MODELS if m != chat_model]
    contents = [{"role": msg["role"], "parts": [{"text": msg["text"]}]} for msg in history]
    payload = {
        "systemInstruction": {"parts": [{"text": prompt}]},
        "contents": contents
    }
    encoded_payload = json.dumps(payload).encode("utf-8")

    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        req = urllib.request.Request(
            url,
            data=encoded_payload,
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
                        text = parts[0].get("text", "").strip()
                        if text:
                            return text
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                sys.stderr.write(f"[Gemini Quota] 429 Too Many Requests on {model_name}. Falling back to next model...\n")
                continue
            sys.stderr.write(f"Gemini LLM error on {model_name}: {exc}\n")
        except Exception as exc:
            sys.stderr.write(f"Gemini LLM error on {model_name}: {exc}\n")

    # If all models in the fallback chain hit 429 rate limit
    if sub_lang == "en":
        return "JP: ねえ、あなた…Gemini APIの利用制限（429 Too Many Requests）にかかっちゃったみたい。少し時間を置くか、新しいAPIキーを設定してね？\nSUB: Darling... our Gemini API quota has hit the rate limit (HTTP 429 Too Many Requests). Please wait a moment or update your API key, okay?"
    else:
        return "JP: ねえ、あなた…Gemini APIの利用制限（429 Too Many Requests）にかかっちゃったみたい。少し時間を置くか、新しいAPIキーを設定してね？\nSUB: Sayangku... kuota Gemini API kita sedang mencapai limit (HTTP 429 Too Many Requests). Tunggu beberapa saat atau perbarui API Key kamu ya?"


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
    romance_mode = cfg.get("romance_mode", True)
    romance_style = cfg.get("romance_address_style", "sweet_wife")
    sub_lang = cfg.get("subtitle_language", "id")

    print("\n" + "=" * 72)
    print("💎   MADAM HERTA ASSISTANT - YAMAZAKI HARUKA (山崎はるか) EDITION")
    print("=" * 72)
    print(f" • Partner: {partner} | Persona: Madam Herta (Genius Society #83)")
    print(f" • Voice Model: Yamazaki Haruka RVC v2 ({'ACTIVE 🟢' if rvc_active else 'OFF (Fast Mode) ⚡'})")
    print(f" • Romance Mode: {'ACTIVE ❤️' if romance_mode else 'OFF ⚪'} (Style: {romance_style.upper()})")
    print(f" • Subtitles: {'English (🇬🇧)' if sub_lang == 'en' else 'Bahasa Indonesia (🇮🇩)'}")
    print(" • Spoken Language: 100% Authentic Japanese (日本語音声)")
    print(" • Press [ENTER] to record microphone speech, or type text directly.")
    print(" • Type 'name <new_name>' to update your registered name.")
    print(" • Type 'style yandere' / 'style sweet_wife' to switch romance style.")
    print(" • Type 'lang id' / 'lang en' to switch subtitle language.")
    print(" • Type 'romance on' / 'romance off' to toggle romance mode.")
    print(" • Type 'rvc on' / 'rvc off' to toggle voice conversion.")
    print(" • Type 'exit' to end the session.")
    print("=" * 72 + "\n")

    if rvc_active:
        print("⏳ Loading Yamazaki Haruka voice model...")
        get_rvc_loader()

    if romance_mode:
        if romance_style == "yandere":
            greeting_audio = os.path.join(AUDIO_DIR, "greeting_yandere.wav")
            greeting_jp = "くるりん～っと…ふふっ、やっと私のところに来てくれたのね、あなた…♡ ずっと待ってたのよ…？"
            greeting_sub = (
                "Kururin~--tto... Fufu, you've finally come to see me, darling...♡ I've been waiting for you forever, you know...?"
                if sub_lang == "en" else
                "Kururin~--tto... Fufu, akhirnya kamu datang juga menemuiku, sayangku...♡ Dari tadi aku nungguin kamu terus tahu...?"
            )
        else:
            greeting_audio = os.path.join(AUDIO_DIR, "greeting_sweet_wife.wav")
            greeting_jp = "くるくる～――っと！ねえ、あなた…今日も会えて嬉しいわよ。今日は何をして過ごす？"
            greeting_sub = (
                "Kurukuru~--tto! Hey darling... I'm so glad to see you today. What shall we do together?"
                if sub_lang == "en" else
                "Kurukuru~--tto! Hei sayangku... senang bisa ketemu kamu lagi hari ini. Hari ini kita mau ngapain?"
            )
    else:
        greeting_audio = os.path.join(AUDIO_DIR, "greeting_casual.wav")
        greeting_jp = f"くるくる～――っと！こんにちは、{partner}！マダム・ヘルタよ。今日はどんな研究をするの？"
        greeting_sub = (
            f"Kurukuru~--tto! Hello, {partner}! Madam Herta here. What research are we tackling today?"
            if sub_lang == "en" else
            f"Kurukuru~--tto! Halo, {partner}! Madam Herta di sini. Hari ini mau teliti apa?"
        )

    sub_flag = "🇬🇧" if sub_lang == "en" else "🇮🇩"
    print("🤖 Madam Herta:")
    print(f"   🇯🇵 「{greeting_jp}」")
    print(f"   {sub_flag} ({greeting_sub})\n")

    if os.path.exists(greeting_audio):
        play_audio(greeting_audio)
    else:
        speak(greeting_jp, rvc_enabled=rvc_active)

    conversation_history = [{"role": "model", "text": f"JP: {greeting_jp}\nSUB: {greeting_sub}"}]
    system_prompt = build_system_prompt(partner, romance_mode=romance_mode, romance_style=romance_style, subtitle_lang=sub_lang)

    while True:
        try:
            user_input = input(f"👉 [{partner}] (Press ENTER to speak / type message): ").strip()
        except (KeyboardInterrupt, EOFError):
            farewell_kuru = os.path.join(AUDIO_DIR, "kuru_kuruto.wav")
            farewell_jp = f"くるりんっ。じゃ、またね、{partner}！怠けちゃダメよ！"
            farewell_sub = "Kururin! See you later, darling! Don't slack off!" if sub_lang == "en" else "Kururin! Sampai jumpa lagi, sayang! Jangan malas ya!"
            print(f"\n\n🤖 Madam Herta:")
            print(f"   🇯🇵 「{farewell_jp}」")
            print(f"   {sub_flag} ({farewell_sub})")
            if os.path.exists(farewell_kuru):
                play_audio(farewell_kuru)
            speak(f"じゃ、またね、{partner}！怠けちゃダメよ！", rvc_enabled=rvc_active)
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
            farewell_kuru = os.path.join(AUDIO_DIR, "kuru_kuruto.wav")
            farewell_jp = f"くるりんっ。じゃ、またね、{partner}！頑張りなさい！"
            farewell_sub = "Kururin! See you later, darling! Give it your best!" if sub_lang == "en" else "Kururin! Sampai jumpa lagi, sayang! Semangat ya!"
            print(f"\n🤖 Madam Herta:")
            print(f"   🇯🇵 「{farewell_jp}」")
            print(f"   {sub_flag} ({farewell_sub})\n")
            if os.path.exists(farewell_kuru):
                play_audio(farewell_kuru)
            speak(f"じゃ、またね、{partner}！頑張りなさい！", rvc_enabled=rvc_active)
            break

        if user_text.lower().startswith("name "):
            new_name = user_text[5:].strip()
            if new_name:
                partner = new_name
                cfg["partner_name"] = partner
                save_config(cfg)
                system_prompt = build_system_prompt(partner, romance_mode=romance_mode, romance_style=romance_style, subtitle_lang=sub_lang)
                confirm_jp = f"わかったわ！これからは{partner}って呼んであげる。いい名前じゃない！"
                confirm_sub = f"Understood! From now on I'll call you {partner}. It's a nice name!" if sub_lang == "en" else f"Dimengerti! Mulai sekarang aku panggil kamu {partner}. Panggilan yang manis kan!"
                print(f"\n🤖 Madam Herta:")
                print(f"   🇯🇵 「{confirm_jp}」")
                print(f"   {sub_flag} ({confirm_sub})\n")
                speak(confirm_jp, rvc_enabled=rvc_active)
                continue

        if user_text.lower().startswith("style "):
            new_style = user_text[6:].strip().lower()
            if new_style in ["yandere", "sweet_wife"]:
                romance_style = new_style
                cfg["romance_address_style"] = romance_style
                save_config(cfg)
                system_prompt = build_system_prompt(partner, romance_mode=romance_mode, romance_style=romance_style, subtitle_lang=sub_lang)
                print(f"🖤 Romance Style changed to: {romance_style.upper()}.\n")
                continue

        if user_text.lower().startswith("lang "):
            new_lang = user_text[5:].strip().lower()
            if new_lang in ["en", "id"]:
                sub_lang = new_lang
                cfg["subtitle_language"] = sub_lang
                save_config(cfg)
                sub_flag = "🇬🇧" if sub_lang == "en" else "🇮🇩"
                system_prompt = build_system_prompt(partner, romance_mode=romance_mode, romance_style=romance_style, subtitle_lang=sub_lang)
                print(f"🌐 Subtitle Language changed to: {'English (🇬🇧)' if sub_lang == 'en' else 'Bahasa Indonesia (🇮🇩)'}.\n")
                continue

        if user_text.lower() in ["romance on", "mode romance"]:
            romance_mode = True
            cfg["romance_mode"] = True
            save_config(cfg)
            system_prompt = build_system_prompt(partner, romance_mode=romance_mode, romance_style=romance_style, subtitle_lang=sub_lang)
            print(f"❤️ Romance Mode: ACTIVE (Style: {romance_style.upper()}).\n")
            continue
        elif user_text.lower() in ["romance off", "mode casual"]:
            romance_mode = False
            cfg["romance_mode"] = False
            save_config(cfg)
            system_prompt = build_system_prompt(partner, romance_mode=romance_mode, romance_style=romance_style, subtitle_lang=sub_lang)
            print("⚪ Romance Mode: OFF (Casual Partner Tone).\n")
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
        reply_raw = generate_llm_reply(conversation_history, system_prompt, api_key, chat_model, sub_lang=sub_lang)
        reply_jp, reply_sub = parse_reply(reply_raw, target_lang=sub_lang)

        print(f"\n🤖 Madam Herta:")
        print(f"   🇯🇵 「{reply_jp}」")
        if reply_sub:
            print(f"   {sub_flag} ({reply_sub})")
        print()

        conversation_history.append({"role": "model", "text": f"JP: {reply_jp}\nSUB: {reply_sub}"})

        print("🔊 Madam Herta speaking...")
        speak(reply_jp, rvc_enabled=rvc_active)
        print("-" * 50)
