"""Horizontal-slide container.

Pages are siblings positioned manually. `set_current(idx)` animates the
outgoing page off one side while the incoming page slides in from the other.
"""
from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPoint, QPropertyAnimation
from PySide6.QtWidgets import QWidget


class SlideStack(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pages: list[QWidget] = []
        self._current_index: int = -1
        self._animations: list[QPropertyAnimation] = []

    def add_page(self, widget: QWidget) -> int:
        widget.setParent(self)
        widget.hide()
        self._pages.append(widget)
        return len(self._pages) - 1

    def count(self) -> int:
        return len(self._pages)

    def current_index(self) -> int:
        return self._current_index

    def set_current_immediately(self, index: int) -> None:
        if not (0 <= index < len(self._pages)):
            return
        w, h = self.width(), self.height()
        for i, p in enumerate(self._pages):
            p.resize(w, h)
            if i == index:
                p.move(0, 0)
                p.show()
                p.raise_()
            else:
                p.move(w, 0)
                p.hide()
        self._current_index = index

    def set_current(self, index: int, direction: str = "left", duration_ms: int = 600) -> None:
        """Slide to `index`. `direction='left'` mimics a forward navigation:
        new page enters from the right, old page exits to the left."""
        if index == self._current_index or not (0 <= index < len(self._pages)):
            return

        w, h = self.width(), self.height()
        old = self._pages[self._current_index] if 0 <= self._current_index < len(self._pages) else None
        new = self._pages[index]

        for anim in self._animations:
            anim.stop()
        self._animations.clear()

        new.resize(w, h)
        if direction == "left":
            new.move(w, 0)
            old_end = QPoint(-w, 0)
        else:
            new.move(-w, 0)
            old_end = QPoint(w, 0)
        new.show()
        new.raise_()

        anim_in = QPropertyAnimation(new, b"pos", self)
        anim_in.setDuration(duration_ms)
        anim_in.setStartValue(new.pos())
        anim_in.setEndValue(QPoint(0, 0))
        anim_in.setEasingCurve(QEasingCurve.Type.InOutCubic)
        anim_in.start()
        self._animations.append(anim_in)

        if old is not None:
            anim_out = QPropertyAnimation(old, b"pos", self)
            anim_out.setDuration(duration_ms)
            anim_out.setStartValue(old.pos())
            anim_out.setEndValue(old_end)
            anim_out.setEasingCurve(QEasingCurve.Type.InOutCubic)
            anim_out.finished.connect(old.hide)
            anim_out.start()
            self._animations.append(anim_out)

        self._current_index = index

    def resizeEvent(self, event):  # type: ignore[override]
        w, h = self.width(), self.height()
        for i, p in enumerate(self._pages):
            p.resize(w, h)
            if i == self._current_index:
                p.move(0, 0)
            else:
                p.move(w, 0)
        super().resizeEvent(event)
