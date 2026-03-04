"""Background thread that runs the gateway server as a subprocess."""

from __future__ import annotations

import os
import signal
import subprocess
import sys

from PySide6.QtCore import QThread, Signal


class ServerThread(QThread):
    """Runs ``uvicorn codex_gateway.server:app`` in an isolated subprocess.

    Environment variables are configured from the GUI settings *before* the
    subprocess starts, so the ``config.py`` module-level initialisation picks
    them up cleanly.
    """

    log_message = Signal(str)
    server_started = Signal()
    server_stopped = Signal(int)
    server_error = Signal(str)

    def __init__(
        self,
        *,
        provider: str = "codex",
        host: str = "127.0.0.1",
        port: int = 8000,
        preset: str = "",
        token: str = "",
        log_mode: str = "qa",
        parent=None,
    ):
        super().__init__(parent)
        self.provider = provider
        self.host = host
        self.port = port
        self.preset = preset
        self.token = token
        self.log_mode = log_mode
        self._process: subprocess.Popen | None = None
        self._stop_requested = False

    # ── QThread entry point ──────────────────────────────

    def run(self) -> None:
        env = os.environ.copy()

        env["CODEX_PROVIDER"] = self.provider
        if self.preset:
            env["CODEX_PRESET"] = self.preset
        if self.token:
            env["CODEX_GATEWAY_TOKEN"] = self.token
        if self.log_mode:
            env["CODEX_LOG_MODE"] = self.log_mode

        # Disable rich / TTY-only formatting in the subprocess – we capture
        # plain text and display it in our own log viewer.
        env["CODEX_RICH_LOGS"] = "0"
        env["CODEX_LOG_RENDER_MARKDOWN"] = "0"
        env["CODEX_LOG_STREAM_INLINE"] = "0"
        env["CODEX_NO_DOTENV"] = "1"

        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "codex_gateway.server:app",
            "--host",
            self.host,
            "--port",
            str(self.port),
            "--log-level",
            "info",
        ]

        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
                text=True,
                bufsize=1,
            )

            self.server_started.emit()

            assert self._process.stdout is not None
            for line in iter(self._process.stdout.readline, ""):
                if not line:
                    break
                self.log_message.emit(line.rstrip("\n"))

            exit_code = self._process.wait()
            self.server_stopped.emit(0 if self._stop_requested else exit_code)

        except Exception as exc:
            self.server_error.emit(str(exc))

    # ── Public helpers ───────────────────────────────────

    def stop(self) -> None:
        """Request a graceful shutdown of the server subprocess."""
        self._stop_requested = True
        proc = self._process
        if proc is None or proc.poll() is not None:
            return
        # SIGINT triggers uvicorn's graceful shutdown handler.
        if sys.platform == "win32":
            proc.terminate()
        else:
            proc.send_signal(signal.SIGINT)
        try:
            proc.wait(timeout=6)
        except subprocess.TimeoutExpired:
            proc.kill()

    @property
    def is_running(self) -> bool:
        return self._process is not None and self._process.poll() is None
