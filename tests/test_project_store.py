import pandas as pd
import pytest
from insurance_ai.core.project_store import ProjectStore


def test_project_and_versions(tmp_path):
    s=ProjectStore(tmp_path)
    pid=s.create_project("Test","u")
    df=pd.DataFrame({"a":[1,2]})
    raw=s.save_dataframe(pid,df,name="x",stage="RAW",source_type="csv",source_name="x.csv")
    cur=s.save_dataframe(pid,df.copy(),name="x",stage="CURATED",source_type="derived",source_name="clean",parent_id=raw.dataset_id)
    assert s.load_dataframe(pid,raw.dataset_id).shape == (2,1)
    assert cur.parent_id == raw.dataset_id
    assert {x["stage"] for x in s.list_datasets(pid)} == {"RAW","CURATED"}


def test_project_store_rejects_path_traversal(tmp_path):
    s = ProjectStore(tmp_path)
    with pytest.raises(ValueError):
        s.project_dir("..")
    with pytest.raises(ValueError):
        s.get_dataset_meta("missing", "../outside")
