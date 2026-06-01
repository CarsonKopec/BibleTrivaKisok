"""Project-wide configuration: paths, palette, and game constants.

Numeric and boolean settings can be overridden by environment variables
(prefix ``BT_``). This is how ``main.py``'s CLI flags reach the rest of
the codebase — main.py writes the env vars before any other module
imports from ``config``.
"""
from __future__ import annotations

import os
from pathlib import Path


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _env_opt_int(name: str) -> int | None:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except ValueError:
        return None


ROOT_DIR: Path = Path(__file__).resolve().parent
DATA_DIR: Path = ROOT_DIR / "data"
ASSETS_DIR: Path = ROOT_DIR / "assets"
STYLES_PATH: Path = ASSETS_DIR / "styles.qss"

_db_override = os.environ.get("BT_DB_PATH")
DB_PATH: Path = Path(_db_override) if _db_override else (DATA_DIR / "bible_trivia.db")

DATA_DIR.mkdir(parents=True, exist_ok=True)

STARTING_LIVES: int = _env_int("BT_LIVES", 3)
QUESTION_TIMEOUT_SEC: int = _env_int("BT_QUESTION_TIMEOUT", 10)
BASE_POINTS: int = _env_int("BT_BASE_POINTS", 100)
STREAK_BONUS_PER_STEP: int = _env_int("BT_STREAK_BONUS", 25)
STREAK_MAX_BONUS_STEPS: int = _env_int("BT_STREAK_MAX", 5)

COLOR_BG = "#1A1410"
COLOR_CARD = "#2A2118"
COLOR_TEXT = "#E8D5B0"
COLOR_MUTED = "#A89379"
COLOR_GOLD = "#D4AC36"
COLOR_RED = "#C45757"
COLOR_GREEN = "#92A84A"

GPIO_PINS: dict[str, int] = {
    "A": 17,
    "B": 18,
    "C": 27,
    "D": 22,
}

DUAL_SCREEN_ENABLED: bool = _env_bool("BT_DUAL_SCREEN", True)
FULLSCREEN_KIOSK: bool = _env_bool("BT_FULLSCREEN", False)
MAIN_SCREEN_INDEX: int | None = _env_opt_int("BT_MAIN_SCREEN")
SPECTATOR_SCREEN_INDEX: int | None = _env_opt_int("BT_SPECTATOR_SCREEN")
IDLE_CYCLE_INTERVAL_MS: int = _env_int("BT_CYCLE_INTERVAL_MS", 8000)
CROSSFADE_MS: int = _env_int("BT_CROSSFADE_MS", 400)

ONSCREEN_KEYBOARD_ENABLED: bool = _env_bool("BT_OSK", False)

DEBUG: bool = _env_bool("BT_DEBUG", False)
