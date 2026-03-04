"""Desktop GUI for agent-cli-to-api gateway.

Launch via::

    agent-cli-to-api-desktop          # installed entry-point
    python -m codex_gateway.desktop   # module invocation
    uv run agent-cli-to-api-desktop   # with uv
"""

from __future__ import annotations

import sys


def main() -> None:
    """Entry-point for the desktop application."""
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        print(
            "Error: PySide6 is required for the desktop GUI.\n"
            "Install it with:\n"
            "  uv sync --extra desktop\n"
            "  # or\n"
            "  pip install 'agent-cli-to-api[desktop]'",
            file=sys.stderr,
        )
        raise SystemExit(1)

    from .main_window import MainWindow
    from .styles import DARK_THEME

    app = QApplication(sys.argv)
    app.setApplicationName("Agent CLI to API")
    app.setOrganizationName("agent-cli-to-api")
    app.setApplicationVersion("0.2.2")
    app.setStyleSheet(DARK_THEME)

    # Prevent the app from quitting when the window is hidden to tray.
    app.setQuitOnLastWindowClosed(False)

    window = MainWindow()
    window.setWindowIcon(window._make_icon())
    window.show()

    sys.exit(app.exec())
