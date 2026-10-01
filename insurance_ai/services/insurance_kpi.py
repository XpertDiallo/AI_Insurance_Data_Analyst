from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass
class KPIResult:
    code: str
    label: str
    value: float | None
    unit: str
    formula: str
    notes: str = ""


class InsuranceKPIService:
    """Deterministic insurance KPI library."""

    @staticmethod
    def _sum(df: pd.DataFrame, col: str) -> float:
        if col not in df.columns:
            raise KeyError(col)
        return float(pd.to_numeric(df[col], errors="coerce").fillna(0).sum())

    @staticmethod
    def _safe_div(num: float, den: float) -> float | None:
        if den == 0 or pd.isna(den):
            return None
        return float(num / den)

    def loss_ratio(self, df: pd.DataFrame, claims_col: str, premium_col: str) -> KPIResult:
        claims = self._sum(df, claims_col)
        premium = self._sum(df, premium_col)
        value = self._safe_div(claims, premium)
        return KPIResult("loss_ratio", "Ratio de sinistralité", value, "%", "Sinistres / Primes")

    def average_claim_cost(self, df: pd.DataFrame, claims_col: str, claim_id_col: str | None = None) -> KPIResult:
        claims = self._sum(df, claims_col)
        if claim_id_col and claim_id_col in df.columns:
            count = int(df.loc[pd.to_numeric(df[claims_col], errors="coerce").fillna(0) != 0, claim_id_col].nunique())
        else:
            count = int((pd.to_numeric(df[claims_col], errors="coerce").fillna(0) != 0).sum())
        value = self._safe_div(claims, float(count))
        return KPIResult("avg_claim_cost", "Coût moyen des sinistres", value, "currency", "Montant sinistres / Nombre de sinistres")

    def claim_frequency(self, df: pd.DataFrame, claim_id_col: str, exposure_col: str | None = None) -> KPIResult:
        if claim_id_col not in df.columns:
            raise KeyError(claim_id_col)
        claims = float(df[claim_id_col].dropna().nunique())
        if exposure_col:
            exposure = self._sum(df, exposure_col)
            formula = "Nombre de sinistres / Exposition"
        else:
            exposure = float(len(df))
            formula = "Nombre de sinistres / Nombre de lignes (proxy d'exposition)"
        value = self._safe_div(claims, exposure)
        return KPIResult("claim_frequency", "Fréquence sinistres", value, "%", formula)

    def collection_rate(self, df: pd.DataFrame, collected_col: str, written_col: str) -> KPIResult:
        collected = self._sum(df, collected_col)
        written = self._sum(df, written_col)
        return KPIResult("collection_rate", "Taux d'encaissement", self._safe_div(collected, written), "%", "Primes encaissées / Primes émises")

    def cession_rate(self, df: pd.DataFrame, ceded_premium_col: str, gross_premium_col: str) -> KPIResult:
        ceded = self._sum(df, ceded_premium_col)
        gross = self._sum(df, gross_premium_col)
        return KPIResult("cession_rate", "Taux de cession", self._safe_div(ceded, gross), "%", "Primes cédées / Primes brutes")

    def retention_rate(self, df: pd.DataFrame, net_premium_col: str, gross_premium_col: str) -> KPIResult:
        net = self._sum(df, net_premium_col)
        gross = self._sum(df, gross_premium_col)
        return KPIResult("retention_rate", "Taux de rétention", self._safe_div(net, gross), "%", "Primes nettes / Primes brutes")

    def growth_rate(self, current: float, previous: float) -> KPIResult:
        value = self._safe_div(current - previous, previous)
        return KPIResult("growth_rate", "Taux de croissance", value, "%", "(N - N-1) / N-1")

    @staticmethod
    def as_display(result: KPIResult) -> dict[str, Any]:
        value = result.value
        if value is None:
            display = "N/A"
        elif result.unit == "%":
            display = f"{value * 100:,.2f}%"
        else:
            display = f"{value:,.2f}"
        return {**result.__dict__, "display": display}
