"""
Cross-platform desktop notification banner module.
Supports Linux (notify-send) and Windows (PowerShell Toast Notifications).
"""

import subprocess
from herta.config import IS_WINDOWS


def show_notification(title: str, message: str):
    """Display native desktop notification toast."""
    if IS_WINDOWS:
        # PowerShell Windows 10/11 Toast Notification
        ps_script = (
            "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null; "
            "$template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02); "
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
        # Linux notify-send
        try:
            subprocess.run(
                [
                    "notify-send",
                    "-a", "Madam Herta (ヘルタ)",
                    "-i", "dialog-information",
                    title,
                    message,
                ],
                check=False,
                timeout=5
            )
        except Exception:
            pass
