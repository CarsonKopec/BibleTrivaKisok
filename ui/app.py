"""Bootstrap the QApplication and load the parchment stylesheet."""
from __future__ import annotations

import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from config import STYLES_PATH


def build_app(argv: list[str] | None = None) -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName("Bible Trivia")
    app.setOrganizationName("BibleTriviaKiosk")
    app.setFont(QFont("Segoe UI", 11))
    if STYLES_PATH.exists():
        try:
            app.setStyleSheet(STYLES_PATH.read_text(encoding="utf-8"))
        except OSError as exc:
            print(f"[Bible Trivia] Failed to load stylesheet: {exc}")
    return app
