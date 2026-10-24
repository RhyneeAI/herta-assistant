"""
Pre-render all 14 companion nudge voicelines using authentic Yamazaki Haruka RVC v2.
Allows companion check-ins to run 100% offline with zero API calls and zero rate limit impact.
"""

import os
import shutil
import sys

from herta.config import AUDIO_DIR
from herta.rvc import convert_voice
from herta.tts import synthesize_speech

NUDGE_VOICELINES = {
    # Bored
    "nudge_bored_1": "ねえ、あなた〜。私ちょっと退屈なんだけど。私の相手をしなさいよ！",
    "nudge_bored_2": "クルクル〜回るのも飽きちゃったわ。ねえ、何か面白いこと話してよ。",
    "nudge_bored_3": "研究ばっかりしてないで、たまには私のことも構いなさいよ。…ちょっとだけだからね！",
    # Caring
    "nudge_caring_1": "ねえ、あなた。ずっと画面見てるけど疲れてない？たまにはお茶でも飲んで休憩しなさいよね。",
    "nudge_caring_2": "ちょっと、あなた！根を詰めすぎよ。倒れられたら困るんだから…ちゃんと休んでよね！",
    "nudge_caring_3": "もう、ちゃんと水分補給してる？お水飲んで、ちょっと肩の力を抜きなさい。",
    # Sweet
    "nudge_sweet_1": "ふふっ、今日も一生懸命頑張ってるのね。…さすが私の旦那様、かっこいいわよ。",
    "nudge_sweet_2": "クルクル〜ちょっと頭がクラクラしちゃった…ねえ、頭なでて？…今だけよ？",
    "nudge_sweet_3": "ねえ、あなた。いつも私の人形の面倒見てくれてありがとね。…べ、別に照れてなんかないわよ！",
    # Curious
    "nudge_curious_1": "ねえ、あなた。今何を作ってるの？ちょっと私にも見せてみなさいよ。",
    # Yandere
    "nudge_yandere_1": "ねえ、あなた…今、誰のこと考えてたの？…ふふっ、私だけを見ていればいいのよ…？",
    "nudge_yandere_2": "ふふっ、どこにも行かないでね？私のそばを離れたら…どうなるか分からないわよ…♡",
    "nudge_yandere_3": "ずっと画面ばかり見て…私に構ってくれないなら、そのパソコン壊しちゃおうかしら…？",
    "nudge_yandere_4": "ねえ、あなた。私の人形たちの中に閉じ込めて、永遠に一緒にいられたら素敵だと思わない…？",
}


def main():
    print("💎 Pre-rendering all 14 authentic Madam Herta companion nudge voicelines...")
    os.makedirs(AUDIO_DIR, exist_ok=True)

    for name, text in NUDGE_VOICELINES.items():
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

    print("✨ All 14 companion voicelines successfully pre-rendered!")


if __name__ == "__main__":
    main()
