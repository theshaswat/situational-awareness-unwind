"""Portfolio concentration metrics."""
import pandas as pd


def herfindahl(weights: pd.Series) -> float:
    """Sum of squared weights. 1/n for an equal-weighted book of n names;
    1.0 for a single-name book."""
    w = weights[weights > 0]
    return float((w ** 2).sum())


def top_n_share(weights: pd.Series, n: int = 5) -> float:
    return float(weights.sort_values(ascending=False).head(n).sum())


def concentration_summary(panel: pd.DataFrame, value_col: str = "value_usd") -> pd.DataFrame:
    """One row per quarter: n positions, gross, long/put/call split, top-5,
    HHI. `panel` must have columns [period, issuer, put_call, value_usd]."""
    rows = []
    for period, g in panel.groupby("period"):
        total = g[value_col].sum()
        if total == 0:
            continue
        w = g[value_col] / total
        rows.append({
            "period": period,
            "n_positions": len(g),
            "gross_usd": total,
            "long_usd": g.loc[g.put_call == "LONG", value_col].sum(),
            "put_usd": g.loc[g.put_call == "PUT", value_col].sum(),
            "call_usd": g.loc[g.put_call == "CALL", value_col].sum(),
            "top5_share": top_n_share(w, 5),
            "hhi": herfindahl(w),
        })
    return pd.DataFrame(rows).sort_values("period").reset_index(drop=True)
