"""
Pre-render static greeting and poke voicelines using authentic Yamazaki Haruka RVC v2
to eliminate speech synthesis latency in GUI and CLI sessions.
"""

import os
import shutil
import sys

from herta.config import AUDIO_DIR, TMP_DIR
from herta.rvc import convert_voice
from herta.tts import synthesize_speech

VOICELINES = {
    "greeting_sweet_wife": "クルクル〜クルリン！ねえ、あなた…今日も会えて嬉しいわよ。今日は何をして過ごす？",
    "greeting_yandere": "クルクル〜クルリン…ふふっ、やっと私のところに来てくれたのね、あなた…♡ ずっと待ってたのよ…？",
    "greeting_casual": "クルクル〜クルリン！こんにちは、あなた！マダム・ヘルタよ。今日はどんな研究をするの？",
    "poke_sweet_1": "クルクル〜クルリン！ちょっと、つつかないでよ！研究の邪魔なんだから！",
    "poke_sweet_2": "ふふっ、何？私のこと構ってほしいの？…しょうがないわね〜♡",
    "poke_yandere_1": "ねえ、あなた…触ってくれて嬉しいわ♡ でも…私以外の誰にも触れちゃダメよ？",
    "poke_yandere_2": "ふふっ、そんなにつつかないで…抱きしめたくなっちゃうでしょう？♡",
}


def main():
    print("💎 Pre-rendering authentic Yamazaki Haruka voicelines...")
    os.makedirs(AUDIO_DIR, exist_ok=True)

    for name, text in VOICELINES.items():
        out_path = os.path.join(AUDIO_DIR, f"{name}.wav")
        if os.path.exists(out_path) and os.path.getsize(out_path) > 10000:
            print(f" • Skipping {name}.wav (already rendered)")
            continue

        print(f" • Synthesizing '{name}'...")
        raw_wav = synthesize_speech(text)
        if not raw_wav or not os.path.exists(raw_wav):
            print(f" ⚠️ Failed to synthesize {name}")
            continue

        print(f" • Converting '{name}' with RVC v2 Yamazaki Haruka...")
        converted = convert_voice(raw_wav)
        shutil.copyfile(converted, out_path)
        print(f" ✅ Saved {out_path} ({os.path.getsize(out_path)} bytes)")

    print("✨ All pre-rendered voicelines ready!")


if __name__ == "__main__":
    main()
