from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from insurance_ai.core.config import settings


class AuthService:
    ROLES = {"admin", "analyst", "business", "manager", "auditor"}

    def __init__(self, users_file: str | Path | None = None):
        self.users_file = Path(users_file or settings.users_file)

    def _load(self) -> dict[str, Any]:
        if not self.users_file.exists():
            return {"users": []}
        return json.loads(self.users_file.read_text(encoding="utf-8"))

    def authenticate(self, username: str, password: str) -> dict[str, Any] | None:
        try:
            import bcrypt  # type: ignore
        except Exception as exc:
            raise RuntimeError("bcrypt n'est pas installé") from exc
        for user in self._load().get("users", []):
            if user.get("username") == username and user.get("active", True):
                hashed = str(user.get("password_hash", "")).encode()
                if hashed and bcrypt.checkpw(password.encode(), hashed):
                    role = user.get("role", "business")
                    if role not in self.ROLES:
                        role = "business"
                    return {"username": username, "role": role, "display_name": user.get("display_name", username)}
        return None
