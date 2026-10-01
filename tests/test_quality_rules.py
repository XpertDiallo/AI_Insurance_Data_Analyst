import pandas as pd
from insurance_ai.services.quality_rules import DataQualityRuleEngine


def test_quality_rules():
    df=pd.DataFrame({"id":[1,1,3],"amount":[10,-2,None],"start":["2026-01-01","2026-02-01","2026-03-01"],"end":["2026-01-02","2026-01-20","2026-03-02"],"branch":["Auto","X","MRH"]})
    rules=[
        {"type":"unique","column":"id"},
        {"type":"non_negative","column":"amount"},
        {"type":"date_order","start_column":"start","end_column":"end"},
        {"type":"allowed_values","column":"branch","values":["Auto","MRH"]},
    ]
    r=DataQualityRuleEngine().evaluate(df,rules)
    assert [x.violations for x in r] == [2,1,1,1]
