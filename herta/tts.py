"""
Text-to-Speech synthesis module.
Generates natural Japanese female anime base audio using Edge-TTS
with Google Gemini audio generation fallback.
"""

import asyncio
import base64
import json
import os
import sys
import urllib.request
import wave

from herta.config import TMP_DIR, load_config


async def _synthesize_edge_async(text: str, output_path: str, voice: str) -> bool:
    import edge_tts
    communicate = edge_tts.Communicate(text, voice, pitch="+10Hz", rate="+5%")
    await communicate.save(output_path)
    return os.path.exists(output_path) and os.path.getsize(output_path) > 500


def synthesize_speech(text: str, output_path: str = None) -> str:
    """
    Synthesize base Japanese voice audio for Madam Herta.
    Returns the filepath of the generated audio file.
    """
    cfg = load_config()
    if output_path is None:
        output_path = os.path.join(TMP_DIR, "base_speech.mp3")

    if os.path.exists(output_path):
        try:
            os.remove(output_path)
        except OSError:
            pass

    # 1. Primary: Edge-TTS Japanese Neural Voice
    voice = cfg.get("tts_voice", "ja-JP-NanamiNeural")
    try:
        success = asyncio.run(_synthesize_edge_async(text, output_path, voice))
        if success:
            return output_path
    except Exception as exc:
        sys.stderr.write(f"Edge-TTS synthesis error: {exc}\n")

    # 2. Fallback: Google Gemini TTS
    api_key = cfg.get("gemini_api_key", "")
    if api_key:
        wav_path = os.path.splitext(output_path)[0] + ".wav"
        model = cfg.get("gemini_tts_model", "gemini-2.5-flash-preview-tts")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": text}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {"voiceName": "Kore"}
                    }
                }
            }
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
                    for part in parts:
                        if "inlineData" in part:
                            pcm_bytes = base64.b64decode(part["inlineData"]["data"])
                            with wave.open(wav_path, "wb") as wav_file:
                                wav_file.setnchannels(1)
                                wav_file.setsampwidth(2)
                                wav_file.setframerate(24000)
                                wav_file.writeframes(pcm_bytes)
                            return wav_path
        except Exception as exc:
            sys.stderr.write(f"Gemini TTS fallback error: {exc}\n")

    return ""
