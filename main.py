"""Bible Trivia entry point.

Run with no arguments for the regular kiosk experience:

    python main.py

Or pass debug flags — see ``python main.py --help``. Common ones:

    python main.py --simulate-dual           # both windows side-by-side
    python main.py --single-screen           # disable spectator
    python main.py --question-timeout 3      # quick timer for testing timeouts
    python main.py --seed-scores 50          # populate the leaderboard
    python main.py --reset-db                # wipe DB and reseed
    python main.py --list-screens            # diagnose screen detection
"""
from __future__ import annotations

import argparse
import os
import random
import sys


# CLI
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="bible-trivia",
        description="Parchment-themed Bible trivia kiosk. Run with no flags "
                    "for the normal experience.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    display = p.add_argument_group("Display")
    display.add_argument(
        "--single-screen", action="store_true",
        help="Force single-window mode even if multiple monitors are detected.",
    )
    display.add_argument(
        "--simulate-dual", action="store_true",
        help="Open both player and spectator windows side-by-side on the "
             "primary screen. Useful on a single-monitor dev machine.",
    )
    fs = display.add_mutually_exclusive_group()
    fs.add_argument(
        "--fullscreen", action="store_true",
        help="Fullscreen both windows on their assigned screens (kiosk mode).",
    )
    fs.add_argument(
        "--no-fullscreen", action="store_true",
        help="Keep windows windowed regardless of FULLSCREEN_KIOSK config.",
    )
    display.add_argument(
        "--main-screen", type=int, metavar="N", default=None,
        help="Pin the main (player) window to screen index N (see --list-screens).",
    )
    display.add_argument(
        "--spectator-screen", type=int, metavar="N", default=None,
        help="Pin the spectator window to screen index N.",
    )
    display.add_argument(
        "--list-screens", action="store_true",
        help="Print detected screens and exit.",
    )
    display.add_argument(
        "--onscreen-keyboard", "--osk", dest="osk", action="store_true",
        help="Show a tap-friendly QWERTY keyboard on the home screen for "
             "nickname entry. Useful on touchscreen kiosks.",
    )

    tune = p.add_argument_group("Game tuning")
    tune.add_argument(
        "--question-timeout", type=int, metavar="SEC", default=None,
        help="Seconds allowed per question.",
    )
    tune.add_argument(
        "--lives", type=int, metavar="N", default=None,
        help="Starting lives.",
    )
    tune.add_argument(
        "--cycle-interval", type=int, metavar="MS", default=None,
        help="Idle leaderboard rotation interval (ms).",
    )
    tune.add_argument(
        "--crossfade", type=int, metavar="MS", default=None,
        help="Spectator idle <-> play crossfade duration (ms).",
    )

    data = p.add_argument_group("Data")
    data.add_argument(
        "--db", type=str, metavar="PATH", default=None,
        help="Use an alternate SQLite database file (keeps your real one untouched).",
    )
    data.add_argument(
        "--reset-db", action="store_true",
        help="Delete the database file before launching, then reseed questions.",
    )
    data.add_argument(
        "--seed-scores", type=int, metavar="N", default=0,
        help="Insert N synthetic scores spread over the past 60 days, for "
             "leaderboard testing.",
    )

    p.add_argument(
        "-v", "--debug", action="store_true",
        help="Verbose engine logging to stdout.",
    )
    return p.parse_args(argv)


def apply_env_overrides(args: argparse.Namespace) -> None:
    """Translate CLI flags into BT_* env vars before config.py is imported."""
    if args.question_timeout is not None:
        os.environ["BT_QUESTION_TIMEOUT"] = str(args.question_timeout)
    if args.lives is not None:
        os.environ["BT_LIVES"] = str(args.lives)
    if args.cycle_interval is not None:
        os.environ["BT_CYCLE_INTERVAL_MS"] = str(args.cycle_interval)
    if args.crossfade is not None:
        os.environ["BT_CROSSFADE_MS"] = str(args.crossfade)
    if args.single_screen:
        os.environ["BT_DUAL_SCREEN"] = "false"
    if args.fullscreen:
        os.environ["BT_FULLSCREEN"] = "true"
    elif args.no_fullscreen:
        os.environ["BT_FULLSCREEN"] = "false"
    if args.main_screen is not None:
        os.environ["BT_MAIN_SCREEN"] = str(args.main_screen)
    if args.spectator_screen is not None:
        os.environ["BT_SPECTATOR_SCREEN"] = str(args.spectator_screen)
    if args.db:
        os.environ["BT_DB_PATH"] = args.db
    if args.osk:
        os.environ["BT_OSK"] = "true"
    if args.debug:
        os.environ["BT_DEBUG"] = "true"


