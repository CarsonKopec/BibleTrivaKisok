"""Persist scores and query the leaderboard with time-based filters."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from db.database import connect
from db.models import ScoreRow

Timeframe = Literal["daily", "weekly", "monthly", "all"]

_WINDOW_CLAUSE: dict[Timeframe, str] = {
    "daily": "WHERE s.created_at >= datetime('now', '-1 day')",
    "weekly": "WHERE s.created_at >= datetime('now', '-7 days')",
    "monthly": "WHERE s.created_at >= datetime('now', '-30 days')",
    "all": "",
}


def _get_or_create_player(nickname: str) -> int:
    nickname = nickname.strip()
    with connect() as conn:
        row = conn.execute(
            "SELECT id FROM players WHERE nickname = ?", (nickname,),
        ).fetchone()
        if row:
            return row["id"]
        cur = conn.execute(
            "INSERT INTO players (nickname) VALUES (?)", (nickname,),
        )
        conn.commit()
        return cur.lastrowid


def save_score(nickname: str, score: int, total_questions: int) -> None:
    if not nickname.strip():
        return
    player_id = _get_or_create_player(nickname)
    with connect() as conn:
        conn.execute(
            "INSERT INTO scores (player_id, score, total_questions) "
            "VALUES (?, ?, ?)",
            (player_id, score, total_questions),
        )
        conn.commit()


def top_scores(timeframe: Timeframe = "all", limit: int = 25) -> list[ScoreRow]:
    where = _WINDOW_CLAUSE[timeframe]
    sql = (
        "SELECT p.nickname, s.score, s.total_questions, s.created_at "
        "FROM scores s "
        "JOIN players p ON p.id = s.player_id "
        f"{where} "
        "ORDER BY s.score DESC, s.created_at ASC "
        "LIMIT ?"
    )
    with connect() as conn:
        rows = conn.execute(sql, (limit,)).fetchall()
    result: list[ScoreRow] = []
    for r in rows:
        try:
            created = datetime.fromisoformat(r["created_at"])
        except (TypeError, ValueError):
            created = datetime.utcnow()
        result.append(ScoreRow(
            nickname=r["nickname"],
            score=r["score"],
            total_questions=r["total_questions"],
            created_at=created,
        ))
    return result
