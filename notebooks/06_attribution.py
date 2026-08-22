# %% [markdown]
# # 06 — Attribution
#
# Decomposes the fund's reported July 2026 book-level decline into four
# drivers: market beta, concentration (excess loss vs. an equal-weighted
# version of the same names), hedge removal (counterfactual — what if the
# Q1 put book had been retained), and forced-liquidation slippage (from the
# CORZ blotter). Reports the counterfactual as a range, not a point estimate.

# %%
import sys
from pathlib import Path
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf

warnings.filterwarnings("ignore")

ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
sys.path.insert(0, str(ROOT))

from src.utils import config as cfg
from src.viz.style import apply_style, PALETTE, source_note

apply_style()
panel = pd.read_parquet(cfg.PROCESSED / "position_panel.parquet")

CUSIP_TICKER = {
    "80004C200": "SNDK", "595112103": "MU", "093712107": "BE",
    "874039100": "TSM", "N97284108": "NBIS", "21873S108": "CRWV",
    "21874A106": "CORZ", "861012102": "STM", "038169207": "APLD",
    "767292105": "RIOT", "Q4982L109": "IREN", "18452B209": "CLSK",
    "83418M103": "SEI", "G96115103": "WYFI", "G11448100": "BTDR",
    "35834F104": "TE", "928298108": "VSH", "05614L209": "BW",
    "433921103": "HIVE", "74347M108": "PUMP", "15675D103": "CBRS",
}

q2_long = panel[(panel.period == "2026-06-30") & (panel.put_call == "LONG")].copy()
q2_long["ticker"] = q2_long.cusip.map(CUSIP_TICKER)
book = q2_long.dropna(subset=["ticker"]).copy()
book["weight"] = book.value_usd / book.value_usd.sum()

# %% [markdown]
# ## 1. Reprice the disclosed book through July 2026

# %%
tickers = sorted(book.ticker.unique())
px = yf.download(tickers, start="2026-06-25", end="2026-08-05",
                  progress=False, auto_adjust=True)["Close"]
px = px.dropna(how="all")
start_px = px.iloc[0]
end_px = px.loc["2026-07-31":].iloc[0] if "2026-07-31" in px.index or True else px.iloc[-1]
# Use last trading day at/before 31 Jul as "end of July"
july_end_idx = px.index[px.index <= "2026-07-31"][-1]
end_px = px.loc[july_end_idx]

ret = (end_px / start_px - 1)
book = book.set_index("ticker")
book["jul_return"] = ret
book_return_actual = float((book.weight * book.jul_return).sum())
print(f"Pricing window: {px.index[0].date()} to {july_end_idx.date()}")
print(f"Actual book-level return, disclosed long book, June-end to July-end: {book_return_actual:.1%}")
print(book[["value_usd", "weight", "jul_return"]].sort_values("jul_return").to_string())

# %% [markdown]
# ## 2. Driver 1 — Beta: what if the book had moved with the market instead of its own names?

# %%
benchmark = yf.download("^SOX", start="2026-06-25", end="2026-08-05",
                         progress=False, auto_adjust=True)["Close"]
bench_start = benchmark.iloc[0]
bench_end = benchmark.loc[benchmark.index <= "2026-07-31"].iloc[-1]
sox_return = float(bench_end / bench_start - 1)
print(f"SOX (PHLX Semiconductor Index) return over the same window: {sox_return:.1%}")
print(f"Driver 1 (beta) — return attributable to the sector simply falling: {sox_return:.1%}")

# %% [markdown]
# ## 3. Driver 2 — Concentration: excess loss vs. an equal-weighted version of the same names

# %%
equal_weight_return = float(book.jul_return.mean())
concentration_effect = book_return_actual - equal_weight_return
print(f"Equal-weighted return on the SAME 21 names: {equal_weight_return:.1%}")
print(f"Actual (concentration-weighted) return: {book_return_actual:.1%}")
print(f"Driver 2 (concentration) — excess loss from weighting, holding names fixed: {concentration_effect:+.1%}")

