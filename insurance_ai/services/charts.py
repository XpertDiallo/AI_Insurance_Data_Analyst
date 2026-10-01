from __future__ import annotations

from io import BytesIO
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd


class ChartService:
    @staticmethod
    def matplotlib_png(
        df: pd.DataFrame,
        chart_type: str,
        *,
        x: str | None = None,
        y: str | None = None,
        title: str = "",
    ) -> bytes:
        fig, ax = plt.subplots(figsize=(9, 4.8))
        chart_type = chart_type.lower()
        if chart_type == "bar":
            if not x or not y:
                raise ValueError("x et y requis pour bar")
            df.plot(kind="bar", x=x, y=y, ax=ax, legend=False)
        elif chart_type == "line":
            if not x or not y:
                raise ValueError("x et y requis pour line")
            df.plot(kind="line", x=x, y=y, marker="o", ax=ax, legend=False)
        elif chart_type == "histogram":
            if not x:
                raise ValueError("x requis pour histogram")
            pd.to_numeric(df[x], errors="coerce").dropna().plot(kind="hist", bins=20, ax=ax)
        elif chart_type == "box":
            if not y and not x:
                raise ValueError("x ou y requis pour box")
            col = y or x
            pd.to_numeric(df[col], errors="coerce").dropna().plot(kind="box", ax=ax)
        elif chart_type == "scatter":
            if not x or not y:
                raise ValueError("x et y requis pour scatter")
            ax.scatter(pd.to_numeric(df[x], errors="coerce"), pd.to_numeric(df[y], errors="coerce"), alpha=0.65)
            ax.set_xlabel(x)
            ax.set_ylabel(y)
        else:
            raise ValueError(f"Type de graphique non supporté: {chart_type}")
        ax.set_title(title or "Graphique")
        ax.grid(alpha=0.2)
        fig.tight_layout()
        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        plt.close(fig)
        return buf.getvalue()
