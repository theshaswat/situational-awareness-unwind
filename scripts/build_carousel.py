"""Builds a three-slide LinkedIn carousel at 1200x1500 each:

    outputs/charts/carousel_1_story.png    what happened, in order
    outputs/charts/carousel_2_numbers.png  the rise and the fall
    outputs/charts/carousel_3_filings.png  what the filings show

Shared design language across all three so they read as one set. Type is
sized for a phone, not a monitor.

Sourcing is marked throughout. FILED means read directly from an SEC filing
committed in this repository. REPORTED means press coverage not independently
verified — including the $45bn peak (inconsistent between outlets) and the
Citadel purchase (Millennium is reported to have bid too, and the one filed
blotter names no counterparty at all).

Run from repo root:  python3 scripts/build_carousel.py
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

BG = "#0d1117"
CARD = "#161b26"
EDGE = "#232b38"
TEXT = "#e6edf3"
MUTED = "#8b98a5"
DIM = "#5c6b7a"
ACCENT = "#b39ddb"
BUILD = "#4aa8ff"
LOSS = "#f2545b"
GRID = "#1e2530"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    "text.color": TEXT, "axes.labelcolor": MUTED,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.edgecolor": EDGE,
})

L, R = 0.055, 0.945
W = R - L

conc = pd.read_csv(cfg.TABLES / "concentration_series.csv")
conc["label"] = pd.to_datetime(conc.period).dt.strftime("%b\n%y")
px_close = pd.read_parquet(cfg.PRICES / "close_jun_aug_2026_20260822.parquet")


def d(t):
    """Escape $ — an unescaped pair is parsed as LaTeX mathtext."""
    return t.replace("$", r"\$")


def new_slide():
    return plt.figure(figsize=(12, 15), dpi=100, facecolor=BG)


def card(fig, x, y, w, h, radius=0.013, face=CARD, edge=EDGE):
    fig.add_artist(FancyBboxPatch(
        (x, y), w, h, transform=fig.transFigure,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        facecolor=face, edgecolor=edge, linewidth=1.3, zorder=0))
    return x, y, w, h


def kicker(fig, text, color=ACCENT):
    fig.text(L, 0.968, text, fontsize=13, color=color,
             fontweight="700", va="top")


def headline(fig, text, size=38, y=0.943):
    fig.text(L, y, d(text), fontsize=size, fontweight="700",
             color=TEXT, va="top", linespacing=1.18)


def slide_footer(fig, n, note=None):
    for i in range(3):
        fig.add_artist(plt.Circle((L + i * 0.022, 0.030), 0.0058,
                                  transform=fig.transFigure,
                                  facecolor=ACCENT if i == n - 1 else EDGE,
                                  edgecolor="none", zorder=5))
    if note:
        fig.text(L, 0.055, d(note), fontsize=10.5, color=DIM, va="top")
    fig.text(R, 0.0335, "github.com/theshaswat/situational-awareness-unwind",
             fontsize=11, color=MUTED, va="center", ha="right")


def style_axes(ax):
    ax.set_zorder(3); ax.patch.set_alpha(0)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color(EDGE)
    ax.tick_params(length=0, labelsize=11)
    ax.grid(axis="y", color=GRID, lw=1)
    ax.set_axisbelow(True)


# ═══════════════════════════════════════════════ SLIDE 1 — the story
fig = new_slide()
kicker(fig, "S I T U A T I O N A L   A W A R E N E S S   L P")
headline(fig, "A hedge fund went from\n$255m to liquidation\nin 20 months.")
fig.text(L, 0.812,
         "Founded 2024 by a former OpenAI researcher. Up 439% in six months.\n"
         "Gone in five weeks. Here is the order it happened in.",
         fontsize=15, color=MUTED, va="top", linespacing=1.6)

cx, cy, cw, ch = card(fig, L, 0.098, W, 0.665)
ax = fig.add_axes([cx + 0.030, cy + 0.022, cw - 0.060, ch - 0.044])
ax.set_zorder(3); ax.patch.set_alpha(0); ax.axis("off")
ax.set_xlim(0, 1); ax.set_ylim(0, 1)

events = [
    ("Jun 2024", "Publishes a 165-page essay on AGI", BUILD, "REPORTED"),
    ("Jul 2024", "Launches a fund on the back of it", BUILD, "REPORTED"),
    ("Nov 2024", "First investor money lands. $1.76bn raised in all", BUILD, "FILED"),
    ("Dec 2024", "First public filing: $255m, six positions", BUILD, "FILED"),
    ("Dec 2025", "Book reaches $5.5bn", BUILD, "FILED"),
    ("Mar 2026", "$13.7bn, with 62% of it in put options", BUILD, "FILED"),
    ("Jun 2026", "Peak: $20.2bn, up 439%. The puts are gone", ACCENT, "FILED"),
    ("24 Jul", "Tells investors the sell-off is a buying opportunity", LOSS, "REPORTED"),
    ("29 Jul", "Three prime brokers call for margin at once", LOSS, "REPORTED"),
    ("30 Jul", "The public book is sold in one block trade", LOSS, "REPORTED"),
    ("3 Aug", "The least liquid position is still being sold", LOSS, "FILED"),
]
n = len(events)
top, bot = 0.965, 0.030
ys = [top - i * (top - bot) / (n - 1) for i in range(n)]
LX = 0.150
ax.plot([LX, LX], [ys[-1], ys[0]], color=EDGE, lw=2.4, zorder=1)
for (date, what, col, src), y in zip(events, ys):
    ax.plot([LX], [y], marker="o", ms=11, color=col,
            markeredgecolor=BG, markeredgewidth=3, zorder=3)
    ax.text(LX - 0.028, y, date, fontsize=13, color=TEXT,
            fontweight="700", ha="right", va="center")
    ax.text(LX + 0.030, y, d(what), fontsize=13.5, color=MUTED, va="center")
    ax.text(1.0, y, src, fontsize=8.5, color=DIM, fontweight="700",
            ha="right", va="center")

slide_footer(fig, 1, "FILED = read from an SEC filing.  REPORTED = press coverage, not independently verified.")
fig.savefig(cfg.CHARTS / "carousel_1_story.png", dpi=100, facecolor=BG)
plt.close(fig)

# ═══════════════════════════════════════════════ SLIDE 2 — the numbers
fig = new_slide()
kicker(fig, "T H E   R I S E   A N D   T H E   F A L L", BUILD)
headline(fig, "It grew 79x.\nThen July happened.")
fig.text(L, 0.845,
         "Both charts are built from the fund's own filings and daily closes.",
         fontsize=15, color=MUTED, va="top")

kpis = [("79x", "book growth", ACCENT), ("+439%", "first half of 2026", BUILD),
        ("−67%", "July alone", LOSS), ("5 weeks", "peak to liquidation", TEXT)]
gap = 0.016
kw = (W - 3 * gap) / 4
for i, (big, lab, col) in enumerate(kpis):
    kx = L + i * (kw + gap)
    card(fig, kx, 0.718, kw, 0.088)
    fig.text(kx + 0.020, 0.718 + 0.088 - 0.020, d(big), fontsize=25,
             fontweight="700", color=col, va="top")
    fig.text(kx + 0.020, 0.718 + 0.088 - 0.060, lab, fontsize=12,
             color=MUTED, va="top")

cx, cy, cw, ch = card(fig, L, 0.408, W, 0.283)
fig.text(cx + 0.024, cy + ch - 0.024, "Disclosed book, by quarter",
         fontsize=16, fontweight="700", color=TEXT, va="top")
fig.text(cx + 0.024, cy + ch - 0.050,
         "Blue is the share held in put options — protection that came and went, then stopped",
         fontsize=11.5, color=DIM, va="top")
ax1 = fig.add_axes([cx + 0.060, cy + 0.088, cw - 0.090, ch - 0.155])
style_axes(ax1)
x = range(len(conc))
gross = conc.gross_usd / 1e9
ax1.bar(x, gross, color="#2a3242", width=0.62, zorder=2)
ax1.bar(x, gross * conc.put_pct, color=BUILD, width=0.62, zorder=3)
for i, v in enumerate(gross):
    ax1.text(i, v + 0.7, f"${v:,.1f}bn", ha="center", fontsize=11,
             color=TEXT, fontweight="600", zorder=4)
ax1.set_ylim(0, 25); ax1.set_yticks([]); ax1.set_xticklabels([])
ax1.set_xticks(list(x))
axs = fig.add_axes([cx + 0.060, cy + 0.040, cw - 0.090, 0.034])
axs.set_zorder(3); axs.patch.set_alpha(0)
axs.bar(x, conc.put_pct * 100, color=BUILD, width=0.62, zorder=3)
axs.set_ylim(0, 100); axs.set_xlim(-0.6, 6.6); axs.set_yticks([])
axs.set_xticks(list(x)); axs.set_xticklabels(conc.label, fontsize=11)
axs.tick_params(length=0)
for sp in ["top", "right", "left"]:
    axs.spines[sp].set_visible(False)
axs.spines["bottom"].set_color(EDGE)
for i, v in enumerate(conc.put_pct * 100):
    inside = v >= 26
    axs.text(i, v / 2 if inside else v + 17, f"{v:.0f}%" if v >= 1 else "0%",
             ha="center", fontsize=10.5, color=BG if inside else (BUILD if v >= 1 else DIM),
             fontweight="700", va="center", zorder=4)

cx, cy, cw, ch = card(fig, L, 0.098, W, 0.283)
fig.text(cx + 0.024, cy + ch - 0.024, "July, indexed to 1 June",
         fontsize=16, fontweight="700", color=TEXT, va="top")
fig.text(cx + 0.024, cy + ch - 0.050,
         "Every major holding fell together. Core Scientific, in red, is the one that could not clear",
         fontsize=11.5, color=DIM, va="top")
ax3 = fig.add_axes([cx + 0.060, cy + 0.048, cw - 0.185, ch - 0.115])
style_axes(ax3)
norm = px_close / px_close.iloc[0] * 100
nm = {"SNDK": "SanDisk", "MU": "Micron", "BE": "Bloom Energy",
      "NBIS": "Nebius", "CRWV": "CoreWeave", "CORZ": "Core Scientific"}
for t in norm.columns:
    corz = t == "CORZ"
    ax3.plot(norm.index, norm[t], lw=3 if corz else 1.6,
             color=LOSS if corz else "#5c6b7a", zorder=4 if corz else 2)
placed = []
for val, t in sorted(((norm[t].iloc[-1], t) for t in norm.columns)):
    y = val if not placed else max(val, placed[-1][0] + 11)
    placed.append((y, t))
for y, t in placed:
    corz = t == "CORZ"
    ax3.text(norm.index[-1] + pd.Timedelta(days=3), y, nm[t], fontsize=11,
             va="center", color=LOSS if corz else DIM,
             fontweight="700" if corz else "normal")
ax3.axhline(100, color=EDGE, lw=1.2, zorder=1)
ax3.set_ylim(40, 145); ax3.set_yticks([50, 100])
ax3.set_xlim(px_close.index[0], px_close.index[-1] + pd.Timedelta(days=2))
ax3.xaxis.set_major_locator(mdates.MonthLocator())
ax3.xaxis.set_major_formatter(mdates.DateFormatter("%b"))

slide_footer(fig, 2, "Sources: SEC Form 13F-HR, seven filings. Daily closes via yfinance.")
fig.savefig(cfg.CHARTS / "carousel_2_numbers.png", dpi=100, facecolor=BG)
plt.close(fig)

# ═══════════════════════════════════════════════ SLIDE 3 — the filings
fig = new_slide()
kicker(fig, "W H A T   T H E   F I L I N G S   S H O W", LOSS)
headline(fig, "Three things the\ncoverage got wrong.")
fig.text(L, 0.845,
         "I rebuilt the book from primary SEC filings. The record differs from the story.",
         fontsize=15, color=MUTED, va="top")

findings = [
    ("01", "It wasn't only leverage",
     "Every account blames 4x leverage. The filings also\n"
     "show put cover falling to almost nothing in the\n"
     "quarter before the collapse. Micron and TSMC each\n"
     "flipped from a put to a larger long on the same stock.",
     "62%", "to 0.03%", BUILD),
    ("02", "A liquid-looking book that died in a day",
     "On the standard measure the whole book needed\n"
     "1.55 days to sell. It flagged one name. That name is\n"
     "the one a filing shows still being sold by block trade\n"
     "five days later, 12.2% below its mid-July price.",
     "9.25", "days, Core Scientific", ACCENT),
    ("03", "\"Citadel bought it\" is press, not filing",
     "Citadel is reported as the buyer and Millennium is\n"
     "reported to have bid. But the one blotter actually\n"
     "filed names nobody: it records block trades, plural,\n"
     "with \"unaffiliated third parties\", dated 3 August.",
     "0", "counterparties named", LOSS),
]
fy = 0.638
for num, head, body, stat, statlab, col in findings:
    cx, cy, cw, ch = card(fig, L, fy, W, 0.152)
    fig.text(cx + 0.026, cy + ch - 0.026, num, fontsize=15, color=col,
             fontweight="700", va="top")
    fig.text(cx + 0.070, cy + ch - 0.026, d(head), fontsize=18.5,
             fontweight="700", color=TEXT, va="top")
    fig.text(cx + 0.070, cy + ch - 0.068, d(body), fontsize=12.5,
             color=MUTED, va="top", linespacing=1.75)
    fig.text(cx + cw - 0.032, cy + ch / 2 + 0.016, d(stat), fontsize=34,
             color=col, fontweight="700", ha="right", va="center")
    fig.text(cx + cw - 0.032, cy + ch / 2 - 0.026, statlab, fontsize=11,
             color=DIM, ha="right", va="center")
    fy -= 0.170

fig.text(L, 0.232,
         "Every figure above is reproducible from filings committed in the repository.",
         fontsize=13.5, color=TEXT, va="top", fontweight="600")
fig.text(L, 0.208,
         "Seven 13F-HR filings, a Schedule 13D/A trade blotter, a Form D, and eight executed notebooks.",
         fontsize=12, color=MUTED, va="top")

slide_footer(fig, 3, "Independent research. Not investment advice.")
fig.savefig(cfg.CHARTS / "carousel_3_filings.png", dpi=100, facecolor=BG)
plt.close(fig)

print("wrote carousel_1_story.png, carousel_2_numbers.png, carousel_3_filings.png")
