"""
Service management module for Madam Herta Assistant.
Cross-platform control for starting, stopping, and inspecting background services:
- Linux: systemd user service (herta-sleep-monitor.service)
- Windows: Windows Task / background monitor process
"""

import os
import subprocess
import sys

from herta.config import IS_WINDOWS

LINUX_SERVICE = "herta-sleep-monitor.service"


def is_service_running() -> bool:
    """Check whether the background service is actively running."""
    if IS_WINDOWS:
        try:
            out = subprocess.check_output(["tasklist", "/FI", "IMAGENAME eq python.exe"], text=True)
            return "herta.cli monitor" in out or "python.exe" in out
        except Exception:
            return False
    else:
        try:
            res = subprocess.run(["systemctl", "--user", "is-active", LINUX_SERVICE], capture_output=True, text=True)
            return res.stdout.strip() == "active"
        except Exception:
            return False


def start_service() -> bool:
    """Start and enable background service."""
    if IS_WINDOWS:
        # Start background monitor via VBS launcher
        vbs_path = os.path.expanduser("~\\AppData\\Local\\HertaAssistant\\herta_monitor_background.vbs")
        if not os.path.exists(vbs_path):
            vbs_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "herta_monitor_background.vbs")
        try:
            subprocess.Popen(["wscript.exe", vbs_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("🟢 Madam Herta Background Service STARTED.")
            return True
        except Exception as exc:
            sys.stderr.write(f"Failed to start service on Windows: {exc}\n")
            return False
    else:
        try:
            subprocess.run(["systemctl", "--user", "enable", "--now", LINUX_SERVICE], check=True, capture_output=True)
            print(f"🟢 Madam Herta Background Service ACTIVATED ({LINUX_SERVICE}).")
            return True
        except Exception as exc:
            sys.stderr.write(f"Failed to start systemd service: {exc}\n")
            return False


def stop_service() -> bool:
    """Stop and disable background service."""
    if IS_WINDOWS:
        try:
            # Terminate running monitor instances
            subprocess.run(["taskkill", "/F", "/FI", "WINDOWTITLE eq MadamHerta*"], check=False, capture_output=True)
            print("🔴 Madam Herta Background Service STOPPED.")
            return True
        except Exception as exc:
            sys.stderr.write(f"Failed to stop service on Windows: {exc}\n")
            return False
    else:
        try:
            subprocess.run(["systemctl", "--user", "stop", LINUX_SERVICE], check=False, capture_output=True)
            subprocess.run(["systemctl", "--user", "disable", LINUX_SERVICE], check=False, capture_output=True)
            print(f"🔴 Madam Herta Background Service DEACTIVATED ({LINUX_SERVICE}).")
            return True
        except Exception as exc:
            sys.stderr.write(f"Failed to stop systemd service: {exc}\n")
            return False


def restart_service() -> bool:
    """Restart background service."""
    stop_service()
    import time
    time.sleep(1)
    return start_service()


def show_service_status():
    """Print current service status to terminal."""
    running = is_service_running()
    status_str = "RUNNING 🟢" if running else "STOPPED 🔴"
    print("\n" + "=" * 50)
    print("💎   MADAM HERTA BACKGROUND SERVICE STATUS")
    print("=" * 50)
    print(f" • Platform: {'Windows' if IS_WINDOWS else 'Linux (systemd)'}")
    print(f" • Status:   {status_str}")
    if not IS_WINDOWS:
        try:
            out = subprocess.check_output(["systemctl", "--user", "status", LINUX_SERVICE, "--no-pager"], text=True)
            lines = [l for l in out.splitlines() if "Active:" in l or "Main PID:" in l or "Tasks:" in l]
            for l in lines:
                print(f"  {l.strip()}")
        except Exception:
            pass
    print("=" * 50)
    print("Commands:")
    print("  • herta service on       - Enable and start background monitor")
    print("  • herta service off      - Stop and disable background monitor")
    print("  • herta service restart  - Restart background monitor")
    print("=" * 50 + "\n")
