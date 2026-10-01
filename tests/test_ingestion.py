from pathlib import Path
from insurance_ai.services.ingestion import IngestionService

ROOT = Path(__file__).resolve().parents[1] / "sample_data"


def test_csv_detection_and_read():
    svc = IngestionService()
    raw = (ROOT / "insurance_sample_semicolon.csv").read_bytes()
    det = svc.detect_csv(raw)
    assert det.delimiter == ";"
    df, _ = svc.read_csv(raw, delimiter=";", decimal=",")
    assert len(df) == 6
    assert "written_premium" in df.columns


def test_excel_and_json():
    svc = IngestionService()
    xraw = (ROOT / "insurance_sample.xlsx").read_bytes()
    assert svc.excel_sheets(xraw)
    xdf = svc.read_excel(xraw)
    assert xdf.shape[0] == 6
    jdf = svc.read_json((ROOT / "insurance_sample.json").read_bytes())
    assert jdf.shape[0] == 6
