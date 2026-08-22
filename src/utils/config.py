"""Project-wide paths and constants. No hardcoded paths anywhere else in src/."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

DATA = ROOT / "data"
RAW = DATA / "raw"
EDGAR_13F = RAW / "edgar" / "13f"
EDGAR_13DG = RAW / "edgar" / "13dg"
EDGAR_FORMD = RAW / "edgar" / "formd"
PRICES = RAW / "prices"
PROCESSED = DATA / "processed"
EXTERNAL = DATA / "external"
BENCHMARK_FILERS = EXTERNAL / "benchmark_filers"
CROWDING = EXTERNAL / "crowding_universe"
FINAL = DATA / "final"

OUTPUTS = ROOT / "outputs"
CHARTS = OUTPUTS / "charts"
TABLES = OUTPUTS / "tables"

MODEL = ROOT / "model"
REPORTS = ROOT / "reports"

SEC_UA = "Shaswat Sharma shaswatsharma21@gmail.com"

# Situational Awareness LP files under two related CIKs that report duplicate
# holdings — see notebook 01 for the de-duplication check.
SA_CIK = "2045724"
SA_PARTNERS_CIK = "2038540"

SA_13F_FILINGS = [
    ("2024-12-31", "0000935836-25-000120"),
    ("2025-03-31", "0002045724-25-000002"),
    ("2025-06-30", "0002045724-25-000006"),
    ("2025-09-30", "0002045724-25-000008"),
    ("2025-12-31", "0002045724-26-000002"),
    ("2026-03-31", "0002045724-26-000008"),
    ("2026-06-30", "0000935836-26-000418"),
]

# Out-of-sample benchmark filers (verified to actually file 13F-HR; Archegos
# does not — it traded via total-return swaps and is excluded, see notebook 07)
BENCHMARK_CIKS = {
    "Melvin Capital Management LP": "0001628110",
    "Tiger Global Management LLC": "0001167483",
}

for _p in (EDGAR_13F, EDGAR_13DG, EDGAR_FORMD, PRICES, PROCESSED, BENCHMARK_FILERS,
           CROWDING, FINAL, CHARTS, TABLES, MODEL, REPORTS):
    _p.mkdir(parents=True, exist_ok=True)
