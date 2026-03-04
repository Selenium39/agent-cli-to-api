"""Main application window for the Agent CLI to API desktop gateway."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QSettings, QSize, Qt
from PySide6.QtGui import (
    QAction,
    QCloseEvent,
    QColor,
    QFont,
    QIcon,
    QPainter,
    QPixmap,
)
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from .server_thread import ServerThread

_APP_VERSION = "0.2.2"
_MAX_LOG_LINES = 8000

_PROVIDERS = ["codex", "claude", "gemini", "cursor-agent", "auto"]
_PRESETS = [
    "(auto)",
    "codex-fast",
    "multi-fast",
    "autoglm-phone",
    "cursor-fast",
    "cursor-auto",
    "claude-oauth",
    "gemini-cloudcode",
]
_LOG_MODES = ["qa", "summary", "full"]


class MainWindow(QMainWindow):
    """Single-window desktop GUI for agent-cli-to-api."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Agent CLI to API Gateway")
        self.setMinimumSize(720, 560)
        self.resize(800, 620)

        self._server: ServerThread | None = None
        self._settings = QSettings("agent-cli-to-api", "desktop")
        self._is_quitting = False

        self._build_ui()
        self._build_tray()
        self._restore_settings()
        self._update_status("stopped")

    # ── UI construction ──────────────────────────────────

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(10)

        # ── Header ──
        header = QHBoxLayout()
        title = QLabel("\U0001f916  Agent CLI to API")
        title.setObjectName("title_label")
        version = QLabel(f"v{_APP_VERSION}")
        version.setObjectName("version_label")
        header.addWidget(title)
        header.addStretch()
        header.addWidget(version, alignment=Qt.AlignmentFlag.AlignBottom)
        root.addLayout(header)

        # ── Configuration card ──
        cfg_group = QGroupBox("Server Configuration")
        cfg_grid = QGridLayout(cfg_group)
        cfg_grid.setHorizontalSpacing(12)
        cfg_grid.setVerticalSpacing(8)

        # Row 0 – Provider / Preset
        cfg_grid.addWidget(QLabel("Provider"), 0, 0)
        self._provider_combo = QComboBox()
        self._provider_combo.addItems(_PROVIDERS)
        cfg_grid.addWidget(self._provider_combo, 0, 1)

        cfg_grid.addWidget(QLabel("Preset"), 0, 2)
        self._preset_combo = QComboBox()
        self._preset_combo.addItems(_PRESETS)
        cfg_grid.addWidget(self._preset_combo, 0, 3)

        # Row 1 – Host / Port
        cfg_grid.addWidget(QLabel("Host"), 1, 0)
        self._host_input = QLineEdit("127.0.0.1")
        cfg_grid.addWidget(self._host_input, 1, 1)

        cfg_grid.addWidget(QLabel("Port"), 1, 2)
        self._port_input = QSpinBox()
        self._port_input.setRange(1, 65535)
        self._port_input.setValue(8000)
        cfg_grid.addWidget(self._port_input, 1, 3)

        # Row 2 – Token / Log mode
        cfg_grid.addWidget(QLabel("Auth Token"), 2, 0)
        self._token_input = QLineEdit()
        self._token_input.setPlaceholderText("optional – leave blank for no auth")
        cfg_grid.addWidget(self._token_input, 2, 1)

        cfg_grid.addWidget(QLabel("Log Mode"), 2, 2)
        self._logmode_combo = QComboBox()
        self._logmode_combo.addItems(_LOG_MODES)
        cfg_grid.addWidget(self._logmode_combo, 2, 3)

        root.addWidget(cfg_group)

        # ── Controls row ──
        ctrl = QHBoxLayout()
        ctrl.setSpacing(12)

        self._start_btn = QPushButton("\u25b6  Start Server")
        self._start_btn.setFixedHeight(36)
        self._start_btn.clicked.connect(self._on_start)
        ctrl.addWidget(self._start_btn)

        self._stop_btn = QPushButton("\u25a0  Stop Server")
        self._stop_btn.setObjectName("stop_btn")
        self._stop_btn.setFixedHeight(36)
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._on_stop)
        ctrl.addWidget(self._stop_btn)

        self._status_label = QLabel()
        self._status_label.setObjectName("status_label")
        ctrl.addWidget(self._status_label, stretch=1)

        root.addLayout(ctrl)

        # ── Connection info row ──
        conn = QHBoxLayout()
        conn.setSpacing(8)
        conn.addWidget(QLabel("Base URL:"))
        self._url_label = QLabel()
        self._url_label.setObjectName("url_display")
        self._url_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        conn.addWidget(self._url_label, stretch=1)
        copy_btn = QPushButton("Copy")
        copy_btn.setObjectName("copy_btn")
        copy_btn.setFixedWidth(60)
        copy_btn.clicked.connect(self._on_copy_url)
        conn.addWidget(copy_btn)
        root.addLayout(conn)

        self._refresh_url_label()

        # ── Log viewer ──
        log_header = QHBoxLayout()
        log_header.addWidget(QLabel("Server Logs"))
        log_header.addStretch()
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("clear_btn")
        clear_btn.setFixedWidth(60)
        clear_btn.clicked.connect(self._on_clear_logs)
        log_header.addWidget(clear_btn)
        root.addLayout(log_header)

        self._log_viewer = QPlainTextEdit()
        self._log_viewer.setObjectName("log_viewer")
        self._log_viewer.setReadOnly(True)
        self._log_viewer.setFont(
            QFont(
                ["Cascadia Code", "SF Mono", "Menlo", "Consolas", "monospace"], 12
            )
        )
        root.addWidget(self._log_viewer, stretch=1)

        # Update URL when host/port change.
        self._host_input.textChanged.connect(self._refresh_url_label)
        self._port_input.valueChanged.connect(self._refresh_url_label)

    # ── System tray ──────────────────────────────────────

    def _build_tray(self) -> None:
        self._tray = QSystemTrayIcon(self._make_icon(), self)
        self._tray.setToolTip("Agent CLI to API Gateway")
        self._tray.activated.connect(self._on_tray_activated)

        menu = QMenu()
        show_action = QAction("Show Window", self)
        show_action.triggered.connect(self._show_window)
        menu.addAction(show_action)
        menu.addSeparator()

        self._tray_start = QAction("Start Server", self)
        self._tray_start.triggered.connect(self._on_start)
        menu.addAction(self._tray_start)

        self._tray_stop = QAction("Stop Server", self)
        self._tray_stop.setEnabled(False)
        self._tray_stop.triggered.connect(self._on_stop)
        menu.addAction(self._tray_stop)

        menu.addSeparator()
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self._on_quit)
        menu.addAction(quit_action)

        self._tray.setContextMenu(menu)
        self._tray.show()

    # ── Icon generation (no external files needed) ───────

    @staticmethod
    def _make_icon() -> QIcon:
        icon = QIcon()
        for sz in (16, 24, 32, 48, 64, 128):
            pm = QPixmap(QSize(sz, sz))
            pm.fill(Qt.GlobalColor.transparent)
            p = QPainter(pm)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            # Rounded-rect background
            p.setBrush(QColor("#7aa2f7"))
            p.setPen(Qt.PenStyle.NoPen)
            r = sz * 0.18
            p.drawRoundedRect(1, 1, sz - 2, sz - 2, r, r)
            # "API" text
            p.setPen(QColor("#1a1b26"))
            font = QFont("Arial", max(sz // 4, 6), QFont.Weight.Bold)
            p.setFont(font)
            p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, "API")
            p.end()
            icon.addPixmap(pm)
        return icon

    # ── Server lifecycle ─────────────────────────────────

    def _on_start(self) -> None:
        if self._server and self._server.is_running:
            return

        preset = self._preset_combo.currentText()
        if preset == "(auto)":
            preset = ""

        self._server = ServerThread(
            provider=self._provider_combo.currentText(),
            host=self._host_input.text().strip() or "127.0.0.1",
            port=self._port_input.value(),
            preset=preset,
            token=self._token_input.text().strip(),
            log_mode=self._logmode_combo.currentText(),
            parent=self,
        )
        self._server.log_message.connect(self._append_log)
        self._server.server_started.connect(lambda: self._update_status("running"))
        self._server.server_stopped.connect(self._on_server_stopped)
        self._server.server_error.connect(self._on_server_error)
        self._server.start()

        self._update_status("starting")
        self._set_config_enabled(False)

    def _on_stop(self) -> None:
        if self._server:
            self._update_status("stopping")
            self._server.stop()

    def _on_server_stopped(self, code: int) -> None:
        self._update_status("stopped")
        self._set_config_enabled(True)
        if code != 0:
            self._append_log(f"[desktop] server exited with code {code}")

    def _on_server_error(self, msg: str) -> None:
        self._update_status("stopped")
        self._set_config_enabled(True)
        self._append_log(f"[desktop] ERROR: {msg}")

    # ── UI helpers ───────────────────────────────────────

    def _update_status(self, state: str) -> None:
        colors = {
            "stopped": ("#f7768e", "\u25cf  Stopped"),
            "starting": ("#e0af68", "\u25cf  Starting\u2026"),
            "running": ("#9ece6a", "\u25cf  Running"),
            "stopping": ("#e0af68", "\u25cf  Stopping\u2026"),
        }
        color, text = colors.get(state, ("#565f89", "\u25cf  Unknown"))
        self._status_label.setText(text)
        self._status_label.setStyleSheet(f"color: {color};")

        is_running = state in ("running", "starting", "stopping")
        self._start_btn.setEnabled(not is_running)
        self._stop_btn.setEnabled(state == "running")
        self._tray_start.setEnabled(not is_running)
        self._tray_stop.setEnabled(state == "running")

        self._tray.setToolTip(f"Agent CLI to API — {text}")

    def _set_config_enabled(self, enabled: bool) -> None:
        for w in (
            self._provider_combo,
            self._preset_combo,
            self._host_input,
            self._port_input,
            self._token_input,
            self._logmode_combo,
        ):
            w.setEnabled(enabled)

    def _refresh_url_label(self) -> None:
        host = self._host_input.text().strip() or "127.0.0.1"
        port = self._port_input.value()
        display_host = "127.0.0.1" if host == "0.0.0.0" else host
        self._url_label.setText(f"http://{display_host}:{port}/v1")

    def _append_log(self, line: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        self._log_viewer.appendPlainText(f"[{ts}] {line}")
        # Trim old lines to avoid unbounded memory growth.
        if self._log_viewer.blockCount() > _MAX_LOG_LINES:
            cursor = self._log_viewer.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.movePosition(
                cursor.MoveOperation.Down,
                cursor.MoveMode.KeepAnchor,
                self._log_viewer.blockCount() - _MAX_LOG_LINES,
            )
            cursor.removeSelectedText()
            cursor.deleteChar()  # trailing newline

    def _on_clear_logs(self) -> None:
        self._log_viewer.clear()

    def _on_copy_url(self) -> None:
        text = self._url_label.text()
        cb = QApplication.clipboard()
        if cb:
            cb.setText(text)
        self._tray.showMessage(
            "Copied", text, QSystemTrayIcon.MessageIcon.Information, 1500
        )

    # ── Tray interaction ─────────────────────────────────

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._show_window()

    def _show_window(self) -> None:
        self.showNormal()
        self.activateWindow()
        self.raise_()

    # ── Window close / quit logic ────────────────────────

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        if self._is_quitting:
            self._save_settings()
            event.accept()
            return
        # If the server is running, minimize to tray instead of quitting.
        if self._server and self._server.is_running:
            event.ignore()
            self.hide()
            self._tray.showMessage(
                "Still running",
                "Gateway is running in the background.\nRight-click the tray icon to quit.",
                QSystemTrayIcon.MessageIcon.Information,
                2000,
            )
        else:
            self._save_settings()
            event.accept()

    def _on_quit(self) -> None:
        self._is_quitting = True
        if self._server and self._server.is_running:
            self._server.server_stopped.connect(self._finish_quit)
            self._server.stop()
            self._update_status("stopping")
        else:
            self._finish_quit()

    def _finish_quit(self, _code: int = 0) -> None:
        self._save_settings()
        self._tray.hide()
        QApplication.quit()

    # ── Settings persistence ─────────────────────────────

    def _save_settings(self) -> None:
        s = self._settings
        s.setValue("provider", self._provider_combo.currentText())
        s.setValue("preset", self._preset_combo.currentText())
        s.setValue("host", self._host_input.text())
        s.setValue("port", self._port_input.value())
        s.setValue("token", self._token_input.text())
        s.setValue("log_mode", self._logmode_combo.currentText())
        s.setValue("geometry", self.saveGeometry())

    def _restore_settings(self) -> None:
        s = self._settings

        provider = s.value("provider", "codex")
        idx = self._provider_combo.findText(provider)
        if idx >= 0:
            self._provider_combo.setCurrentIndex(idx)

        preset = s.value("preset", "(auto)")
        idx = self._preset_combo.findText(preset)
        if idx >= 0:
            self._preset_combo.setCurrentIndex(idx)

        self._host_input.setText(s.value("host", "127.0.0.1"))
        self._port_input.setValue(int(s.value("port", 8000)))
        self._token_input.setText(s.value("token", ""))

        log_mode = s.value("log_mode", "qa")
        idx = self._logmode_combo.findText(log_mode)
        if idx >= 0:
            self._logmode_combo.setCurrentIndex(idx)

        geom = s.value("geometry")
        if geom:
            self.restoreGeometry(geom)
