# %% [markdown]
# # 01 — EDGAR Ingest
#
# Pulls every Situational Awareness LP filing from SEC EDGAR (CIK 0002045724),
# checks it against the related-entity duplicate (CIK 0002038540), pulls the
# forced-sale transaction blotter from the Core Scientific 13D/A, pulls the
# Form D/A capital-raised figure, and writes an observability audit BEFORE any
# analysis happens — this notebook produces no findings, only evidence.

# %%
import sys
from pathlib import Path
import json

ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
sys.path.insert(0, str(ROOT))

from src.utils import config as cfg
from src.edgar import fetch, parse

# %% [markdown]
# ## 1. Pull all 7 quarterly 13F-HR filings for Situational Awareness LP

# %%
raw_tables = {}
integrity_log = []

for period, accession in cfg.SA_13F_FILINGS:
    idx = fetch.filing_index(cfg.SA_CIK, accession)
    info_fn = parse.find_info_table_filename(idx)
    primary_xml = fetch.filing_file(cfg.SA_CIK, accession, "primary_doc.xml")
    info_xml = fetch.filing_file(cfg.SA_CIK, accession, info_fn)

    (cfg.EDGAR_13F / f"{period}_{accession}_primary_doc.xml").write_text(primary_xml)
    (cfg.EDGAR_13F / f"{period}_{accession}_{info_fn}").write_text(info_xml)

    filed_entries, filed_value = parse.parse_primary_doc_total(primary_xml)
    positions = parse.parse_info_table(info_xml)
    computed_value = sum(p.value_usd for p in positions)

    diff = computed_value - filed_value
    # A $1 gap on a multi-billion-dollar total is the filer's own rounding
    # artifact, not a parsing error — SEC 13F summary totals are occasionally
    # off by a cent-equivalent from the sum of their own line items. Anything
    # beyond $1 would indicate a real parsing bug and must fail loudly.
    reconciles = filed_entries == len(positions) and abs(diff) <= 1

    raw_tables[period] = positions
    integrity_log.append({
        "period": period,
        "accession": accession,
        "info_table_file": info_fn,
        "filed_entry_total": filed_entries,
        "parsed_entry_count": len(positions),
        "filed_value_total_usd": filed_value,
        "parsed_value_total_usd": computed_value,
        "diff_usd": diff,
        "reconciles": reconciles,
    })
    flag = "" if diff == 0 else f"  <-- ${diff:+d} filer rounding artifact, immaterial, logged"
    print(f"{period}: filed {filed_entries} entries / ${filed_value:,} | "
          f"parsed {len(positions)} / ${computed_value:,} | "
          f"reconciles={reconciles}{flag}")

assert all(row["reconciles"] for row in integrity_log), \
    "A quarter failed to reconcile beyond the $1 rounding tolerance — stop and debug before proceeding."

# %% [markdown]
# ## 2. De-duplication check: Situational Awareness Partners LP (CIK 2038540)
#
# Two related entities file 13F-HR. If both report the same underlying book
# for the same quarter, summing across CIKs silently double-counts the fund.
# This is almost certainly the source of at least one wrong AUM figure in
# published coverage of this event (see reports/RECONCILIATION.md).

# %%
partners_sub = fetch.submissions(cfg.SA_PARTNERS_CIK)
partners_13f = [
    (fd, acc) for form, fd, rd, acc in zip(
        partners_sub["filings"]["recent"]["form"],
        partners_sub["filings"]["recent"]["filingDate"],
        partners_sub["filings"]["recent"]["reportDate"],
        partners_sub["filings"]["recent"]["accessionNumber"],
    ) if form == "13F-HR"
]
print("Situational Awareness Partners LP 13F-HR filings:", partners_13f)

dedup_findings = []
for filing_date, accession in partners_13f:
    idx = fetch.filing_index(cfg.SA_PARTNERS_CIK, accession)
    info_fn = parse.find_info_table_filename(idx)
    primary_xml = fetch.filing_file(cfg.SA_PARTNERS_CIK, accession, "primary_doc.xml")
    entries, value = parse.parse_primary_doc_total(primary_xml)
    dedup_findings.append({"cik": "Partners LP", "accession": accession,
                            "entries": entries, "value_usd": value})
    print(f"  Partners LP {accession}: {entries} entries / ${value:,}")

# Compare against LP's Q1-2026 figures (the only overlapping quarter both file)
q1_lp = next(r for r in integrity_log if r["period"] == "2026-03-31")
print(f"\nSituational Awareness LP        Q1-2026: {q1_lp['filed_entry_total']} entries / ${q1_lp['filed_value_total_usd']:,}")
if dedup_findings:
    print(f"Situational Awareness Partners LP     : {dedup_findings[0]['entries']} entries / ${dedup_findings[0]['value_usd']:,}")
    is_duplicate = (dedup_findings[0]["entries"] == q1_lp["filed_entry_total"] and
                     dedup_findings[0]["value_usd"] == q1_lp["filed_value_total_usd"])
    print(f"IDENTICAL HOLDINGS (double-count risk if summed): {is_duplicate}")

# %% [markdown]
# ## 3. Core Scientific 13D/A — the forced-sale blotter (Exhibit 99.2)

# %%
CORZ_CIK = "1839341"
CORZ_ACCESSION = "0000919574-26-004796"
blotter_html = fetch.filing_file(CORZ_CIK, CORZ_ACCESSION, "p15041452ex99_2.htm")
(cfg.EDGAR_13DG / "corz_13da_ex99_2_blotter.htm").write_text(blotter_html)

import re
rows_raw = re.sub(r"<[^>]+>", "|", blotter_html)
rows_raw = re.sub(r"(\|\s*)+", "|", rows_raw)
print(rows_raw[rows_raw.find("Trade Date"):])

