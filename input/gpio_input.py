"""Optional Raspberry Pi GPIO buttons. No-op on systems without gpiozero.

GPIO mapping (from the spec):
    GPIO17 -> A   GPIO18 -> B   GPIO27 -> C   GPIO22 -> D
"""
from __future__ import annotations

from typing import Any

from config import GPIO_PINS
from input.base_input import InputHandler

try:  # pragma: no cover - hardware-specific
    from gpiozero import Button  # type: ignore[import-not-found]
    _GPIO_AVAILABLE = True
except Exception:
    Button = None  # type: ignore[assignment]
    _GPIO_AVAILABLE = False


class GPIOInput(InputHandler):
    """Binds A/B/C/D answers to physical buttons. Disabled gracefully off-Pi."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._buttons: list[Any] = []

    @property
    def available(self) -> bool:
        return _GPIO_AVAILABLE

    def start(self) -> None:
        if not _GPIO_AVAILABLE:
            return
        for letter, pin in GPIO_PINS.items():
            try:
                btn = Button(pin, bounce_time=0.05)
                btn.when_pressed = lambda b=letter: self.answered.emit(b)
                btn.when_released = lambda b=letter: self.released.emit(b)
                self._buttons.append(btn)
            except Exception:
                continue

    def stop(self) -> None:
        for btn in self._buttons:
            try:
                btn.close()
            except Exception:
                pass
        self._buttons.clear()
