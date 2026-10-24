"""
Desktop GUI Module for Madam Herta Assistant.
Features:
1. Floating Desktop Mascot:
   - Frameless, translucent, draggable anime mascot overlay.
   - Animated Madam Herta Kuru Kuru spinning animation.
   - Interactive Speech Bubble displaying Japanese voicelines & ID/EN subtitles.
   - Click-to-poke reaction and push-to-talk microphone trigger.
2. System Tray Applet:
   - Persistent tray icon in OS taskbar.
   - Quick menu: Show/Hide Mascot, Live Chat Window, Nudge, Romance Style,
     Language Subtitles, Voice Conversion, and Quit.
"""

import os
import random
import sys
import threading
import time

from PyQt6.QtCore import (
    QPoint,
    QRect,
    QSize,
    Qt,
    QThread,
    QTimer,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QAction,
    QActionGroup,
    QColor,
    QFont,
    QIcon,
    QMovie,
    QPainter,
    QPixmap,
)
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from herta.audio import play_audio, record_microphone
from herta.chat import build_system_prompt, generate_llm_reply, parse_reply, speak, transcribe_audio
from herta.companion import BUILTIN_MOMENTS, generate_dynamic_moment
from herta.config import ASSETS_DIR, load_config, save_config

HERTA_ICON_PATH = os.path.join(ASSETS_DIR, "images", "herta_avatar_64.png")
HERTA_LARGE_ICON = os.path.join(ASSETS_DIR, "images", "herta_avatar_256.png")
HERTA_GIF_PATH = os.path.join(ASSETS_DIR, "images", "herta_kuru1.gif")


class SpeechWorker(QThread):
    """Background worker for synthesizing and playing audio without freezing the GUI."""
    finished_speaking = pyqtSignal()

    def __init__(self, jp_text: str, rvc_enabled: bool = True):
        super().__init__()
        self.jp_text = jp_text
        self.rvc_enabled = rvc_enabled

    def run(self):
        try:
            speak(self.jp_text, rvc_enabled=self.rvc_enabled)
        except Exception as exc:
            sys.stderr.write(f"GUI speak error: {exc}\n")
        self.finished_speaking.emit()


class ChatWorker(QThread):
    """Background worker for transcribing and generating LLM replies."""
    reply_ready = pyqtSignal(str, str, str)  # (user_text, reply_jp, reply_sub)
    error_occurred = pyqtSignal(str)

    def __init__(self, user_input: str, is_voice: bool, config: dict, history: list):
        super().__init__()
        self.user_input = user_input
        self.is_voice = is_voice
        self.cfg = config
        self.history = history

    def run(self):
        api_key = self.cfg.get("gemini_api_key", "")
        chat_model = self.cfg.get("gemini_chat_model", "gemini-3.5-flash")
        partner = self.cfg.get("partner_name", "あなた")
        romance_mode = self.cfg.get("romance_mode", True)
        romance_style = self.cfg.get("romance_address_style", "sweet_wife")
        sub_lang = self.cfg.get("subtitle_language", "id")

        user_text = self.user_input
        if self.is_voice:
            mic_wav = record_microphone()
            user_text = transcribe_audio(mic_wav, api_key, chat_model)
            if not user_text:
                self.error_occurred.emit("No speech detected. Please speak clearly into your mic.")
                return

        system_prompt = build_system_prompt(
            partner_name=partner,
            romance_mode=romance_mode,
            romance_style=romance_style,
            subtitle_lang=sub_lang
        )

        turns = list(self.history)
        turns.append({"role": "user", "text": user_text})

        try:
            reply_raw = generate_llm_reply(turns, system_prompt, api_key, chat_model)
            reply_jp, reply_sub = parse_reply(reply_raw)
            self.reply_ready.emit(user_text, reply_jp, reply_sub)
        except Exception as exc:
            self.error_occurred.emit(f"LLM Error: {exc}")


