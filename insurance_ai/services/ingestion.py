from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Iterable

import pandas as pd

try:
    import chardet  # type: ignore
except Exception:  # pragma: no cover
    chardet = None


@dataclass
class CsvDetection:
    encoding: str = "utf-8"
    delimiter: str = ","
    decimal: str = "."
    quotechar: str = '"'
    confidence: float = 0.0


class IngestionService:
    CSV_EXTENSIONS = {".csv", ".txt", ".tsv"}
    EXCEL_EXTENSIONS = {".xls", ".xlsx", ".xlsm"}
    JSON_EXTENSIONS = {".json"}

    @staticmethod
    def _read_bytes(source: bytes | BinaryIO) -> bytes:
        if isinstance(source, bytes):
            return source
        data = source.read()
        try:
            source.seek(0)
        except Exception:
            pass
        return data

    def detect_csv(self, source: bytes | BinaryIO, sample_size: int = 65536) -> CsvDetection:
        raw = self._read_bytes(source)[:sample_size]
        encoding = "utf-8"
        confidence = 0.0
        if chardet is not None:
            result = chardet.detect(raw)
            encoding = result.get("encoding") or "utf-8"
            confidence = float(result.get("confidence") or 0.0)
        try:
            text = raw.decode(encoding, errors="replace")
        except LookupError:
            encoding = "utf-8"
            text = raw.decode("utf-8", errors="replace")

        candidates = [",", ";", "\t", "|"]
        delimiter = ","
        try:
            dialect = csv.Sniffer().sniff(text, delimiters="".join(candidates))
            delimiter = dialect.delimiter
            quotechar = dialect.quotechar or '"'
        except Exception:
            counts = {d: text.count(d) for d in candidates}
            delimiter = max(counts, key=counts.get) if counts else ","
            quotechar = '"'

        # Heuristic: if delimiter is ';' and decimal commas are common, prefer comma decimal.
        decimal = "," if delimiter == ";" and any("," in token for token in text.split()[:200]) else "."
        return CsvDetection(encoding=encoding, delimiter=delimiter, decimal=decimal, quotechar=quotechar, confidence=confidence)

    def read_csv(
        self,
        source: bytes | BinaryIO,
        *,
        delimiter: str | None = None,
        encoding: str | None = None,
        decimal: str | None = None,
        header: int | None = 0,
    ) -> tuple[pd.DataFrame, CsvDetection]:
        raw = self._read_bytes(source)
        detection = self.detect_csv(raw)
        params = {
            "sep": delimiter or detection.delimiter,
            "encoding": encoding or detection.encoding,
            "decimal": decimal or detection.decimal,
            "header": header,
            "engine": "python",
        }
        df = pd.read_csv(io.BytesIO(raw), **params)
        return df, detection

    def excel_sheets(self, source: bytes | BinaryIO) -> list[str]:
        raw = self._read_bytes(source)
        xls = pd.ExcelFile(io.BytesIO(raw))
        return list(xls.sheet_names)

    def read_excel(self, source: bytes | BinaryIO, sheet_name: str | int = 0) -> pd.DataFrame:
        raw = self._read_bytes(source)
        return pd.read_excel(io.BytesIO(raw), sheet_name=sheet_name)

    def read_json(self, source: bytes | BinaryIO) -> pd.DataFrame:
        raw = self._read_bytes(source)
        text = raw.decode("utf-8-sig", errors="replace")
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return pd.json_normalize(parsed)
        if isinstance(parsed, dict):
            # common wrappers: data/results/items
            for key in ("data", "results", "items", "records"):
                value = parsed.get(key)
                if isinstance(value, list):
                    return pd.json_normalize(value)
            return pd.json_normalize(parsed)
        raise ValueError("Structure JSON non tabulaire.")

    def read_uploaded(
        self,
        filename: str,
        source: bytes | BinaryIO,
        **kwargs,
    ) -> tuple[pd.DataFrame, dict]:
        suffix = Path(filename).suffix.lower()
        if suffix in self.CSV_EXTENSIONS:
            df, detection = self.read_csv(source, **{k: v for k, v in kwargs.items() if k in {"delimiter","encoding","decimal","header"}})
            return df, {"format": "csv", **detection.__dict__}
        if suffix in self.EXCEL_EXTENSIONS:
            sheet = kwargs.get("sheet_name", 0)
            return self.read_excel(source, sheet), {"format": "excel", "sheet": sheet}
        if suffix in self.JSON_EXTENSIONS:
            return self.read_json(source), {"format": "json"}
        raise ValueError(f"Format non pris en charge: {suffix or 'sans extension'}")
