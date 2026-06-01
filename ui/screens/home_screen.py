"""Title, nickname entry, and primary navigation."""
from __future__ import annotations

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget,
)

from config import ONSCREEN_KEYBOARD_ENABLED
from ui.widgets.osk import OnScreenKeyboard


_ARROW_NAV: dict[int, str] = {
    Qt.Key.Key_Up: "up",
    Qt.Key.Key_Down: "down",
    Qt.Key.Key_Left: "left",
    Qt.Key.Key_Right: "right",
}

_LETTER_NAV: dict[str, str] = {"A": "up", "B": "right", "C": "left", "D": "down"}

_LETTER_BUTTON_ACTIONS: dict[str, str] = {"A": "begin", "B": "hall", "D": "exit"}


class HomeScreen(QWidget):
    start_requested = Signal(str)
    leaderboard_requested = Signal()
    exit_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HomeScreen")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(40, 40, 40, 40)

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(56, 40, 56, 40)
        card_layout.setSpacing(14)

        title = QLabel("BIBLE  TRIVIA")
        title.setObjectName("Title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("An arcade challenge of Scripture wisdom")
        subtitle.setObjectName("Subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        field_label = QLabel("ENTER YOUR NAME")
        field_label.setObjectName("FieldLabel")
        field_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.nickname = QLineEdit()
        self.nickname.setObjectName("NicknameField")
        self.nickname.setMaxLength(20)
        self.nickname.setPlaceholderText("e.g. David")
        self.nickname.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.error = QLabel("")
        self.error.setObjectName("ErrorLabel")
        self.error.setAlignment(Qt.AlignmentFlag.AlignCenter)

        begin_label = "Begin Challenge" if ONSCREEN_KEYBOARD_ENABLED else "A.  Begin Challenge"
        hall_label = "Hall of Records" if ONSCREEN_KEYBOARD_ENABLED else "B.  Hall of Records"
        exit_label = "Exit" if ONSCREEN_KEYBOARD_ENABLED else "D.  Exit"

        begin = QPushButton(begin_label)
        begin.setObjectName("PrimaryButton")
        begin.setMinimumHeight(56)
        begin.setCursor(Qt.CursorShape.PointingHandCursor)

        hall = QPushButton(hall_label)
        hall.setObjectName("SecondaryButton")
        hall.setMinimumHeight(48)
        hall.setCursor(Qt.CursorShape.PointingHandCursor)

        exit_btn = QPushButton(exit_label)
        exit_btn.setObjectName("TertiaryButton")
        exit_btn.setMinimumHeight(40)
        exit_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        begin.clicked.connect(self._on_begin)
        hall.clicked.connect(self.leaderboard_requested.emit)
        exit_btn.clicked.connect(self.exit_requested.emit)
        if not ONSCREEN_KEYBOARD_ENABLED:
            self.nickname.returnPressed.connect(self._on_begin)

        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(18)
        card_layout.addWidget(field_label)
        card_layout.addWidget(self.nickname)
        card_layout.addWidget(self.error)
        card_layout.addSpacing(12)
        card_layout.addWidget(begin)
        card_layout.addWidget(hall)
        card_layout.addWidget(exit_btn)

        center = QHBoxLayout()
        center.addStretch(1)
        center.addWidget(card, 0)
        center.addStretch(1)

        self.osk: OnScreenKeyboard | None = None
        if ONSCREEN_KEYBOARD_ENABLED:
            outer.addSpacing(24)
            outer.addLayout(center)
            outer.addStretch(1)
            self.osk = OnScreenKeyboard()
            self.osk.text_inserted.connect(self._osk_insert)
            self.osk.backspace_requested.connect(self._osk_backspace)
            self.osk.submit_requested.connect(self._on_begin)
            outer.addWidget(self.osk)
            self.nickname.installEventFilter(self)
        else:
            outer.addStretch(1)
            outer.addLayout(center)
            outer.addStretch(1)

    # External input routing (called by MainWindow for GPIO/keyboard letters)
    def handle_directional_press(self, letter: str) -> bool:
        if self.osk is None:
            action = _LETTER_BUTTON_ACTIONS.get(letter)
            if action == "begin":
                self._on_begin()
                return True
            if action == "hall":
                self.leaderboard_requested.emit()
                return True
            if action == "exit":
                self.exit_requested.emit()
                return True
            return False
        direction = _LETTER_NAV.get(letter)
        if direction is None:
            return False
        self.osk.handle_press(direction)  # type: ignore[arg-type]
        return True

    def handle_directional_release(self, letter: str) -> bool:
        if self.osk is None:
            return False
        direction = _LETTER_NAV.get(letter)
        if direction is None:
            return False
        self.osk.handle_release(direction)  # type: ignore[arg-type]
        return True

    # OSK slots
    def _osk_insert(self, text: str) -> None:
        current = self.nickname.text()
        if len(current) >= self.nickname.maxLength():
            return
        self.nickname.setText(current + text)
        self.nickname.setFocus()

    def _osk_backspace(self) -> None:
        self.nickname.setText(self.nickname.text()[:-1])
        self.nickname.setFocus()

    def focus_nickname(self) -> None:
        self.nickname.setFocus()
        self.nickname.selectAll()
        if self.osk is not None:
            self.osk.reset()

    # Event filter: arrow keys drive the OSK while the nickname field is focused
    def eventFilter(self, obj, event):  # type: ignore[override]
        if obj is self.nickname and self.osk is not None:
            etype = event.type()
            if etype == QEvent.Type.KeyPress and not event.isAutoRepeat():
                direction = _ARROW_NAV.get(event.key())
                if direction is not None:
                    self.osk.handle_press(direction)  # type: ignore[arg-type]
                    return True
            elif etype == QEvent.Type.KeyRelease and not event.isAutoRepeat():
                direction = _ARROW_NAV.get(event.key())
                if direction is not None:
                    self.osk.handle_release(direction)  # type: ignore[arg-type]
                    return True
        return super().eventFilter(obj, event)

    def _on_begin(self) -> None:
        name = self.nickname.text().strip()
        if not name:
            self.error.setText("Please enter a name before beginning.")
            return
        self.error.setText("")
        self.start_requested.emit(name)
