"""HDMI play page: spectator view of the current game.

Subscribes to the same GameEngine as the player's GameScreen. Read-only —
audience can see the question, options, lives, score, streak, and timer
without interacting.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QProgressBar, QVBoxLayout, QWidget,
)

from config import QUESTION_TIMEOUT_SEC, STARTING_LIVES
from db.models import Question
from game.engine import GameEngine
from ui.widgets.answer_button import AnswerButton
from ui.widgets.question_card import QuestionCard


class PlayPage(QWidget):
    """Mirrors engine state with audience-readable sizing."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SpectatorPlay")
        self._engine: GameEngine | None = None
        self._nickname: str = ""

        banner = QFrame()
        banner.setObjectName("SpectatorBanner")
        banner_layout = QHBoxLayout(banner)
        banner_layout.setContentsMargins(28, 14, 28, 14)

        self.player_label = QLabel("")
        self.player_label.setObjectName("SpectatorPlayer")
        self.streak_label = QLabel("")
        self.streak_label.setObjectName("SpectatorStreak")
        self.score_label = QLabel("0")
        self.score_label.setObjectName("SpectatorScore")

        banner_layout.addWidget(self.player_label)
        banner_layout.addStretch(1)
        banner_layout.addWidget(self.streak_label)
        banner_layout.addStretch(1)
        banner_layout.addWidget(self.score_label)

        self.lives_label = QLabel("")
        self.lives_label.setObjectName("SpectatorLives")
        self.lives_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.card = QuestionCard()
        self.card.setObjectName("SpectatorQuestionCard")

        self.timer_bar = QProgressBar()
        self.timer_bar.setObjectName("SpectatorTimer")
        self.timer_bar.setRange(0, QUESTION_TIMEOUT_SEC)
        self.timer_bar.setValue(QUESTION_TIMEOUT_SEC)
        self.timer_bar.setFormat("%v s")
        self.timer_bar.setTextVisible(True)

        grid = QGridLayout()
        grid.setSpacing(20)
        self.buttons: dict[str, AnswerButton] = {}
        for i, letter in enumerate(("A", "B", "C", "D")):
            btn = AnswerButton(letter)
            btn.setEnabled(False)
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.setMinimumHeight(96)
            self.buttons[letter] = btn
            grid.addWidget(btn, i // 2, i % 2)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(56, 36, 56, 36)
        outer.setSpacing(20)
        outer.addWidget(banner)
        outer.addWidget(self.lives_label)
        outer.addWidget(self.card, 1)
        outer.addWidget(self.timer_bar)
        outer.addLayout(grid, 2)

    # Engine attach / detach
    def attach(self, engine: GameEngine, nickname: str) -> None:
        self.detach()
        self._engine = engine
        self._nickname = nickname
        self.player_label.setText(nickname.upper())

        engine.question_changed.connect(self._on_question)
        engine.score_changed.connect(self._on_score)
        engine.lives_changed.connect(self._on_lives)
        engine.streak_changed.connect(self._on_streak)
        engine.timer_tick.connect(self._on_tick)
        engine.answer_resolved.connect(self._on_answer)

        self._on_lives(STARTING_LIVES)
        self._on_score(0)
        self._on_streak(0)
        self._on_tick(QUESTION_TIMEOUT_SEC)
        for btn in self.buttons.values():
            btn.set_option("")

    def detach(self) -> None:
        if self._engine is None:
            return
        try:
            self._engine.question_changed.disconnect(self._on_question)
            self._engine.score_changed.disconnect(self._on_score)
            self._engine.lives_changed.disconnect(self._on_lives)
            self._engine.streak_changed.disconnect(self._on_streak)
            self._engine.timer_tick.disconnect(self._on_tick)
            self._engine.answer_resolved.disconnect(self._on_answer)
        except (RuntimeError, TypeError):
            pass
        self._engine = None
        self._nickname = ""

    # Engine slots
    def _on_question(self, q: Question) -> None:
        self.card.set_question(q.text, q.category, q.difficulty)
        for letter, btn in self.buttons.items():
            btn.set_option(q.options[letter])
            btn.setEnabled(False)

    def _on_score(self, score: int) -> None:
        self.score_label.setText(str(score))

    def _on_lives(self, lives: int) -> None:
        filled = "♥ " * lives
        empty = "♡ " * (STARTING_LIVES - lives)
        self.lives_label.setText((filled + empty).strip())

    def _on_streak(self, streak: int) -> None:
        self.streak_label.setText(f"STREAK  x{streak}" if streak >= 2 else "")

    def _on_tick(self, seconds: int) -> None:
        self.timer_bar.setValue(max(0, seconds))
        state = "critical" if seconds <= 3 else ""
        if self.timer_bar.property("state") != state:
            self.timer_bar.setProperty("state", state)
            self.timer_bar.style().unpolish(self.timer_bar)
            self.timer_bar.style().polish(self.timer_bar)

    def _on_answer(self, correct: bool, correct_letter: str) -> None:
        for letter, btn in self.buttons.items():
            if letter == correct_letter:
                btn.mark("correct")
            else:
                btn.mark("")
