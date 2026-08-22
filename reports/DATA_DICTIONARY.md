# Data Dictionary — data/processed/position_panel.parquet

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
