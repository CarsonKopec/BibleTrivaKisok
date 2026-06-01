"""Active gameplay screen: question, lives, score, timer, answer buttons.

The GameEngine is injected by MainWindow so the SpectatorWindow can observe
the same instance.
"""
from __future__ import annotations

from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QProgressBar, QPushButton,
    QVBoxLayout, QWidget,
)

from config import QUESTION_TIMEOUT_SEC, STARTING_LIVES
from db.models import Question
from game.engine import GameEngine
from ui.widgets.answer_button import AnswerButton
from ui.widgets.question_card import QuestionCard


class GameScreen(QWidget):
    quit_requested = Signal()

    def __init__(self, engine: GameEngine, parent=None):
        super().__init__(parent)
        self.setObjectName("GameScreen")
        self._engine = engine
        self._last_pick: str | None = None

        top = QFrame()
        top.setObjectName("TopBar")
        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(22, 14, 22, 14)

        self.lives_label = QLabel()
        self.lives_label.setObjectName("LivesLabel")

        self.streak_label = QLabel("")
        self.streak_label.setObjectName("StreakLabel")

        self.score_label = QLabel("Score: 0")
        self.score_label.setObjectName("ScoreLabel")

        quit_btn = QPushButton("Quit")
        quit_btn.setObjectName("TertiaryButton")
        quit_btn.clicked.connect(self.quit_requested.emit)

        top_layout.addWidget(self.lives_label)
        top_layout.addStretch(1)
        top_layout.addWidget(self.streak_label)
        top_layout.addStretch(1)
        top_layout.addWidget(self.score_label)
        top_layout.addSpacing(20)
        top_layout.addWidget(quit_btn)

        self.card = QuestionCard()

        self.timer_bar = QProgressBar()
        self.timer_bar.setObjectName("TimerBar")
        self.timer_bar.setRange(0, QUESTION_TIMEOUT_SEC)
        self.timer_bar.setValue(QUESTION_TIMEOUT_SEC)
        self.timer_bar.setFormat("%v s")
        self.timer_bar.setTextVisible(True)

        grid = QGridLayout()
        grid.setSpacing(18)
        self.buttons: dict[str, AnswerButton] = {}
        for i, letter in enumerate(("A", "B", "C", "D")):
            btn = AnswerButton(letter)
            btn.chosen.connect(self.submit_answer)
            self.buttons[letter] = btn
            grid.addWidget(btn, i // 2, i % 2)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(36, 28, 36, 36)
        outer.setSpacing(18)
        outer.addWidget(top)
        outer.addWidget(self.card, 1)
        outer.addWidget(self.timer_bar)
        outer.addLayout(grid, 2)

        self._engine.question_changed.connect(self._on_question)
        self._engine.score_changed.connect(self._on_score)
        self._engine.lives_changed.connect(self._on_lives)
        self._engine.streak_changed.connect(self._on_streak)
        self._engine.timer_tick.connect(self._on_tick)
        self._engine.answer_resolved.connect(self._on_answer)

        self._on_lives(STARTING_LIVES)
        self._on_score(0)
        self._on_streak(0)

    # Player input
    def submit_answer(self, letter: str) -> None:
        if letter not in ("A", "B", "C", "D"):
            return
        self._last_pick = letter
        self._engine.submit(letter)  # type: ignore[arg-type]

    # Engine slots
    def _on_question(self, q: Question) -> None:
        self._last_pick = None
        self.card.set_question(q.text, q.category, q.difficulty)
        for letter, btn in self.buttons.items():
            btn.set_option(q.options[letter])
            btn.setEnabled(True)

    def _on_score(self, score: int) -> None:
        self.score_label.setText(f"Score: {score}")

    def _on_lives(self, lives: int) -> None:
        filled = "♥ " * lives
        empty = "♡ " * (STARTING_LIVES - lives)
        self.lives_label.setText((filled + empty).strip())
        if lives < STARTING_LIVES:
            self._flash(self.lives_label)

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
            btn.setEnabled(False)
            if letter == correct_letter:
                btn.mark("correct")
            elif not correct and letter == self._last_pick:
                btn.mark("wrong")
            else:
                btn.mark("")
        if not correct:
            self._flash(self.timer_bar)

    # Effects
    def _flash(self, widget) -> None:
        widget.setProperty("alert", True)
        widget.style().unpolish(widget)
        widget.style().polish(widget)

        def restore():
            widget.setProperty("alert", False)
            widget.style().unpolish(widget)
            widget.style().polish(widget)

        QTimer.singleShot(280, restore)
