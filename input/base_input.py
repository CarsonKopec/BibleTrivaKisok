"""Pluggable input handler base.

All implementations expose the same `answered` signal that emits one of
``"A" / "B" / "C" / "D"`` whenever the player chooses an option.
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject, Signal


class InputHandler(QObject):
    """Subclass and emit `answered`/`released` from your device-specific binding.

    `answered` fires on press, `released` on the matching release. The release
    signal is required for chord-style combos (e.g. ←+→ held together).
    """

    answered = Signal(str)
    released = Signal(str)

    def start(self) -> None:
        """Begin listening. Subclasses override."""

    def stop(self) -> None:
        """Stop listening and release resources. Subclasses override."""

    def get_input(self) -> Optional[str]:
        """Synchronous compatibility hook from the spec.

        Most implementations are event-driven and return None here.
        """
        return None
