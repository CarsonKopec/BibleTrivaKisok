"""Core game loop: state, timer, lives, scoring, streak bonus."""
from __future__ import annotations

from PySide6.QtCore import QObject, QTimer, Signal

from config import (
    BASE_POINTS,
    QUESTION_TIMEOUT_SEC,
    STARTING_LIVES,
    STREAK_BONUS_PER_STEP,
    STREAK_MAX_BONUS_STEPS,
)
from db.models import Answer, Question
from game.question_manager import QuestionManager


class GameEngine(QObject):
    """Drives a single play session. UI screens subscribe to its signals."""

    question_changed = Signal(object)
    score_changed = Signal(int)
    lives_changed = Signal(int)
    streak_changed = Signal(int)
    timer_tick = Signal(int)
    answer_resolved = Signal(bool, str)
    game_over = Signal(int, int, int)

    _REVEAL_DELAY_MS = 1100

    def __init__(self, manager: QuestionManager, parent: QObject | None = None):
        super().__init__(parent)
        self._manager = manager
        self._lives = STARTING_LIVES
        self._score = 0
        self._streak = 0
        self._correct = 0
        self._answered = 0
        self._current: Question | None = None
        self._remaining = QUESTION_TIMEOUT_SEC
        self._accepting_input = False

        self._tick = QTimer(self)
        self._tick.setInterval(1000)
        self._tick.timeout.connect(self._on_tick)

    # Public API
    @property
    def lives(self) -> int:
        return self._lives

    @property
    def score(self) -> int:
        return self._score

    @property
    def streak(self) -> int:
        return self._streak

    def start(self) -> None:
        self._lives = STARTING_LIVES
        self._score = 0
        self._streak = 0
        self._correct = 0
        self._answered = 0
        self.lives_changed.emit(self._lives)
        self.score_changed.emit(self._score)
        self.streak_changed.emit(self._streak)
        self._next_question()

    def stop(self) -> None:
        self._tick.stop()
        self._accepting_input = False

    def submit(self, answer: Answer) -> None:
        if not self._accepting_input or self._current is None:
            return
        self._accepting_input = False
        self._tick.stop()
        self._resolve(correct=(answer == self._current.correct))

    # Internals
    def _next_question(self) -> None:
        try:
            self._current = self._manager.next()
        except StopIteration:
            self.game_over.emit(self._score, self._correct, self._answered)
            return
        self._remaining = QUESTION_TIMEOUT_SEC
        self._accepting_input = True
        self.question_changed.emit(self._current)
        self.timer_tick.emit(self._remaining)
        self._tick.start()

    def _on_tick(self) -> None:
        self._remaining -= 1
        self.timer_tick.emit(self._remaining)
        if self._remaining <= 0:
            self._accepting_input = False
            self._tick.stop()
            self._resolve(correct=False)

    def _resolve(self, correct: bool) -> None:
        self._answered += 1
        if correct:
            self._correct += 1
            bonus_steps = min(self._streak, STREAK_MAX_BONUS_STEPS)
            self._score += BASE_POINTS + bonus_steps * STREAK_BONUS_PER_STEP
            self._streak += 1
        else:
            self._lives -= 1
            self._streak = 0

        self.score_changed.emit(self._score)
        self.lives_changed.emit(self._lives)
        self.streak_changed.emit(self._streak)
        correct_letter = self._current.correct if self._current else ""
        self.answer_resolved.emit(correct, correct_letter)

        if self._lives <= 0:
            QTimer.singleShot(
                self._REVEAL_DELAY_MS,
                lambda: self.game_over.emit(self._score, self._correct, self._answered),
            )
        else:
            QTimer.singleShot(self._REVEAL_DELAY_MS, self._next_question)
