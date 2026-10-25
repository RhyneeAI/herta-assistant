"""
Command-Line Interface (CLI) entrypoint for Madam Herta Assistant.
"""

import argparse
import sys
import warnings

# Suppress PyTorch future deprecation notices for cleaner terminal display
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

from herta.alarm import (
    add_alarm,
    add_timer,
    delete_alarm,
    load_alarms,
    toggle_alarm,
    trigger_alarm,
)
from herta.chat import start_chat
from herta.companion import run_companion_loop, trigger_spontaneous_interaction
from herta.config import CONFIG_FILE, load_config, save_config
from herta.greeting import trigger_greeting
from herta.power_monitor import on_sleep, on_wake, run_monitor
from herta.service import restart_service, show_service_status, start_service, stop_service



def main():
    parser = argparse.ArgumentParser(
        prog="herta",
        description="Madam Herta AI Assistant - Voice Chat, Boot Greeting, and Sleep Monitor."
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Chat command
    chat_parser = subparsers.add_parser("chat", help="Start interactive live voice chat session")
    chat_parser.add_argument("--fast", "--no-rvc", action="store_true", help="Fast mode without RVC voice conversion")

    # GUI command
    subparsers.add_parser("gui", help="Launch Madam Herta Desktop Mascot & System Tray GUI")

    # Greeting command
    subparsers.add_parser("greet", help="Trigger boot / startup voice greeting")

    # Power monitor command
    subparsers.add_parser("monitor", help="Run background sleep and wake power event monitor")

    # Service management command (on/off/status/restart)
    service_parser = subparsers.add_parser("service", help="Manage background service (on/off/status/restart)")
    service_parser.add_argument(
        "action", nargs="?", choices=["on", "off", "start", "stop", "status", "restart"],
        default="status", help="Service action: on, off, status, restart"
    )

    # Direct sleep / wake triggers
    subparsers.add_parser("sleep", help="Trigger bedtime / sleep voiceline")
    subparsers.add_parser("wake", help="Trigger wake-from-sleep voiceline")

    # Companion command
    comp_parser = subparsers.add_parser("companion", help="Run proactive companion check-in daemon")
    comp_parser.add_argument("--now", action="store_true", help="Trigger a spontaneous interaction immediately")
    comp_parser.add_argument("--interval", type=int, default=60, help="Check-in interval in minutes")

    subparsers.add_parser("nudge", help="Ask Madam Herta to say something cute / check in on you right now")

    # Alarm and Timer command
    alarm_parser = subparsers.add_parser("alarm", help="Manage Madam Herta alarms and timers")
    alarm_sub = alarm_parser.add_subparsers(dest="alarm_action", help="Alarm action: add, timer, list, delete, test")
    
    # alarm add
    alm_add = alarm_sub.add_parser("add", help="Add a scheduled daily alarm (e.g. herta alarm add 07:00 'Bangun Pagi')")
    alm_add.add_argument("time", type=str, help="Alarm time in HH:MM format (e.g. 07:00, 14:30)")
    alm_add.add_argument("label", nargs="?", default="Alarm Madam Herta", help="Alarm label description")
    alm_add.add_argument("--once", action="store_true", help="One-shot alarm (disabled after triggering once)")

    # alarm timer
    alm_tmr = alarm_sub.add_parser("timer", help="Add a countdown timer (e.g. herta alarm timer 25 'Rehat')")
    alm_tmr.add_argument("minutes", type=float, help="Timer duration in minutes")
    alm_tmr.add_argument("label", nargs="?", default="Timer", help="Timer label description")

    # alarm list
    alarm_sub.add_parser("list", help="List all registered alarms and timers")

    # alarm delete
    alm_del = alarm_sub.add_parser("delete", help="Delete alarm or timer by ID")
    alm_del.add_argument("id", type=str, help="Alarm ID (e.g. alm_123456)")

    # alarm test
    alarm_sub.add_parser("test", help="Test Madam Herta wake-up alarm sound and pop-up immediately")

    # Configuration command
    config_parser = subparsers.add_parser("config", help="View or modify configuration")
    config_parser.add_argument("--name", type=str, help="Set partner name")
    config_parser.add_argument("--key", type=str, help="Set Gemini API key")
    config_parser.add_argument("--rvc", choices=["on", "off"], help="Enable or disable RVC by default")
    config_parser.add_argument("--romance", choices=["on", "off"], help="Enable or disable romance mode (intimate wife tone)")
    config_parser.add_argument("--style", choices=["sweet_wife", "yandere"], help="Set romance address style: sweet_wife or yandere")
    config_parser.add_argument("--lang", choices=["id", "en"], help="Set subtitle translation language: id (Indonesian) or en (English)")
    config_parser.add_argument("--companion-min", type=int, help="Minimum companion interval in minutes")
    config_parser.add_argument("--companion-max", type=int, help="Maximum companion interval in minutes")
    config_parser.add_argument("--telegram-token", type=str, help="Telegram Bot Token for phone notifications")
    config_parser.add_argument("--telegram-chat-id", type=str, help="Telegram Chat ID for phone notifications")


    args = parser.parse_args()

    # Default to chat if no subcommand is given
    if args.command is None or args.command == "chat":
        fast_mode = getattr(args, "fast", False)
        start_chat(fast_mode=fast_mode)
    elif args.command == "gui":
        from herta.gui import run_gui
        run_gui()
    elif args.command == "greet":
        trigger_greeting()
    elif args.command == "monitor":
        run_monitor()
    elif args.command == "service":
        action = getattr(args, "action", "status")
        if action in ["on", "start"]:
            start_service()
        elif action in ["off", "stop"]:
            stop_service()
        elif action == "restart":
            restart_service()
        else:
            show_service_status()
    elif args.command == "sleep":
        on_sleep()
    elif args.command == "wake":
        on_wake()
    elif args.command == "companion":
        if getattr(args, "now", False):
            trigger_spontaneous_interaction()
        else:
            interval = getattr(args, "interval", 60)
            run_companion_loop(min_interval_minutes=max(15, interval - 15), max_interval_minutes=interval + 15)
    elif args.command == "alarm":
        action = getattr(args, "alarm_action", "list") or "list"
        if action == "add":
            try:
                res = add_alarm(args.time, label=args.label, once=args.once)
                print(f"✅ Alarm successfully set for {res['time']} - '{res['label']}' (ID: {res['id']})")
            except Exception as exc:
                print(f"❌ Failed to set alarm: {exc}")
        elif action == "timer":
            try:
                res = add_timer(args.minutes, label=args.label)
                print(f"✅ Timer set for {res['duration_minutes']} minutes (Target: {res['target_time_str']}) - '{res['label']}' (ID: {res['id']})")
            except Exception as exc:
                print(f"❌ Failed to set timer: {exc}")
        elif action == "delete":
            if delete_alarm(args.id):
                print(f"✅ Deleted alarm {args.id}")
            else:
                print(f"❌ Alarm {args.id} not found.")
        elif action == "test":
            print("🔔 Testing Madam Herta wake-up alarm sound and pop-up...")
            test_alm = {"id": "test", "time": "TEST", "label": "Test Alarm Madam Herta", "sound": "herta_morning.wav"}
            trigger_alarm(test_alm)
        else:
            # list alarms
            alarms = load_alarms()
            print("\n" + "=" * 60)
            print("💎   MADAM HERTA ALARMS & TIMERS")
            print("=" * 60)
            if not alarms:
                print(" No alarms or timers currently set.")
                print(" Use 'herta alarm add <time> [label]' or 'herta alarm timer <minutes> [label]'")
            else:
                for idx, a in enumerate(alarms, 1):
                    a_type = a.get("type", "alarm").upper()
                    status = "🟢 ON" if a.get("enabled", True) else "⚪ OFF"
                    if a_type == "TIMER":
                        time_display = f"Target: {a.get('target_time_str')} ({a.get('duration_minutes')} min)"
                    else:
                        days = ",".join(a.get("days", [])) if a.get("days") else "Daily"
                        time_display = f"Time: {a.get('time')} [{days}]"
                    print(f" {idx}. [{a_type}] {time_display} | {a.get('label')} | {status} (ID: {a.get('id')})")
            print("=" * 60 + "\n")
    elif args.command == "nudge":
        trigger_spontaneous_interaction()
    elif args.command == "config":
        cfg = load_config()
        changed = False
        if args.name:
            cfg["partner_name"] = args.name
            changed = True
        if args.key:
            cfg["gemini_api_key"] = args.key
            changed = True
        if args.rvc:
            cfg["rvc_enabled"] = (args.rvc == "on")
            changed = True
        if args.romance:
            cfg["romance_mode"] = (args.romance == "on")
            changed = True
        if args.style:
            cfg["romance_address_style"] = args.style
            changed = True
        if args.lang:
            cfg["subtitle_language"] = args.lang
            changed = True
        if args.companion_min is not None:
            cfg["companion_min_minutes"] = max(1, args.companion_min)
            changed = True
        if args.companion_max is not None:
            cfg["companion_max_minutes"] = max(1, args.companion_max)
            changed = True
        if args.telegram_token:
            cfg["telegram_bot_token"] = args.telegram_token
            changed = True
        if args.telegram_chat_id:
            cfg["telegram_chat_id"] = args.telegram_chat_id
            changed = True

        if changed:
            save_config(cfg)
            print("Configuration updated successfully.")

        print(f"\nConfiguration file: {CONFIG_FILE}")
        for k, v in cfg.items():
            if k == "gemini_api_key" and v:
                v = v[:4] + "..." + v[-4:] if len(v) > 8 else "***"
            elif k == "telegram_bot_token" and v:
                v = v[:6] + "..." + v[-4:] if len(v) > 10 else "***"
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