# Helpers
def _seed_fake_scores(n: int) -> None:
    """Insert N synthetic scores backdated up to 60 days, for leaderboard tests."""
    from db.database import connect

    names = [
        "Asher", "Bezalel", "Caleb", "Deborah", "Elihu", "Faithful", "Gideon",
        "Hannah", "Isaiah", "Jonah", "Keturah", "Lydia", "Malachi", "Naomi",
        "Obadiah", "Peter", "Ruth", "Silas", "Tabitha", "Uriah", "Vashti",
        "Zachariah",
    ]
    rng = random.Random(42)
    with connect() as conn:
        player_ids: dict[str, int] = {}
        for name in names:
            row = conn.execute(
                "SELECT id FROM players WHERE nickname = ?", (name,),
            ).fetchone()
            if row:
                player_ids[name] = row["id"]
            else:
                cur = conn.execute(
                    "INSERT INTO players (nickname) VALUES (?)", (name,),
                )
                player_ids[name] = cur.lastrowid
        for _ in range(n):
            name = rng.choice(names)
            conn.execute(
                "INSERT INTO scores (player_id, score, total_questions, created_at) "
                "VALUES (?, ?, ?, datetime('now', '-' || ? || ' days', '-' || ? || ' hours'))",
                (
                    player_ids[name],
                    rng.randint(100, 4500),
                    rng.randint(3, 25),
                    rng.randint(0, 60),
                    rng.randint(0, 23),
                ),
            )
        conn.commit()


def _print_screens() -> None:
    from PySide6.QtGui import QGuiApplication

    primary = QGuiApplication.primaryScreen()
    for i, s in enumerate(QGuiApplication.screens()):
        geo = s.geometry()
        marker = " (primary)" if s is primary else ""
        print(
            f"[{i}] {s.name()!r:30}  {geo.width():>5}x{geo.height():<5}"
            f"  at ({geo.x()},{geo.y()}){marker}"
        )


def _place_on_screen(window, screen, fullscreen: bool) -> None:
    geo = screen.geometry()
    window.setGeometry(geo)
    window.show()
    handle = window.windowHandle()
    if handle is not None:
        handle.setScreen(screen)
        window.setGeometry(screen.geometry())
    if fullscreen:
        window.showFullScreen()


def _place_at_rect(window, screen, rect) -> None:
    window.setGeometry(rect)
    window.show()
    handle = window.windowHandle()
    if handle is not None:
        handle.setScreen(screen)
        window.setGeometry(rect)


def _pick_screens(screens, dual_enabled, main_idx, spec_idx):
    """Return (main_screen, spectator_screen_or_None)."""
    if not dual_enabled or len(screens) < 2:
        return screens[0], None
    if main_idx is None or spec_idx is None:
        by_area = sorted(
            enumerate(screens),
            key=lambda pair: pair[1].geometry().width() * pair[1].geometry().height(),
        )
        auto_main = by_area[0][0]
        auto_spec = by_area[-1][0]
        if main_idx is None:
            main_idx = auto_main
        if spec_idx is None:
            spec_idx = auto_spec if auto_spec != main_idx else (main_idx + 1) % len(screens)
    main_idx = max(0, min(main_idx, len(screens) - 1))
    spec_idx = max(0, min(spec_idx, len(screens) - 1))
    if spec_idx == main_idx:
        spec_idx = (main_idx + 1) % len(screens)
    return screens[main_idx], screens[spec_idx]


# Main
def main() -> int:
    args = parse_args()
    apply_env_overrides(args)

    from PySide6.QtCore import QRect
    from PySide6.QtGui import QGuiApplication

    import config
    from db.database import init_db
    from db.seed import seed
    from ui.app import build_app
    from ui.main_window import MainWindow
    from ui.spectator.spectator_window import SpectatorWindow

    if args.reset_db:
        try:
            config.DB_PATH.unlink(missing_ok=True)
            print(f"[reset-db] removed {config.DB_PATH}")
        except OSError as exc:
            print(f"[reset-db] failed: {exc}")

    init_db()
    n_seeded = seed()
    if config.DEBUG and n_seeded:
        print(f"[debug] seeded {n_seeded} questions")

    if args.seed_scores > 0:
        _seed_fake_scores(args.seed_scores)
        print(f"[seed-scores] inserted {args.seed_scores} synthetic scores")

    app = build_app()

    if args.list_screens:
        _print_screens()
        return 0

    screens = QGuiApplication.screens()
    spectator: SpectatorWindow | None = None

    if args.simulate_dual:
        primary = QGuiApplication.primaryScreen()
        avail = primary.availableGeometry()
        half_w = avail.width() // 2
        main_rect = QRect(avail.x(), avail.y(), half_w, avail.height())
        spec_rect = QRect(avail.x() + half_w, avail.y(), avail.width() - half_w, avail.height())
        spectator = SpectatorWindow()
        _place_at_rect(spectator, primary, spec_rect)
        window = MainWindow(spectator=spectator)
        _place_at_rect(window, primary, main_rect)
    else:
        main_screen, spectator_screen = _pick_screens(
            screens,
            dual_enabled=config.DUAL_SCREEN_ENABLED,
            main_idx=config.MAIN_SCREEN_INDEX,
            spec_idx=config.SPECTATOR_SCREEN_INDEX,
        )
        if spectator_screen is not None:
            spectator = SpectatorWindow()
            _place_on_screen(spectator, spectator_screen, config.FULLSCREEN_KIOSK)
        window = MainWindow(spectator=spectator)
        _place_on_screen(window, main_screen, config.FULLSCREEN_KIOSK)

    window.activateWindow()
    window.raise_()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
