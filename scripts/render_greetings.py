"""
Pre-render static greeting, wake, and poke voicelines using authentic in-game
"Kuru kuru~" / "Kururin~" samples combined with Yamazaki Haruka RVC v2 dialogue.
"""

import os
import shutil
import sys
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

from herta.config import AUDIO_DIR, TMP_DIR
from herta.rvc import convert_voice
from herta.tts import synthesize_speech

TARGET_SR = 44100

VOICELINES = {
    "greeting_sweet_wife": {
        "kuru_intro": "kuru_kuru.wav",
        "dialogue": "ねえ、あなた…今日も会えて嬉しいわよ。今日は何をして過ごす？"
    },
    "greeting_yandere": {
        "kuru_intro": "kuru_kururin.wav",
        "dialogue": "…ふふっ、やっと私のところに来てくれたのね、あなた…♡ ずっと待ってたのよ…？"
    },
    "greeting_casual": {
        "kuru_intro": "kuru_kuru.wav",
        "dialogue": "こんにちは、あなた！マダム・ヘルタよ。今日はどんな研究をするの？"
    },
    "herta_morning": {
        "kuru_intro": "kuru_kuru.wav",
        "dialogue": "おはよう、あなた！マダム・ヘルタよ。今日も一日、しっかり研究に励みなさい！"
    },
    "herta_afternoon": {
        "kuru_intro": "kuru_kururin.wav",
        "dialogue": "こんにちは、あなた！マダム・ヘルタよ。午後の研究もサボっちゃダメよ！"
    },
    "herta_evening": {
        "kuru_intro": "kuru_kuru.wav",
        "dialogue": "こんばんは、あなた！マダム・ヘルタよ。今日の進捗はどうかしら？成果を期待してるわよ。"
    },
    "herta_sleep": {
        "kuru_intro": "kuru_kuruto.wav",
        "dialogue": "もう寝るの、あなた？おやすみ、また明日ね！"
    },
    "herta_wake": {
        "kuru_intro": "kuru_kururin.wav",
        "dialogue": "おかえり、あなた！さあ、研究の続きを始めましょう！"
    },
    "poke_sweet_1": {
        "kuru_intro": "kuru_kuruto.wav",
        "dialogue": "ちょっと、つつかないでよ！研究の邪魔なんだから！"
    },
    "poke_sweet_2": {
        "kuru_intro": None,
        "dialogue": "ふふっ、何？私のこと構ってほしいの？…しょうがないわね〜♡"
    },
    "poke_yandere_1": {
        "kuru_intro": None,
        "dialogue": "ねえ、あなた…触ってくれて嬉しいわ♡ でも…私以外の誰にも触れちゃダメよ？"
    },
    "poke_yandere_2": {
        "kuru_intro": None,
        "dialogue": "ふふっ、そんなにつつかないで…抱きしめたくなっちゃうでしょう？♡"
    }
}


def load_resampled(path: str, target_sr: int = TARGET_SR) -> np.ndarray:
    """Load audio file and resample to target sampling rate."""
    data, sr = sf.read(path)
    if data.ndim > 1:
        data = data.mean(axis=1)
    if sr != target_sr:
        gcd = np.gcd(sr, target_sr)
        data = resample_poly(data, target_sr // gcd, sr // gcd)
    return data.astype(np.float32)


def main():
    print("Rendering voicelines with authentic in-game Kuru Kuru samples + Yamazaki Haruka RVC...")
    os.makedirs(AUDIO_DIR, exist_ok=True)

    for name, item in VOICELINES.items():
        kuru_intro = item["kuru_intro"]
        dialogue = item["dialogue"]
        out_path = os.path.join(AUDIO_DIR, f"{name}.wav")

        print(f" • Synthesizing dialogue for '{name}'...")
        raw_wav = synthesize_speech(dialogue)
        if not raw_wav or not os.path.exists(raw_wav):
            print(f" [!] Failed to synthesize {name}")
            continue

        print(f" • Converting '{name}' with RVC v2 Yamazaki Haruka...")
        converted = convert_voice(raw_wav)

        if kuru_intro:
            intro_path = os.path.join(AUDIO_DIR, kuru_intro)
            if os.path.exists(intro_path):
                print(f" • Merging authentic in-game sample '{kuru_intro}' with dialogue...")
                try:
                    intro_audio = load_resampled(intro_path)
                    dlg_audio = load_resampled(converted)
                    pause = np.zeros(int(TARGET_SR * 0.12), dtype=np.float32)
                    merged = np.concatenate([intro_audio, pause, dlg_audio])
                    sf.write(out_path, merged, TARGET_SR)
                    print(f" [OK] Saved {out_path} ({os.path.getsize(out_path)} bytes) [Authentic Kuru + RVC]")
                    continue
                except Exception as exc:
                    print(f" [!] Merge failed ({exc}), copying converted...")

        shutil.copyfile(converted, out_path)
        print(f" [OK] Saved {out_path} ({os.path.getsize(out_path)} bytes) [RVC]")

    print("All authentic voicelines successfully rendered!")


if __name__ == "__main__":
    main()
