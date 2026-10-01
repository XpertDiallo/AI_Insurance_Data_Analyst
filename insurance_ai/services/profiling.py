from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass
class ProfileResult:
    summary: dict[str, Any]
    columns: pd.DataFrame
    duplicate_rows: int
    quality_score: float
    warnings: list[str]


class ProfilingService:
    @staticmethod
    def _infer_semantic_type(series: pd.Series) -> str:
        if pd.api.types.is_datetime64_any_dtype(series):
            return "datetime"
        if pd.api.types.is_numeric_dtype(series):
            return "numeric"
        non_null = series.dropna()
        if non_null.empty:
            return "unknown"
        # Date coercion only if a meaningful proportion parses.
        if series.dtype == object:
            sample = non_null.astype(str).head(200)
            # Avoid interpreting arbitrary IDs/text as dates. Only attempt date parsing
            # when most sampled values visually resemble a date.
            date_like = sample.str.match(r"^\s*\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}(?:[ T].*)?\s*$")
            if float(date_like.mean()) >= 0.70:
                date_ratio = pd.to_datetime(sample.where(date_like), errors="coerce", dayfirst=True).notna().mean()
                if date_ratio >= 0.70:
                    return "datetime_candidate"
            numeric_ratio = pd.to_numeric(sample.str.replace(" ", "", regex=False).str.replace(",", ".", regex=False), errors="coerce").notna().mean()
            if numeric_ratio >= 0.9:
                return "numeric_candidate"
            if non_null.nunique(dropna=True) <= max(30, int(len(non_null) * 0.05)):
                return "categorical"
        return "text"

    def profile(self, df: pd.DataFrame) -> ProfileResult:
        if not isinstance(df, pd.DataFrame):
            raise TypeError("df doit être un DataFrame pandas")
        rows = len(df)
        cols = len(df.columns)
        details = []
        total_cells = max(rows * cols, 1)
        missing_cells = int(df.isna().sum().sum())
        duplicate_rows = int(df.duplicated().sum())
        warnings: list[str] = []

        for col in df.columns:
            s = df[col]
            detail: dict[str, Any] = {
                "column": str(col),
                "dtype": str(s.dtype),
                "semantic_type": self._infer_semantic_type(s),
                "missing": int(s.isna().sum()),
                "missing_pct": round(float(s.isna().mean() * 100), 2) if rows else 0.0,
                "unique": int(s.nunique(dropna=True)),
                "unique_pct": round(float(s.nunique(dropna=True) / max(rows, 1) * 100), 2),
                "sample": ", ".join(map(str, s.dropna().astype(str).head(3).tolist())),
            }
            if pd.api.types.is_numeric_dtype(s):
                clean = pd.to_numeric(s, errors="coerce")
                detail.update({
                    "min": float(clean.min()) if clean.notna().any() else None,
                    "max": float(clean.max()) if clean.notna().any() else None,
                    "mean": float(clean.mean()) if clean.notna().any() else None,
                    "median": float(clean.median()) if clean.notna().any() else None,
                })
            details.append(detail)

        completeness = 100.0 * (1 - missing_cells / total_cells)
        uniqueness_penalty = 100.0 * duplicate_rows / max(rows, 1)
        validity = 100.0
        candidate_count = sum(1 for d in details if str(d["semantic_type"]).endswith("_candidate"))
        if cols:
            validity -= min(25.0, candidate_count / cols * 25.0)
        score = max(0.0, min(100.0, 0.55 * completeness + 0.25 * (100 - uniqueness_penalty) + 0.20 * validity))

        if missing_cells:
            warnings.append(f"{missing_cells} valeur(s) manquante(s) détectée(s).")
        if duplicate_rows:
            warnings.append(f"{duplicate_rows} ligne(s) dupliquée(s) détectée(s).")
        if candidate_count:
            warnings.append(f"{candidate_count} colonne(s) méritent une vérification de type.")

        return ProfileResult(
            summary={
                "rows": rows,
                "columns": cols,
                "missing_cells": missing_cells,
                "missing_pct": round(missing_cells / total_cells * 100, 2),
                "duplicate_rows": duplicate_rows,
                "memory_mb": round(float(df.memory_usage(deep=True).sum() / (1024**2)), 3),
            },
            columns=pd.DataFrame(details),
            duplicate_rows=duplicate_rows,
            quality_score=round(score, 2),
            warnings=warnings,
        )

    @staticmethod
    def outliers_iqr(series: pd.Series, factor: float = 1.5) -> pd.Series:
        s = pd.to_numeric(series, errors="coerce")
        q1, q3 = s.quantile([0.25, 0.75])
        iqr = q3 - q1
        if pd.isna(iqr) or iqr == 0:
            return pd.Series(False, index=series.index)
        lower, upper = q1 - factor * iqr, q3 + factor * iqr
        return (s < lower) | (s > upper)
