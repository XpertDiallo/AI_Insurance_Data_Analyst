import pytest
from insurance_ai.services.database import DatabaseService


def test_sql_read_only_validator():
    assert DatabaseService.validate_read_only_sql("SELECT 1") == "SELECT 1"
    assert DatabaseService.validate_read_only_sql("WITH x AS (SELECT 1 a) SELECT * FROM x").startswith("WITH")
    for q in ["DROP TABLE t", "DELETE FROM t", "UPDATE t SET x=1", "INSERT INTO t VALUES (1)"]:
        with pytest.raises(PermissionError):
            DatabaseService.validate_read_only_sql(q)


def test_sqlite_query():
    db = DatabaseService(); db.connect("sqlite:///:memory:")
    df = db.read_query("SELECT 1 AS a UNION ALL SELECT 2 AS a")
    assert df["a"].tolist() == [1,2]


def test_build_url_escapes_credentials():
    url = DatabaseService.build_url("postgresql", host="db", database="claims", username="a@b", password="p@ss/word")
    assert "a%40b" in url
    assert "p%40ss%2Fword" in url