class CompanionWorker(QThread):
    """Background companion monitor loop emitting spontaneous interactions to GUI."""
    moment_triggered = pyqtSignal(str, str, str)  # (jp, sub, flag)

    def run(self):
        while True:
            cfg = load_config()
            min_m = int(cfg.get("companion_min_minutes", 20))
            max_m = int(cfg.get("companion_max_minutes", 45))
            if min_m > max_m:
                min_m, max_m = max_m, min_m

            wait_seconds = random.randint(max(1, min_m) * 60, max(1, max_m) * 60)
            time.sleep(wait_seconds)

            try:
                cfg = load_config()
                partner = cfg.get("partner_name", "あなた")
                api_key = cfg.get("gemini_api_key", "")
                chat_model = cfg.get("gemini_chat_model", "gemini-3.5-flash")
                romance_style = cfg.get("romance_address_style", "sweet_wife")
                sub_lang = cfg.get("subtitle_language", "id")
                rvc_enabled = cfg.get("rvc_enabled", True)

                moment = None
                if api_key and random.random() < 0.5:
                    moment = generate_dynamic_moment(
                        partner_name=partner,
                        api_key=api_key,
                        chat_model=chat_model,
                        romance_style=romance_style,
                        subtitle_lang=sub_lang
                    )

                if moment:
                    jp_text = moment["jp"]
                    sub_text = moment["sub"]
                    flag = "🇬🇧" if sub_lang == "en" else "🇮🇩"
                else:
                    if romance_style == "yandere":
                        y_moments = [m for m in BUILTIN_MOMENTS if m.get("category") == "yandere"]
                        chosen = random.choice(y_moments if y_moments else BUILTIN_MOMENTS)
                    else:
                        s_moments = [m for m in BUILTIN_MOMENTS if m.get("category") != "yandere"]
                        chosen = random.choice(s_moments if s_moments else BUILTIN_MOMENTS)

                    jp_text = chosen["jp"].replace("あなた", partner)
                    if sub_lang == "en":
                        flag = "🇬🇧"
                        sub_text = chosen.get("en", chosen.get("id")).replace("darling", "darling" if partner == "あなた" else partner)
                    else:
                        flag = "🇮🇩"
                        sub_text = chosen.get("id", chosen.get("en")).replace("sayang", "sayang" if partner == "あなた" else partner)

                self.moment_triggered.emit(jp_text, sub_text, flag)
                speak(jp_text, rvc_enabled=rvc_enabled)
            except Exception as exc:
                sys.stderr.write(f"Companion worker error: {exc}\n")


