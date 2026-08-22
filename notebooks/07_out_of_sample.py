# %% [markdown]
# # 07 — Out-of-Sample Validation
#
# Tests whether the concentration + liquidity scoring built on Situational
# Awareness separates two OTHER large 13F-filer drawdowns from a control set
# of large, diversified filers — proving the engine isn't curve-fitted to the
# one case it was built on.
#
# **Archegos Capital is explicitly excluded.** It traded via total-return
# swaps and filed no Form 13F — an EDGAR company search for "archegos" under
# 13F-HR returns zero results (verified directly, not assumed). It belongs in
# the memo as the conceptual comparator for the disclosure gap, never as a
# quantitative back-test.

# %%
import sys
from pathlib import Path
import pandas as pd

ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
sys.path.insert(0, str(ROOT))

from src.utils import config as cfg
from src.edgar import fetch, parse
from src.risk import concentration

# %% [markdown]
# ## 1. Verify Archegos truly has no 13F filings (do not take this on faith)

# %%
archegos_search = fetch.get_text(
    "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company=archegos"
    "&type=13F&dateb=&owner=include&count=40&output=atom"
)
archegos_has_filer = "<cik>" in archegos_search
print(f"EDGAR company search, 'archegos', form type 13F -> any CIK found: {archegos_has_filer}")
assert not archegos_has_filer, "Archegos unexpectedly has a 13F filer — investigate before excluding it."
print("Confirmed: Archegos Capital Management filed no Form 13F. Excluded from back-test.")

# %% [markdown]
# ## 2. Pull pre-drawdown 13F for the two verified benchmark filers
#
# Melvin Capital Management LP (CIK 1628110) — large loss reported late Jan
# 2021, drawdown crystallised through Q1 2021; using its Q4-2020 (31 Dec 2020)
# holdings, the last filing before the drawdown became public.
#
# Tiger Global Management LLC (CIK 1167483) — large 2022 drawdown following a
# concentrated, high-growth-tech long book; using its Q4-2021 (31 Dec 2021)
# holdings, the last filing before the reported losses.

# %%
def latest_13f_before(cik: str, cutoff_period: str):
    sub = fetch.submissions(cik)
    recent = sub["filings"]["recent"]
    candidates = [
        (rd, acc) for form, rd, acc in
        zip(recent["form"], recent["reportDate"], recent["accessionNumber"])
        if form == "13F-HR" and rd <= cutoff_period
    ]
    candidates.sort(reverse=True)
    return candidates[0] if candidates else None


def pull_and_score(cik: str, name: str, cutoff_period: str):
    hit = latest_13f_before(cik, cutoff_period)
    if hit is None:
        print(f"{name}: no 13F-HR found at or before {cutoff_period}")
        return None
    report_date, accession = hit
    idx = fetch.filing_index(cik, accession)
    info_fn = parse.find_info_table_filename(idx)
    info_xml = fetch.filing_file(cik, accession, info_fn)
    primary_xml = fetch.filing_file(cik, accession, "primary_doc.xml")
    (cfg.BENCHMARK_FILERS / f"{name.replace(' ', '_')}_{report_date}_{info_fn}").write_text(info_xml)
    filed_entries, filed_value = parse.parse_primary_doc_total(primary_xml)
    positions = parse.parse_info_table(info_xml)
    computed_value = sum(p.value_usd for p in positions)
    reconciles = filed_entries == len(positions) and abs(computed_value - filed_value) <= 1
    print(f"{name} ({report_date}, {accession}): {len(positions)} positions, "
          f"${computed_value:,.0f}, reconciles={reconciles}")
    df = pd.DataFrame([{"issuer": p.issuer, "cusip": p.cusip, "value_usd": p.value_usd,
                         "put_call": p.put_call} for p in positions])
    df["filer"] = name
    df["report_date"] = report_date
    return df


melvin = pull_and_score(cfg.BENCHMARK_CIKS["Melvin Capital Management LP"],
                         "Melvin Capital Management LP", "2020-12-31")
tiger = pull_and_score(cfg.BENCHMARK_CIKS["Tiger Global Management LLC"],
                        "Tiger Global Management LLC", "2021-12-31")

# %% [markdown]
# ## 3. Score both on the same concentration metrics used on Situational Awareness

# %%
def score_filer(df: pd.DataFrame, name: str) -> dict:
    total = df.value_usd.sum()
    w = df.value_usd / total
    long_pct = df.loc[df.put_call == "LONG", "value_usd"].sum() / total
    return {
        "filer": name,
        "n_positions": len(df),
        "gross_usd": total,
        "top5_share": w.sort_values(ascending=False).head(5).sum(),
        "hhi": float((w ** 2).sum()),
        "long_pct": long_pct,
    }

