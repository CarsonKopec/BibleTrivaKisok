"""Top-level window shown on the HDMI / secondary display."""
from __future__ import annotations

from PySide6.QtWidgets import QMainWindow

from config import CROSSFADE_MS
from game.engine import GameEngine
from ui.spectator.idle_page import IdlePage
from ui.spectator.play_page import PlayPage
from ui.widgets.crossfade_stack import CrossfadeStack


class SpectatorWindow(QMainWindow):
    """Hosts the idle leaderboard and the in-game spectator view."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bible Trivia — Spectator")
        self.setMinimumSize(960, 540)

        self.stack = CrossfadeStack()
        self.setCentralWidget(self.stack)

        self.idle = IdlePage()
        self.play = PlayPage()
        self._idle_idx = self.stack.add_page(self.idle)
        self._play_idx = self.stack.add_page(self.play)

        self.stack.set_current_immediately(self._idle_idx)
        self.idle.start_cycle()

    def show_idle(self) -> None:
        self.play.detach()
        self.idle.start_cycle()
        self.stack.set_current(self._idle_idx, duration_ms=CROSSFADE_MS)

    def show_play(self, engine: GameEngine, nickname: str) -> None:
        self.idle.stop_cycle()
        self.play.attach(engine, nickname)
        self.stack.set_current(self._play_idx, duration_ms=CROSSFADE_MS)

    def closeEvent(self, event):  # type: ignore[override]
        try:
            self.idle.stop_cycle()
            self.play.detach()
        except Exception:
            pass
        super().closeEvent(event)
