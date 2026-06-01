"""Main window that hosts every screen and routes input + navigation.

Owns the live GameEngine when a round is in progress so the optional
SpectatorWindow can observe the same instance.
"""
from __future__ import annotations

from PySide6.QtWidgets import QMainWindow, QStackedWidget

from game.engine import GameEngine
from game.question_manager import QuestionManager
from input.gpio_input import GPIOInput
from input.keyboard_input import KeyboardInput
from ui.screens.game_screen import GameScreen
from ui.screens.home_screen import HomeScreen
from ui.screens.leaderboard_screen import LeaderboardScreen
from ui.screens.results_screen import ResultsScreen
from ui.spectator.spectator_window import SpectatorWindow


class MainWindow(QMainWindow):
    def __init__(self, spectator: SpectatorWindow | None = None):
        super().__init__()
        self.setWindowTitle("Bible Trivia")
        self.setMinimumSize(980, 660)

        self.spectator = spectator

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.keyboard = KeyboardInput(self)
        self.keyboard.start()
        self.keyboard.answered.connect(self._route_input)
        self.keyboard.released.connect(self._route_release)

        self.gpio = GPIOInput(self)
        self.gpio.start()
        self.gpio.answered.connect(self._route_input)
        self.gpio.released.connect(self._route_release)

        self.home = HomeScreen()
        self.results = ResultsScreen()
        self.leaderboard = LeaderboardScreen()
        self.game: GameScreen | None = None
        self._engine: GameEngine | None = None
        self._current_nickname: str = ""

        self.stack.addWidget(self.home)
        self.stack.addWidget(self.results)
        self.stack.addWidget(self.leaderboard)

        self.home.start_requested.connect(self._start_game)
        self.home.leaderboard_requested.connect(self._show_leaderboard)
        self.home.exit_requested.connect(self.close)
        self.results.again_requested.connect(self._again)
        self.results.home_requested.connect(self._show_home)
        self.leaderboard.home_requested.connect(self._show_home)

        self._show_home()

    # Navigation
    def _show_home(self) -> None:
        self._teardown_game()
        self.stack.setCurrentWidget(self.home)
        self.home.focus_nickname()
        if self.spectator is not None:
            self.spectator.show_idle()

    def _show_leaderboard(self) -> None:
        self.leaderboard.refresh()
        self.stack.setCurrentWidget(self.leaderboard)

    def _start_game(self, nickname: str) -> None:
        self._launch_game(nickname)

    def _again(self) -> None:
        nickname = self.results.last_nickname or ""
        if nickname:
            self._launch_game(nickname)
        else:
            self._show_home()

    # Game lifecycle
    def _launch_game(self, nickname: str) -> None:
        self._teardown_game()
        manager = QuestionManager()
        if manager.total == 0:
            self.home.error.setText("No questions found. Please reseed the database.")
            self.stack.setCurrentWidget(self.home)
            return

        self._current_nickname = nickname
        self._engine = GameEngine(manager, self)
        self._engine.game_over.connect(self._on_game_over)

        self.game = GameScreen(engine=self._engine)
        self.game.quit_requested.connect(self._show_home)
        self.stack.addWidget(self.game)
        self.stack.setCurrentWidget(self.game)

        if self.spectator is not None:
            self.spectator.show_play(self._engine, nickname)

        self._engine.start()

    def _teardown_game(self) -> None:
        if self._engine is not None:
            try:
                self._engine.stop()
            except Exception:
                pass
            if self.spectator is not None:
                self.spectator.play.detach()
            self._engine.deleteLater()
            self._engine = None
        if self.game is not None:
            self.stack.removeWidget(self.game)
            self.game.deleteLater()
            self.game = None

    def _on_game_over(self, score: int, correct: int, answered: int) -> None:
        nickname = self._current_nickname
        self.results.set_result(
            nickname=nickname, score=score, correct=correct, answered=answered,
        )
        self.stack.setCurrentWidget(self.results)
        self._teardown_game()
        if self.spectator is not None:
            self.spectator.show_idle()

    # Input routing
    def _route_input(self, letter: str) -> None:
        current = self.stack.currentWidget()
        if self.game is not None and current is self.game:
            self.game.submit_answer(letter)
        elif current is self.home:
            self.home.handle_directional_press(letter)
        elif current is self.results:
            self.results.handle_letter(letter)
        elif current is self.leaderboard:
            self.leaderboard.handle_letter(letter)

    def _route_release(self, letter: str) -> None:
        current = self.stack.currentWidget()
        if current is self.home:
            self.home.handle_directional_release(letter)
        elif current is self.leaderboard:
            self.leaderboard.handle_release(letter)

    # Shutdown
    def closeEvent(self, event):  # type: ignore[override]
        try:
            self.keyboard.stop()
        except Exception:
            pass
        try:
            self.gpio.stop()
        except Exception:
            pass
        self._teardown_game()
        if self.spectator is not None:
            try:
                self.spectator.close()
            except Exception:
                pass
        super().closeEvent(event)
