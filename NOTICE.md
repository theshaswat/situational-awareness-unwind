# Notice on scope of the licence

[`LICENSE`](LICENSE) is the MIT licence, and it applies to **the source code in this
repository** - everything under `src/` and `scripts/`. That code is free to reuse,
modify and redistribute with attribution.

It is not intended as a grant over the rest of the repository:

| What | Status |
|---|---|
| `src/`, `scripts/` | MIT — reuse freely with attribution |
| `reports/` | Written analysis. © 2026 Shaswat Sharma, all rights reserved. Quote with attribution; do not republish wholesale. |
| `model/` | Financial model. © 2026 Shaswat Sharma, all rights reserved. |
| `notebooks/`, `outputs/` | Analysis and its rendered exhibits. © 2026 Shaswat Sharma, all rights reserved. |
| SEC filings under `data/raw/edgar/` and `data/external/` | US federal government filings retrieved from SEC EDGAR, retained verbatim as evidence. Public record; not licensed by this repository. |
| Price and volume data under `data/raw/prices/` | Retrieved via yfinance. Subject to the source provider's terms; not licensed by this repository. |

The distinction matters because MIT is a software licence. Applying it unqualified to a
repository that also contains written analysis and third-party material would purport to
license work this author has no right to license, and to give away work this author did not
intend to give away.

## On the live screen

The screen in `notebooks/08_live_screen.py` and `reports/RISK_MEMO.pdf` names real,
currently-operating investment managers. It reports **risk geometry computed from their own
public SEC filings** — concentration level, concentration trend, and overlap in specific
illiquid names — and nothing more. It does not assert, imply, or predict that any named
filer is in distress, mismanaged, or likely to suffer losses. It cannot see any filer's
leverage, short book, or off-exchange exposure, and says so throughout.

Nothing here is investment advice.
