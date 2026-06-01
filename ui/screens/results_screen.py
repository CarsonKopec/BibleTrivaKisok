"""Post-game summary: score, percentage, replay/return options."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

from game.scoreboard import save_score


class ResultsScreen(QWidget):
    again_requested = Signal()
    home_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ResultsScreen")
        self.last_nickname: str = ""

        outer = QVBoxLayout(self)
        outer.setContentsMargins(40, 40, 40, 40)

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(56, 48, 56, 48)
        card_layout.setSpacing(12)

        title = QLabel("GAME  OVER")
        title.setObjectName("Title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.nickname_label = QLabel("")
        self.nickname_label.setObjectName("Subtitle")
        self.nickname_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        score_caption = QLabel("FINAL SCORE")
        score_caption.setObjectName("FieldLabel")
        score_caption.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.score_label = QLabel("0")
        self.score_label.setObjectName("BigScore")
        self.score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.detail_label = QLabel("")
        self.detail_label.setObjectName("Subtitle")
        self.detail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.percent_label = QLabel("")
        self.percent_label.setObjectName("FieldLabel")
        self.percent_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        again = QPushButton("Begin Again")
        again.setObjectName("PrimaryButton")
        again.setMinimumHeight(54)
        again.setCursor(Qt.CursorShape.PointingHandCursor)

        home = QPushButton("Return to Menu")
        home.setObjectName("SecondaryButton")
        home.setMinimumHeight(48)
        home.setCursor(Qt.CursorShape.PointingHandCursor)

        again.clicked.connect(self.again_requested.emit)
        home.clicked.connect(self.home_requested.emit)

        card_layout.addWidget(title)
        card_layout.addWidget(self.nickname_label)
        card_layout.addSpacing(8)
        card_layout.addWidget(score_caption)
        card_layout.addWidget(self.score_label)
        card_layout.addWidget(self.percent_label)
        card_layout.addWidget(self.detail_label)
        card_layout.addSpacing(20)
        card_layout.addWidget(again)
        card_layout.addWidget(home)

        center = QHBoxLayout()
        center.addStretch(1)
        center.addWidget(card, 0)
        center.addStretch(1)

        outer.addStretch(1)
        outer.addLayout(center)
        outer.addStretch(1)

    def set_result(self, nickname: str, score: int, correct: int, answered: int) -> None:
        self.last_nickname = nickname
        self.nickname_label.setText(nickname)
        self.score_label.setText(str(score))
        pct = (correct / answered * 100.0) if answered else 0.0
        self.percent_label.setText(f"{pct:.0f}% CORRECT")
        self.detail_label.setText(f"{correct} of {answered} questions answered correctly")
        try:
            save_score(nickname, score, answered)
        except Exception as exc:  # noqa: BLE001 — DB errors shouldn't crash UI
            print(f"[Bible Trivia] Failed to save score: {exc}")
