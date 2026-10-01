from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _secret_or_env(name: str, default: str = "") -> str:
    """Read a secret without making Streamlit mandatory for the core layer."""
    value = os.getenv(name)
    if value:
        return value
    try:
        import streamlit as st  # type: ignore
        secret = st.secrets.get(name, default)
        return str(secret) if secret else default
    except Exception:
        return default


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "AI Insurance Data Analyst V2")
    app_env: str = os.getenv("APP_ENV", "development")
    auth_enabled: bool = _env_bool("AUTH_ENABLED", False)
    data_dir: Path = Path(os.getenv("APP_DATA_DIR", "./data"))
    artifact_dir: Path = Path(os.getenv("APP_ARTIFACT_DIR", "./artifacts"))
    log_dir: Path = Path(os.getenv("APP_LOG_DIR", "./logs"))
    max_upload_mb: int = int(os.getenv("MAX_UPLOAD_MB", "200"))
    google_api_key: str = _secret_or_env("GOOGLE_API_KEY")
    gemini_models: tuple[str, ...] = tuple(
        m.strip() for m in os.getenv(
            "GEMINI_MODELS",
            "gemini-3.5-flash-lite,gemini-3.1-flash-lite,gemini-3.8-flash",
        ).split(",") if m.strip()
    )
    gemini_timeout_seconds: int = int(os.getenv("GEMINI_TIMEOUT_SECONDS", "45"))
    gemini_max_retries: int = int(os.getenv("GEMINI_MAX_RETRIES", "2"))
    users_file: Path = Path(os.getenv("USERS_FILE", "./data/users.json"))

    def ensure_dirs(self) -> None:
        for path in (self.data_dir, self.artifact_dir, self.log_dir):
            path.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "projects").mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_dirs()
