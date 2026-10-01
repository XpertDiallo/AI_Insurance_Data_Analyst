"""Generate the deterministic fictitious insurance dataset used by the demo.

The sample intentionally contains 71 records: 66 distinct policies and 5
exact duplicate records, plus missing values for quality/imputation demos.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "sample_data"
OUTPUT_DIR = ROOT / "sample_outputs"


def build_rows() -> list[dict]:
    branches = ["Auto", "MRH", "Santé", "Entreprise", "Transport"]
    regions = ["Abidjan", "Bouaké", "Yamoussoukro", "Korhogo", "San-Pédro"]
    rows: list[dict] = []
    for number in range(1, 67):
        branch = branches[(number - 1) % len(branches)]
        region = regions[(number - 1) % len(regions)]
        written = 80_000 + number * 7_500
        collected = written - (number % 5) * 2_500
        has_claim = number % 3 != 1
        claim_id = f"S{number:03d}" if has_claim else None
        claim_amount = float(25_000 + number * 12_500) if has_claim else 0.0
        row = {
            "policy_id": f"P{number:03d}",
            "branch": branch,
            "region": None if number % 10 == 0 else region,
            "written_premium": written,
            "collected_premium": None if number % 13 == 0 else float(collected),
            "claim_id": claim_id,
            "claim_amount": None if number % 17 == 0 else claim_amount,
            "ceded_premium": written * 0.10,
            "net_premium": written * 0.90,
            "effective_date": f"2026-{((number - 1) % 12) + 1:02d}-{((number - 1) % 27) + 1:02d}",
        }
        rows.append(row)

    # Exact duplicates are intentional for the data-quality and deduplication demos.
    rows.extend(rows[index].copy() for index in (3, 11, 26, 40, 54))
    assert len(rows) == 71
    return rows


def main() -> None:
    rows = build_rows()
    frame = pd.DataFrame(rows)
    DATA_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    frame.to_csv(DATA_DIR / "insurance_sample.csv", index=False)
    frame.to_csv(DATA_DIR / "insurance_sample_semicolon.csv", index=False, sep=";", decimal=",")
    (DATA_DIR / "insurance_sample.json").write_text(
        json.dumps(rows, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    frame.to_excel(DATA_DIR / "insurance_sample.xlsx", index=False, sheet_name="Insurance")

    curated = frame.drop_duplicates().copy()
    curated["region"] = curated["region"].fillna("Non renseignée")
    curated["collected_premium"] = curated["collected_premium"].fillna(curated["written_premium"])
    curated["claim_amount"] = curated["claim_amount"].fillna(0)
    curated.to_csv(OUTPUT_DIR / "insurance_sample_curated.csv", index=False)


if __name__ == "__main__":
    main()