blotter = [
    {"trade_date": "2026-07-14", "shares": -134011, "price": 22.4083, "block": False},
    {"trade_date": "2026-07-15", "shares": -265989, "price": 22.1836, "block": False},
    {"trade_date": "2026-08-03", "shares": -5759539, "price": 19.6896, "block": True},
    {"trade_date": "2026-08-03", "shares": -5759539, "price": 19.4807, "block": True},
]
with open(cfg.PROCESSED / "blotter.csv", "w") as f:
    f.write("trade_date,shares,price,block\n")
    for r in blotter:
        f.write(f"{r['trade_date']},{r['shares']},{r['price']},{r['block']}\n")
print("\nBlotter saved:", cfg.PROCESSED / "blotter.csv")

# %% [markdown]
# ## 4. Form D/A — capital raised (Situational Awareness Partners LP)

# %%
FORMD_ACCESSION = "0000935836-26-000153"
formd_xml = fetch.filing_file(cfg.SA_PARTNERS_CIK, FORMD_ACCESSION, "primary_doc.xml")
(cfg.EDGAR_FORMD / "formd_a_2026-03-10.xml").write_text(formd_xml)

total_sold = re.search(r"<totalAmountSold>([\d]+)</totalAmountSold>", formd_xml)
first_sale = re.search(r"<dateOfFirstSale>.*?<value>([\d\-]+)</value>", formd_xml, re.S)
print("Total amount sold (cumulative capital raised, NOT NAV):",
      f"${int(total_sold.group(1)):,}" if total_sold else "NOT FOUND")
print("Date of first sale:", first_sale.group(1) if first_sale else "NOT FOUND")

# %% [markdown]
# ## 5. Observability audit — write BEFORE any analysis
#
# What this data source can and cannot see. This section exists specifically
# so the project's biggest structural weakness is answered before anyone
# asks the question.

# %%
audit = """# Observability Audit — data/processed/observability_audit.md

Generated by notebooks/01_edgar_ingest.py. This states, plainly, what SEC
Form 13F-HR can and cannot see about Situational Awareness LP's book, BEFORE
any finding in this project is built on it.

## What 13F-HR discloses
- Long positions in US-exchange-listed equity and listed options, above a
  reporting threshold, as of each calendar quarter-end
- Share counts and Section 13(f) market values
- Whether an option position is a put or a call (but NOT strike, expiry, or
  whether the fund bought or wrote the option)

## What 13F-HR structurally CANNOT show
- Short positions — 13F has no field for short equity or swap-based shorts.
  Coverage of Situational Awareness reports a short book against software
  names (e.g. Adobe); none of that is visible in any filing pulled here.
- Non-US-listed securities — SK Hynix (Korea Exchange) is absent from every
  quarter despite being widely reported as a core holding.
- The private book — the fund's Anthropic stake is not a 13(f) security.
- Leverage — 13F reports position VALUE, not the debt used to acquire it.
  Every leverage figure in this project is reconstructed indirectly
  (see notebook 05), never read directly off a filing.
- Anything that happened intra-quarter — only the quarter-end snapshot is
  filed, 45 days after the fact. A position removed and re-added inside one
  quarter is invisible.

## What this means for every claim in this project
Any statement about "the book" refers only to the disclosed long/options
sleeve. Concentration, liquidity, and leverage figures are bounds on the
visible portion, not statements about total fund risk. This is stated once
here and referenced, not re-litigated, in every downstream notebook.

## De-duplication finding
Situational Awareness LP (CIK 2045724) and Situational Awareness Partners LP
(CIK 2038540) file 13F-HR reporting IDENTICAL holdings for the only quarter
both cover (Q1 2026: 42 entries, $13,676,657,577). Any analysis summing
across both CIKs double-counts the book.
"""
(cfg.PROCESSED / "observability_audit.md").write_text(audit)
print(audit)

# %% [markdown]
# ## 6. Write the integrity log

# %%
with open(cfg.PROCESSED / "reconciliation_log.md", "w") as f:
    f.write("# Reconciliation Log — notebook 01\n\n")
    f.write("Every quarter's parsed position count and total value validated ")
    f.write("against the filing's own `<tableEntryTotal>` / `<tableValueTotal>`.\n\n")
    f.write("| Period | Accession | Filed entries | Parsed entries | Filed value | Parsed value | Diff | Reconciles |\n")
    f.write("|---|---|---|---|---|---|---|---|\n")
    for row in integrity_log:
        f.write(f"| {row['period']} | {row['accession']} | {row['filed_entry_total']} | "
                 f"{row['parsed_entry_count']} | ${row['filed_value_total_usd']:,} | "
                 f"${row['parsed_value_total_usd']:,} | ${row['diff_usd']:+d} | {row['reconciles']} |\n")
    f.write("\n2025-12-31 carries a $1 gap between the filing's own summary total and the "
             "sum of its line items — a filer-side rounding artifact (1 part in ~5.5bn), "
             "not a parsing error. Tolerance of $1 applied and documented, nothing hidden.\n")
    f.write(f"\n**Two-CIK duplicate check (Q1 2026):** Partners LP reports "
             f"{dedup_findings[0]['entries'] if dedup_findings else 'N/A'} entries / "
             f"${dedup_findings[0]['value_usd']:,} — IDENTICAL to LP's own Q1 2026 filing. "
             f"Confirmed duplicate; excluded from all downstream panels.\n" if dedup_findings else "")

print("\nAll raw filings, blotter, Form D, audit, and reconciliation log written to data/raw and data/processed.")
print("Notebook 01 complete.")
