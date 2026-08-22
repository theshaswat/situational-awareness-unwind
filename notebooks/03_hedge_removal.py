# %% [markdown]
# # 03 — Hedge Removal
#
# The central finding of this project: between 31 Mar and 30 Jun 2026, the
# fund's put book collapsed from 61.9% of gross exposure to 0.03%, while
# concentration in the top 5 names rose sharply. This notebook establishes
# the finding, quantifies it position-by-position, and states explicitly what
# 13F data can and cannot prove about *why* it happened.

# %%
import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
sys.path.insert(0, str(ROOT))

from src.utils import config as cfg
from src.viz.style import apply_style, PALETTE, source_note

apply_style()

panel = pd.read_parquet(cfg.PROCESSED / "position_panel.parquet")
conc = pd.read_csv(cfg.TABLES / "concentration_series.csv")

# %% [markdown]
# ## 1. Position-level Q1 2026 -> Q2 2026 delta

# %%
q1 = panel[panel.period == "2026-03-31"].groupby(["issuer", "put_call"], as_index=False).value_usd.sum()
q2 = panel[panel.period == "2026-06-30"].groupby(["issuer", "put_call"], as_index=False).value_usd.sum()
q1 = q1.rename(columns={"value_usd": "q1_value"})
q2 = q2.rename(columns={"value_usd": "q2_value"})
delta = pd.merge(q1, q2, on=["issuer", "put_call"], how="outer").fillna(0)
delta["change_usd"] = delta.q2_value - delta.q1_value
delta = delta.sort_values("change_usd")
delta.to_csv(cfg.TABLES / "q1_q2_delta.csv", index=False)

print("Largest DECREASES (Q1 -> Q2):")
print(delta.head(10).to_string(index=False))
print("\nLargest INCREASES (Q1 -> Q2):")
print(delta.tail(10).to_string(index=False))

# %% [markdown]
# ## 2. Isolate the put book that went to zero

# %%
put_q1 = q1[q1.put_call == "PUT"].sort_values("q1_value", ascending=False)
put_q1["still_present_q2"] = put_q1.issuer.isin(q2[(q2.put_call == "PUT") & (q2.q2_value > 0)].issuer)
print(f"Put positions held Q1-2026 (total ${put_q1.q1_value.sum():,.0f}):")
print(put_q1.to_string(index=False))
print(f"\nOf {len(put_q1)} put positions in Q1, {put_q1.still_present_q2.sum()} still present in Q2.")

# %% [markdown]
# ## 3. Sign flips — a put in Q1 becomes a long in Q2 on the same issuer

# %%
q1_puts_set = set(put_q1[put_q1.q1_value > 0].issuer)
q2_longs = q2[(q2.put_call == "LONG") & (q2.q2_value > 0)]
flips = q2_longs[q2_longs.issuer.isin(q1_puts_set)].copy()
flips = flips.merge(put_q1[["issuer", "q1_value"]], on="issuer", suffixes=("", "_put"))
flips = flips.rename(columns={"q1_value": "q1_put_value", "q2_value": "q2_long_value"})
print("Issuers with a PUT in Q1-2026 that became a LONG in Q2-2026:")
print(flips[["issuer", "q1_put_value", "q2_long_value"]].to_string(index=False))

# %% [markdown]
# ## 4. Seven-quarter long/put/call decomposition — the headline exhibit

# %%
fig, ax = plt.subplots(figsize=(11, 6))
x = range(len(conc))
ax.bar(x, conc.long_pct, color=PALETTE["long"], label="Long")
ax.bar(x, conc.put_pct, bottom=conc.long_pct, color=PALETTE["put"], label="Put")
ax.bar(x, conc.call_pct, bottom=conc.long_pct + conc.put_pct, color=PALETTE["call"], label="Call")
ax.set_xticks(list(x))
ax.set_xticklabels(conc.period, rotation=30, ha="right")
ax.set_ylabel("Share of disclosed gross exposure")
ax.set_title("Situational Awareness LP — Disclosed Book Composition, 7 Quarters\n"
              "Put-linked exposure fell from 61.9% to 0.03% of gross the quarter before the collapse")
ax.legend(loc="upper left")
ax.set_ylim(0, 1.05)
source_note(ax, "Source: SEC Form 13F-HR, CIK 0002045724, filed quarterly. "
                 "Put/call figures reflect value of underlying only (no strike/expiry disclosed).")
plt.tight_layout()
plt.savefig(cfg.CHARTS / "hedge_removal.png", dpi=300)
plt.close()
print("Saved outputs/charts/hedge_removal.png")

# %% [markdown]
# ## 5. The bounded finding — write it once, precisely
#
# 13F cannot distinguish a deliberate close-out from an unrolled expiry. The
# finding below is written to be true under EITHER explanation.

# %%
finding = f"""# The Hedge-Removal Finding — bounded statement

**What the filings show:** Situational Awareness LP's Q1-2026 (31 Mar) 13F-HR
disclosed {len(put_q1)} put positions totalling ${put_q1.q1_value.sum():,.0f},
equal to {conc.loc[conc.period=='2026-03-31','put_pct'].values[0]:.1%} of
disclosed gross exposure. The Q2-2026 (30 Jun) filing — the LAST filed before
the July collapse — discloses put-linked exposure of
${conc.loc[conc.period=='2026-06-30','put_usd'].values[0]:,.0f}, or
{conc.loc[conc.period=='2026-06-30','put_pct'].values[0]:.2%} of gross.
Two names ({', '.join(flips.issuer.tolist())}) show a PUT position in Q1
replaced by a LONG position of larger dollar value in Q2 on the identical
issuer.

**What this does NOT prove:** 13F reports quarter-end snapshots only. A put
position absent at quarter-end may have been actively sold, or may simply
have expired without being rolled — both produce an identical filing. Neither
can be distinguished from public data. No claim in this project asserts
Leopold Aschenbrenner "chose" to remove the hedge on a specific date.

**The defensible sentence:** Whether by expiry or by decision, Situational
Awareness entered July 2026 with no disclosed downside protection on its
public book, versus {conc.loc[conc.period=='2026-03-31','put_pct'].values[0]:.0%}
of gross in puts three months earlier — a bounded, filing-evidenced fact,
independent of intent.
"""
(cfg.REPORTS / "FINDING_hedge_removal.md").write_text(finding)
print(finding)
print("Notebook 03 complete.")
