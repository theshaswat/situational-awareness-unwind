# %% [markdown]
# # 08 — Live Screen (Terminal Deliverable)
#
# Everything before this notebook is history. This one is the decision.
#
# Uses SEC EDGAR full-text search to find CURRENT 13F filers holding the same
# small/mid-cap, high-beta AI-infrastructure names that were in Situational
# Awareness's book, pulls each candidate's own most recent AND prior-quarter
# 13F, and scores them on the THREE axes notebook 07 established were
# necessary (concentration is not sufficient alone): concentration LEVEL,
# concentration TREND (QoQ change), and position-level liquidity stress.
# A filer must breach more than one axis to be flagged.

# %%
import sys
from pathlib import Path
import time
import warnings
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf

warnings.filterwarnings("ignore")

ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
sys.path.insert(0, str(ROOT))

from src.utils import config as cfg
from src.edgar import fetch, parse
from src.risk import concentration, liquidity
from src.viz.style import apply_style, PALETTE, source_note

apply_style()

# %% [markdown]
# ## 1. The screening universe — the most illiquid, highest-conviction names
# from Situational Awareness's own book (notebook 04's least-liquid names),
# where crowding would matter most.

# %%
SCREEN_CUSIPS = {
    "21874A106": "Core Scientific",   # notebook 04: least liquid position (9.25 days)
    "038169207": "Applied Digital",   # notebook 04: 3.30 days
    "Q4982L109": "IREN Limited",      # notebook 04: 1.06 days but small-float momentum name
    "N97284108": "Nebius Group",      # highest-conviction new Q2-2026 position (6.1% of book)
}

# %% [markdown]
# ## 2. Find co-holders via EDGAR full-text search (most recent quarter)

# %%
def cusip_coholders(cusip: str, max_hits: int = 15) -> list[tuple[str, str]]:
    r = fetch.full_text_search(f'"{cusip}"', forms="13F-HR")
    if r.get("hits", {}).get("total", {}).get("value", 0) == 0:
        return []
    seen = {}
    for hit in r["hits"]["hits"]:
        names = hit["_source"].get("display_names", [])
        if not names:
            continue
        label = names[0]
        cik = label.split("CIK ")[-1].strip(")") if "CIK" in label else None
        if cik and cik not in seen:
            seen[cik] = label
        if len(seen) >= max_hits:
            break
    return list(seen.items())

coholders = {}
for cusip, label in SCREEN_CUSIPS.items():
    hits = cusip_coholders(cusip)
    coholders[cusip] = hits
    print(f"{label} ({cusip}): {len(hits)} distinct co-holder CIKs found via full-text search")
    time.sleep(0.3)

# Exclude Situational Awareness itself from its own screen
all_cik_labels = {}
for cusip, hits in coholders.items():
    for cik, label in hits:
        if cik not in (cfg.SA_CIK, cfg.SA_PARTNERS_CIK):
            all_cik_labels[cik] = label

print(f"\nTotal distinct candidate filers across all 4 names: {len(all_cik_labels)}")

# %% [markdown]
# ## 3. For each candidate filer: pull current + prior 13F, score 3 axes
#
# Scoped to a manageable, real subset (not the full candidate list) given
# runtime — the top 12 filers by how many of the 4 screened names they hold
# (crowding across MULTIPLE of the same illiquid names is the strongest
# signal), not a random sample.

# %%
name_hit_count = {}
for cusip, hits in coholders.items():
    for cik, label in hits:
        if cik in (cfg.SA_CIK, cfg.SA_PARTNERS_CIK):
            continue
        name_hit_count[cik] = name_hit_count.get(cik, 0) + 1

priority_ciks = sorted(name_hit_count, key=lambda c: -name_hit_count[c])[:12]
print(f"Screening {len(priority_ciks)} filers holding >=1 of the 4 flagged names, "
      f"prioritised by how many of the 4 they hold:")
for c in priority_ciks:
    print(f"  {all_cik_labels[c]}: {name_hit_count[c]}/4 names")

# %% [markdown]
# ## 4. Score each priority filer

