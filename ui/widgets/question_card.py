"""Parchment card that displays the current question and its metadata."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class QuestionCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("QuestionCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 28, 36, 28)
        layout.setSpacing(10)

        self.meta = QLabel("")
        self.meta.setObjectName("QuestionMeta")
        self.meta.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.text = QLabel("")
        self.text.setObjectName("QuestionText")
        self.text.setWordWrap(True)
        self.text.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addStretch(1)
        layout.addWidget(self.meta)
        layout.addWidget(self.text)
        layout.addStretch(1)

    def set_question(self, text: str, category: str | None, difficulty: str | None) -> None:
        parts = [p for p in (category, difficulty) if p]
        self.meta.setText("  ·  ".join(parts).upper() if parts else "")
        self.text.setText(text)
