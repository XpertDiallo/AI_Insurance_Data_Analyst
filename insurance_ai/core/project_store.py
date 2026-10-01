from __future__ import annotations

import hashlib
import json
import shutil
import uuid
from pathlib import Path
from typing import Any

import pandas as pd

from .config import settings
from .models import DatasetMeta, TransformationRecord, utc_now_iso


class ProjectStore:
    """Local project store. Production deployments can replace this adapter with S3/DB storage."""

    def __init__(self, base_dir: str | Path | None = None):
        self.base_dir = Path(base_dir or settings.data_dir / "projects")
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def create_project(self, name: str, owner: str = "anonymous") -> str:
        project_id = uuid.uuid4().hex[:12]
        root = self.base_dir / project_id
        for folder in ("datasets", "metadata", "reports"):
            (root / folder).mkdir(parents=True, exist_ok=True)
        meta = {"project_id": project_id, "name": name, "owner": owner, "created_at": utc_now_iso()}
        (root / "project.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        (root / "transformations.jsonl").touch()
        return project_id

    @staticmethod
    def _safe_identifier(value: str, label: str) -> str:
        """Validate identifiers used as path components."""
        value = str(value)
        if not value or value in {".", ".."} or Path(value).name != value:
            raise ValueError(f"Identifiant {label} invalide.")
        return value

    def project_dir(self, project_id: str) -> Path:
        project_id = self._safe_identifier(project_id, "projet")
        root = (self.base_dir / project_id).resolve()
        if root.parent != self.base_dir.resolve():
            raise ValueError("Chemin de projet invalide.")
        if not root.exists():
            raise FileNotFoundError(f"Projet introuvable: {project_id}")
        return root

    def list_projects(self) -> list[dict[str, Any]]:
        projects = []
        for p in self.base_dir.iterdir():
            meta = p / "project.json"
            if p.is_dir() and meta.exists():
                try:
                    projects.append(json.loads(meta.read_text(encoding="utf-8")))
                except Exception:
                    continue
        return sorted(projects, key=lambda x: x.get("created_at", ""), reverse=True)

    @staticmethod
    def dataframe_fingerprint(df: pd.DataFrame) -> str:
        try:
            hashed = pd.util.hash_pandas_object(df, index=True).values.tobytes()
        except TypeError:
            # Nested JSON-like objects can be unhashable; stringify deterministically.
            hashed = df.astype(str).to_csv(index=True).encode("utf-8")
        return hashlib.sha256(hashed).hexdigest()

    def save_dataframe(
        self,
        project_id: str,
        df: pd.DataFrame,
        *,
        name: str,
        stage: str,
        source_type: str,
        source_name: str,
        parent_id: str | None = None,
    ) -> DatasetMeta:
        root = self.project_dir(project_id)
        dataset_id = uuid.uuid4().hex[:12]
        path = root / "datasets" / f"{dataset_id}_{stage.lower()}.parquet"
        try:
            df.to_parquet(path, index=False)
        except Exception:
            path = path.with_suffix(".csv")
            df.to_csv(path, index=False)
        meta = DatasetMeta(
            dataset_id=dataset_id,
            project_id=project_id,
            name=name,
            source_type=source_type,
            source_name=source_name,
            stage=stage.upper(),
            parent_id=parent_id,
            row_count=len(df),
            column_count=len(df.columns),
            fingerprint=self.dataframe_fingerprint(df),
            # Relative metadata remains valid when the project is moved or mounted.
            file_path=str(path.relative_to(root)),
        )
        (root / "metadata" / f"{dataset_id}.json").write_text(
            json.dumps(meta.to_dict(), indent=2), encoding="utf-8"
        )
        return meta

    def load_dataframe(self, project_id: str, dataset_id: str) -> pd.DataFrame:
        meta = self.get_dataset_meta(project_id, dataset_id)
        root = self.project_dir(project_id)
        raw_path = Path(meta["file_path"])
        path = raw_path if raw_path.is_absolute() else root / raw_path
        path = path.resolve()
        if root not in path.parents:
            raise ValueError("Chemin de dataset invalide.")
        if path.suffix.lower() == ".parquet":
            return pd.read_parquet(path)
        return pd.read_csv(path)

    def get_dataset_meta(self, project_id: str, dataset_id: str) -> dict[str, Any]:
        dataset_id = self._safe_identifier(dataset_id, "dataset")
        path = self.project_dir(project_id) / "metadata" / f"{dataset_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"Dataset introuvable: {dataset_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def list_datasets(self, project_id: str) -> list[dict[str, Any]]:
        meta_dir = self.project_dir(project_id) / "metadata"
        rows = []
        for path in meta_dir.glob("*.json"):
            rows.append(json.loads(path.read_text(encoding="utf-8")))
        return sorted(rows, key=lambda x: x.get("created_at", ""), reverse=True)

    def log_transformation(self, project_id: str, record: TransformationRecord) -> None:
        path = self.project_dir(project_id) / "transformations.jsonl"
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record.to_dict(), default=str) + "\n")

    def transformation_history(self, project_id: str) -> list[dict[str, Any]]:
        path = self.project_dir(project_id) / "transformations.jsonl"
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
