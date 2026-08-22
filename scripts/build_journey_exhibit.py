"""Builds outputs/charts/journey.png — the full arc of the fund as a dark,
card-based dashboard sized for social (1200x1500, 4:5).

Every figure comes from data already committed in this repository: the
concentration series parsed from seven 13F-HR filings, the daily closes pulled
for the July window, and the forced-sale blotter recovered from the Schedule
13D/A. Nothing here is illustrative.

Run from repo root:  python3 scripts/build_journey_exhibit.py
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.utils import config as cfg  # noqa: E402

# Dark dashboard palette. Accent matches the author's existing dark-mode
# profile assets (#b39ddb) so the exhibit reads as part of the same body of
# work rather than a one-off.
BG = "#0d1117"
CARD = "#161b26"
EDGE = "#232b38"
TEXT = "#e6edf3"
MUTED = "#8b98a5"
DIM = "#5c6b7a"
ACCENT = "#b39ddb"
HEDGE = "#3fb984"
LOSS = "#f2545b"
GRID = "#1e2530"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    "text.color": TEXT,
    "axes.labelcolor": MUTED,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "axes.edgecolor": EDGE,
})

conc = pd.read_csv(cfg.TABLES / "concentration_series.csv")
conc["label"] = pd.to_datetime(conc.period).dt.strftime("%b\n%y")
px = pd.read_parquet(cfg.PRICES / "close_jun_aug_2026_20260822.parquet")
blot = pd.read_csv(cfg.PROCESSED / "blotter.csv", parse_dates=["trade_date"])

fig = plt.figure(figsize=(12, 15), dpi=100, facecolor=BG)


def card(x, y, w, h, radius=0.012):
    """Draw a rounded card on the figure and return its rect for insetting."""
    # add_artist, not fig.patches.append: appending to the list leaves
    # patch.figure unset, and the card then draws after the axes and hides
    # the chart inside it.
    fig.add_artist(FancyBboxPatch(
        (x, y), w, h, transform=fig.transFigure,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        facecolor=CARD, edgecolor=EDGE, linewidth=1.2, zorder=0))
    return x, y, w, h


def style_axes(ax):
    ax.set_zorder(3)          # above the card patch
    ax.patch.set_alpha(0)     # let the card colour show through
    ax.set_facecolor("none")
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color(EDGE)
    ax.tick_params(length=0, labelsize=10)
    ax.grid(axis="y", color=GRID, lw=1, zorder=0)
    ax.set_axisbelow(True)


L, R = 0.045, 0.955
W = R - L

# ------------------------------------------------------------------ header
fig.text(L, 0.972, "S I T U A T I O N A L   A W A R E N E S S   L P",
         fontsize=11.5, color=ACCENT, fontweight="600", va="top")
fig.text(L, 0.949, "\\$255m to \\$20bn to forced liquidation",
         fontsize=27, fontweight="700", color=TEXT, va="top")
fig.text(L, 0.9155, "Eighteen months, reconstructed from primary SEC filings",
         fontsize=13, color=MUTED, va="top")
fig.text(R, 0.9525, "JUL 2026", fontsize=11, color=LOSS,
         fontweight="700", va="top", ha="right")
fig.text(R, 0.9335, "7 filings · 1 blotter", fontsize=10.5, color=DIM,
         va="top", ha="right")

# --------------------------------------------------------------- KPI cards
kpis = [
    ("79x", "book growth", "6 quarters", ACCENT),
    ("62% to 0.03%", "put-linked exposure", "final quarter", HEDGE),
    ("1.55 days", "days-to-liquidate", "screened liquid", TEXT),
    ("−67%", "fund equity, July", "unaudited", LOSS),
]
gap = 0.014
kw = (W - 3 * gap) / 4
ky, kh = 0.788, 0.108
for i, (big, lab, sub, col) in enumerate(kpis):
    kx = L + i * (kw + gap)
    card(kx, ky, kw, kh)
    size = 21 if len(big) <= 9 else 16.5
    fig.text(kx + 0.018, ky + kh - 0.026, big, fontsize=size,
             fontweight="700", color=col, va="top")
    fig.text(kx + 0.018, ky + kh - 0.063, lab, fontsize=11,
             color=TEXT, va="top")
    fig.text(kx + 0.018, ky + kh - 0.082, sub, fontsize=9.8,
             color=DIM, va="top")

# --------------------------------------------- act 1: the rise + the hedge
cx, cy, cw, ch = card(L, 0.533, W, 0.232)
fig.text(cx + 0.020, cy + ch - 0.020, "01   The book grows 79x, hedged until the last quarter",
         fontsize=14, fontweight="700", color=TEXT, va="top")
ax1 = fig.add_axes([cx + 0.055, cy + 0.040, cw - 0.085, ch - 0.098])
style_axes(ax1)
x = range(len(conc))
gross_bn = conc.gross_usd / 1e9
hedged_bn = gross_bn * conc.put_pct
ax1.bar(x, gross_bn, color="#2a3242", width=0.6, label="Disclosed gross exposure", zorder=2)
ax1.bar(x, hedged_bn, color=HEDGE, width=0.6, label="Of which put-linked", zorder=3)
for i, v in enumerate(gross_bn):
    ax1.text(i, v + 0.6, f"${v:,.1f}bn", ha="center", fontsize=10,
             color=TEXT, fontweight="600", zorder=4)
ax1.set_xticks(list(x)); ax1.set_xticklabels(conc.label)
ax1.set_ylim(0, 25)
ax1.set_yticks([0, 10, 20])
ax1.legend(frameon=False, fontsize=10, loc="upper left",
           labelcolor=MUTED, handlelength=1.4)
ax1.annotate("$8.46bn of puts", xy=(5, hedged_bn.iloc[5]), xytext=(3.6, 16.4),
             fontsize=10.5, color=HEDGE, fontweight="600", ha="center",
             arrowprops=dict(arrowstyle="->", color=HEDGE, lw=1.4))
ax1.annotate("0.03%", xy=(6, 0.4), xytext=(6, 7.6),
             fontsize=11.5, color=LOSS, fontweight="700", ha="center",
             arrowprops=dict(arrowstyle="->", color=LOSS, lw=1.6))

# ------------------------------------------- act 2: concentration reverses
cx, cy, cw, ch = card(L, 0.302, W, 0.212)
fig.text(cx + 0.020, cy + ch - 0.020, "02   Concentration more than doubles in one quarter",
         fontsize=14, fontweight="700", color=TEXT, va="top")
ax2 = fig.add_axes([cx + 0.055, cy + 0.040, cw - 0.085, ch - 0.098])
style_axes(ax2)
ax2.plot(x, conc.hhi, color=ACCENT, lw=2.8, marker="o", ms=7,
         markerfacecolor=BG, markeredgewidth=2.2, zorder=3)
ax2.fill_between(x, conc.hhi, color=ACCENT, alpha=0.11, zorder=2)
ax2.set_xticks(list(x)); ax2.set_xticklabels(conc.label)
ax2.set_ylim(0, 0.30)
ax2.set_yticks([0, 0.1, 0.2])
ax2.set_ylabel("Herfindahl index", fontsize=10.5, color=MUTED)
ax2.annotate("0.070\nmost diversified", xy=(5, conc.hhi.iloc[5]),
             xytext=(4.55, 0.022), fontsize=10, color=DIM, ha="center",
             linespacing=1.5)
ax2.annotate("0.176\ntop 5 = 77%", xy=(6, conc.hhi.iloc[6]),
             xytext=(5.35, 0.245), fontsize=10.5, color=ACCENT,
             fontweight="600", ha="center",
             arrowprops=dict(arrowstyle="->", color=ACCENT, lw=1.4))

# ------------------------------------------------------------ act 3: end
cx, cy, cw, ch = card(L, 0.062, W, 0.221)
fig.text(cx + 0.020, cy + ch - 0.020, "03   July: the long book falls 33.9%",
         fontsize=14, fontweight="700", color=TEXT, va="top")
ax3 = fig.add_axes([cx + 0.055, cy + 0.040, cw - 0.175, ch - 0.098])
style_axes(ax3)
ax3.grid(axis="y", color=GRID, lw=1)
norm = px / px.iloc[0] * 100
name = {"SNDK": "SanDisk", "MU": "Micron", "BE": "Bloom Energy",
        "NBIS": "Nebius", "CRWV": "CoreWeave", "CORZ": "Core Scientific"}
for t in norm.columns:
    is_corz = t == "CORZ"
    ax3.plot(norm.index, norm[t], lw=2.6 if is_corz else 1.4,
             color=LOSS if is_corz else "#3d4757",
             zorder=4 if is_corz else 2)
MIN_GAP = 11.0
placed = []
for val, t in sorted(((norm[t].iloc[-1], t) for t in norm.columns)):
    y = val if not placed else max(val, placed[-1][0] + MIN_GAP)
    placed.append((y, t))
for y, t in placed:
    is_corz = t == "CORZ"
    ax3.text(norm.index[-1] + pd.Timedelta(days=3), y, name[t], fontsize=10,
             va="center", color=LOSS if is_corz else DIM,
             fontweight="600" if is_corz else "normal")
ax3.axhline(100, color=EDGE, lw=1.2, zorder=1)
for _, r in blot[blot.block].iterrows():
    ax3.axvline(r.trade_date, color=LOSS, ls=":", lw=1.6, alpha=0.8, zorder=3)
ax3.annotate("Still selling by block trade on 3 Aug,\n12.2% below its mid-July prints",
             xy=(blot[blot.block].trade_date.iloc[0], 82),
             xytext=(pd.Timestamp("2026-07-05"), 128),
             fontsize=10, color=LOSS, fontweight="600", linespacing=1.55,
             arrowprops=dict(arrowstyle="->", color=LOSS, lw=1.4,
                             connectionstyle="arc3,rad=-0.18"))
ax3.set_ylabel("1 Jun = 100", fontsize=10.5, color=MUTED)
ax3.set_xlim(px.index[0], px.index[-1] + pd.Timedelta(days=2))
ax3.set_ylim(40, 145)
ax3.set_yticks([50, 75, 100, 125])
ax3.xaxis.set_major_locator(mdates.MonthLocator())
ax3.xaxis.set_major_formatter(mdates.DateFormatter("%b"))

# ------------------------------------------------------------------ footer
fig.text(L, 0.040,
         "SEC EDGAR 13F-HR (CIK 0002045724, 7 filings) · Schedule 13D/A Ex-99.2 · daily closes via yfinance · snapshot 22 Aug 2026",
         fontsize=9.5, color=DIM, va="top")
fig.text(L, 0.0225,
         "github.com/theshaswat/situational-awareness-unwind    Independent research. Not investment advice.",
         fontsize=9.5, color=MUTED, va="top")

out = cfg.CHARTS / "journey.png"
fig.savefig(out, dpi=100, facecolor=BG)
plt.close(fig)
print(f"wrote {out}")