# %% [markdown]
# ## 4. Driver 3 — Hedge removal counterfactual (reported as a RANGE)
#
# 13F does not disclose strike or expiry for the Q1-2026 put book. Run a grid
# over plausible strike moneyness and tenor rather than presenting one false-
# precision number.

# %%
q1_puts = panel[(panel.period == "2026-03-31") & (panel.put_call == "PUT")].copy()
q1_puts["ticker"] = q1_puts.cusip.map(CUSIP_TICKER)
put_book = q1_puts.dropna(subset=["ticker"])
put_notional = float(put_book.value_usd.sum())
mapped_put_notional = put_notional
print(f"Q1-2026 put notional mapped to tradeable underlyings: ${mapped_put_notional:,.0f} "
      f"of ${q1_puts.value_usd.sum():,.0f} total put book")

# Grid: moneyness (ATM, 10% OTM) x simplified delta-based payoff approximation.
# A put's value roughly moves inversely with the underlying, scaled by its
# delta; delta is higher (closer to -1) for ATM puts and shorter tenors when
# the underlying falls sharply, lower (closer to 0) for far-OTM puts.
# This is a stated approximation, not an options-pricing model — see the
# limitations section for why a real vol surface is not available here.
scenarios = {
    "ATM, high delta (~0.75)": 0.75,
    "10% OTM, moderate delta (~0.45)": 0.45,
    "20% OTM, low delta (~0.20)": 0.20,
}
underlying_return_on_put_names = float(
    (put_book.set_index("ticker").value_usd / put_book.value_usd.sum() *
     book.reindex(put_book.ticker.values)["jul_return"].fillna(sox_return).values).sum()
)
print(f"\nWeighted July return of the underlyings that WERE put-protected in Q1: "
      f"{underlying_return_on_put_names:.1%}")

counterfactual_gains = {}
for label, delta in scenarios.items():
    put_pnl = -underlying_return_on_put_names * delta * mapped_put_notional
    counterfactual_gains[label] = put_pnl
    print(f"  {label}: put book P&L if retained through July ≈ ${put_pnl:,.0f} "
          f"({put_pnl/mapped_put_notional:+.1%} of put notional)")

low, high = min(counterfactual_gains.values()), max(counterfactual_gains.values())
print(f"\nCounterfactual range: retaining the Q1 put book would have added "
      f"${low:,.0f} to ${high:,.0f} against July's losses, DEPENDING ON "
      f"UNVERIFIABLE strike/tenor assumptions. Reported as a range, not a point estimate.")

# %% [markdown]
# ## 5. Driver 4 — Forced-liquidation slippage (from the CORZ blotter, notebook 01)

# %%
blotter = pd.read_csv(cfg.PROCESSED / "blotter.csv")
open_market_avg = blotter[~blotter.block].price.mean()
block_avg = blotter[blotter.block].price.mean()
slippage_pct = block_avg / open_market_avg - 1
corz_shares_blocked = int((-blotter[blotter.block].shares).sum())
corz_slippage_usd = corz_shares_blocked * open_market_avg * -slippage_pct if slippage_pct < 0 else 0
print(f"CORZ open-market avg (14-15 Jul): ${open_market_avg:.2f}")
print(f"CORZ block-trade avg (3 Aug): ${block_avg:.2f}  ({slippage_pct:+.1%})")
print(f"Driver 4 (slippage) — dollar cost on CORZ alone: ${corz_slippage_usd:,.0f}")
print(f"NOTE: this is evidenced for CORZ specifically via its 13D/A blotter. "
      f"No equivalent trade-level blotter exists for SanDisk or Micron — the "
      f"largest positions. Driver 4 is therefore a LOWER BOUND on total "
      f"slippage, stated as such, not extrapolated beyond what the filing shows.")

# %% [markdown]
# ## 6. The waterfall — with an honest residual

# %%
reported_equity_loss = -0.67  # per the fund's own 30 Jul investor letter (unaudited)

