import pandas as pd
from insurance_ai.services.insurance_kpi import InsuranceKPIService
from insurance_ai.services.analytics import AnalyticsService


def df():
    return pd.DataFrame({"premium":[100,200],"claims":[40,60],"region":["A","B"],"claim_id":["C1","C2"]})


def test_loss_ratio():
    r = InsuranceKPIService().loss_ratio(df(), "claims", "premium")
    assert round(r.value, 6) == round(100/300, 6)


def test_groupby_and_filters():
    a = AnalyticsService()
    result = a.execute(df(), {"operation":"groupby_sum","group_by":"region","column":"premium","filters":[]})
    assert result.data["premium"].sum() == 300
    r2 = a.execute(df(), {"operation":"sum","column":"premium","filters":[{"column":"region","operator":"==","value":"A"}]})
    assert r2.data == 100.0
