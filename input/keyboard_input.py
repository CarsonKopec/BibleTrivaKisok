"""Map A/B/C/D (and 1/2/3/4) keystrokes to game answers."""
from __future__ import annotations

from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import QApplication, QLineEdit

from input.base_input import InputHandler

_KEY_MAP: dict[int, str] = {
    Qt.Key.Key_A: "A",
    Qt.Key.Key_B: "B",
    Qt.Key.Key_C: "C",
    Qt.Key.Key_D: "D",
    Qt.Key.Key_1: "A",
    Qt.Key.Key_2: "B",
    Qt.Key.Key_3: "C",
    Qt.Key.Key_4: "D",
    Qt.Key.Key_Up: "A",
    Qt.Key.Key_Right: "B",
    Qt.Key.Key_Down: "D",
    Qt.Key.Key_Left: "C",
}


class KeyboardInput(InputHandler):
    """Application-wide key event filter. Skips text-entry widgets."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._installed = False

    def start(self) -> None:
        if self._installed:
            return
        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self)
            self._installed = True

    def stop(self) -> None:
        if not self._installed:
            return
        app = QApplication.instance()
        if app is not None:
            app.removeEventFilter(self)
        self._installed = False

    def eventFilter(self, obj, event):  # type: ignore[override]
        etype = event.type()
        if etype == QEvent.Type.KeyPress:
            if isinstance(QApplication.focusWidget(), QLineEdit):
                return False
            if event.isAutoRepeat():
                return False
            letter = _KEY_MAP.get(event.key())
            if letter is not None:
                self.answered.emit(letter)
                return True
        elif etype == QEvent.Type.KeyRelease:
            if isinstance(QApplication.focusWidget(), QLineEdit):
                return False
            if event.isAutoRepeat():
                return False
            letter = _KEY_MAP.get(event.key())
            if letter is not None:
                self.released.emit(letter)
                return False
        return False