class SpeechBubble(QFrame):
    """Translucent glassmorphism speech bubble attached above the mascot."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(20, 20, 32, 220);
                border: 1px solid rgba(138, 92, 246, 160);
                border-radius: 14px;
                padding: 10px;
            }
            QLabel {
                color: #ffffff;
                background: transparent;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        self.jp_label = QLabel(self)
        self.jp_label.setWordWrap(True)
        self.jp_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #f5f3ff;")

        self.sub_label = QLabel(self)
        self.sub_label.setWordWrap(True)
        self.sub_label.setStyleSheet("font-size: 11px; color: #c4b5fd; font-style: italic;")

        layout.addWidget(self.jp_label)
        layout.addWidget(self.sub_label)

        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide)

    def show_message(self, jp: str, sub: str, flag: str = "🇮🇩", duration_ms: int = 8000):
        self.jp_label.setText(jp)
        self.sub_label.setText(f"{flag} {sub}")
        self.show()
        self.hide_timer.stop()
        if duration_ms > 0:
            self.hide_timer.start(duration_ms)


class FloatingMascot(QWidget):
    """Frameless, transparent desktop mascot widget with drag-and-drop & animated GIF."""
    poke_triggered = pyqtSignal()
    chat_requested = pyqtSignal()
    hide_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.drag_position = QPoint()
        self.is_dragging = False

        # Configure frameless & transparent overlay
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.SubWindow
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.init_ui()
        self.restore_position()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 1. Speech bubble
        self.speech_bubble = SpeechBubble(self)
        self.speech_bubble.setMaximumWidth(280)
        self.speech_bubble.hide()
        layout.addWidget(self.speech_bubble, alignment=Qt.AlignmentFlag.AlignCenter)

        # 2. Animated Herta GIF label
        self.avatar_label = QLabel(self)
        self.avatar_label.setFixedSize(160, 160)
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_label.setCursor(Qt.CursorShape.PointingHandCursor)

        if os.path.exists(HERTA_GIF_PATH):
            self.movie = QMovie(HERTA_GIF_PATH)
            self.movie.setScaledSize(QSize(150, 150))
            self.avatar_label.setMovie(self.movie)
            self.movie.start()
        elif os.path.exists(HERTA_LARGE_ICON):
            pix = QPixmap(HERTA_LARGE_ICON).scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.avatar_label.setPixmap(pix)

        layout.addWidget(self.avatar_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # 3. Mini action toolbar
        self.toolbar = QFrame(self)
        self.toolbar.setStyleSheet("""
            QFrame {
                background-color: rgba(18, 18, 28, 200);
                border: 1px solid rgba(138, 92, 246, 120);
                border-radius: 12px;
                padding: 2px 6px;
            }
            QPushButton {
                background: transparent;
                border: none;
                color: #e2e8f0;
                font-size: 13px;
                padding: 3px 6px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: rgba(139, 92, 246, 100);
            }
        """)
        tb_layout = QHBoxLayout(self.toolbar)
        tb_layout.setContentsMargins(4, 2, 4, 2)
        tb_layout.setSpacing(4)

        btn_chat = QPushButton("💬", self.toolbar)
        btn_chat.setToolTip("Open Live Chat Window")
        btn_chat.clicked.connect(self.chat_requested.emit)

        btn_poke = QPushButton("✨", self.toolbar)
        btn_poke.setToolTip("Poke / Interact with Madam Herta")
        btn_poke.clicked.connect(self.poke_triggered.emit)

        btn_hide = QPushButton("⬇️", self.toolbar)
        btn_hide.setToolTip("Hide Mascot to System Tray")
        btn_hide.clicked.connect(self.hide_requested.emit)

        tb_layout.addWidget(btn_chat)
        tb_layout.addWidget(btn_poke)
        tb_layout.addWidget(btn_hide)

        layout.addWidget(self.toolbar, alignment=Qt.AlignmentFlag.AlignCenter)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.is_dragging = False
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            new_pos = event.globalPosition().toPoint() - self.drag_position
            self.move(new_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.is_dragging:
                # User clicked (poked) Madam Herta without dragging
                self.poke_triggered.emit()
            else:
                self.save_position()
            event.accept()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1e1e2e;
                color: #f8fafc;
                border: 1px solid #7c3aed;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 18px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #7c3aed;
            }
        """)
        act_chat = menu.addAction("💬 Live Chat Window")
        act_poke = menu.addAction("✨ Poke Madam Herta")
        menu.addSeparator()
        act_hide = menu.addAction("⬇️ Minimize to System Tray")

        action = menu.exec(event.globalPos())
        if action == act_chat:
            self.chat_requested.emit()
        elif action == act_poke:
            self.poke_triggered.emit()
        elif action == act_hide:
            self.hide_requested.emit()

    def save_position(self):
        cfg = load_config()
        cfg["mascot_x"] = self.x()
        cfg["mascot_y"] = self.y()
        save_config(cfg)

    def restore_position(self):
        cfg = load_config()
        screen = QApplication.primaryScreen().geometry()
        default_x = screen.width() - 320
        default_y = screen.height() - 380
        x = cfg.get("mascot_x", default_x)
        y = cfg.get("mascot_y", default_y)
        self.move(x, y)