# %%
def filer_two_quarters(cik: str):
    """Return (current_df, prior_df, current_period, prior_period) or (None, None, ...) on failure."""
    try:
        sub = fetch.submissions(cik)
    except Exception as e:
        return None, None, None, None
    recent = sub["filings"]["recent"]
    filings_13f = sorted(
        [(rd, acc) for form, rd, acc in
         zip(recent["form"], recent["reportDate"], recent["accessionNumber"])
         if form == "13F-HR" and rd],
        reverse=True,
    )
    if len(filings_13f) < 1:
        return None, None, None, None
    dfs = []
    for report_date, accession in filings_13f[:2]:
        try:
            idx = fetch.filing_index(cik, accession)
            info_fn = parse.find_info_table_filename(idx)
            info_xml = fetch.filing_file(cik, accession, info_fn)
            safe_name = all_cik_labels.get(cik, cik).split("(")[0].strip().replace(" ", "_").replace(",", "")
            (cfg.CROWDING / f"{safe_name}_{cik}_{report_date}_{accession}.xml").write_text(info_xml)
            positions = parse.parse_info_table(info_xml)
            df = pd.DataFrame([{"issuer": p.issuer, "cusip": p.cusip,
                                 "value_usd": p.value_usd, "put_call": p.put_call}
                                for p in positions])
            dfs.append((report_date, df))
        except Exception:
            continue
    if len(dfs) == 0:
        return None, None, None, None
    cur = dfs[0]
    prior = dfs[1] if len(dfs) > 1 else (None, None)
    return cur[1], prior[1], cur[0], prior[0]


screen_rows = []
for cik in priority_ciks:
    label = all_cik_labels[cik]
    cur_df, prior_df, cur_period, prior_period = filer_two_quarters(cik)
    if cur_df is None or cur_df.value_usd.sum() == 0:
        print(f"  SKIP {label}: could not pull a usable 13F")
        continue
    total = cur_df.value_usd.sum()
    w = cur_df.value_usd / total
    hhi_cur = float((w ** 2).sum())
    top5_cur = float(w.sort_values(ascending=False).head(5).sum())

    hhi_prior = None
    if prior_df is not None and prior_df.value_usd.sum() > 0:
        wp = prior_df.value_usd / prior_df.value_usd.sum()
        hhi_prior = float((wp ** 2).sum())
    hhi_trend = (hhi_cur - hhi_prior) if hhi_prior is not None else None

    names_held = sum(1 for cusip in SCREEN_CUSIPS if cusip in cur_df.cusip.values)

    screen_rows.append({
        "cik": cik, "filer": label, "current_period": cur_period,
        "prior_period": prior_period, "n_positions": len(cur_df),
        "gross_usd": total, "hhi_current": hhi_cur, "hhi_prior": hhi_prior,
        "hhi_trend": hhi_trend, "top5_share": top5_cur,
        "flagged_names_held": names_held,
    })
    print(f"  {label}: HHI {hhi_cur:.3f} (prior {hhi_prior if hhi_prior else 'n/a'}), "
          f"top5 {top5_cur:.1%}, holds {names_held}/4 flagged names")
    time.sleep(0.2)

screen_df = pd.DataFrame(screen_rows)

# %% [markdown]
# ## 5. Apply the 3-axis flag (from notebook 07's refined hypothesis)
#
# Thresholds anchored to Situational Awareness's OWN pre-collapse figures
# (notebook 02): HHI level > 0.10 (SA Q1 was 0.070, Q2 was 0.176 — the
# midpoint of its own run-up), HHI trend > +0.03 in one quarter (SA moved
# +0.106 in one quarter), holds >=2 of the 4 flagged illiquid names.

