"""Builds reports/EXECUTIVE_SUMMARY.pdf and reports/RISK_MEMO.pdf.
Run from repo root: python3 scripts/build_reports.py
Not a notebook — this is a one-shot report-formatting utility, kept separate
from the analytical pipeline per this project's standards.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, KeepTogether, Image)
from reportlab.lib.enums import TA_LEFT

from src.utils import config as cfg

styles = getSampleStyleSheet()
styles.add(ParagraphStyle("H1", fontSize=16, leading=20, spaceAfter=10,
                           fontName="Helvetica-Bold", textColor=colors.HexColor("#1F4E78")))
styles.add(ParagraphStyle("H2", fontSize=12, leading=15, spaceBefore=12, spaceAfter=6,
                           fontName="Helvetica-Bold", textColor=colors.HexColor("#1F4E78")))
styles.add(ParagraphStyle("Body", fontSize=9.5, leading=13.5, spaceAfter=6,
                           fontName="Helvetica", alignment=TA_LEFT))
styles.add(ParagraphStyle("Small", fontSize=7.5, leading=10, textColor=colors.grey))
styles.add(ParagraphStyle("Recommendation", fontSize=10.5, leading=14, spaceAfter=8,
                           fontName="Helvetica-Bold", textColor=colors.HexColor("#B23B3B")))
styles.add(ParagraphStyle("CellHeader", fontSize=8.5, leading=10.5,
                           fontName="Helvetica-Bold", textColor=colors.white))
styles.add(ParagraphStyle("Cell", fontSize=8.5, leading=11, fontName="Helvetica"))


def wrapped_table(data, col_widths):
    """Table with every cell as a Paragraph so long text wraps inside its
    column instead of overflowing past the page margin."""
    body = [[Paragraph(str(c), styles["CellHeader"]) for c in data[0]]]
    for row in data[1:]:
        body.append([Paragraph(str(c), styles["Cell"]) for c in row])
    t = Table(body, colWidths=col_widths)
    t.setStyle(TABLE_STYLE)
    return t

TABLE_STYLE = TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F6FA")]),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ("LEFTPADDING", (0, 0), (-1, -1), 6),
])


def build_executive_summary():
    doc = SimpleDocTemplate(str(cfg.REPORTS / "EXECUTIVE_SUMMARY.pdf"), pagesize=LETTER,
                             topMargin=0.6 * inch, bottomMargin=0.6 * inch,
                             leftMargin=0.7 * inch, rightMargin=0.7 * inch)
    story = []
    story.append(Paragraph("Situational Awareness Unwind — Executive Summary", styles["H1"]))
    story.append(Paragraph(
        "Situational Awareness LP's 4x-leverage narrative is incomplete. Its own SEC filings "
        "show a fund that entered July 2026 with its put-linked exposure eliminated — 61.9% of "
        "gross to 0.03% in one quarter — while concentration in its top five positions rose to "
        "77.3%. This reconstruction, built entirely from SEC EDGAR primary filings and priced "
        "market data, decomposes the collapse and screens today's market for the same signature.",
        styles["Body"]))

    story.append(Paragraph("Headline Numbers", styles["H2"]))
    data = [
        ["Metric", "Value"],
        ["Disclosed 13F book, 30 Jun 2026", "$20.24bn gross / 26 entries ($20.17bn long, 23 positions)"],
        ["Top-2 concentration (SanDisk + Micron)", "55.5% of disclosed gross"],
        ["Put-linked exposure, Q1 2026 -> Q2 2026", "61.9% -> 0.03% of gross"],
        ["Herfindahl index, Q1 2026 -> Q2 2026", "0.070 -> 0.176"],
        ["Book-weighted days-to-liquidate @ 20% ADV", "1.55 days (book screened LIQUID)"],
        ["Least-liquid position (Core Scientific)", "9.25 days -- confirmed could not clear on schedule"],
        ["Documented forced block-trade discount", "12.2% below mid-July prints"],
        ["Actual priced long-book return, Jun-end -> Jul-end", "-33.9%"],
        ["  of which sector beta (SOX)", "-18.9%"],
        ["  of which concentration effect", "-5.6%"],
        ["Reported fund-level equity loss (unaudited)", "-67% (not force-reconciled -- see memo)"],
        ["Live screen: current filers breaching 2+ of 3 risk axes", "1 of 12 screened"],
    ]
    t = wrapped_table(data, [3.6 * inch, 3.0 * inch])
    story.append(KeepTogether([t]))

    story.append(Spacer(1, 10))
    story.append(Paragraph("The Central Finding", styles["H2"]))
    story.append(Paragraph(
        "Whether by active close-out or unrolled expiry -- 13F cannot distinguish the two -- "
        "Situational Awareness entered July with no disclosed downside protection on its public "
        "book, versus 62% of gross in puts three months earlier. Two positions (Micron, TSMC) show "
        "a put replaced by a larger long on the identical issuer between quarters. This is a "
        "bounded, filing-evidenced fact, stated independent of intent.",
        styles["Body"]))

    story.append(Paragraph("What the Attribution Shows", styles["H2"]))
    story.append(Paragraph(
        "The disclosed long book fell 33.9% from June-end to July-end, priced against real market "
        "data. Sector beta (SOX index, -18.9%) explains just over half; concentration versus an "
        "equal-weighted version of the same names explains a further -5.6%; the remainder is "
        "stock-specific. The fund's own reported -67% equity loss is a leveraged, net-of-shorts "
        "number this project deliberately does not force-reconcile to the long-book figure -- "
        "doing so would require assuming leverage and short-book P&L that cannot be independently "
        "verified from public filings.",
        styles["Body"]))

    story.append(KeepTogether([
        Paragraph("Validation, Including a Negative Result", styles["H2"]),
        Paragraph(
            "The liquidity model was tested against a documented outcome: it correctly flagged "
            "Core Scientific as the single least-liquid position in the book, and that position "
            "was confirmed by SEC filing to still be under forced sale five days after the main "
            "unwind. The concentration-scoring engine was also tested out-of-sample on two "
            "unrelated historical blow-ups (Melvin Capital, Tiger Global) against two large "
            "diversified controls (Berkshire Hathaway, Renaissance Technologies) -- and a naive, "
            "single-metric version of the engine FAILED to separate them cleanly. That negative "
            "result, reported rather than suppressed, is what led to a three-axis screen "
            "(concentration level, concentration trend, multi-name crowding) rather than a single "
            "static threshold.",
            styles["Body"]),
    ]))

    story.append(Paragraph("The Decision", styles["Recommendation"]))
    story.append(Paragraph(
        "One of twelve current 13F filers screened -- Symmetry Peak Management LLC -- breaches 2 "
        "of the 3 risk axes that preceded the Situational Awareness unwind, with its concentration "
        "index rising from 0.103 to 0.237 in a single quarter. This is risk geometry, not a "
        "prediction, and is not investment advice. See reports/RISK_MEMO.pdf for the full basis "
        "and recommended next step.",
        styles["Body"]))

    story.append(Spacer(1, 14))
    story.append(Paragraph(
        "Source: SEC EDGAR (13F-HR, 13D/A, Form D/A), CIK 0002045724 / 0002038540. Prices: "
        "yfinance, snapshot 22 Aug 2026. Full methodology, limitations, and reconciliation of "
        "conflicting press figures: see README.md and reports/RECONCILIATION.md. Prepared by "
        "Shaswat Sharma -- github.com/theshaswat.",
        styles["Small"]))

    doc.build(story)
    print(f"Wrote {cfg.REPORTS / 'EXECUTIVE_SUMMARY.pdf'}")


def build_risk_memo():
    # This memo is deliberately held to ONE page — it is the artifact a risk
    # officer reads standing up. Body leading is tightened slightly versus
    # the executive summary to keep it there as content grew.
    memo_body = ParagraphStyle("MemoBody", parent=styles["Body"],
                                fontSize=9.2, leading=12.4, spaceAfter=5)
    doc = SimpleDocTemplate(str(cfg.REPORTS / "RISK_MEMO.pdf"), pagesize=LETTER,
                             topMargin=0.45 * inch, bottomMargin=0.45 * inch,
                             leftMargin=0.7 * inch, rightMargin=0.7 * inch)
    story = []
    story.append(Paragraph("Risk Memo: Crowded-Trade Signature Screen", styles["H1"]))
    story.append(Paragraph(
        "To: Prime brokerage / multi-strategy risk desk &nbsp;&nbsp;|&nbsp;&nbsp; "
        "From: Shaswat Sharma &nbsp;&nbsp;|&nbsp;&nbsp; Re: Filers sharing the Situational "
        "Awareness pre-collapse signature",
        styles["Small"]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Recommendation", styles["Recommendation"]))
    story.append(Paragraph(
        "Flag Symmetry Peak Management LLC (CIK 0001389234) for a closer position-level liquidity "
        "and leverage review. Its 13F-disclosed concentration index rose from 0.103 to 0.237 in the "
        "most recent quarter -- a larger single-quarter jump than Situational Awareness's own "
        "pre-collapse move (0.070 to 0.176). It breaches the concentration LEVEL and TREND axes; it "
        "does NOT breach the multi-name crowding axis (it holds 1 of the 4 tracked names, not 2+). "
        "No other filer in the 12 screened breaches 2 of the 3 risk axes established below.",
        memo_body))

    story.append(Paragraph("Basis for the Screen", styles["H2"]))
    story.append(Paragraph(
        "A single static concentration threshold does not work. Tested out-of-sample against two "
        "historical blow-ups (Melvin Capital pre-GME, Tiger Global pre-2022) and two large "
        "diversified controls (Berkshire Hathaway, Renaissance Technologies), a naive Herfindahl-"
        "index cutoff misclassifies: Berkshire's own concentration (0.064) exceeds Melvin's "
        "pre-blowup figure (0.027), because Melvin's real risk sat in undisclosed swaps and short "
        "positions -- the same structural blind spot documented for Archegos Capital (also excluded "
        "from this project's back-test for the same reason: it filed no 13F at all). The screen "
        "below therefore requires a filer to breach at least 2 of 3 independent axes before "
        "flagging:",
        memo_body))
    axes = [
        ["Axis", "Threshold", "Rationale"],
        ["Concentration level", "Herfindahl index > 0.10",
         "Midpoint of Situational Awareness's own Q1->Q2 2026 run-up (0.070 -> 0.176)"],
        ["Concentration trend", "> +0.03 change, single quarter",
         "SA moved +0.106 in one quarter; a fast rise, not just a high level, is the signal"],
        ["Multi-name crowding", "Holds >= 2 of 4 tracked illiquid names",
         "Concentration in ANY one name is common; overlap across the SAME illiquid names is not"],
    ]
    t = wrapped_table(axes, [1.3 * inch, 1.5 * inch, 3.8 * inch])
    story.append(KeepTogether([t]))

    story.append(Spacer(1, 10))
    story.append(Paragraph("Screening Universe", styles["H2"]))
    story.append(Paragraph(
        "4 CUSIPs, chosen as the least-liquid or highest-conviction names in Situational "
        "Awareness's own final disclosed book (Core Scientific, Applied Digital, IREN, Nebius). "
        "12 filers, prioritised by how many of the 4 they co-hold, out of 51 distinct filers found "
        "via SEC EDGAR full-text search across all four CUSIPs. This is a scoped screen, not an "
        "exhaustive market sweep -- absence of a flag means not found within this stated scope, "
        "not the absence of risk in the broader market.",
        memo_body))

    story.append(Paragraph("Caveat -- what actually separates flagged from unflagged", styles["H2"]))
    story.append(Paragraph(
        "Gullane Capital, LLC shows extreme single-name concentration (Herfindahl index 0.875) but "
        "is not flagged, because it breaches only 1 of the 3 axes: its concentration is extreme yet "
        "essentially unchanged quarter-over-quarter (trend -0.003), so it fails the trend axis. "
        "Note that Symmetry Peak -- the filer that IS flagged -- also holds only 1 of the 4 tracked "
        "names, so multi-name crowding is not the separator between them; concentration TREND is. "
        "Neither filer breaches the crowding axis. Static single-name concentration is a real risk, "
        "but a structurally different one this screen was not designed to catch.",
        memo_body))

    story.append(Paragraph("Scope and Limits", styles["H2"]))
    story.append(Paragraph(
        "This is risk geometry, not a forecast. No claim here asserts that any named filer will "
        "experience losses or distress. Like Situational Awareness's own disclosed book, this "
        "screen sees only 13F-reportable long equity and listed options -- it cannot see a "
        "flagged filer's actual leverage, short book, or off-exchange exposure, which is precisely "
        "the blind spot that obscured the original case this project is built on. A signature match "
        "on the axes above is a prompt for a closer, non-public review -- not a substitute for one.",
        memo_body))

    story.append(Spacer(1, 14))
    story.append(Paragraph(
        "Full methodology, all 8 executed notebooks, and every source citation: "
        "see README.md. Prepared by Shaswat Sharma -- github.com/theshaswat, 22 Aug 2026.",
        styles["Small"]))

    doc.build(story)
    print(f"Wrote {cfg.REPORTS / 'RISK_MEMO.pdf'}")


if __name__ == "__main__":
    build_executive_summary()
    build_risk_memo()
