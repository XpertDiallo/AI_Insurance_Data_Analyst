from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any

from .config import settings
from .models import utc_now_iso

LOGGER = logging.getLogger("insurance_ai.audit")


class AuditLogger:
    def __init__(self, db_path: str | Path | None = None):
        self.db_path = Path(db_path or settings.data_dir / "audit.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    user TEXT NOT NULL,
                    project_id TEXT,
                    event_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    details_json TEXT NOT NULL
                )
                """
            )

    def log(
        self,
        event_type: str,
        details: dict[str, Any] | None = None,
        *,
        user: str = "anonymous",
        project_id: str | None = None,
        status: str = "ok",
    ) -> None:
        safe_details = details or {}
        with self._connect() as con:
            con.execute(
                "INSERT INTO audit_events(created_at,user,project_id,event_type,status,details_json) VALUES(?,?,?,?,?,?)",
                (utc_now_iso(), user, project_id, event_type, status, json.dumps(safe_details, default=str)),
            )

    def recent(self, limit: int = 100, project_id: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT created_at,user,project_id,event_type,status,details_json FROM audit_events"
        params: list[Any] = []
        if project_id:
            query += " WHERE project_id = ?"
            params.append(project_id)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        with self._connect() as con:
            rows = con.execute(query, params).fetchall()
        result = []
        for created_at, user, pid, event_type, status, details_json in rows:
            result.append({
                "created_at": created_at,
                "user": user,
                "project_id": pid,
                "event_type": event_type,
                "status": status,
                "details": json.loads(details_json),
            })
        return result
