"""Load questions from the database and serve them in random order."""
from __future__ import annotations

import random
from typing import Iterator, cast

from db.database import connect
from db.models import Answer, Question


class QuestionManager:
    """Holds a shuffled pool of questions and yields them one by one."""

    def __init__(self, shuffle: bool = True):
        self._pool: list[Question] = self._load()
        if shuffle:
            random.shuffle(self._pool)
        self._iter: Iterator[Question] = iter(self._pool)

    @staticmethod
    def _load() -> list[Question]:
        with connect() as conn:
            rows = conn.execute(
                "SELECT id, question, option_a, option_b, option_c, option_d, "
                "correct_answer, difficulty, category FROM questions"
            ).fetchall()
        questions: list[Question] = []
        for row in rows:
            letter = (row["correct_answer"] or "").strip().upper()
            if letter not in ("A", "B", "C", "D"):
                continue
            questions.append(Question(
                id=row["id"],
                text=row["question"],
                options={
                    "A": row["option_a"],
                    "B": row["option_b"],
                    "C": row["option_c"],
                    "D": row["option_d"],
                },
                correct=cast(Answer, letter),
                difficulty=row["difficulty"],
                category=row["category"],
            ))
        return questions

    @property
    def total(self) -> int:
        return len(self._pool)

    def next(self) -> Question:
        """Return the next question. Raises StopIteration when exhausted."""
        return next(self._iter)
