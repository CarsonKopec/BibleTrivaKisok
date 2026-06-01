"""Horizontal letter-picker OSK driven by 4 directional inputs.

Layout (no tap targets — purely arrow-driven):

      ◀     C     D    [ E ]    F     G     ▶

    ↑ ADD     ↓ BACK     ← + →  SUBMIT

Control mapping:
  ← / →  scroll through letters (wraps A↔Z, with SPACE at the end)
  ↑      insert the selected letter into the nickname
  ↓      backspace the last letter
  ← + →  pressed and held simultaneously: submit the nickname

The chord requires both keys to be down at the same time (not just within a
time window), so quick reverse-scrolling won't accidentally submit.
"""
from __future__ import annotations

from typing import Literal

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget


LETTERS: str = "ABCDEFGHIJKLMNOPQRSTUVWXYZ "
_VISIBLE_RADIUS: int = 2

Direction = Literal["up", "down", "left", "right"]


class _ChordTracker:
    """Detects ← and → being held simultaneously."""

    def __init__(self) -> None:
        self._down: set[str] = set()
        self._fired: bool = False

    def press(self, key: str) -> bool:
        """Record a press. Returns True if this completes a fresh chord."""
        self._down.add(key)
        if "left" in self._down and "right" in self._down and not self._fired:
            self._fired = True
            return True
        return False

    def release(self, key: str) -> None:
        self._down.discard(key)
        if key in ("left", "right"):
            self._fired = False

    def is_active(self) -> bool:
        return self._fired


class OnScreenKeyboard(QWidget):
    text_inserted = Signal(str)
    backspace_requested = Signal()
    submit_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("OnScreenKeyboard")
        self._index: int = 0
        self._chord = _ChordTracker()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 22, 28, 22)
        outer.setSpacing(14)

        self._strip = QFrame()
        self._strip.setObjectName("OSKStrip")
        strip_layout = QHBoxLayout(self._strip)
        strip_layout.setContentsMargins(24, 18, 24, 18)
        strip_layout.setSpacing(0)

        left_chev = QLabel("◀")
        left_chev.setObjectName("OSKChevron")
        left_chev.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_chev = QLabel("▶")
        right_chev.setObjectName("OSKChevron")
        right_chev.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_chev.setFixedWidth(60)
        right_chev.setFixedWidth(60)

        strip_layout.addWidget(left_chev)
        strip_layout.addStretch(1)

        self._labels: list[QLabel] = []
        for i in range(-_VISIBLE_RADIUS, _VISIBLE_RADIUS + 1):
            lbl = QLabel("")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if i == 0:
                lbl.setObjectName("OSKCenter")
                lbl.setFixedWidth(120)
            elif abs(i) == 1:
                lbl.setObjectName("OSKNear")
                lbl.setFixedWidth(80)
            else:
                lbl.setObjectName("OSKFar")
                lbl.setFixedWidth(64)
            strip_layout.addWidget(lbl)
            self._labels.append(lbl)

        strip_layout.addStretch(1)
        strip_layout.addWidget(right_chev)
        outer.addWidget(self._strip)

        hint = QLabel(
            "←  →  scroll       ↑  ADD       ↓  BACK       ← + →  SUBMIT"
        )
        hint.setObjectName("OSKHint")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(hint)

        self._refresh()

    # Public API (called by HomeScreen for keyboard / GPIO routing)
    @property
    def current_letter(self) -> str:
        return LETTERS[self._index]

    def handle_press(self, direction: Direction) -> None:
        if direction == "up":
            self.text_inserted.emit(LETTERS[self._index])
            return
        if direction == "down":
            self.backspace_requested.emit()
            return
        if self._chord.press(direction):
            self.submit_requested.emit()
            return
        if self._chord.is_active():
            return
        self._scroll(-1 if direction == "left" else 1)

    def handle_release(self, direction: Direction) -> None:
        self._chord.release(direction)

    def reset(self) -> None:
        self._index = 0
        self._refresh()

    def _scroll(self, delta: int) -> None:
        self._index = (self._index + delta) % len(LETTERS)
        self._refresh()

    def _refresh(self) -> None:
        n = len(LETTERS)
        for i, lbl in enumerate(self._labels):
            offset = i - _VISIBLE_RADIUS
            ch = LETTERS[(self._index + offset) % n]
            lbl.setText("_" if ch == " " else ch)
