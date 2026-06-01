"""Hall of Records with daily/weekly/monthly/all-time filters."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

from game.scoreboard import Timeframe, top_scores
from ui.widgets.leaderboard_table import LeaderboardTable

_FILTERS: list[tuple[str, Timeframe, str]] = [
    ("A.  Daily", "daily", "A"),
    ("B.  Weekly", "weekly", "B"),
    ("C.  Monthly", "monthly", "C"),
    ("D.  All-Time", "all", "D"),
]

_LETTER_TO_FILTER: dict[str, Timeframe] = {
    "A": "daily",
    "B": "weekly",
    "C": "monthly",
    "D": "all",
}


class LeaderboardScreen(QWidget):
    home_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LeaderboardScreen")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(40, 28, 40, 28)
        outer.setSpacing(18)

        title = QLabel("HALL OF RECORDS")
        title.setObjectName("Title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(title)

        filters = QHBoxLayout()
        filters.addStretch(1)
        self._filter_group = QButtonGroup(self)
        self._filter_group.setExclusive(True)
        self._filter_buttons: dict[Timeframe, QPushButton] = {}
        for label, tf, _letter in _FILTERS:
            btn = QPushButton(label)
            btn.setObjectName("FilterButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _checked=False, t=tf: self._set_filter(t))
            self._filter_group.addButton(btn)
            self._filter_buttons[tf] = btn
            filters.addWidget(btn)
        filters.addStretch(1)
        outer.addLayout(filters)

        self.table = LeaderboardTable()
        outer.addWidget(self.table, 1)

        self.empty_label = QLabel("No scores recorded yet. Play a round to claim the first spot!")
        self.empty_label.setObjectName("Subtitle")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.hide()
        outer.addWidget(self.empty_label)

        bottom = QHBoxLayout()
        bottom.addStretch(1)
        back = QPushButton("Return to Menu  (hold A + D)")
        back.setObjectName("SecondaryButton")
        back.setMinimumHeight(44)
        back.setCursor(Qt.CursorShape.PointingHandCursor)
        back.clicked.connect(self.home_requested.emit)
        bottom.addWidget(back)
        bottom.addStretch(1)
        outer.addLayout(bottom)

        self._current: Timeframe = "all"
        self._filter_buttons["all"].setChecked(True)

        self._down: set[str] = set()
        self._chord_fired: bool = False

    def refresh(self) -> None:
        self._down.clear()
        self._chord_fired = False
        self._set_filter(self._current)

    def handle_letter(self, letter: str) -> bool:
        self._down.add(letter)
        if "A" in self._down and "D" in self._down and not self._chord_fired:
            self._chord_fired = True
            self.home_requested.emit()
            return True
        tf = _LETTER_TO_FILTER.get(letter)
        if tf is None:
            return False
        self._set_filter(tf)
        return True

    def handle_release(self, letter: str) -> bool:
        self._down.discard(letter)
        if letter in ("A", "D"):
            self._chord_fired = False
        return False

    def _set_filter(self, tf: Timeframe) -> None:
        self._current = tf
        self._filter_buttons[tf].setChecked(True)
        try:
            rows = top_scores(tf)
        except Exception as exc:  # noqa: BLE001
            print(f"[Bible Trivia] Failed to load scores: {exc}")
            rows = []
        self.table.populate(rows)
        self.empty_label.setVisible(not rows)
        self.table.setVisible(bool(rows))
