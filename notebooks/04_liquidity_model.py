# %% [markdown]
# # 04 — Liquidity Model
#
# Builds days-to-liquidate for the Q2-2026 (pre-collapse) long book and tests
# it against a documented outcome: which position actually could not clear
# during the forced unwind, per the Core Scientific 13D/A blotter.

# %%
import sys
from pathlib import Path
import warnings
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf

warnings.filterwarnings("ignore")

ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
sys.path.insert(0, str(ROOT))

from src.utils import config as cfg
from src.risk import liquidity
from src.viz.style import apply_style, PALETTE, source_note

apply_style()
panel = pd.read_parquet(cfg.PROCESSED / "position_panel.parquet")

# %% [markdown]
# ## 1. Q2-2026 long book, mapped to tradeable tickers
#
# 13F does not disclose ticker — only issuer name and CUSIP. Mapped by hand
# against each CUSIP (each ticker verified against yfinance's own company
# name before use — SEI, PUMP, and TE in particular collide in spelling with
# unrelated tickers and would silently corrupt the model if unchecked).
# Keel Infrastructure and SharonAI Holdings excluded — no resolvable liquid
# US ticker found; SK Hynix excluded — Korea-listed, no yfinance coverage.

# %%
CUSIP_TICKER = {
    "80004C200": "SNDK", "595112103": "MU", "093712107": "BE",
    "874039100": "TSM", "N97284108": "NBIS", "21873S108": "CRWV",
    "21874A106": "CORZ", "861012102": "STM", "038169207": "APLD",
    "767292105": "RIOT", "Q4982L109": "IREN", "18452B209": "CLSK",
    "83418M103": "SEI", "G96115103": "WYFI", "G11448100": "BTDR",
    "35834F104": "TE", "928298108": "VSH",
    "05614L209": "BW",     # Babcock & Wilcox Enterprises
    "433921103": "HIVE",   # HIVE Digital Technologies
    "74347M108": "PUMP",   # ProPetro Holding Corp
    "15675D103": "CBRS",   # Cerebras Systems
}

q2_long = panel[(panel.period == "2026-06-30") & (panel.put_call == "LONG")].copy()
q2_long["ticker"] = q2_long.cusip.map(CUSIP_TICKER)
mapped = q2_long.dropna(subset=["ticker"]).copy()
unmapped = q2_long[q2_long.ticker.isna()]
print(f"Mapped {len(mapped)}/{len(q2_long)} long positions to tickers "
      f"(${mapped.value_usd.sum():,.0f} of ${q2_long.value_usd.sum():,.0f}, "
      f"{mapped.value_usd.sum()/q2_long.value_usd.sum():.1%} of the long book)")
if len(unmapped):
    print("Unmapped (no liquid US ticker — excluded, not estimated):")
    print(unmapped[["issuer", "value_usd"]].to_string(index=False))

# %% [markdown]
# ## 2. Pull trailing 3-month ADV as of quarter-end (snapshot, timestamped)

# %%
tickers = sorted(mapped.ticker.unique())
snapshot_date = "2026-08-22"  # date this pull was run
px_path = cfg.PRICES / f"ohlcv_{snapshot_date}.parquet"

hist = yf.download(tickers, start="2026-04-01", end="2026-07-01",
                    progress=False, auto_adjust=False)
volume = hist["Volume"]
adv = volume.mean()
volume.to_parquet(px_path.with_name(f"volume_{snapshot_date}.parquet"))
adv.to_frame("adv").to_csv(cfg.PRICES / f"adv_{snapshot_date}.csv")
print(f"ADV window: 2026-04-01 to 2026-06-30 (the quarter the Q2-2026 13F reports)")
print(adv.sort_values(ascending=False).to_string())

# %% [markdown]
# ## 3. Days-to-liquidate

