# %% [markdown]
# # 02 — Position Panel
#
# Turns the 7 raw quarterly info tables from notebook 01 into one tidy panel
# and computes the concentration series (HHI, top-5 share, long/put/call
# split) that motivates every later notebook.

# %%
import sys
from pathlib import Path
import re
import pandas as pd

ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
sys.path.insert(0, str(ROOT))

from src.utils import config as cfg
from src.edgar import parse
from src.risk import concentration

# %% [markdown]
# ## 1. Re-parse each quarter's info table straight from the immutable raw files

# %%
rows = []
for period, accession in cfg.SA_13F_FILINGS:
    matches = list(cfg.EDGAR_13F.glob(f"{period}_{accession}_*"))
    info_file = next(f for f in matches if "primary_doc" not in f.name)
    positions = parse.parse_info_table(info_file.read_text())
    for p in positions:
        rows.append({
            "period": period, "issuer": p.issuer, "cusip": p.cusip,
            "value_usd": p.value_usd, "shares": p.shares, "put_call": p.put_call,
        })

panel = pd.DataFrame(rows)
panel.to_parquet(cfg.PROCESSED / "position_panel.parquet", index=False)
print(f"Panel: {len(panel)} rows across {panel.period.nunique()} quarters")
panel.head()

# %% [markdown]
# ## 2. Concentration series — the headline numbers

# %%
conc = concentration.concentration_summary(panel)
conc["put_pct"] = conc.put_usd / conc.gross_usd
conc["long_pct"] = conc.long_usd / conc.gross_usd
conc["call_pct"] = conc.call_usd / conc.gross_usd
conc.to_csv(cfg.TABLES / "concentration_series.csv", index=False)
print(conc.to_string(index=False))

# %% [markdown]
# ## 3. Cross-check against notebook 01's filed totals
#
# Every quarter total already reconciled to its own `<tableValueTotal>` in
# notebook 01 (see data/processed/reconciliation_log.md). Re-verify the panel
# built here matches that log exactly, as an independent second check.

# %%
recon_log = (cfg.PROCESSED / "reconciliation_log.md").read_text()
recon_values = {}
for line in recon_log.splitlines():
    if not line.startswith("| 20"):
        continue
    cells = [c.strip() for c in line.strip("|").split("|")]
    period_str, filed_value_str = cells[0], cells[4]
    recon_values[period_str] = int(filed_value_str.replace("$", "").replace(",", ""))
mismatches = []
for _, row in conc.iterrows():
    filed_val = recon_values.get(row.period)
    if filed_val is None:
        continue
    if abs(row.gross_usd - filed_val) > 1:
        mismatches.append((row.period, row.gross_usd, filed_val))
print(f"Independent cross-check against notebook 01's log: {len(mismatches)} mismatches.")
assert not mismatches, f"Panel disagrees with reconciliation log: {mismatches}"

# %% [markdown]
# ## 4. Top holdings per quarter (for the data dictionary + README table)

# %%
top_by_q = {}
for period, g in panel.groupby("period"):
    total = g.value_usd.sum()
    top = g.assign(weight=g.value_usd / total).sort_values("weight", ascending=False).head(5)
    top_by_q[period] = top[["issuer", "put_call", "value_usd", "weight"]]
    print(f"\n{period} (top 5 of {len(g)}, total ${total:,.0f}):")
    for _, r in top.iterrows():
        print(f"  {r.weight:6.1%}  {r.put_call:5}  {r.issuer[:36]:36}  ${r.value_usd:,.0f}")

# %% [markdown]
# ## 5. Data dictionary

# %%
data_dict = """# Data Dictionary — data/processed/position_panel.parquet

| Field | Type | Description |
|---|---|---|
| period | str (YYYY-MM-DD) | 13F-HR reporting quarter-end date |
| issuer | str | Issuer name as filed (not normalised across quarters — e.g. "SanDisk Corp" spelling is as-filed) |
| cusip | str | 9-character CUSIP identifier, as filed |
| value_usd | int | Section 13(f) fair market value, whole US dollars (post-2023 SEC amendment) |
| shares | int | Number of shares or principal amount |
| put_call | str | "LONG" (default/blank), "PUT", or "CALL" — options entries give value of the UNDERLYING only; no strike, expiry, or bought/written flag is disclosed |

## Derived fields (outputs/tables/concentration_series.csv)
| Field | Description |
|---|---|
| gross_usd | Sum of value_usd across all entries that quarter |
| top5_share | Share of gross_usd held in the 5 largest positions |
| hhi | Herfindahl-Hirschman index of position weights (sum of squared weights) |
| put_pct / long_pct / call_pct | Share of gross_usd in each instrument type |

## Known data-quality notes
- 2025-12-31 filing has a $1 rounding gap between its own summary total and
  the sum of its line items (see reconciliation_log.md) — immaterial, not
  corrected, documented.
- Two related CIKs (2045724, 2038540) file identical holdings for Q1 2026;
  only CIK 2045724 (Situational Awareness LP) is used throughout this panel.
"""
(cfg.REPORTS / "DATA_DICTIONARY.md").write_text(data_dict)
print("Data dictionary written to reports/DATA_DICTIONARY.md")
print("\nNotebook 02 complete.")
