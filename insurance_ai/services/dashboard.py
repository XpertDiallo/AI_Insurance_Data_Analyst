from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import re
import unicodedata

import pandas as pd

from .insurance_kpi import InsuranceKPIService


@dataclass
class DashboardData:
    cards: list[dict[str, Any]]
    premium_claims_by_group: pd.DataFrame | None
    monthly_trend: pd.DataFrame | None
    top_claims: pd.DataFrame | None


class DashboardService:
    PREMIUM_TOKENS = (
        "premium", "prime", "cotisation", "written", "collected", "earned", "ceded", "cession",
    )
    CLAIM_TOKENS = (
        "claim_amount", "claims_amount", "claim_cost", "claims_cost", "sinistre", "sinistres",
        "indemnity", "indemnisation", "loss_amount", "incurred_loss",
    )

    def __init__(self):
        self.kpis = InsuranceKPIService()

    @staticmethod
    def _normalized_name(column: Any) -> str:
        value = unicodedata.normalize("NFKD", str(column)).encode("ascii", "ignore").decode("ascii")
        return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")

    @classmethod
    def metric_columns(cls, df: pd.DataFrame, metric: str) -> list[str]:
        """Return numeric columns matching the requested insurance concept."""
        tokens = cls.PREMIUM_TOKENS if metric == "premium" else cls.CLAIM_TOKENS if metric == "claims" else ()
        if not tokens:
            raise ValueError("Métrique dashboard non supportée.")
        columns = []
        for column in df.select_dtypes(include="number").columns:
            name = cls._normalized_name(column)
            # Never expose technical identifiers as financial measures.
            if name.endswith("_id") or name in {"id", "identifier"}:
                continue
            if any(token in name for token in tokens):
                columns.append(str(column))
        return columns

    def portfolio_overview(
        self,
        df: pd.DataFrame,
        *,
        premium_col: str,
        claims_col: str,
        group_col: str | None = None,
        date_col: str | None = None,
        top_n: int = 10,
    ) -> DashboardData:
        premium = self.kpis._sum(df, premium_col)
        claims = self.kpis._sum(df, claims_col)
        lr = self.kpis.loss_ratio(df, claims_col, premium_col)
        cards = [
            {"label": "Primes", "value": premium},
            {"label": "Sinistres", "value": claims},
            {"label": "S/P", "value": None if lr.value is None else lr.value * 100, "unit": "%"},
            {"label": "Lignes", "value": len(df)},
        ]

        by_group = None
        if group_col and group_col in df.columns:
            tmp = df.copy()
            tmp["__premium"] = pd.to_numeric(tmp[premium_col], errors="coerce").fillna(0)
            tmp["__claims"] = pd.to_numeric(tmp[claims_col], errors="coerce").fillna(0)
            by_group = tmp.groupby(group_col, dropna=False)[["__premium", "__claims"]].sum().reset_index()
            by_group = by_group.rename(columns={"__premium": "premium", "__claims": "claims"})
            by_group["loss_ratio"] = by_group.apply(
                lambda r: (r["claims"] / r["premium"]) if r["premium"] else None, axis=1
            )

        monthly = None
        if date_col and date_col in df.columns:
            tmp = df.copy()
            tmp["__date"] = pd.to_datetime(tmp[date_col], errors="coerce")
            tmp = tmp[tmp["__date"].notna()].copy()
            if not tmp.empty:
                tmp["month"] = tmp["__date"].dt.to_period("M").astype(str)
                tmp["__premium"] = pd.to_numeric(tmp[premium_col], errors="coerce").fillna(0)
                tmp["__claims"] = pd.to_numeric(tmp[claims_col], errors="coerce").fillna(0)
                monthly = tmp.groupby("month")[["__premium", "__claims"]].sum().reset_index()
                monthly = monthly.rename(columns={"__premium": "premium", "__claims": "claims"})

        tmp_claims = df.copy()
        tmp_claims["__claims"] = pd.to_numeric(tmp_claims[claims_col], errors="coerce")
        top_claims = tmp_claims.nlargest(min(top_n, len(tmp_claims)), "__claims").drop(columns="__claims")

        return DashboardData(cards, by_group, monthly, top_claims)
