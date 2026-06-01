"""Large gold-trimmed answer button labelled with its option letter."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QPushButton


_ARROW_BY_LETTER: dict[str, str] = {
    "A": "↑",
    "B": "→",
    "C": "←",
    "D": "↓",
}


class AnswerButton(QPushButton):
    chosen = Signal(str)

    def __init__(self, letter: str, parent=None):
        super().__init__(parent)
        self.letter = letter
        self._arrow = _ARROW_BY_LETTER.get(letter, "")
        self.setObjectName("AnswerButton")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(76)
        self.set_option("")
        self.clicked.connect(lambda: self.chosen.emit(self.letter))

    def set_option(self, text: str) -> None:
        self.setText(f"  {self._arrow}   {self.letter}.   {text}")
        self.setProperty("state", "")
        self._restyle()

    def mark(self, state: str) -> None:
        """state ∈ {'correct', 'wrong', ''}"""
        self.setProperty("state", state)
        self._restyle()

    def _restyle(self) -> None:
        style = self.style()
        style.unpolish(self)
        style.polish(self)
        self.update()
