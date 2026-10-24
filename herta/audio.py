"""
Cross-platform audio playback and recording module.
Supports Linux (PipeWire / PulseAudio / ALSA) and Windows (winsound / ffplay).
"""

import os
import signal
import subprocess
import sys

from herta.config import IS_WINDOWS, TMP_DIR


def play_audio(filepath: str, timeout: int = 15):
    """Play audio file across Linux and Windows platforms."""
    if not filepath or not os.path.exists(filepath):
        return

    # Windows native player via winsound (WAV format)
    if IS_WINDOWS and filepath.lower().endswith(".wav"):
        try:
            import winsound
            winsound.PlaySound(filepath, winsound.SND_FILENAME)
            return
        except Exception:
            pass

    # Generic CLI audio players
    players = []
    if IS_WINDOWS:
        players = [
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", filepath],
            ["powershell", "-c", f"(New-Object Media.SoundPlayer '{filepath}').PlaySync()"],
        ]
    else:
        players = [
            ["pw-play", filepath],
            ["paplay", filepath],
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", filepath],
            ["aplay", filepath],
        ]

    for cmd in players:
        binary = cmd[0]
        # Check command existence
        if subprocess.run(["where" if IS_WINDOWS else "which", binary], capture_output=True).returncode == 0:
            try:
                subprocess.run(cmd, check=True, timeout=timeout)
                return
            except Exception:
                continue

    sys.stderr.write(f"Warning: No suitable audio player found to play {filepath}\n")


def record_microphone(output_path: str = None) -> str:
    """
    Record user microphone input until user presses Enter.
    Returns path to the recorded WAV audio file.
    """
    if output_path is None:
        output_path = os.path.join(TMP_DIR, "user_speech_input.wav")

    if os.path.exists(output_path):
        try:
            os.remove(output_path)
        except OSError:
            pass

    print("\n🔴 [RECORDING] Speak into your microphone... (Press [ENTER] when finished)")

    proc = None
    if IS_WINDOWS:
        # Use ffmpeg with DirectShow on Windows or fallback
        proc = subprocess.Popen(
            ["ffmpeg", "-y", "-f", "dshow", "-i", "audio=virtual-audio-capturer", output_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    else:
        # Use parecord on Linux PulseAudio / PipeWire
        proc = subprocess.Popen(
            ["parecord", "--format=s16le", "--rate=16000", "--channels=1", output_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    try:
        input()
    finally:
        if proc:
            try:
                if IS_WINDOWS:
                    proc.terminate()
                else:
                    proc.send_signal(signal.SIGINT)
                proc.wait(timeout=2)
            except Exception:
                proc.kill()

    return output_path
