import pandas as pd
import pytest
from insurance_ai.services.profiling import ProfilingService
from insurance_ai.services.cleaning import CleaningService


def sample():
    return pd.DataFrame({"Policy ID":["A","B","B"],"Amount":[1,None,None],"Region":["ABIDJAN","Abidjan","Abidjan"]})


def test_profile_and_duplicates():
    r = ProfilingService().profile(sample())
    assert r.summary["rows"] == 3
    assert r.duplicate_rows == 1
    assert r.summary["missing_cells"] == 2


def test_cleaning_operations():
    svc = CleaningService(); df = sample()
    out = svc.normalize_column_names(df)
    assert "policy_id" in out.dataframe.columns
    out2 = svc.impute(out.dataframe, "amount", "median")
    assert out2.dataframe["amount"].isna().sum() == 0
    out3 = svc.standardize_categories(out2.dataframe, "region", {"ABIDJAN":"Abidjan"})
    assert set(out3.dataframe["region"]) == {"Abidjan"}


def test_protected_identifier_cannot_be_imputed():
    df = pd.DataFrame({"policy_id":["A",None]})
    with pytest.raises(ValueError):
        CleaningService().impute(df, "policy_id", "mode")


def test_cell_imputation_is_row_specific_and_allows_manual_identifier_repair():
    svc = CleaningService()
    df = pd.DataFrame({"claim_id": [None, None], "amount": [10.0, None], "branch": ["A", "A"]})
    with pytest.raises(ValueError):
        svc.impute_cell(df, "claim_id", 0, "mode")
    repaired = svc.impute_cell(df, "claim_id", 0, "manual", "S004")
    assert repaired.dataframe.loc[0, "claim_id"] == "S004"
    assert pd.isna(repaired.dataframe.loc[1, "claim_id"])
    numeric = svc.impute_cell(repaired.dataframe, "amount", 1, "median")
    assert numeric.dataframe.loc[1, "amount"] == 10.0
