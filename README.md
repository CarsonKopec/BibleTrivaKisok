# Bible Trivia Kiosk

An arcade-style Bible trivia game with a parchment-themed PySide6 UI, SQLite
persistence, multi-timeframe leaderboards, and optional Raspberry Pi GPIO
button input. Built to the spec in [GUIDE.md](GUIDE.md).

## Features

- 30+ multiple-choice Bible trivia questions (easy / medium across OT, NT, general)
- 3 lives, 10-second per-question timer that does not freeze the UI
- Streak bonus scoring (`+25` per consecutive correct, capped at `+125`)
- Hall of Records leaderboard with Daily / Weekly / Monthly / All-Time filters
- **Dual-screen kiosk mode**: small touchscreen runs the menu and accepts input;
  HDMI cycles the leaderboard while idle and crossfades into a big spectator
  view (question, options, lives, score, timer) during a round
- Keyboard input (A/B/C/D or 1/2/3/4) — works out of the box
- Optional Raspberry Pi GPIO buttons (GPIO 17/18/27/22) — auto-disabled off-Pi
- Parchment & gold themed `.qss` stylesheet with hover, correct/wrong, and
  low-time visual feedback

## Project layout

```
.
├── main.py                # Entry point
├── config.py              # Paths, palette, game constants
├── db/                    # SQLite connection, models, seed
├── game/                  # Engine (timer/lives/score), questions, scoreboard
├── input/                 # Pluggable keyboard + GPIO input handlers
├── ui/
│   ├── app.py             # QApplication bootstrap + stylesheet loader
│   ├── main_window.py     # QStackedWidget host + navigation/input router
│   ├── screens/           # home / game / results / leaderboard
│   ├── spectator/         # HDMI window: idle leaderboard + play view
│   └── widgets/           # answer_button, question_card, crossfade_stack, …
├── assets/
│   ├── styles.qss         # Parchment theme
│   ├── sounds/            # (placeholder)
│   └── fonts/             # (placeholder)
└── data/
    └── bible_trivia.db    # Auto-created on first run
```

## Desktop usage (Windows / macOS / Linux)

Requires **conda** (Anaconda or Miniconda).

```powershell
# 1. Create the environment (Python 3.11 + PySide6 from conda-forge)
conda env create -f environment.yml

# 2. Activate it
conda activate bible-trivia

# 3. Run
python main.py
```

To update later: `conda env update -f environment.yml --prune`
To remove: `conda env remove -n bible-trivia`

> Prefer pip/venv? `python -m venv .venv` + `pip install -r requirements.txt`
> still works.

The database (`data/bible_trivia.db`) is created automatically on first launch
and seeded with the starter question bank.

### Keyboard controls

Multiple input styles are supported simultaneously so you can play with whatever's
comfortable — and the arrow keys mirror the Pi's physical D-pad for parity testing.

| Key                       | Maps to    |
| ------------------------- | ---------- |
| `A` `B` `C` `D`           | A / B / C / D |
| `1` `2` `3` `4`           | A / B / C / D |
| `↑` Up                    | A (top-left)     |
| `→` Right                 | B (top-right)    |
| `←` Left                  | C (bottom-left)  |
| `↓` Down                  | D (bottom-right) |
| `Enter` (home screen)     | Begin Challenge with typed name |

Each on-screen answer button shows both its letter and the matching arrow so the
mapping is visible at a glance.

## Raspberry Pi usage

Tested approach: a Pi running Raspberry Pi OS (Bookworm or later) wired to
four momentary push buttons.

```bash
sudo apt update && sudo apt install -y python3-pip python3-venv
git clone <this repo>            # or copy the folder over
cd BibleTrivaKisok

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
pip install gpiozero               # Pi only

python main.py
```

### GPIO wiring (4-direction pad)

Wire the four physical directional buttons as follows. Each button connects
between its GPIO pin and ground; `gpiozero.Button` enables the internal pull-up
automatically.

| Physical button | BCM pin | Sends |
| --------------- | ------- | ----- |
| Up    `↑`       | GPIO 17 | A (top-left)     |
| Right `→`       | GPIO 18 | B (top-right)    |
| Left  `←`       | GPIO 27 | C (bottom-left)  |
| Down  `↓`       | GPIO 22 | D (bottom-right) |

