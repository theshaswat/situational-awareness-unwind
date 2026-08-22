# RECONCILIATION.md — Documented Source Conflicts

Every published account of this event checked during this project's research contains at least one figure that does not match the underlying SEC filing. Each conflict below is stated with both sides and how it was resolved — nothing is silently picked.

## Peak AUM
- **Claim A:** CNBC (31 Jul 2026): '$45 billion in assets'
- **Claim B:** SpotGamma analysis: '~$24 billion by mid-2026'
- **Resolution:** Unresolved from public sources — no source defines whether its figure is gross notional, NAV, or NAV+leverage. Both are reported below without picking a winner.

## Prime brokers
- **Claim A:** Original video source implies Goldman Sachs alone issued the margin call
- **Claim B:** CNBC (30 Jul 2026): three brokers — Goldman Sachs, JPMorgan Chase, and Bank of America
- **Resolution:** Three-broker version is the better-sourced claim; used throughout this project.

## Q1-2026 13F composition
- **Claim A:** SpotGamma: '$1.86bn, 26 positions, Bloom Energy 22.8%, SanDisk 18.8%'
- **Claim B:** SEC 13F-HR (this project, notebook 01-02): $13,676,657,577 across 42 positions; Bloom 6.4%, SanDisk 5.3%
- **Resolution:** CONTRADICTED by the filing. SpotGamma's figures match no quarter in the 7-quarter panel built here. The filing's own <tableValueTotal> is used throughout.

## Block trade timing
- **Claim A:** Multiple outlets: single block trade, 30 July 2026
- **Claim B:** SEC 13D/A Ex-99.2 (this project): CORZ block trades dated 3 August 2026, five days after 30 July
- **Resolution:** Both are true. The bulk of the book cleared 29-30 July; the least-liquid tail (CORZ, confirmed by notebook 04's liquidity model) cleared several days later. The 'single trade' narrative is incomplete, not wrong.

## Options-hedge notional
- **Claim A:** SpotGamma: '~$10bn notional SMH puts, $3.6bn NVDA puts'
- **Claim B:** SEC 13F-HR Q1-2026 (this project): SMH/VanEck ETF put $2.04bn; NVDA put $1.57bn
- **Resolution:** Right instruments, wrong magnitudes by a factor of roughly 2-5x. Filed figures used throughout.

