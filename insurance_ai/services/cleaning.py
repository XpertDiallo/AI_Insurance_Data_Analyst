from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass
class CleaningOutcome:
    dataframe: pd.DataFrame
    changed_rows: int
    details: dict[str, Any]


class CleaningService:
    PROTECTED_NAME_HINTS = {"id", "identifier", "identifiant", "police", "policy", "claim_id", "sinistre_id"}

    @staticmethod
    def normalize_column_name(name: str) -> str:
        value = str(name).strip().lower()
        value = re.sub(r"[^a-zA-Z0-9_à-ÿ]+", "_", value)
        value = re.sub(r"_+", "_", value).strip("_")
        return value or "column"

    def normalize_column_names(self, df: pd.DataFrame) -> CleaningOutcome:
        new = df.copy()
        mapping = {c: self.normalize_column_name(c) for c in new.columns}
        # guarantee uniqueness
        seen: dict[str, int] = {}
        unique_mapping: dict[Any, str] = {}
        for old, proposed in mapping.items():
            seen[proposed] = seen.get(proposed, 0) + 1
            unique_mapping[old] = proposed if seen[proposed] == 1 else f"{proposed}_{seen[proposed]}"
        new = new.rename(columns=unique_mapping)
        return CleaningOutcome(new, 0, {"mapping": unique_mapping})

    @staticmethod
    def rename_columns(df: pd.DataFrame, mapping: dict[str, str]) -> CleaningOutcome:
        missing = [c for c in mapping if c not in df.columns]
        if missing:
            raise KeyError(f"Colonnes introuvables: {missing}")
        new = df.rename(columns=mapping).copy()
        return CleaningOutcome(new, 0, {"mapping": mapping})

    @staticmethod
    def drop_duplicates(df: pd.DataFrame, subset: list[str] | None = None, keep: str = "first") -> CleaningOutcome:
        before = len(df)
        new = df.drop_duplicates(subset=subset or None, keep=keep).copy()
        return CleaningOutcome(new, before - len(new), {"subset": subset, "keep": keep})

    @staticmethod
    def cast_column(df: pd.DataFrame, column: str, target_type: str, dayfirst: bool = True) -> CleaningOutcome:
        if column not in df.columns:
            raise KeyError(column)
        new = df.copy()
        before_na = int(new[column].isna().sum())
        if target_type == "numeric":
            source = new[column]
            if source.dtype == object:
                source = source.astype(str).str.replace(" ", "", regex=False).str.replace(",", ".", regex=False)
            new[column] = pd.to_numeric(source, errors="coerce")
        elif target_type == "datetime":
            new[column] = pd.to_datetime(new[column], errors="coerce", dayfirst=dayfirst)
        elif target_type == "string":
            new[column] = new[column].astype("string")
        elif target_type == "category":
            new[column] = new[column].astype("category")
        elif target_type == "boolean":
            mapping = {
                "true": True, "false": False, "1": True, "0": False,
                "yes": True, "no": False, "oui": True, "non": False,
            }
            new[column] = new[column].map(lambda x: mapping.get(str(x).strip().lower(), x)).astype("boolean")
        else:
            raise ValueError(f"Type cible non supporté: {target_type}")
        after_na = int(new[column].isna().sum())
        return CleaningOutcome(new, max(0, after_na - before_na), {"column": column, "target_type": target_type, "new_na": max(0, after_na - before_na)})

    def impute(self, df: pd.DataFrame, column: str, strategy: str, value: Any = None, group_by: str | None = None) -> CleaningOutcome:
        if column not in df.columns:
            raise KeyError(column)
        if any(hint == column.lower() or column.lower().endswith(f"_{hint}") for hint in self.PROTECTED_NAME_HINTS):
            raise ValueError("Imputation automatique interdite sur un identifiant potentiel.")
        new = df.copy()
        mask = new[column].isna()
        count = int(mask.sum())
        if count == 0:
            return CleaningOutcome(new, 0, {"column": column, "strategy": strategy})
        if strategy == "median":
            fill = pd.to_numeric(new[column], errors="coerce").median()
            new[column] = new[column].fillna(fill)
        elif strategy == "mean":
            fill = pd.to_numeric(new[column], errors="coerce").mean()
            new[column] = new[column].fillna(fill)
        elif strategy == "mode":
            mode = new[column].mode(dropna=True)
            fill = mode.iloc[0] if not mode.empty else value
            new[column] = new[column].fillna(fill)
        elif strategy == "constant":
            new[column] = new[column].fillna(value)
        elif strategy == "group_median":
            if not group_by or group_by not in new.columns:
                raise ValueError("group_by valide requis")
            numeric = pd.to_numeric(new[column], errors="coerce")
            medians = numeric.groupby(new[group_by], dropna=False).transform("median")
            new[column] = numeric.fillna(medians)
        else:
            raise ValueError(f"Stratégie d'imputation non supportée: {strategy}")
        return CleaningOutcome(new, count, {"column": column, "strategy": strategy, "value": value, "group_by": group_by})

    def impute_cell(
        self,
        df: pd.DataFrame,
        column: str,
        row_position: int,
        strategy: str,
        value: Any = None,
        group_by: str | None = None,
    ) -> CleaningOutcome:
        """Impute one missing cell using an explicit, auditable decision.

        A protected identifier can only be filled manually. This keeps the
        integrity guard of ``impute`` while allowing an analyst to repair one
        known key after human verification.
        """
        if column not in df.columns:
            raise KeyError(column)
        if not isinstance(row_position, int) or not 0 <= row_position < len(df):
            raise IndexError("Position de ligne invalide.")
        protected = any(
            hint == column.lower() or column.lower().endswith(f"_{hint}")
            for hint in self.PROTECTED_NAME_HINTS
        )
        if protected and strategy != "manual":
            raise ValueError("Un identifiant potentiel doit être renseigné manuellement, cellule par cellule.")

        col_position = df.columns.get_loc(column)
        current = df.iloc[row_position, col_position]
        if not pd.isna(current):
            raise ValueError("La cellule sélectionnée ne contient plus de valeur manquante.")

        new = df.copy()
        if strategy == "manual":
            if value is None or not str(value).strip():
                raise ValueError("Une valeur manuelle est requise.")
            fill = value
            if pd.api.types.is_numeric_dtype(df[column]):
                fill = pd.to_numeric(value, errors="coerce")
            elif pd.api.types.is_datetime64_any_dtype(df[column]):
                fill = pd.to_datetime(value, errors="coerce")
            if pd.isna(fill):
                raise ValueError("La valeur manuelle n'est pas compatible avec le type de la colonne.")
        elif strategy in {"median", "mean"}:
            numeric = pd.to_numeric(df[column], errors="coerce")
            fill = numeric.median() if strategy == "median" else numeric.mean()
        elif strategy == "mode":
            modes = df[column].mode(dropna=True)
            fill = modes.iloc[0] if not modes.empty else None
        elif strategy == "constant":
            if value is None or not str(value).strip():
                raise ValueError("Une valeur constante est requise.")
            fill = value
        elif strategy == "group_median":
            if not group_by or group_by not in df.columns:
                raise ValueError("group_by valide requis")
            numeric = pd.to_numeric(df[column], errors="coerce")
            medians = numeric.groupby(df[group_by], dropna=False).transform("median")
            fill = medians.iloc[row_position]
        else:
            raise ValueError(f"Stratégie d'imputation non supportée: {strategy}")

        if fill is None or pd.isna(fill):
            raise ValueError("Aucune valeur d'imputation calculable pour cette cellule.")
        new.iat[row_position, col_position] = fill
        return CleaningOutcome(
            new,
            1,
            {
                "column": column,
                "row_position": row_position,
                "strategy": strategy,
                "value": value if strategy in {"manual", "constant"} else fill,
                "group_by": group_by,
            },
        )

    @staticmethod
    def standardize_categories(df: pd.DataFrame, column: str, mapping: dict[Any, Any]) -> CleaningOutcome:
        if column not in df.columns:
            raise KeyError(column)
        new = df.copy()
        before = new[column].copy()
        new[column] = new[column].replace(mapping)
        changed = int((before.astype(str) != new[column].astype(str)).sum())
        return CleaningOutcome(new, changed, {"column": column, "mapping": mapping})

    @staticmethod
    def filter_rows(df: pd.DataFrame, column: str, operator: str, value: Any) -> CleaningOutcome:
        if column not in df.columns:
            raise KeyError(column)
        s = df[column]
        ops = {
            "==": s == value,
            "!=": s != value,
            ">": s > value,
            ">=": s >= value,
            "<": s < value,
            "<=": s <= value,
            "contains": s.astype(str).str.contains(str(value), case=False, na=False, regex=False),
        }
        if operator not in ops:
            raise ValueError("Opérateur non autorisé")
        mask = ops[operator]
        new = df.loc[mask].copy()
        return CleaningOutcome(new, len(df) - len(new), {"column": column, "operator": operator, "value": value})
