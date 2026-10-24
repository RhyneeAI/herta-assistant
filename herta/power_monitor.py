"""
Cross-platform power event monitor (sleep and wake) with strict debounce protection.
Supports Linux (systemd-logind DBus) and Windows (WM_POWERBROADCAST message loop).
Includes a 15-minute cooldown between triggers to prevent notification/audio spam
and avoid failed suspend states that cause laptop overheating.
"""

import json
import os
import subprocess
import sys
import threading
import time

from herta.audio import play_audio
from herta.companion import run_companion_loop
from herta.config import AUDIO_DIR, CACHE_DIR, IS_WINDOWS, load_config
from herta.notifier import show_notification

SLEEP_AUDIO = os.path.join(AUDIO_DIR, "herta_sleep.wav")
WAKE_AUDIO = os.path.join(AUDIO_DIR, "herta_wake.wav")
STATE_FILE = os.path.join(CACHE_DIR, "power_state.json")

# Strict 15-minute cooldown (900 seconds) to prevent spam and suspend loops
COOLDOWN_SECONDS = 900


def get_last_event_time(event_type: str) -> float:
    """Retrieve timestamp of last recorded sleep/wake event."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return float(data.get(event_type, 0))
        except Exception:
            pass
    return 0.0


def save_event_time(event_type: str, timestamp: float):
    """Persist event timestamp to disk."""
    data = {}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    data[event_type] = timestamp
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass


def on_sleep() -> bool:
    """
    Triggered right before the machine enters sleep / suspend.
    Enforces a strict 15-minute cooldown to prevent notification spam and suspend aborts.
    Returns True if voiceline was played, False if skipped.
    """
    now = time.time()
    last_sleep = get_last_event_time("last_sleep")
    elapsed = now - last_sleep

    if elapsed < COOLDOWN_SECONDS:
        sys.stderr.write(
            f"Sleep detected within cooldown ({int(elapsed)}s < {COOLDOWN_SECONDS}s). Skipping to protect hardware.\n"
        )
        return False

    save_event_time("last_sleep", now)

    # Note: We strictly avoid desktop notifications (notify-send) right before sleep,
    # because notification popups in desktop environments (like GNOME) wake up the
    # display server and cause systemd to abort sleep back to standby!
    if os.path.exists(SLEEP_AUDIO):
        try:
            play_audio(SLEEP_AUDIO, timeout=8)
        except Exception:
            pass
        # Brief 0.5s pause allowing PipeWire/ALSA to release hardware codec before kernel suspend
        time.sleep(0.5)

    return True


def on_wake() -> bool:
    """
    Triggered right after the machine resumes from sleep.
    Enforces cooldown and minimum sleep duration check.
    """
    now = time.time()
    last_wake = get_last_event_time("last_wake")
    last_sleep = get_last_event_time("last_sleep")

    # If the system "woke up" in less than 8 seconds, it was an aborted suspend / glitch
    if (now - last_sleep) < 8:
        sys.stderr.write("Premature resume detected (< 8s from sleep request). Skipping wake greeting.\n")
        return False

    elapsed = now - last_wake
    if elapsed < COOLDOWN_SECONDS:
        sys.stderr.write(
            f"Wake detected within cooldown ({int(elapsed)}s < {COOLDOWN_SECONDS}s). Skipping to avoid spam.\n"
        )
        return False

    save_event_time("last_wake", now)

    time.sleep(2)  # Wait for display and audio subsystem to settle

    cfg = load_config()
    partner = cfg.get("partner_name", "あなた")
    jp = f"クルクル〜クルリン！おかえり、{partner}！さあ、研究の続きを始めましょう！"
    id_sub = f"Kuru kuru~ Kururin! Selamat datang kembali, {partner}! Ayo, mari kita lanjutkan risetnya!"

    show_notification(f"💎 Madam Herta: {jp}", f"🇮🇩 {id_sub}")
    play_audio(WAKE_AUDIO, timeout=10)
    return True


def run_linux_monitor():
    """Linux power monitor using systemd-logind DBus interface with delay inhibitor."""
    cmd = [
        "gdbus", "monitor", "--system",
        "--dest", "org.freedesktop.login1",
        "--object-path", "/org/freedesktop/login1"
    ]

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    except Exception as exc:
        sys.stderr.write(f"Failed to start gdbus monitor: {exc}\n")
        return

    try:
        for line in proc.stdout:
            if "PrepareForSleep (true," in line:
                on_sleep()
            elif "PrepareForSleep (false," in line:
                on_wake()
    finally:
        if proc:
            proc.terminate()


def run_windows_monitor():
    """Windows power monitor using Win32 WM_POWERBROADCAST event pump."""
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    WM_POWERBROADCAST = 0x0218
    PBT_APMSUSPEND = 0x0004
    PBT_APMRESUMEAUTOMATIC = 0x0012
    PBT_APMRESUMESUSPEND = 0x0007

    WNDPROCTYPE = ctypes.WINFUNCTYPE(ctypes.c_long, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

    def wndproc(hwnd, msg, wparam, lparam):
        if msg == WM_POWERBROADCAST:
            if wparam == PBT_APMSUSPEND:
                on_sleep()
            elif wparam in (PBT_APMRESUMEAUTOMATIC, PBT_APMRESUMESUSPEND):
                on_wake()
            return 1
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    class WNDCLASSEX(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.UINT),
            ("style", wintypes.UINT),
            ("lpfnWndProc", WNDPROCTYPE),
            ("cbClsExtra", ctypes.c_int),
            ("cbWndExtra", ctypes.c_int),
            ("hInstance", wintypes.HINSTANCE),
            ("hIcon", wintypes.HICON),
            ("hCursor", wintypes.HICON),
            ("hbrBackground", wintypes.HBRUSH),
            ("lpszMenuName", wintypes.LPCWSTR),
            ("lpszClassName", wintypes.LPCWSTR),
            ("hIconSm", wintypes.HICON),
        ]

    wndproc_ptr = WNDPROCTYPE(wndproc)
    wndclass = WNDCLASSEX()
    wndclass.cbSize = ctypes.sizeof(WNDCLASSEX)
    wndclass.lpfnWndProc = wndproc_ptr
    wndclass.hInstance = kernel32.GetModuleHandleW(None)
    wndclass.lpszClassName = "MadamHertaPowerMonitor"

    user32.RegisterClassExW(ctypes.byref(wndclass))
    hwnd = user32.CreateWindowExW(
        0, wndclass.lpszClassName, "Madam Herta Monitor",
        0, 0, 0, 0, 0, None, None, wndclass.hInstance, None
    )

    msg = wintypes.MSG()
    while user32.GetMessageW(ctypes.byref(msg), hwnd, 0, 0) > 0:
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageW(ctypes.byref(msg))


def run_monitor():
    """Run power event listener loop and spontaneous companion thread."""
    companion_thread = threading.Thread(
        target=run_companion_loop,
        kwargs={"min_interval_minutes": 45, "max_interval_minutes": 90},
        daemon=True
    )
    companion_thread.start()

    if IS_WINDOWS:
        run_windows_monitor()
    else:
        run_linux_monitor()
