from __future__ import annotations

import json
import re
from typing import Any

import pandas as pd

from insurance_ai.core.models import AnalysisResult
from insurance_ai.services.analytics import AnalyticsService
from insurance_ai.services.gemini_manager import GeminiModelManager


class AnalysisAgent:
    """Plans natural-language analysis, then executes only allow-listed operations."""

    def __init__(self, llm: GeminiModelManager | None = None, analytics: AnalyticsService | None = None):
        self.llm = llm or GeminiModelManager()
        self.analytics = analytics or AnalyticsService()

    @staticmethod
    def _schema_summary(df: pd.DataFrame) -> str:
        rows = []
        for col in df.columns[:100]:
            s = df[col]
            rows.append(f"- {col}: dtype={s.dtype}, non_null={int(s.notna().sum())}, unique={int(s.nunique(dropna=True))}")
        return "\n".join(rows)

    def plan(self, question: str, df: pd.DataFrame) -> dict[str, Any]:
        if self.llm.enabled:
            prompt = f"""
You are the planning component of a secure insurance data analyst.
Return ONLY one JSON object. Never return Python or SQL.
Choose exactly one operation from:
{sorted(self.analytics.OPS)}

Schema:
{self._schema_summary(df)}

User question:
{question}

JSON fields:
operation (required), title, column (optional), group_by (optional), n (optional integer 1..100),
filters (optional list of objects with column/operator/value; operator only ==,!=,>,>=,<,<=,contains),
chart_type (optional: bar,line,histogram,scatter,box,none),
x (optional column), y (optional column).
If the question is ambiguous, set operation to describe and title to a short clarification-oriented label.
"""
            payload, _ = self.llm.generate_json(prompt)
            return self._validate_plan(payload, df)
        return self._heuristic_plan(question, df)

    def _validate_plan(self, plan: dict[str, Any], df: pd.DataFrame) -> dict[str, Any]:
        op = plan.get("operation")
        if op not in self.analytics.OPS:
            raise ValueError(f"Plan interdit: {op}")
        for key in ("column", "group_by", "x", "y"):
            value = plan.get(key)
            if value is not None and value not in df.columns:
                raise ValueError(f"Colonne inconnue dans le plan: {value}")
        allowed_filter_ops = {"==", "!=", ">", ">=", "<", "<=", "contains"}
        clean_filters = []
        for f in plan.get("filters") or []:
            if f.get("column") not in df.columns or f.get("operator") not in allowed_filter_ops:
                continue
            clean_filters.append({"column": f["column"], "operator": f["operator"], "value": f.get("value")})
        plan["filters"] = clean_filters
        if "n" in plan:
            plan["n"] = max(1, min(int(plan["n"]), 100))
        return plan

    def _heuristic_plan(self, question: str, df: pd.DataFrame) -> dict[str, Any]:
        q = question.lower()
        cols = list(map(str, df.columns))
        mentioned = next((c for c in cols if c.lower() in q), None)
        if any(k in q for k in ["décris", "describe", "résumé", "summary"]):
            return {"operation": "describe", "title": "Statistiques descriptives"}
        if any(k in q for k in ["moyenne", "mean", "average"]):
            return {"operation": "mean", "column": mentioned or self._first_numeric(df), "title": "Moyenne"}
        if any(k in q for k in ["somme", "total", "sum"]):
            return {"operation": "sum", "column": mentioned or self._first_numeric(df), "title": "Total"}
        if any(k in q for k in ["corrélation", "correlation"]):
            return {"operation": "correlation", "title": "Corrélations"}
        if any(k in q for k in ["top", "modalités", "valeurs fréquentes"]):
            return {"operation": "top_values", "column": mentioned or cols[0], "n": 10, "title": "Top valeurs"}
        return {"operation": "describe", "title": "Analyse descriptive"}

    @staticmethod
    def _first_numeric(df: pd.DataFrame) -> str:
        numeric = list(df.select_dtypes(include="number").columns)
        if not numeric:
            raise ValueError("Aucune colonne numérique disponible.")
        return str(numeric[0])

    def ask(self, question: str, df: pd.DataFrame) -> tuple[AnalysisResult, dict[str, Any]]:
        plan = self.plan(question, df)
        result = self.analytics.execute(df, plan)
        if self.llm.enabled:
            compact = result.data.head(20).to_dict(orient="records") if isinstance(result.data, pd.DataFrame) else result.data
            explain_prompt = f"""
You are an insurance analytics copilot. Explain the deterministic result below in French.
Do not invent any number. Mention the calculation method. Be concise and professional.
Question: {question}
Plan: {json.dumps(plan, ensure_ascii=False, default=str)}
Calculation: {result.calculation}
Result: {json.dumps(compact, ensure_ascii=False, default=str)}
"""
            try:
                llm_resp = self.llm.generate(explain_prompt)
                result.answer = llm_resp.text.strip() or result.answer
            except Exception as exc:
                result.warnings.append(f"Explication Gemini indisponible: {type(exc).__name__}")
        return result, plan
