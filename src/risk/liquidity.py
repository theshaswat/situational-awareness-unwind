"""Days-to-liquidate under stated ADV-participation assumptions.

Known limitation, stated explicitly rather than hidden: this treats ADV as
exogenous. In a correlated, crowded unwind it is not — every levered holder
of the same name sells at once, so realised liquidity is worse than trailing
ADV implies. See notebook 08 for the stressed-ADV variant used in the live
screen.
"""
import pandas as pd


def days_to_liquidate(shares: float, adv: float, participation: float) -> float:
    if adv <= 0:
        return float("inf")
    return shares / (adv * participation)


def liquidity_table(positions: pd.DataFrame, adv: pd.Series,
                     participations=(1.0, 0.20, 0.10)) -> pd.DataFrame:
    """`positions` needs columns [ticker, issuer, value_usd, shares].
    `adv` is a Series indexed by ticker (mean daily volume, shares)."""
    df = positions.copy()
    df["adv"] = df["ticker"].map(adv)
    for p in participations:
        col = f"days_to_liquidate_{int(p*100)}pct"
        df[col] = df.apply(lambda r: days_to_liquidate(r["shares"], r["adv"], p), axis=1)
    return df


def book_weighted_days(df: pd.DataFrame, days_col: str, weight_col: str = "value_usd") -> float:
    valid = df.dropna(subset=[days_col])
    if valid[weight_col].sum() == 0:
        return float("nan")
    return float((valid[days_col] * valid[weight_col]).sum() / valid[weight_col].sum())
