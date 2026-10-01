from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class DatasetMeta:
    dataset_id: str
    project_id: str
    name: str
    source_type: str
    source_name: str
    stage: str = "RAW"
    parent_id: str | None = None
    created_at: str = field(default_factory=utc_now_iso)
    row_count: int = 0
    column_count: int = 0
    fingerprint: str = ""
    file_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TransformationRecord:
    transformation_id: str
    dataset_id: str
    operation: str
    column: str | None
    parameters: dict[str, Any]
    rows_before: int
    rows_after: int
    user: str = "anonymous"
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AnalysisResult:
    title: str
    answer: str
    data: Any = None
    chart_spec: dict[str, Any] | None = None
    calculation: str = ""
    warnings: list[str] = field(default_factory=list)


@dataclass
class ReportPayload:
    title: str
    subtitle: str
    executive_summary: str
    kpis: list[dict[str, Any]] = field(default_factory=list)
    tables: list[dict[str, Any]] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    charts: list[dict[str, Any]] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
