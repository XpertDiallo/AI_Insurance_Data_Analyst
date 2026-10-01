from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

import pandas as pd
from sqlalchemy import MetaData, Table, create_engine, inspect, select, text
from sqlalchemy.engine import Engine


FORBIDDEN_SQL = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE|REPLACE|GRANT|REVOKE|MERGE|CALL|EXEC|COPY)\b",
    re.IGNORECASE,
)


class DatabaseService:
    """Read-only oriented database adapter.

    SQLAlchemy handles PostgreSQL/MySQL/SQLite/SQL Server. Microsoft Access is
    supported directly through pyodbc on hosts where the Access ODBC driver is
    installed (typically Windows).
    """

    def __init__(self):
        self.engine: Engine | None = None
        self.access_connection: Any = None
        self.kind: str | None = None

    def connect(self, url: str, **engine_kwargs: Any) -> Engine:
        if not url or "://" not in url:
            raise ValueError("URL SQLAlchemy invalide.")
        self.engine = create_engine(url, pool_pre_ping=True, future=True, **engine_kwargs)
        with self.engine.connect() as con:
            con.execute(text("SELECT 1"))
        self.access_connection = None
        self.kind = "sqlalchemy"
        return self.engine

    def connect_access(self, file_path: str, driver: str = "Microsoft Access Driver (*.mdb, *.accdb)") -> Any:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(path)
        if path.suffix.lower() not in {".mdb", ".accdb"}:
            raise ValueError("Le fichier Access doit être .mdb ou .accdb")
        try:
            import pyodbc  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("pyodbc n'est pas installé.") from exc
        conn_str = f"DRIVER={{{driver}}};DBQ={path.resolve()};READONLY=1;"
        self.access_connection = pyodbc.connect(conn_str, autocommit=True, timeout=15)
        self.engine = None
        self.kind = "access"
        return self.access_connection

    def require_engine(self) -> Engine:
        if self.engine is None:
            raise RuntimeError("Aucune connexion SQLAlchemy active.")
        return self.engine

    @staticmethod
    def validate_read_only_sql(query: str) -> str:
        q = query.strip().rstrip(";").strip()
        if not q:
            raise ValueError("Requête vide.")
        if FORBIDDEN_SQL.search(q):
            raise PermissionError("Seules les requêtes en lecture sont autorisées.")
        if not re.match(r"^(SELECT|WITH)\b", q, flags=re.IGNORECASE):
            raise PermissionError("La requête doit commencer par SELECT ou WITH.")
        if ";" in q:
            raise PermissionError("Les requêtes multiples sont interdites.")
        return q

    def schemas(self) -> list[str]:
        if self.kind == "access":
            return []
        return inspect(self.require_engine()).get_schema_names()

    def tables(self, schema: str | None = None) -> list[str]:
        if self.kind == "access":
            cursor = self.access_connection.cursor()
            names = {row.table_name for row in cursor.tables(tableType="TABLE")}
            names |= {row.table_name for row in cursor.tables(tableType="VIEW")}
            return sorted(n for n in names if not n.startswith("MSys"))
        inspector = inspect(self.require_engine())
        return sorted(inspector.get_table_names(schema=schema) + inspector.get_view_names(schema=schema))

    def columns(self, table: str, schema: str | None = None) -> list[dict[str, Any]]:
        if self.kind == "access":
            cursor = self.access_connection.cursor()
            return [
                {"name": row.column_name, "type": str(row.type_name), "nullable": bool(row.nullable)}
                for row in cursor.columns(table=table)
            ]
        return inspect(self.require_engine()).get_columns(table, schema=schema)

    def read_query(self, query: str, max_rows: int = 100_000) -> pd.DataFrame:
        q = self.validate_read_only_sql(query)
        if self.kind == "access":
            # Access uses TOP rather than LIMIT; fetch and cap client-side for arbitrary SELECTs.
            return pd.read_sql_query(q, self.access_connection).head(max_rows).copy()
        wrapped = f"SELECT * FROM ({q}) AS aiida_v2_q LIMIT {int(max_rows)}"
        try:
            return pd.read_sql_query(text(wrapped), self.require_engine())
        except Exception:
            df = pd.read_sql_query(text(q), self.require_engine())
            return df.head(max_rows).copy()

    def read_table(self, table: str, schema: str | None = None, max_rows: int = 100_000) -> pd.DataFrame:
        available = set(self.tables(schema))
        if table not in available:
            raise ValueError("Table ou vue inconnue.")
        if self.kind == "access":
            safe_table = table.replace("]", "]]" )
            return pd.read_sql_query(f"SELECT * FROM [{safe_table}]", self.access_connection).head(max_rows).copy()
        engine = self.require_engine()
        metadata = MetaData()
        tbl = Table(table, metadata, schema=schema, autoload_with=engine)
        stmt = select(tbl).limit(int(max_rows))
        return pd.read_sql_query(stmt, engine)

    @staticmethod
    def build_url(
        dialect: str,
        host: str = "",
        port: int | None = None,
        database: str = "",
        username: str = "",
        password: str = "",
        sqlite_path: str = "",
    ) -> str:
        dialect = dialect.lower()
        if dialect == "sqlite":
            if not sqlite_path:
                raise ValueError("Chemin SQLite requis.")
            return f"sqlite:///{sqlite_path}"
        if dialect == "postgresql":
            return f"postgresql+psycopg://{quote_plus(username)}:{quote_plus(password)}@{host}:{port or 5432}/{database}"
        if dialect == "mysql":
            return f"mysql+pymysql://{quote_plus(username)}:{quote_plus(password)}@{host}:{port or 3306}/{database}"
        if dialect == "sqlserver":
            driver = "ODBC+Driver+18+for+SQL+Server"
            return f"mssql+pyodbc://{quote_plus(username)}:{quote_plus(password)}@{host}:{port or 1433}/{database}?driver={driver}&TrustServerCertificate=yes"
        raise ValueError(f"Dialecte non supporté par URL: {dialect}")
