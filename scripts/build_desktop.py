#!/usr/bin/env python3
"""Build a standalone desktop executable using PyInstaller.

Usage
-----
    uv run --extra build python scripts/build_desktop.py

The resulting binary will be in ``dist/``.

Platform notes
--------------
- **macOS**: produces a .app bundle (add ``--windowed`` by default).
- **Windows**: produces a .exe (``--windowed`` hides the console).
- **Linux**: produces a single-file ELF binary.

For a proper macOS .icns or Windows .ico, place the icon file next to this
script and pass ``--icon`` to PyInstaller (see below).
"""

from __future__ import annotations

import platform
import subprocess
import sys


def build() -> None:
    app_name = "Agent-CLI-to-API"

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name",
        app_name,
        "--onefile",
        "--windowed",
        "--noconfirm",
        # Collect the entire codex_gateway package so server.py / config.py
        # and all provider modules are available at runtime.
        "--collect-all",
        "codex_gateway",
        # Hidden imports that PyInstaller may not auto-detect.
        "--hidden-import",
        "uvicorn.logging",
        "--hidden-import",
        "uvicorn.loops.auto",
        "--hidden-import",
        "uvicorn.protocols.http.auto",
        "--hidden-import",
        "uvicorn.protocols.websockets.auto",
        "--hidden-import",
        "uvicorn.lifespan.on",
        # Entry script.
        "codex_gateway/desktop/__init__.py",
    ]

    print(f"[build] platform={platform.system()} python={sys.version}")
    print(f"[build] running: {' '.join(cmd)}")
    subprocess.check_call(cmd)
    print(f"[build] done — check dist/{app_name}")


if __name__ == "__main__":
    build()
