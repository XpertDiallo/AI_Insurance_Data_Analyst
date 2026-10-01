import pandas as pd
from insurance_ai.services.dashboard import DashboardService


def test_portfolio_dashboard():
    df=pd.DataFrame({"premium":[100,200],"claims":[50,20],"branch":["A","B"],"date":["2026-01-01","2026-02-01"]})
    d=DashboardService().portfolio_overview(df,premium_col="premium",claims_col="claims",group_col="branch",date_col="date")
    assert len(d.cards)==4
    assert d.premium_claims_by_group is not None
    assert d.monthly_trend is not None
    assert len(d.top_claims)==2
