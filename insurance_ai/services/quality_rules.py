from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass
class RuleResult:
    rule: dict[str, Any]
    passed: bool
    violations: int
    violation_pct: float
    message: str


class DataQualityRuleEngine:
    RULE_TYPES = {"not_null", "unique", "non_negative", "allowed_values", "date_order"}

    def evaluate(self, df: pd.DataFrame, rules: list[dict[str, Any]]) -> list[RuleResult]:
        results: list[RuleResult] = []
        for rule in rules:
            rtype = rule.get("type")
            if rtype not in self.RULE_TYPES:
                raise ValueError(f"Règle non supportée: {rtype}")
            if rtype == "not_null":
                col = self._col(df, rule.get("column"))
                mask = df[col].isna()
                message = f"{col} doit être renseigné"
            elif rtype == "unique":
                col = self._col(df, rule.get("column"))
                mask = df[col].notna() & df[col].duplicated(keep=False)
                message = f"{col} doit être unique"
            elif rtype == "non_negative":
                col = self._col(df, rule.get("column"))
                numeric = pd.to_numeric(df[col], errors="coerce")
                mask = numeric.notna() & (numeric < 0)
                message = f"{col} doit être >= 0"
            elif rtype == "allowed_values":
                col = self._col(df, rule.get("column"))
                allowed = set(rule.get("values") or [])
                mask = df[col].notna() & ~df[col].isin(allowed)
                message = f"{col} contient des valeurs hors référentiel"
            else:
                start = self._col(df, rule.get("start_column"))
                end = self._col(df, rule.get("end_column"))
                s = pd.to_datetime(df[start], errors="coerce")
                e = pd.to_datetime(df[end], errors="coerce")
                mask = s.notna() & e.notna() & (e < s)
                message = f"{end} doit être >= {start}"
            violations = int(mask.sum())
            pct = float(violations / max(len(df), 1) * 100)
            results.append(RuleResult(rule, violations == 0, violations, round(pct, 2), message))
        return results

    @staticmethod
    def _col(df: pd.DataFrame, value: Any) -> str:
        if value not in df.columns:
            raise ValueError(f"Colonne inconnue: {value}")
        return str(value)