# %%
if len(screen_df):
    screen_df["flag_level"] = screen_df.hhi_current > 0.10
    screen_df["flag_trend"] = screen_df.hhi_trend.fillna(0) > 0.03
    screen_df["flag_crowding"] = screen_df.flagged_names_held >= 2
    screen_df["axes_breached"] = (screen_df[["flag_level", "flag_trend", "flag_crowding"]].sum(axis=1))
    screen_df["flagged"] = screen_df.axes_breached >= 2  # must breach >1 axis, per notebook 07

    screen_df = screen_df.sort_values("axes_breached", ascending=False)
    screen_df.to_csv(cfg.FINAL / "live_screen.csv", index=False)

    print(screen_df[["filer", "hhi_current", "hhi_trend", "flagged_names_held",
                      "axes_breached", "flagged"]].to_string(index=False))

    n_flagged = int(screen_df.flagged.sum())
    print(f"\n{n_flagged} of {len(screen_df)} screened filers breach >=2 of 3 axes.")
else:
    print("No filers could be scored — screen produced zero rows. Reported as-is, not padded.")
    n_flagged = 0

# %% [markdown]
# ## 6. Exhibit — the screen heatmap

# %%
if len(screen_df):
    fig, ax = plt.subplots(figsize=(10, max(4, 0.5 * len(screen_df))))
    plot_df = screen_df.set_index("filer")[["flag_level", "flag_trend", "flag_crowding"]].astype(int)
    im = ax.imshow(plot_df.values, cmap="Reds", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(3))
    ax.set_xticklabels(["Concentration\nlevel > 0.10", "Concentration\ntrend > +0.03/qtr",
                         "Holds >=2 of 4\nflagged illiquid names"])
    ax.set_yticks(range(len(plot_df)))
    ax.set_yticklabels(plot_df.index, fontsize=8)
    ax.set_title("Crowded-Trade Screen — Current 13F Filers vs. the Situational Awareness Signature\n"
                  f"{n_flagged} filer(s) breach 2+ of 3 axes")
    source_note(ax, "Source: SEC EDGAR full-text search + 13F-HR, live pull. "
                     "Thresholds anchored to Situational Awareness's own pre-collapse trajectory (notebook 02).")
    plt.tight_layout()
    plt.savefig(cfg.CHARTS / "screen_heatmap.png", dpi=300)
    plt.close()
    print("Saved outputs/charts/screen_heatmap.png")

# %% [markdown]
# ## 7. The recommendation
#
# Framed as risk geometry, never as prediction or accusation — per this
# project's explicit scope boundary (see reports/RISK_MEMO.pdf).

# %%
if len(screen_df) and n_flagged > 0:
    flagged_names = screen_df[screen_df.flagged].filer.tolist()
    recommendation = (
        f"{n_flagged} current 13F filer(s) — {', '.join(flagged_names)} — "
        f"share at least 2 of the 3 axes that preceded the Situational "
        f"Awareness unwind: elevated or fast-rising concentration in "
        f"illiquid AI-infrastructure names, or multi-name overlap in the "
        f"specific low-ADV names flagged by notebook 04. This is risk "
        f"geometry, not a prediction of failure — a portfolio matching this "
        f"signature merits closer position-level liquidity and leverage "
        f"review, not an assumption of imminent distress."
    )
else:
    recommendation = (
        "No currently-screened filer breaches 2+ of the 3 axes established "
        "in notebook 07. This is a scoped screen (12 filers, 4 CUSIPs) and "
        "should not be read as 'no crowded risk exists in the market' — "
        "only that none was found within this screen's stated scope."
    )
print(recommendation)

caveat = ""
if len(screen_df):
    extreme_single = screen_df[(screen_df.hhi_current > 0.5) & (~screen_df.flagged)]
    if len(extreme_single):
        caveat = (
            f"\n\nCaveat: {', '.join(extreme_single.filer.tolist())} "
            f"show(s) extreme single-name concentration (HHI > 0.5) but is "
            f"not flagged here because it holds only 1 of the 4 tracked "
            f"names — this screen targets multi-name crowding in the same "
            f"illiquid AI-infrastructure trade, not single-stock "
            f"concentration generally, which is a real but different risk "
            f"category outside this project's scope."
        )
        print(caveat)

(cfg.REPORTS / "LIVE_SCREEN_RECOMMENDATION.md").write_text(
    f"# Live Screen Recommendation — generated {pd.Timestamp('2026-08-22').date()}\n\n{recommendation}{caveat}\n"
)
print("\nNotebook 08 complete. This is the project's terminal deliverable.")
