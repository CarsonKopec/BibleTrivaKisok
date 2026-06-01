"""HDMI idle page: fullscreen leaderboard that cycles through timeframes.

The timeframe section (label + table) slides horizontally on each rotation;
the title and call-to-action stay put.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from config import IDLE_CYCLE_INTERVAL_MS
from db.models import ScoreRow
from game.scoreboard import Timeframe, top_scores
from ui.widgets.leaderboard_table import LeaderboardTable
from ui.widgets.slide_stack import SlideStack


_CYCLE: list[tuple[str, Timeframe]] = [
    ("Today's Champions", "daily"),
    ("This Week", "weekly"),
    ("This Month", "monthly"),
    ("All-Time Legends", "all"),
]

_SLIDE_MS: int = 600


class _LeaderboardSection(QWidget):
    """One pane of the slide stack: a timeframe label plus a leaderboard."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        self.timeframe_label = QLabel("")
        self.timeframe_label.setObjectName("SpectatorTimeframe")
        self.timeframe_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.table = LeaderboardTable()
        self.table.setObjectName("SpectatorLeaderboard")

        self.empty_label = QLabel("No scores yet. Be the first to claim a spot!")
        self.empty_label.setObjectName("SpectatorEmpty")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.hide()

        layout.addWidget(self.timeframe_label)
        layout.addWidget(self.table, 1)
        layout.addWidget(self.empty_label)

    def populate(self, label_text: str, rows: list[ScoreRow]) -> None:
        self.timeframe_label.setText(label_text.upper())
        self.table.populate(rows)
        self.empty_label.setVisible(not rows)
        self.table.setVisible(bool(rows))


class IdlePage(QWidget):
    """Auto-rotates through Daily -> Weekly -> Monthly -> All-Time."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SpectatorIdle")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(60, 40, 60, 40)
        outer.setSpacing(18)

        title = QLabel("HALL  OF  RECORDS")
        title.setObjectName("SpectatorTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(title)

        self._slide = SlideStack()
        self._section_a = _LeaderboardSection()
        self._section_b = _LeaderboardSection()
        self._idx_a = self._slide.add_page(self._section_a)
        self._idx_b = self._slide.add_page(self._section_b)
        outer.addWidget(self._slide, 1)

        cta = QLabel("Step up to the kiosk and enter your name to play!")
        cta.setObjectName("SpectatorCTA")
        cta.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(cta)

        self._cycle_index: int = 0
        self._populate_section(self._section_a, *_CYCLE[self._cycle_index])
        self._slide.set_current_immediately(self._idx_a)

        self._timer = QTimer(self)
        self._timer.setInterval(IDLE_CYCLE_INTERVAL_MS)
        self._timer.timeout.connect(self._advance)

    def start_cycle(self) -> None:
        section = self._section_a if self._slide.current_index() == self._idx_a else self._section_b
        self._populate_section(section, *_CYCLE[self._cycle_index])
        if not self._timer.isActive():
            self._timer.start()

    def stop_cycle(self) -> None:
        self._timer.stop()

    def _advance(self) -> None:
        self._cycle_index = (self._cycle_index + 1) % len(_CYCLE)
        if self._slide.current_index() == self._idx_a:
            next_section, next_idx = self._section_b, self._idx_b
        else:
            next_section, next_idx = self._section_a, self._idx_a
        self._populate_section(next_section, *_CYCLE[self._cycle_index])
        self._slide.set_current(next_idx, direction="left", duration_ms=_SLIDE_MS)

    def _populate_section(
        self, section: _LeaderboardSection, label: str, tf: Timeframe,
    ) -> None:
        try:
            rows = top_scores(tf, limit=10)
        except Exception as exc:  # noqa: BLE001
            print(f"[Bible Trivia] Idle leaderboard load failed: {exc}")
            rows = []
        section.populate(label, rows)
