"""
Cross-platform power event monitor (sleep and wake).
Supports Linux (systemd-logind DBus) and Windows (WM_POWERBROADCAST message loop).
"""

import os
import subprocess
import sys
import time

from herta.audio import play_audio
from herta.config import AUDIO_DIR, IS_WINDOWS, load_config
from herta.notifier import show_notification

SLEEP_AUDIO = os.path.join(AUDIO_DIR, "herta_sleep.wav")
WAKE_AUDIO = os.path.join(AUDIO_DIR, "herta_wake.wav")


def on_sleep():
    """Triggered right before the machine enters sleep / suspend."""
    cfg = load_config()
    partner = cfg.get("partner_name", "Rinne")
    jp = f"もう寝るの、{partner}？クルクル〜おやすみ、また明日ね！"
    id_sub = f"Mau tidur sekarang, {partner}? Kuru kuru~ Selamat malam, sampai jumpa besok!"

    show_notification(f"💎 Madam Herta: {jp}", f"🇮🇩 {id_sub}")
    play_audio(SLEEP_AUDIO, timeout=6)


def on_wake():
    """Triggered right after the machine resumes from sleep."""
    cfg = load_config()
    partner = cfg.get("partner_name", "Rinne")
    jp = f"クルクル〜クルリン！おかえり、{partner}！さあ、研究の続きを始めましょう！"
    id_sub = f"Kuru kuru~ Kururin! Selamat datang kembali, {partner}! Ayo, mari kita lanjutkan risetnya!"

    time.sleep(2)  # Wait for audio driver to settle
    show_notification(f"💎 Madam Herta: {jp}", f"🇮🇩 {id_sub}")
    play_audio(WAKE_AUDIO, timeout=12)


def run_linux_monitor():
    """Linux power monitor using systemd-logind DBus interface."""
    inhibitor_proc = None

    def start_inhibitor():
        try:
            return subprocess.Popen(
                ["systemd-inhibit", "--what=sleep", "--why=Madam Herta Sleep Audio", "--mode=delay", "sleep", "infinity"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception:
            return None

    def stop_inhibitor(proc):
        if proc:
            try:
                proc.terminate()
                proc.wait(timeout=1)
            except Exception:
                pass

    inhibitor_proc = start_inhibitor()
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
                stop_inhibitor(inhibitor_proc)
                inhibitor_proc = None
            elif "PrepareForSleep (false," in line:
                inhibitor_proc = start_inhibitor()
                on_wake()
    finally:
        stop_inhibitor(inhibitor_proc)
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
    """Run power event listener loop on the current OS."""
    if IS_WINDOWS:
        run_windows_monitor()
    else:
        run_linux_monitor()
