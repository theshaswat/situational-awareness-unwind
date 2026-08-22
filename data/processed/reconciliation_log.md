# Reconciliation Log — notebook 01

Every quarter's parsed position count and total value validated against the filing's own `<tableEntryTotal>` / `<tableValueTotal>`.

| Period | Accession | Filed entries | Parsed entries | Filed value | Parsed value | Diff | Reconciles |
|---|---|---|---|---|---|---|---|
| 2024-12-31 | 0000935836-25-000120 | 6 | 6 | $254,813,765 | $254,813,765 | $+0 | True |
| 2025-03-31 | 0002045724-25-000002 | 12 | 12 | $1,005,567,727 | $1,005,567,727 | $+0 | True |
| 2025-06-30 | 0002045724-25-000006 | 9 | 9 | $2,123,023,762 | $2,123,023,762 | $+0 | True |
| 2025-09-30 | 0002045724-25-000008 | 28 | 28 | $4,138,368,748 | $4,138,368,748 | $+0 | True |
| 2025-12-31 | 0002045724-26-000002 | 29 | 29 | $5,516,758,344 | $5,516,758,345 | $+1 | True |
| 2026-03-31 | 0002045724-26-000008 | 42 | 42 | $13,676,657,577 | $13,676,657,577 | $+0 | True |
| 2026-06-30 | 0000935836-26-000418 | 26 | 26 | $20,242,292,228 | $20,242,292,228 | $+0 | True |

2025-12-31 carries a $1 gap between the filing's own summary total and the sum of its line items — a filer-side rounding artifact (1 part in ~5.5bn), not a parsing error. Tolerance of $1 applied and documented, nothing hidden.

**Two-CIK duplicate check (Q1 2026):** Partners LP reports 42 entries / $13,676,657,577 — IDENTICAL to LP's own Q1 2026 filing. Confirmed duplicate; excluded from all downstream panels.
