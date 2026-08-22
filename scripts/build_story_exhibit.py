"""Builds outputs/charts/story.png — a plain factual explainer of the fund:
who founded it, what it was for, who funded it, how big it got, what happened,
and who bought it. 1200x1500, sized for social.

Deliberately separate from journey.png, which is the analytical exhibit. This
one carries no findings of my own; it is a record of events.

Sourcing is marked on every fact. FILED means I read it out of an SEC filing
committed in this repository. REPORTED means it comes from press coverage and
I could not verify it independently from filings — including the widely-cited
$45bn peak, which two outlets state differently (see reports/RECONCILIATION.md).

Run from repo root:  python3 scripts/build_story_exhibit.py
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
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

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    "text.color": TEXT,
})

def d(text):
    """Escape dollar signs. A pair of unescaped $ is parsed as LaTeX mathtext
    and silently eats everything between them, which has bitten this repo
    twice — once turning "$255m to $20bn" into "255mto20bn"."""
    return text.replace("$", r"\$")


fig = plt.figure(figsize=(12, 15), dpi=100, facecolor=BG)


def card(x, y, w, h, radius=0.012, face=CARD, edge=EDGE):
    fig.add_artist(FancyBboxPatch(
        (x, y), w, h, transform=fig.transFigure,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        facecolor=face, edgecolor=edge, linewidth=1.2, zorder=0))
    return x, y, w, h


L, R = 0.045, 0.955
W = R - L

# ------------------------------------------------------------------ header
fig.text(L, 0.975, "S I T U A T I O N A L   A W A R E N E S S   L P",
         fontsize=11.5, color=ACCENT, fontweight="600", va="top")
fig.text(L, 0.952, "The whole story, in order", fontsize=27,
         fontweight="700", color=TEXT, va="top")
fig.text(L, 0.9185,
         "An AI hedge fund that launched in 2024, returned 439% in six months, "
         "and was liquidated in a week.",
         fontsize=12.5, color=MUTED, va="top")

# -------------------------------------------------------------- fact cards
facts = [
    ("WHO", "Leopold Aschenbrenner", "Former OpenAI researcher.\nAged 22 at launch.", ACCENT),
    ("WHAT FOR", "Long AI infrastructure", "Chips, data centres, power.\nShort the software AI disrupts.", BUILD),
    ("HOW IT ENDED", "Sold to Citadel", "Public book bought whole,\nat a discount, in one trade.", LOSS),
]
gap = 0.016
fw = (W - 2 * gap) / 3
fy, fh = 0.788, 0.112
for i, (kicker, head, body, col) in enumerate(facts):
    fx = L + i * (fw + gap)
    card(fx, fy, fw, fh)
    fig.text(fx + 0.018, fy + fh - 0.020, kicker, fontsize=9.5, color=col,
             fontweight="700", va="top")
    fig.text(fx + 0.018, fy + fh - 0.043, d(head), fontsize=14.5, color=TEXT,
             fontweight="700", va="top")
    fig.text(fx + 0.018, fy + fh - 0.070, d(body), fontsize=10.5, color=MUTED,
             va="top", linespacing=1.55)

# ----------------------------------------------------------- money raised
cx, cy, cw, ch = card(L, 0.660, W, 0.108)
fig.text(cx + 0.020, cy + ch - 0.020, "THE MONEY", fontsize=9.5,
         color=BUILD, fontweight="700", va="top")
money = [
    ("$1.76bn", "capital raised from investors", "FILED"),
    ("Nov 2024", "date of first sale", "FILED"),
    ("Multi-year", "investor lock-up", "REPORTED"),
    ("No cap", "on leverage or instrument", "REPORTED"),
]
for i, (big, lab, src) in enumerate(money):
    mx = cx + 0.022 + i * ((cw - 0.05) / 4)
    fig.text(mx, cy + ch - 0.048, d(big), fontsize=17, color=TEXT,
             fontweight="700", va="top")
    fig.text(mx, cy + ch - 0.072, lab, fontsize=10, color=MUTED, va="top")
    fig.text(mx, cy + ch - 0.090, src, fontsize=8, color=DIM,
             fontweight="700", va="top")
fig.text(cx + cw - 0.020, cy + ch - 0.020,
         "Backers reported to include Patrick and John Collison, Nat Friedman, and Jane Street",
         fontsize=9.5, color=DIM, va="top", ha="right")

# -------------------------------------------------------------- timeline
cx, cy, cw, ch = card(L, 0.150, W, 0.492)
fig.text(cx + 0.020, cy + ch - 0.022, "WHAT HAPPENED", fontsize=9.5,
         color=ACCENT, fontweight="700", va="top")

ax = fig.add_axes([cx + 0.020, cy + 0.018, cw - 0.040, ch - 0.058])
ax.set_zorder(3); ax.patch.set_alpha(0); ax.axis("off")
ax.set_xlim(0, 1); ax.set_ylim(0, 1)

events = [
    ("Jun 2024", "Publishes \"Situational Awareness\", a 165-page essay on AGI", BUILD, "REPORTED"),
    ("Jul 2024", "Launches the fund on the back of it", BUILD, "REPORTED"),
    ("Dec 2024", "First 13F: $255m across 6 positions", BUILD, "FILED"),
    ("2025", "Raises past $1bn. Book reaches $5.5bn by year-end", BUILD, "FILED"),
    ("Mar 2026", "Book at $13.7bn, with 62% of it in puts", BUILD, "FILED"),
    ("Jun 2026", "Peak. $20.2bn disclosed, up 439% in six months. Puts gone", ACCENT, "FILED"),
    ("24 Jul 2026", "Letter to investors calls the sell-off a buying opportunity", LOSS, "REPORTED"),
    ("29 Jul 2026", "Margin calls from three prime brokers at once", LOSS, "REPORTED"),
    ("30 Jul 2026", "Citadel buys the entire public book in a single trade", LOSS, "REPORTED"),
    ("3 Aug 2026", "The least liquid position is still being sold off", LOSS, "FILED"),
]
n = len(events)
top, bot = 0.965, 0.035
ys = [top - i * (top - bot) / (n - 1) for i in range(n)]
LINE_X = 0.118
ax.plot([LINE_X, LINE_X], [ys[-1], ys[0]], color=EDGE, lw=2, zorder=1)
for (date, what, col, src), y in zip(events, ys):
    ax.plot([LINE_X], [y], marker="o", ms=9.5, color=col,
            markeredgecolor=BG, markeredgewidth=2.5, zorder=3)
    ax.text(LINE_X - 0.022, y, date, fontsize=11, color=TEXT,
            fontweight="700", ha="right", va="center")
    ax.text(LINE_X + 0.024, y, d(what), fontsize=11.5, color=MUTED, va="center")
    ax.text(0.995, y, src, fontsize=8, color=DIM, fontweight="700",
            ha="right", va="center")

# ------------------------------------------------------------- the result
cx, cy, cw, ch = card(L, 0.062, W, 0.076)
fig.text(cx + 0.020, cy + ch - 0.019, "THE RESULT", fontsize=9.5,
         color=LOSS, fontweight="700", va="top")
res = [
    ("−67%", "in July alone", LOSS),
    ("+80%", "still up on the year", TEXT),
    ("~$5.5bn", "private book retained", MUTED),
    ("Citadel", "bought the rest", TEXT),
]
for i, (big, lab, col) in enumerate(res):
    rx = cx + 0.022 + i * ((cw - 0.05) / 4)
    fig.text(rx, cy + ch - 0.040, d(big), fontsize=17, color=col,
             fontweight="700", va="top")
    fig.text(rx, cy + ch - 0.062, lab, fontsize=10, color=MUTED, va="top")

# ------------------------------------------------------------------ footer
fig.text(L, 0.043,
         "FILED = read directly from an SEC filing (13F-HR, Schedule 13D/A, Form D) held in the repository below.   "
         "REPORTED = press coverage, not independently verified.",
         fontsize=9, color=DIM, va="top")
fig.text(L, 0.0265,
         d("The often-quoted $45bn peak is REPORTED and inconsistent between outlets, "
           "so it is not used here. $20.2bn is what the fund itself filed."),
         fontsize=9, color=DIM, va="top")
fig.text(L, 0.010,
         "github.com/theshaswat/situational-awareness-unwind    Independent research. Not investment advice.",
         fontsize=9.5, color=MUTED, va="top")

out = cfg.CHARTS / "story.png"
fig.savefig(out, dpi=100, facecolor=BG)
plt.close(fig)
print(f"wrote {out}")
