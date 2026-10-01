import pandas as pd
from insurance_ai.agents.analysis_agent import AnalysisAgent
from insurance_ai.services.gemini_manager import GeminiModelManager


def test_offline_heuristic_analysis():
    mgr=GeminiModelManager(api_key="",models=[])
    agent=AnalysisAgent(llm=mgr)
    df=pd.DataFrame({"premium":[10,20,30],"region":["A","A","B"]})
    result, plan=agent.ask("Quelle est la moyenne de premium ?",df)
    assert plan["operation"] == "mean"
    assert result.data == 20.0