If you wire to different pins, update `GPIO_PINS` in [config.py](config.py).
The keyboard handler stays active alongside the GPIO handler, so the arrow
keys on any attached keyboard work too — useful for testing the same layout
on a PC before deploying.

If `gpiozero` is not installed (or the pins can't be claimed), the GPIO
backend silently disables itself — keyboard play continues to work.

## Command-line flags (debugging)

```powershell
python main.py [flags]
python main.py --help        # full list
```

Common debugging recipes:

```powershell
# Single-monitor dev: open both windows side-by-side on this screen
python main.py --simulate-dual

# Disable the spectator window even if a second monitor is attached
python main.py --single-screen

# Fast-iterate the timeout flow (3-second questions)
python main.py --question-timeout 3 --lives 5

# Speed up the idle leaderboard rotation to see the slide animation quickly
python main.py --cycle-interval 1500

# Fill the leaderboard with 50 synthetic scores spread over the last 60 days
python main.py --seed-scores 50

# Sandbox DB: don't touch your real bible_trivia.db
python main.py --db data/dev.db --reset-db --seed-scores 30

# Diagnose screen detection
python main.py --list-screens

# 4-button kiosk — show the horizontal-picker OSK for nickname entry
python main.py --onscreen-keyboard          # or the shorter --osk
```

### OSK controls (4-direction kiosk)

The OSK is a horizontal letter picker driven by the same 4 directional inputs as
the game (arrow keys on a PC, GPIO buttons on the Pi):

| Input            | Action |
| ---------------- | --------------------------------------- |
| `←` / `→`        | Scroll through letters (wraps A↔Z, with SPACE at the end) |
| `↑`              | Add the highlighted letter to the nickname |
| `↓`              | Backspace |
| `←` + `→`        | Hold both at once to submit the nickname |

The chord requires both keys to be *held simultaneously* (not just pressed in
sequence), so reversing a mis-scroll won't accidentally submit.

All flags pass through to env vars (`BT_*`) that `config.py` reads, so they
compose cleanly with whatever's already set in [config.py](config.py).

## Dual-screen kiosk mode

When the app detects two or more displays it spawns a second window on the
larger screen.

| State    | Small screen (player)        | HDMI / large screen (audience)              |
| -------- | ---------------------------- | ------------------------------------------- |
| Idle     | Home menu, nickname entry    | Leaderboard, auto-cycles every 8s through Daily → Weekly → Monthly → All-Time, with a "Step up to the kiosk" prompt |
| Playing  | Question, lives, timer, answer buttons | Same game state in larger fonts (read-only spectator view) |
| Results  | Final score + replay/return  | Returns to idle leaderboard so the room sees the refreshed standings |

Transitions between idle and play are a ~400 ms opacity crossfade.

### Config (see [config.py](config.py))

```python
DUAL_SCREEN_ENABLED   = True     # set False to force single-window
FULLSCREEN_KIOSK      = False    # set True on the Pi
MAIN_SCREEN_INDEX     = None     # None = auto (smaller screen → main)
SPECTATOR_SCREEN_INDEX = None    # None = auto (larger screen → spectator)
IDLE_CYCLE_INTERVAL_MS = 8000
CROSSFADE_MS           = 400
```

If only one screen is connected, the spectator window is skipped silently and
the app runs exactly as the single-window build. Useful for desktop dev.

### Kiosk tips (Raspberry Pi)

To launch fullscreen at boot, create
`~/.config/autostart/bible-trivia.desktop`:

```ini
[Desktop Entry]
Type=Application
Name=Bible Trivia
Exec=/home/pi/BibleTrivaKisok/.venv/bin/python /home/pi/BibleTrivaKisok/main.py
X-GNOME-Autostart-enabled=true
```

You can also hide the cursor with `unclutter`. For fullscreen kiosk mode set
`FULLSCREEN_KIOSK = True` in [config.py](config.py) — both windows will
fullscreen onto their assigned displays.

## Resetting / refilling the question bank

`db/seed.py` is idempotent — running again does nothing if questions already
exist. To wipe and reseed:

```powershell
python -c "from db.seed import seed; print(seed(force=True), 'questions seeded')"
```

Or delete `data/bible_trivia.db` and rerun `python main.py`.
