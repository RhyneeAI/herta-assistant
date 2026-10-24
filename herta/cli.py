"""
Command-Line Interface (CLI) entrypoint for Madam Herta Assistant.
"""

import argparse
import sys
import warnings

# Suppress PyTorch future deprecation notices for cleaner terminal display
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

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

        if changed:
            save_config(cfg)
            print("Configuration updated successfully.")

        print(f"\nConfiguration file: {CONFIG_FILE}")
        for k, v in cfg.items():
            if k == "gemini_api_key" and v:
                v = v[:4] + "..." + v[-4:] if len(v) > 8 else "***"
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
