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


def main():
    parser = argparse.ArgumentParser(
        prog="herta",
        description="Madam Herta AI Assistant - Voice Chat, Boot Greeting, and Sleep Monitor."
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Chat command
    chat_parser = subparsers.add_parser("chat", help="Start interactive live voice chat session")
    chat_parser.add_argument("--fast", "--no-rvc", action="store_true", help="Fast mode without RVC voice conversion")

    # Greeting command
    subparsers.add_parser("greet", help="Trigger boot / startup voice greeting")

    # Power monitor command
    subparsers.add_parser("monitor", help="Run background sleep and wake power event monitor")

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

    args = parser.parse_args()

    # Default to chat if no subcommand is given
    if args.command is None or args.command == "chat":
        fast_mode = getattr(args, "fast", False)
        start_chat(fast_mode=fast_mode)
    elif args.command == "greet":
        trigger_greeting()
    elif args.command == "monitor":
        run_monitor()
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
