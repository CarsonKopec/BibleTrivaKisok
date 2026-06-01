"""Read-only ranked table used by the leaderboard screen."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHeaderView, QTableWidget, QTableWidgetItem

from db.models import ScoreRow


class LeaderboardTable(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LeaderboardTable")
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(["#", "Nickname", "Score", "Date"])
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setShowGrid(False)
        self.setAlternatingRowColors(True)

        hdr = self.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

    def populate(self, rows: list[ScoreRow]) -> None:
        self.setRowCount(len(rows))
        for i, row in enumerate(rows):
            cells = [
                str(i + 1),
                row.nickname,
                str(row.score),
                row.created_at.strftime("%Y-%m-%d"),
            ]
            for col, value in enumerate(cells):
                item = QTableWidgetItem(value)
                if col != 1:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.setItem(i, col, item)