# %%
liq = liquidity.liquidity_table(mapped, adv, participations=(1.0, 0.20, 0.10))
liq = liq.sort_values("days_to_liquidate_20pct", ascending=False)
liq[["ticker", "issuer", "value_usd", "shares", "adv",
     "days_to_liquidate_100pct", "days_to_liquidate_20pct",
     "days_to_liquidate_10pct"]].to_csv(cfg.TABLES / "liquidity_table.csv", index=False)
print(liq[["ticker", "value_usd", "shares", "adv",
           "days_to_liquidate_100pct", "days_to_liquidate_20pct"]].to_string(index=False))

bw_20 = liquidity.book_weighted_days(liq, "days_to_liquidate_20pct")
bw_10 = liquidity.book_weighted_days(liq, "days_to_liquidate_10pct")
print(f"\nBook-weighted days-to-liquidate @20% ADV participation: {bw_20:.2f} trading days")
print(f"Book-weighted days-to-liquidate @10% ADV participation: {bw_10:.2f} trading days")
print(f"Most illiquid single position (@20% ADV): {liq.iloc[0]['ticker']} at "
      f"{liq.iloc[0]['days_to_liquidate_20pct']:.2f} days")

# %% [markdown]
# ## 4. Validate against the documented outcome
#
# The Core Scientific (CORZ) 13D/A Exhibit 99.2 blotter (pulled in notebook
# 01) shows the fund still forcibly selling CORZ via block trade on 3 August
# — five days after the main 30 July unwind. If the model is right, CORZ
# should be the (or among the) least liquid position(s) in the book.

# %%
blotter = pd.read_csv(cfg.PROCESSED / "blotter.csv")
corz_row = liq[liq.ticker == "CORZ"].iloc[0]
rank = int((liq["days_to_liquidate_20pct"] >= corz_row["days_to_liquidate_20pct"]).sum())
print(f"Core Scientific (CORZ): {corz_row['days_to_liquidate_20pct']:.2f} days-to-liquidate "
      f"@20% ADV — rank {rank} of {len(liq)} (1 = least liquid)")
print(f"\nBlotter evidence: CORZ was still being sold via block trade on "
      f"{blotter[blotter.block].trade_date.iloc[0]}, {(-blotter[blotter.block].shares).sum():,} "
      f"shares, at an average price of "
      f"${(blotter[blotter.block].price * -blotter[blotter.block].shares).sum() / (-blotter[blotter.block].shares).sum():.2f}, "
      f"while the earlier 14-15 July open-market sales cleared at "
      f"${blotter[~blotter.block].price.mean():.2f}.")
discount = 1 - (blotter[blotter.block].price.mean() / blotter[~blotter.block].price.mean())
print(f"Block-trade discount to the mid-July open-market prints: {discount:.1%}")

model_correctly_flags_corz = rank == 1
print(f"\nModel correctly identifies CORZ as the single least-liquid position: "
      f"{model_correctly_flags_corz}")

# %% [markdown]
# ## 5. The counterintuitive result — chart it, don't bury it

# %%
fig, ax = plt.subplots(figsize=(10, 6))
colors = [PALETTE["put"] if t == "CORZ" else PALETTE["neutral"] for t in liq.ticker]
ax.barh(liq.ticker, liq.days_to_liquidate_20pct, color=colors)
ax.set_xlabel("Days to liquidate @ 20% of trailing 3-month ADV")
ax.set_title("Situational Awareness — Pre-Collapse Book Looked Liquid on a Standard Screen\n"
              f"Book-weighted: {bw_20:.1f} days. The one name flagged (CORZ, in red) is the "
              f"one that\ndemonstrably could not clear — forced block trade 5 days after the main unwind")
source_note(ax, f"Source: SEC 13F-HR (30 Jun 2026) position sizes; yfinance ADV, "
                 f"Apr-Jun 2026 snapshot pulled {snapshot_date}. CORZ outcome: SEC 13D/A Ex-99.2.")
plt.tight_layout()
plt.savefig(cfg.CHARTS / "liquidity_screen.png", dpi=300)
plt.close()
print("Saved outputs/charts/liquidity_screen.png")
print("\nNotebook 04 complete.")
