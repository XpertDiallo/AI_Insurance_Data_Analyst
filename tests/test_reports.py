import pandas as pd
from insurance_ai.core.models import ReportPayload
from insurance_ai.reports.generator import ReportGenerator


def payload():
    return ReportPayload(
        title="Test report", subtitle="Insurance", executive_summary="Summary",
        kpis=[{"label":"Loss ratio","display":"50.00%","formula":"Claims / Premium"}],
        tables=[{"title":"Data","data":pd.DataFrame({"a":[1,2]})}],
        findings=["Finding"], recommendations=["Recommendation"], sources=["sample.csv"]
    )


def test_report_formats():
    g=ReportGenerator(); p=payload()
    outputs={"html":g.html(p),"pdf":g.pdf(p),"docx":g.docx(p),"pptx":g.pptx(p),"xlsx":g.xlsx(p,pd.DataFrame({"x":[1]}))}
    assert outputs["html"].startswith(b"\n<!doctype html>") or b"<!doctype html>" in outputs["html"][:100]
    assert outputs["pdf"].startswith(b"%PDF")
    assert outputs["docx"].startswith(b"PK")
    assert outputs["pptx"].startswith(b"PK")
    assert outputs["xlsx"].startswith(b"PK")
