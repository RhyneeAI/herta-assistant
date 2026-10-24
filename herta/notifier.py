"""
Cross-platform desktop notification banner module.
Supports Linux (notify-send) and Windows (PowerShell Toast Notifications).
"""

import os
import subprocess
from herta.config import ASSETS_DIR, IS_WINDOWS

HERTA_ICON_PATH = os.path.join(ASSETS_DIR, "images", "herta_avatar_256.png")


def show_notification(title: str, message: str):
    """Display native desktop notification toast with authentic Madam Herta avatar."""
    if IS_WINDOWS:
        # PowerShell Windows 10/11 Toast Notification
        image_clause = ""
        if os.path.exists(HERTA_ICON_PATH):
            win_icon_path = HERTA_ICON_PATH.replace("/", "\\")
            image_clause = f"$image = $template.GetElementsByTagName('image'); $image.Item(0).Attributes.GetNamedItem('src').NodeValue = '{win_icon_path}'; "

        ps_script = (
            "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null; "
            "$template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastImageAndText02); "
            f"{image_clause}"
            "$nodes = $template.GetElementsByTagName('text'); "
            f"$nodes.Item(0).AppendChild($template.CreateTextNode('{title}')) > $null; "
            f"$nodes.Item(1).AppendChild($template.CreateTextNode('{message}')) > $null; "
            "$toast = [Windows.UI.Notifications.ToastNotification]::new($template); "
            "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Madam Herta').Show($toast);"
        )
        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_script],
                check=False,
                timeout=5
            )
        except Exception:
            pass
    else:
        # Linux notify-send with Herta avatar icon
        icon_arg = HERTA_ICON_PATH if os.path.exists(HERTA_ICON_PATH) else "dialog-information"
        try:
            subprocess.run(
                [
                    "notify-send",
                    "-a", "Madam Herta (ヘルタ)",
                    "-i", icon_arg,
                    title,
                    message,
                ],
                check=False,
                timeout=5
            )
        except Exception:
            pass
