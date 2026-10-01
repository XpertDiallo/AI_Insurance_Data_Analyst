from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from insurance_ai.agents.analysis_agent import AnalysisAgent
from insurance_ai.services.cleaning import CleaningService
from insurance_ai.services.profiling import ProfilingService


@dataclass
class RouteDecision:
    action: str
    reason: str


class SupervisorAgent:
    """Lightweight deterministic supervisor; LLM is not required for routing core safety."""

    def __init__(self):
        self.profiler = ProfilingService()
        self.cleaner = CleaningService()
        self.analysis = AnalysisAgent()

    @staticmethod
    def route(intent: str) -> RouteDecision:
        intent = intent.lower().strip()
        if intent in {"profile", "quality"}:
            return RouteDecision("profile", "Diagnostic qualité demandé")
        if intent in {"analyze", "ask"}:
            return RouteDecision("analyze", "Analyse ou question en langage naturel")
        if intent in {"clean", "transform"}:
            return RouteDecision("clean", "Transformation contrôlée")
        return RouteDecision("analyze", "Routage par défaut vers analyse non destructive")

    def profile(self, df: pd.DataFrame):
        return self.profiler.profile(df)

    def ask(self, question: str, df: pd.DataFrame):
        return self.analysis.ask(question, df)