driver_beta = sox_return
driver_concentration = concentration_effect
# Hedge and slippage are COUNTERFACTUAL / add-on drivers relative to the
# reported fund-level EQUITY loss, not decompositions of the observed
# long-book return — kept conceptually separate, not summed into one total.
hedge_mid_gain = np.mean(list(counterfactual_gains.values()))
driver_hedge_pct = -hedge_mid_gain / book.value_usd.sum()  # cost of absence, as % of book
driver_slippage_pct = -corz_slippage_usd / book.value_usd.sum()

print(f"Disclosed LONG BOOK return, Jun-end to Jul-end (actual, priced): {book_return_actual:.1%}")
print(f"  of which Driver 1 (beta/SOX): {driver_beta:.1%}")
print(f"  of which Driver 2 (concentration vs equal-weight): {driver_concentration:+.1%}")
print(f"  residual (stock-specific / idiosyncratic): {book_return_actual - driver_beta - driver_concentration:+.1%}")
print(f"\nReported EQUITY loss (fund-level, per investor letter): {reported_equity_loss:.0%}")
print(f"This is a LEVERAGED, NET-OF-SHORTS number the long-book return above cannot "
      f"be scaled into without the leverage and short-book data this project does "
      f"not have (see notebook 05 and the observability audit). The bridge below "
      f"is presented at the LONG-BOOK level only, with the equity-level number "
      f"shown for reference, not forced to close — a forced close to -67.0% would "
      f"require assuming leverage and short-book P&L this project cannot verify.")

# %% [markdown]
# ## 7. Waterfall chart — long-book level, residual shown honestly

# %%
fig, ax = plt.subplots(figsize=(10, 6))
steps = [
    ("Start", 0),
    ("Beta\n(SOX move)", driver_beta),
    ("Concentration\n(vs equal-weight)", driver_concentration),
    ("Residual\n(stock-specific)", book_return_actual - driver_beta - driver_concentration),
]
cum = 0
for i, (label, val) in enumerate(steps):
    if label == "Start":
        continue
    color = PALETTE["put"] if val < 0 else PALETTE["long"]
    ax.bar(label, val, bottom=cum if val >= 0 else cum + val, color=color, width=0.6)
    cum += val
ax.axhline(0, color="black", linewidth=0.8)
ax.axhline(book_return_actual, color=PALETTE["neutral"], linestyle="--", linewidth=1,
           label=f"Actual long-book return: {book_return_actual:.1%}")
ax.set_ylabel("Contribution to long-book return, Jun-end to Jul-end")
ax.set_title("Long-Book Return Attribution — June-end to July-end 2026\n"
              "(Long-book level only — see notebook text for why fund-level equity "
              "P&L cannot be forced to close without unverifiable leverage data)")
ax.legend()
source_note(ax, "Source: SEC 13F-HR (30 Jun 2026) weights; yfinance prices, "
                 "^SOX benchmark. Snapshot 2026-08-22.")
plt.tight_layout()
plt.savefig(cfg.CHARTS / "attribution_bridge.png", dpi=300)
plt.close()
print("Saved outputs/charts/attribution_bridge.png")

# %% [markdown]
# ## 8. Write the attribution table and counterfactual range to disk

# %%
attribution = pd.DataFrame([
    {"driver": "Actual long-book return (Jun-end to Jul-end)", "value": book_return_actual},
    {"driver": "Beta (SOX)", "value": driver_beta},
    {"driver": "Concentration effect vs equal-weight", "value": driver_concentration},
    {"driver": "Residual (stock-specific)", "value": book_return_actual - driver_beta - driver_concentration},
    {"driver": "Hedge-absence cost, LOW scenario (20% OTM)", "value": -min(counterfactual_gains.values()) / book.value_usd.sum()},
    {"driver": "Hedge-absence cost, HIGH scenario (ATM)", "value": -max(counterfactual_gains.values()) / book.value_usd.sum()},
    {"driver": "Slippage (CORZ only, lower bound)", "value": driver_slippage_pct},
    {"driver": "Reported fund-level equity loss (unaudited, investor letter)", "value": reported_equity_loss},
])
attribution.to_csv(cfg.FINAL / "attribution.csv", index=False)
print(attribution.to_string(index=False))
print("\nNotebook 06 complete.")
