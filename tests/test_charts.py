import pandas as pd
from insurance_ai.services.charts import ChartService


def test_chart_png():
    png=ChartService.matplotlib_png(pd.DataFrame({"x":["A","B"],"y":[1,2]}),"bar",x="x",y="y",title="T")
    assert png.startswith(b"\x89PNG")
