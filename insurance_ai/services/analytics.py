from __future__ import annotations

from typing import Any

import pandas as pd

from insurance_ai.core.models import AnalysisResult


class AnalyticsService:
    """Allow-listed dataframe analytics. No arbitrary exec/eval."""

    OPS = {
        "describe", "count", "sum", "mean", "median", "min", "max", "nunique",
        "groupby_sum", "groupby_mean", "groupby_count", "top_values", "correlation",
    }

    @staticmethod
    def _require_col(df: pd.DataFrame, col: str | None) -> str:
        if not col or col not in df.columns:
            raise ValueError(f"Colonne invalide: {col}")
        return col

    def execute(self, df: pd.DataFrame, plan: dict[str, Any]) -> AnalysisResult:
        op = str(plan.get("operation", "")).strip()
        if op not in self.OPS:
            raise ValueError(f"Opération non autorisée: {op}")
        filters = plan.get("filters") or []
        working = self.apply_filters(df, filters)
        title = str(plan.get("title") or op)
        col = plan.get("column")
        group = plan.get("group_by")

        if op == "describe":
            data = working.describe(include="all").transpose().reset_index(names="column")
            return AnalysisResult(title, "Statistiques descriptives calculées.", data=data, calculation="pandas.DataFrame.describe(include='all')")
        if op == "count":
            value = int(len(working)) if not col else int(working[self._require_col(working, col)].count())
            return AnalysisResult(title, f"Résultat : {value:,}", data=value, calculation="count")
        if op in {"sum", "mean", "median", "min", "max", "nunique"}:
            c = self._require_col(working, col)
            s = working[c]
            if op != "nunique":
                s = pd.to_numeric(s, errors="coerce")
            value = getattr(s, op)() if op != "nunique" else s.nunique(dropna=True)
            value = float(value) if op != "nunique" and pd.notna(value) else int(value) if op == "nunique" else None
            return AnalysisResult(title, f"Résultat : {value}", data=value, calculation=f"{op}({c})")
        if op.startswith("groupby_"):
            g = self._require_col(working, group)
            c = self._require_col(working, col) if col else None
            agg = op.split("_", 1)[1]
            if agg == "count":
                data = working.groupby(g, dropna=False).size().reset_index(name="count")
            else:
                if c is None:
                    raise ValueError("column requis")
                numeric = pd.to_numeric(working[c], errors="coerce")
                tmp = working.assign(__value=numeric)
                data = tmp.groupby(g, dropna=False)["__value"].agg(agg).reset_index(name=c)
            sort_col = data.columns[-1]
            data = data.sort_values(sort_col, ascending=False).reset_index(drop=True)
            return AnalysisResult(title, f"Agrégation {agg} par {g} calculée.", data=data, calculation=f"groupby({g}).{agg}({c or '*'})")
        if op == "top_values":
            c = self._require_col(working, col)
            n = max(1, min(int(plan.get("n", 10)), 100))
            data = working[c].value_counts(dropna=False).head(n).rename_axis(c).reset_index(name="count")
            return AnalysisResult(title, f"Top {n} modalités de {c}.", data=data, calculation=f"value_counts({c}).head({n})")
        if op == "correlation":
            numeric = working.select_dtypes(include="number")
            data = numeric.corr(numeric_only=True)
            return AnalysisResult(title, "Matrice de corrélation calculée.", data=data, calculation="corr(numeric_only=True)")
        raise AssertionError("Opération non traitée")

    @staticmethod
    def apply_filters(df: pd.DataFrame, filters: list[dict[str, Any]]) -> pd.DataFrame:
        out = df
        for f in filters:
            col = f.get("column")
            op = f.get("operator")
            value = f.get("value")
            if col not in out.columns:
                raise ValueError(f"Colonne de filtre invalide: {col}")
            s = out[col]
            typed_value = value
            if pd.api.types.is_numeric_dtype(s) and isinstance(value, str):
                try:
                    typed_value = float(value)
                except ValueError:
                    typed_value = value
            elif pd.api.types.is_datetime64_any_dtype(s) and isinstance(value, str):
                parsed = pd.to_datetime(value, errors="coerce")
                typed_value = parsed if pd.notna(parsed) else value
            if op == "==": out = out[s == typed_value]
            elif op == "!=": out = out[s != typed_value]
            elif op == ">": out = out[s > typed_value]
            elif op == ">=": out = out[s >= typed_value]
            elif op == "<": out = out[s < typed_value]
            elif op == "<=": out = out[s <= typed_value]
            elif op == "contains": out = out[s.astype(str).str.contains(str(value), case=False, na=False, regex=False)]
            else: raise ValueError(f"Opérateur de filtre interdit: {op}")
        return out.copy()