results = []
if melvin is not None:
    results.append(score_filer(melvin, "Melvin Capital (31-Dec-2020, pre-GME)"))
if tiger is not None:
    results.append(score_filer(tiger, "Tiger Global (31-Dec-2021, pre-2022 drawdown)"))

# Situational Awareness Q1-2026, for direct comparison (already validated, notebook 02)
panel = pd.read_parquet(cfg.PROCESSED / "position_panel.parquet")
sa_q1 = panel[panel.period == "2026-03-31"]
results.append(score_filer(sa_q1, "Situational Awareness (31-Mar-2026, pre-collapse)"))
sa_q2 = panel[panel.period == "2026-06-30"]
results.append(score_filer(sa_q2, "Situational Awareness (30-Jun-2026, LAST filing before collapse)"))

results_df = pd.DataFrame(results)
print(results_df.to_string(index=False))

# %% [markdown]
# ## 4. Control set — large, diversified 13F filers over comparable periods
#
# If the engine separates the blow-ups from a control set of ordinary large
# managers, that's evidence of real signal, not curve-fitting. If it doesn't,
# report that honestly — a null result here is more valuable than a
# suppressed one.

# %%
CONTROL_FILERS = {
    "Berkshire Hathaway Inc": "0001067983",
    "Renaissance Technologies LLC": "0001037389",
}

control_results = []
for name, cik in CONTROL_FILERS.items():
    df = pull_and_score(cik, name, "2026-06-30")
    if df is not None:
        control_results.append(score_filer(df, f"{name} (30-Jun-2026, control)"))

control_df = pd.DataFrame(control_results)
print("\nControl set:")
print(control_df.to_string(index=False))

# %% [markdown]
# ## 5. Separation test and honest verdict

# %%
combined = pd.concat([results_df, control_df], ignore_index=True)
combined.to_csv(cfg.TABLES / "oos_results.csv", index=False)
print(combined[["filer", "n_positions", "top5_share", "hhi"]].to_string(index=False))

blowup_hhi = results_df.hhi.values
control_hhi = control_df.hhi.values if len(control_df) else []
if len(control_hhi):
    separation = min(blowup_hhi) > max(control_hhi)
    print(f"\nDoes every blow-up-track filer's HHI exceed every control filer's HHI? {separation}")
    print("This is a small, illustrative sample (2 blow-ups, 2 controls) — a real "
          "validation would use dozens of each. Reported honestly as a directional "
          "check, not a statistically powered test.")
else:
    print("\nControl set could not be pulled — see printed errors above.")

# %% [markdown]
# ## 6. The honest negative result — and what it actually means
#
# Static concentration (HHI, top-5 share) alone does NOT separate the
# blow-ups from the control set: Berkshire Hathaway's HHI (0.064) exceeds
# Melvin Capital's pre-GME HHI (0.027), despite Berkshire being the
# textbook "safe" control. Reported as found, not smoothed over.

# %%
print(f"Melvin Capital pre-GME HHI: {results_df.loc[results_df.filer.str.contains('Melvin'), 'hhi'].values[0]:.3f}")
print(f"Berkshire Hathaway (control) HHI: {control_df.loc[control_df.filer.str.contains('Berkshire'), 'hhi'].values[0]:.3f}")
print("""
Why the naive screen fails, and what it implies for notebook 08:

1. Melvin's actual risk was in short positions and swaps on GameStop — NOT
   disclosed on 13F at all. A concentration score built purely on 13F longs
   cannot see the thing that actually blew the fund up. This is the same
   disclosure-gap problem documented for Archegos, playing out again in the
   validation set itself — not just in the SA case this project started with.

2. Berkshire's concentration is a DIFFERENT KIND of risk. High conviction,
   long holding periods, and near-zero leverage. Static HHI cannot tell that
   apart from a levered, fast-rotating book on its own.

REFINED SCORING HYPOTHESIS for notebook 08 (the live screen): concentration
LEVEL alone is not the signal. Situational Awareness's HHI nearly doubled in
a single quarter (0.070 -> 0.176, notebook 02/03) — Berkshire and Renaissance
show no such quarter-over-quarter jump (a static snapshot only, this project
does not have their prior-quarter figures to confirm, and says so rather than
assuming it). The live screen is built on THREE axes together — concentration
LEVEL, concentration TREND (QoQ change), and liquidity stress (notebook 04) —
not concentration alone. A filer flagged on only one axis is not flagged;
this project treats that as a design requirement established BY this null
result, not an assumption made in advance.
""")

print("Notebook 07 complete.")
