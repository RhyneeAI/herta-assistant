#!/usr/bin/env bash
# ==============================================================================
# Madam Herta Assistant - Linux One-Click Installer
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="${HERTA_VENV:-/mnt/games/rvc-env}"

echo "======================================================================"
echo "💎   INSTALLING MADAM HERTA ASSISTANT (LINUX)"
echo "======================================================================"

# 1. Ensure Python Virtual Environment
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment at $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
fi

echo "Installing Python dependencies..."
TMPDIR=/mnt/games/tmp "$VENV_DIR/bin/pip" install --quiet -r "$PROJECT_DIR/requirements.txt" || true
TMPDIR=/mnt/games/tmp "$VENV_DIR/bin/pip" install -e "$PROJECT_DIR" --quiet
"$VENV_DIR/bin/pip" uninstall -y torchvision >/dev/null 2>&1 || true

# 2. Download / Link Models
echo "Verifying voice models..."
"$VENV_DIR/bin/python3" "$SCRIPT_DIR/download_models.py"

# 3. Create CLI Launcher in ~/.local/bin
mkdir -p "$HOME/.local/bin"
LAUNCHER="$HOME/.local/bin/herta"
cat <<EOF > "$LAUNCHER"
#!/usr/bin/env bash
exec "$VENV_DIR/bin/python3" -m herta.cli "\$@"
EOF
chmod +x "$LAUNCHER"

# Alias talk-live to herta chat
ln -sf "$LAUNCHER" "$HOME/.local/bin/talk-live"

# 4. Install Sleep Monitor Systemd Service
echo "Installing sleep monitor systemd service..."
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
mkdir -p "$SYSTEMD_USER_DIR"

cat <<EOF > "$SYSTEMD_USER_DIR/herta-sleep-monitor.service"
[Unit]
Description=Madam Herta Sleep and Wake Voice Monitor
After=default.target sound.target

[Service]
Type=simple
ExecStart=$HOME/.local/bin/herta monitor
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now herta-sleep-monitor.service || true

# 5. Install Desktop Autostart Greeting
echo "Installing login greeting autostart entry..."
AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"

cat <<EOF > "$AUTOSTART_DIR/herta-greeting.desktop"
[Desktop Entry]
Type=Application
Name=Madam Herta Boot Greeting
Comment=Plays Madam Herta voice greeting on login
Exec=bash -c "sleep 3 && $HOME/.local/bin/herta greet"
Terminal=false
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF

# 6. Optional Initial Configuration (Partner Name & Gemini API Key)
echo ""
echo "======================================================================"
echo "⚙️   INITIAL CONFIGURATION (OPTIONAL)"
echo "======================================================================"
echo "Press [Enter] to keep defaults, or customize your initial settings:"
echo ""

read -r -p "Partner name / title Madam Herta uses to address you (Default: あなた): " input_name
if [ -n "$input_name" ]; then
    "$VENV_DIR/bin/python3" -m herta.cli config --name "$input_name"
fi

read -r -p "Google Gemini API Key (Optional - press [Enter] to skip): " input_key
if [ -n "$input_key" ]; then
    "$VENV_DIR/bin/python3" -m herta.cli config --key "$input_key"
fi

echo ""
echo "======================================================================"
echo "✨ Installation Complete!"
echo "Commands available:"
echo "  • herta chat        - Start live voice conversation"
echo "  • herta greet       - Trigger startup greeting"
echo "  • herta sleep/wake  - Trigger bedtime or wake voicelines"
echo "  • herta config      - View and modify settings"
echo "======================================================================"
