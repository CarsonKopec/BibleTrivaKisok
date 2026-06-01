"""Two-page container that crossfades between its children via opacity."""
from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation
from PySide6.QtWidgets import QGraphicsOpacityEffect, QStackedLayout, QWidget


class CrossfadeStack(QWidget):
    """Like QStackedWidget, but transitions with an opacity crossfade.

    Add pages with `add_page(widget)`. Switch with `set_current(idx, duration)`.
    Use `set_current_immediately(idx)` for the initial page (no animation).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QStackedLayout(self)
        self._layout.setStackingMode(QStackedLayout.StackingMode.StackAll)
        self._current_index: int = -1
        self._animations: list[QPropertyAnimation] = []

    def add_page(self, widget: QWidget) -> int:
        effect = QGraphicsOpacityEffect(widget)
        effect.setOpacity(0.0)
        widget.setGraphicsEffect(effect)
        return self._layout.addWidget(widget)

    def count(self) -> int:
        return self._layout.count()

    def current_index(self) -> int:
        return self._current_index

    def set_current_immediately(self, index: int) -> None:
        for i in range(self._layout.count()):
            w = self._layout.widget(i)
            if w is None:
                continue
            effect = w.graphicsEffect()
            if isinstance(effect, QGraphicsOpacityEffect):
                effect.setOpacity(1.0 if i == index else 0.0)
        target = self._layout.widget(index)
        if target is not None:
            target.raise_()
        self._current_index = index

    def set_current(self, index: int, duration_ms: int = 400) -> None:
        if index == self._current_index or index < 0 or index >= self._layout.count():
            return
        old = self._layout.widget(self._current_index) if self._current_index >= 0 else None
        new = self._layout.widget(index)
        if new is None:
            return

        for anim in self._animations:
            anim.stop()
        self._animations.clear()

        new.raise_()

        if old is not None:
            old_eff = old.graphicsEffect()
            if isinstance(old_eff, QGraphicsOpacityEffect):
                anim_out = QPropertyAnimation(old_eff, b"opacity", self)
                anim_out.setDuration(duration_ms)
                anim_out.setStartValue(old_eff.opacity())
                anim_out.setEndValue(0.0)
                anim_out.setEasingCurve(QEasingCurve.Type.InOutCubic)
                anim_out.start()
                self._animations.append(anim_out)

        new_eff = new.graphicsEffect()
        if isinstance(new_eff, QGraphicsOpacityEffect):
            anim_in = QPropertyAnimation(new_eff, b"opacity", self)
            anim_in.setDuration(duration_ms)
            anim_in.setStartValue(new_eff.opacity())
            anim_in.setEndValue(1.0)
            anim_in.setEasingCurve(QEasingCurve.Type.InOutCubic)
            anim_in.start()
            self._animations.append(anim_in)

        self._current_index = index
