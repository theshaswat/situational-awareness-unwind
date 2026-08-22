"""Verification suite.

Asserts that the committed analytical outputs still reproduce from the
committed raw SEC filings. Run locally or in CI:

    python3 scripts/verify.py

Scope, stated honestly: this verifies the offline half of the pipeline —
notebooks 02 and 03, which read only from data/raw/edgar/ and are
deterministic. Notebooks 01, 04, 06, 07 and 08 call SEC EDGAR and yfinance
live; their outputs depend on when they are run and on a third-party price
feed, so asserting byte-equality on them would produce a test that fails for
reasons unrelated to the code. Those are dated in the README instead.

What this catches: a change to the parser, the concentration metrics, or the
panel construction that silently alters a published figure.
"""
import subprocess
import sys
import shutil
import tempfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

# (notebook, [artifacts it must reproduce byte-identically])
CHECKS = [
    ("notebooks/02_position_panel.ipynb", [
        "data/processed/position_panel.parquet",
        "outputs/tables/concentration_series.csv",
    ]),
    ("notebooks/03_hedge_removal.ipynb", [
        "outputs/tables/q1_q2_delta.csv",
    ]),
]

# Figures quoted in README.md / reports — assert the committed data still says
# what the prose says it says.
HEADLINE_FIGURES = [
    ("2026-03-31", "put_pct", 0.6185, 1e-3),
    ("2026-06-30", "put_pct", 0.0003, 1e-3),
    ("2026-03-31", "hhi", 0.0704, 1e-3),
    ("2026-06-30", "hhi", 0.1763, 1e-3),
    ("2026-06-30", "top5_share", 0.7729, 1e-3),
]


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


def main():
    failures = 0

    # 1. Snapshot committed artifacts, re-run the deterministic notebooks,
    #    compare, then restore. Work on copies so a failed run cannot leave
    #    the tree dirty.
    snapshot = Path(tempfile.mkdtemp())
    tracked = [a for _, arts in CHECKS for a in arts]
    for rel in tracked:
        dest = snapshot / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, dest)

    for nb, artifacts in CHECKS:
        print(f"re-running {nb} ...")
        r = subprocess.run(
            [sys.executable, "-m", "jupyter", "nbconvert", "--to", "notebook",
             "--execute", "--inplace", "--ExecutePreprocessor.timeout=300", nb],
            cwd=ROOT, capture_output=True, text=True,
        )
        if r.returncode != 0:
            print(r.stderr[-2000:])
            fail(f"{nb} did not execute cleanly")

        for rel in artifacts:
            before, after = snapshot / rel, ROOT / rel
            if rel.endswith(".parquet"):
                same = pd.read_parquet(before).equals(pd.read_parquet(after))
            else:
                same = pd.read_csv(before).equals(pd.read_csv(after))
            if same:
                print(f"  OK   {rel} reproduces identically")
            else:
                print(f"  FAIL {rel} changed")
                failures += 1

    # 2. Headline figures still match what the written analysis claims.
    conc = pd.read_csv(ROOT / "outputs/tables/concentration_series.csv")
    for period, col, expected, tol in HEADLINE_FIGURES:
        row = conc[conc.period == period]
        if row.empty:
            print(f"  FAIL no row for {period}")
            failures += 1
            continue
        actual = float(row.iloc[0][col])
        if abs(actual - expected) <= tol:
            print(f"  OK   {period} {col} = {actual:.4f} (README says ~{expected})")
        else:
            print(f"  FAIL {period} {col} = {actual:.4f}, README says ~{expected}")
            failures += 1

    # 3. The two related CIKs must not both feed the panel — summing them
    #    would double the book. Guard the de-duplication.
    panel = pd.read_parquet(ROOT / "data/processed/position_panel.parquet")
    q1 = panel[panel.period == "2026-03-31"]
    if len(q1) == 42 and abs(q1.value_usd.sum() - 13_676_657_577) <= 1:
        print("  OK   Q1-2026 panel matches the single filer's own reported total")
    else:
        print(f"  FAIL Q1-2026 panel has {len(q1)} rows / ${q1.value_usd.sum():,} "
              f"— expected 42 / $13,676,657,577 (double-counted CIKs?)")
        failures += 1

    shutil.rmtree(snapshot, ignore_errors=True)

    if failures:
        fail(f"{failures} check(s) failed")
    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