class ChatDialog(QDialog):
    """Modern translucent glassmorphism Live Chat Window with Madam Herta."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Madam Herta - Live Chat")
        self.resize(460, 520)
        self.conversation_history = []
        self.speech_thread = None
        self.chat_thread = None

        if os.path.exists(HERTA_ICON_PATH):
            self.setWindowIcon(QIcon(HERTA_ICON_PATH))

        self.setStyleSheet("""
            QDialog {
                background-color: #161622;
                color: #f1f5f9;
            }
            QScrollArea {
                border: 1px solid #332d4b;
                border-radius: 10px;
                background-color: #1a1a2e;
            }
            QLineEdit {
                background-color: #24243e;
                border: 1px solid #5b21b6;
                border-radius: 8px;
                padding: 8px 12px;
                color: #ffffff;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #8b5cf6;
            }
            QPushButton {
                background-color: #7c3aed;
                border: none;
                border-radius: 8px;
                color: #ffffff;
                font-weight: bold;
                padding: 8px 14px;
            }
            QPushButton:hover {
                background-color: #6d28d9;
            }
            QPushButton#btn_mic {
                background-color: #4338ca;
            }
            QPushButton#btn_mic:hover {
                background-color: #3730a3;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Chat history container
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.history_widget = QWidget()
        self.history_layout = QVBoxLayout(self.history_widget)
        self.history_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.history_layout.setSpacing(10)
        self.scroll_area.setWidget(self.history_widget)
        layout.addWidget(self.scroll_area)

        # Status label
        self.status_label = QLabel("✨ Ready to converse with Madam Herta", self)
        self.status_label.setStyleSheet("color: #a78bfa; font-size: 11px;")
        layout.addWidget(self.status_label)

        # Input row
        input_row = QHBoxLayout()
        self.input_field = QLineEdit(self)
        self.input_field.setPlaceholderText("Type a message or press Enter to speak...")
        self.input_field.returnPressed.connect(self.on_send_text)

        self.btn_send = QPushButton("Send", self)
        self.btn_send.clicked.connect(self.on_send_text)

        self.btn_mic = QPushButton("🎤 Mic", self)
        self.btn_mic.setObjectName("btn_mic")
        self.btn_mic.clicked.connect(self.on_voice_input)

        input_row.addWidget(self.input_field)
        input_row.addWidget(self.btn_send)
        input_row.addWidget(self.btn_mic)
        layout.addLayout(input_row)

        self.add_initial_greeting()

    def add_bubble(self, sender: str, text: str, sub: str = "", flag: str = ""):
        bubble = QFrame(self.history_widget)
        is_user = sender != "Madam Herta"
        bg = "#2e1065" if not is_user else "#1e293b"
        border = "#7c3aed" if not is_user else "#475569"

        bubble.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 10px;
                padding: 8px 12px;
            }}
            QLabel {{
                color: #ffffff;
                background: transparent;
            }}
        """)
        b_layout = QVBoxLayout(bubble)
        b_layout.setContentsMargins(6, 4, 6, 4)
        b_layout.setSpacing(2)

        lbl_sender = QLabel(f"<b>{sender}</b>", bubble)
        lbl_sender.setStyleSheet("color: #c084fc; font-size: 11px;")
        b_layout.addWidget(lbl_sender)

        lbl_main = QLabel(text, bubble)
        lbl_main.setWordWrap(True)
        lbl_main.setStyleSheet("color: #f8fafc; font-size: 13px;")
        b_layout.addWidget(lbl_main)

        if sub:
            lbl_sub = QLabel(f"{flag} {sub}", bubble)
            lbl_sub.setWordWrap(True)
            lbl_sub.setStyleSheet("color: #cbd5e1; font-size: 11px; font-style: italic;")
            b_layout.addWidget(lbl_sub)

        self.history_layout.addWidget(bubble)
        QTimer.singleShot(50, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))

    def add_initial_greeting(self):
        cfg = load_config()
        partner = cfg.get("partner_name", "あなた")
        romance_mode = cfg.get("romance_mode", True)
        romance_style = cfg.get("romance_address_style", "sweet_wife")
        sub_lang = cfg.get("subtitle_language", "id")

        if romance_mode:
            if romance_style == "yandere":
                jp = "クルクル〜クルリン…ふふっ、やっと来てくれたのね、あなた…♡ ずっと待ってたのよ…？"
                sub = "Kuru kuru~ Kururin... Fufu, you've finally come, darling...♡ I've been waiting for you forever, you know...?" if sub_lang == "en" else "Kuru kuru~ Kururin... Fufu, akhirnya kamu datang juga, sayangku...♡ Dari tadi nungguin kamu tahu...?"
            else:
                jp = "クルクル〜クルリン！ねえ、あなた…今日も会えて嬉しいわよ。今日は何をして過ごす？"
                sub = "Kuru kuru~ Kururin! Hey darling... I'm so glad to see you today. What shall we do together?" if sub_lang == "en" else "Kuru kuru~ Kururin! Hei sayangku... senang bisa ketemu kamu lagi hari ini. Hari ini kita mau ngapain?"
        else:
            jp = f"クルクル〜クルリン！こんにちは、{partner}！マダム・ヘルタよ。今日はどんな研究をするの？"
            sub = f"Kuru kuru~ Kururin! Hello, {partner}! Madam Herta here. What research are we tackling today?" if sub_lang == "en" else f"Kuru kuru~ Kururin! Halo, {partner}! Madam Herta di sini. Hari ini mau teliti apa?"

        flag = "🇬🇧" if sub_lang == "en" else "🇮🇩"
        self.add_bubble("Madam Herta", jp, sub, flag)
        self.conversation_history.append({"role": "model", "text": f"JP: {jp}\nSUB: {sub}"})

    def on_send_text(self):
        text = self.input_field.text().strip()
        if not text:
            return
        self.input_field.clear()
        self.send_to_herta(text, is_voice=False)

    def on_voice_input(self):
        self.status_label.setText("🎙️ Listening... Please speak into your microphone.")
        self.btn_mic.setEnabled(False)
        self.btn_send.setEnabled(False)
        self.send_to_herta("", is_voice=True)

    def send_to_herta(self, user_text: str, is_voice: bool):
        cfg = load_config()
        self.status_label.setText("⏳ Madam Herta is thinking...")
        self.btn_send.setEnabled(False)
        self.btn_mic.setEnabled(False)

        self.chat_thread = ChatWorker(user_text, is_voice, cfg, self.conversation_history)
        self.chat_thread.reply_ready.connect(self.on_reply_ready)
        self.chat_thread.error_occurred.connect(self.on_chat_error)
        self.chat_thread.start()

    def on_reply_ready(self, user_text: str, reply_jp: str, reply_sub: str):
        cfg = load_config()
        partner = cfg.get("partner_name", "あなた")
        sub_lang = cfg.get("subtitle_language", "id")
        rvc_enabled = cfg.get("rvc_enabled", True)
        flag = "🇬🇧" if sub_lang == "en" else "🇮🇩"

        self.add_bubble(partner, user_text)
        self.add_bubble("Madam Herta", reply_jp, reply_sub, flag)

        self.conversation_history.append({"role": "user", "text": user_text})
        self.conversation_history.append({"role": "model", "text": f"JP: {reply_jp}\nSUB: {reply_sub}"})

        self.status_label.setText("🔊 Madam Herta is speaking...")
        self.speech_thread = SpeechWorker(reply_jp, rvc_enabled=rvc_enabled)
        self.speech_thread.finished_speaking.connect(lambda: self.status_label.setText("✨ Ready"))
        self.speech_thread.start()

        self.btn_send.setEnabled(True)
        self.btn_mic.setEnabled(True)

    def on_chat_error(self, err_msg: str):
        self.status_label.setText(f"⚠️ {err_msg}")
        self.btn_send.setEnabled(True)
        self.btn_mic.setEnabled(True)


class HertaTrayApp(QSystemTrayIcon):
    """System Tray controller managing the Mascot and desktop services."""

    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app

        icon = QIcon(HERTA_ICON_PATH) if os.path.exists(HERTA_ICON_PATH) else QIcon()
        self.setIcon(icon)
        self.setToolTip("Madam Herta (ヘルタ) - AI Assistant")

        self.mascot = FloatingMascot()
        self.chat_dialog = ChatDialog()
        self.companion_thread = CompanionWorker()

        self.init_menu()
        self.connect_signals()

        self.show()
        self.mascot.show()
        self.companion_thread.start()

    def init_menu(self):
        self.menu = QMenu()
        self.menu.setStyleSheet("""
            QMenu {
                background-color: #1e1e2e;
                color: #f8fafc;
                border: 1px solid #7c3aed;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 18px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #7c3aed;
            }
        """)

        # 1. Mascot visibility toggle
        self.act_mascot = QAction("👁️ Hide Desktop Mascot", self)
        self.act_mascot.triggered.connect(self.toggle_mascot)
        self.menu.addAction(self.act_mascot)

        # 2. Live Chat Dialog
        self.act_chat = QAction("💬 Open Live Chat", self)
        self.act_chat.triggered.connect(self.open_chat)
        self.menu.addAction(self.act_chat)

        # 3. Nudge
        self.act_nudge = QAction("🔮 Nudge Herta (Ask to Speak)", self)
        self.act_nudge.triggered.connect(self.trigger_nudge)
        self.menu.addAction(self.act_nudge)

        self.menu.addSeparator()

        # 4. Romance Style Submenu
        cfg = load_config()
        self.style_menu = self.menu.addMenu("🎭 Romance Style")
        self.style_group = QActionGroup(self)
        self.act_sweet = QAction("Sweet Wife (Tsundere)", self, checkable=True)
        self.act_yandere = QAction("Yandere (Possessive)", self, checkable=True)
        self.style_group.addAction(self.act_sweet)
        self.style_group.addAction(self.act_yandere)
        self.style_menu.addAction(self.act_sweet)
        self.style_menu.addAction(self.act_yandere)

        current_style = cfg.get("romance_address_style", "sweet_wife")
        if current_style == "yandere":
            self.act_yandere.setChecked(True)
        else:
            self.act_sweet.setChecked(True)

        self.act_sweet.triggered.connect(lambda: self.set_romance_style("sweet_wife"))
        self.act_yandere.triggered.connect(lambda: self.set_romance_style("yandere"))

        # 5. Language Submenu
        self.lang_menu = self.menu.addMenu("🌐 Subtitle Language")
        self.lang_group = QActionGroup(self)
        self.act_lang_id = QAction("Bahasa Indonesia 🇮🇩", self, checkable=True)
        self.act_lang_en = QAction("English 🇬🇧", self, checkable=True)
        self.lang_group.addAction(self.act_lang_id)
        self.lang_group.addAction(self.act_lang_en)
        self.lang_menu.addAction(self.act_lang_id)
        self.lang_menu.addAction(self.act_lang_en)

        current_lang = cfg.get("subtitle_language", "id")
        if current_lang == "en":
            self.act_lang_en.setChecked(True)
        else:
            self.act_lang_id.setChecked(True)

        self.act_lang_id.triggered.connect(lambda: self.set_subtitle_lang("id"))
        self.act_lang_en.triggered.connect(lambda: self.set_subtitle_lang("en"))

        # 6. RVC Toggle
        self.act_rvc = QAction("✨ Voice Conversion (RVC v2)", self, checkable=True)
        self.act_rvc.setChecked(cfg.get("rvc_enabled", True))
        self.act_rvc.triggered.connect(self.toggle_rvc)
        self.menu.addAction(self.act_rvc)

        self.menu.addSeparator()

        # 7. Quit
        self.act_quit = QAction("❌ Exit Madam Herta", self)
        self.act_quit.triggered.connect(self.quit_app)
        self.menu.addAction(self.act_quit)

        self.setContextMenu(self.menu)

    def connect_signals(self):
        self.activated.connect(self.on_tray_activated)
        self.mascot.poke_triggered.connect(self.on_poke_mascot)
        self.mascot.chat_requested.connect(self.open_chat)
        self.mascot.hide_requested.connect(self.hide_mascot)
        self.companion_thread.moment_triggered.connect(self.on_companion_moment)

    def on_tray_activated(self, reason):
        if reason in [QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick]:
            self.toggle_mascot()

    def toggle_mascot(self):
        if self.mascot.isVisible():
            self.hide_mascot()
        else:
            self.show_mascot()

    def show_mascot(self):
        self.mascot.show()
        self.act_mascot.setText("👁️ Hide Desktop Mascot")

    def hide_mascot(self):
        self.mascot.hide()
        self.act_mascot.setText("👁️ Show Desktop Mascot")

    def open_chat(self):
        self.chat_dialog.show()
        self.chat_dialog.raise_()
        self.chat_dialog.activateWindow()

    def trigger_nudge(self):
        cfg = load_config()
        partner = cfg.get("partner_name", "あなた")
        romance_style = cfg.get("romance_address_style", "sweet_wife")
        sub_lang = cfg.get("subtitle_language", "id")
        rvc_enabled = cfg.get("rvc_enabled", True)

        if romance_style == "yandere":
            y_moments = [m for m in BUILTIN_MOMENTS if m.get("category") == "yandere"]
            chosen = random.choice(y_moments if y_moments else BUILTIN_MOMENTS)
        else:
            s_moments = [m for m in BUILTIN_MOMENTS if m.get("category") != "yandere"]
            chosen = random.choice(s_moments if s_moments else BUILTIN_MOMENTS)

        jp = chosen["jp"].replace("あなた", partner)
        if sub_lang == "en":
            flag = "🇬🇧"
            sub = chosen.get("en", chosen.get("id")).replace("darling", "darling" if partner == "あなた" else partner)
        else:
            flag = "🇮🇩"
            sub = chosen.get("id", chosen.get("en")).replace("sayang", "sayang" if partner == "あなた" else partner)

        self.on_companion_moment(jp, sub, flag)
        threading.Thread(target=speak, args=(jp,), kwargs={"rvc_enabled": rvc_enabled}, daemon=True).start()

    def on_poke_mascot(self):
        cfg = load_config()
        partner = cfg.get("partner_name", "あなた")
        romance_style = cfg.get("romance_address_style", "sweet_wife")
        sub_lang = cfg.get("subtitle_language", "id")
        rvc_enabled = cfg.get("rvc_enabled", True)

        if romance_style == "yandere":
            pokes = [
                ("ねえ、あなた…触ってくれて嬉しいわ♡ でも…私以外の誰にも触れちゃダメよ？",
                 "Hei sayang... senang deh kamu sentuh♡ Tapi... kamu nggak boleh nyentuh siapapun selain aku ya?",
                 "Hey darling... I'm happy you touched me♡ But... don't you ever dare touch anyone else, okay?"),
                ("ふふっ、そんなにつつかないで…抱きしめたくなっちゃうでしょう？♡",
                 "Fufu, jangan dicolek terus dong... nanti aku jadi pengen meluk kamu terus kan?♡",
                 "Fufu, don't poke me so much... you'll just make me want to hold you tight forever♡")
            ]
        else:
            pokes = [
                ("クルクル〜クルリン！ちょっと、つつかないでよ！研究の邪魔なんだから！",
                 "Kuru kuru~ Kururin! Hei, jangan dicolek-colek dong! Ganggu riset tahu!",
                 "Kuru kuru~ Kururin! Hey, don't poke me! You're interrupting my research!"),
                ("ふふっ、何？私のこと構ってほしいの？…しょうがないわね〜♡",
                 "Fufu, apa sih? Mau kuperhatiin ya? ...Dasar manja deh~♡",
                 "Fufu, what is it? Do you want my attention? ...You're so spoiled~♡")
            ]

        chosen_poke = random.choice(pokes)
        jp = chosen_poke[0]
        if sub_lang == "en":
            flag = "🇬🇧"
            sub = chosen_poke[2]
        else:
            flag = "🇮🇩"
            sub = chosen_poke[1]

        self.mascot.speech_bubble.show_message(jp, sub, flag, duration_ms=6000)
        threading.Thread(target=speak, args=(jp,), kwargs={"rvc_enabled": rvc_enabled}, daemon=True).start()

    def on_companion_moment(self, jp: str, sub: str, flag: str):
        if self.mascot.isVisible():
            self.mascot.speech_bubble.show_message(jp, sub, flag, duration_ms=8000)

    def set_romance_style(self, style: str):
        cfg = load_config()
        cfg["romance_address_style"] = style
        save_config(cfg)

    def set_subtitle_lang(self, lang: str):
        cfg = load_config()
        cfg["subtitle_language"] = lang
        save_config(cfg)

    def toggle_rvc(self):
        cfg = load_config()
        cfg["rvc_enabled"] = self.act_rvc.isChecked()
        save_config(cfg)

    def quit_app(self):
        self.mascot.save_position()
        self.app.quit()


def run_gui():
    """Launch the Madam Herta Desktop Mascot & System Tray Application."""
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep running in system tray when mascot is hidden

    tray = HertaTrayApp(app)
    sys.exit(app.exec())
