"""Typed records returned by the data layer."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

Answer = Literal["A", "B", "C", "D"]


@dataclass(frozen=True)
class Question:
    id: int
    text: str
    options: dict[Answer, str]
    correct: Answer
    difficulty: str | None = None
    category: str | None = None


@dataclass(frozen=True)
class Player:
    id: int
    nickname: str


@dataclass(frozen=True)
class ScoreRow:
    nickname: str
    score: int
    total_questions: int
    created_at: datetime
