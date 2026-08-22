"""13F information-table parser.

Handles two real-world quirks discovered while building this project:
  1. XML namespace prefixes are inconsistent across quarters from the SAME
     filer (Q1-2026 uses `ns1:` prefixes after stripping the SEC boilerplate,
     other quarters do not). We strip all namespace prefixes before parsing.
  2. Values have been reported in whole dollars since the SEC's 2023
     amendment to Form 13F. Every parsed quarter is validated against the
     filing's own <tableValueTotal> in primary_doc.xml as an integrity check.
"""
import re
from dataclasses import dataclass


@dataclass
class Position:
    issuer: str
    cusip: str
    value_usd: int
    shares: int
    put_call: str  # "LONG", "PUT", or "CALL"


def _strip_ns(xml_text: str) -> str:
    return re.sub(r"<(/?)[A-Za-z0-9]+:", r"<\1", xml_text)


def _tag(block: str, tag: str) -> str:
    m = re.search(rf"<{tag}>(.*?)</{tag}>", block, re.S)
    return m.group(1).strip() if m else ""


def parse_info_table(xml_text: str) -> list[Position]:
    text = _strip_ns(xml_text)
    positions = []
    for block in re.findall(r"<infoTable>(.*?)</infoTable>", text, re.S):
        # As filed this is "Put" / "Call" (mixed case) or absent for a long
        # position — normalise to upper-case so every downstream comparison
        # ("PUT"/"CALL"/"LONG") is reliable regardless of filer formatting.
        put_call = (_tag(block, "putCall") or "LONG").upper()
        positions.append(Position(
            issuer=_tag(block, "nameOfIssuer"),
            cusip=_tag(block, "cusip"),
            value_usd=int(_tag(block, "value") or 0),
            shares=int(_tag(block, "sshPrnamt") or 0),
            put_call=put_call,
        ))
    return positions


def parse_primary_doc_total(xml_text: str) -> tuple[int, int]:
    """Returns (tableEntryTotal, tableValueTotal) as filed — the integrity
    anchor every parsed quarter must reconcile against."""
    text = _strip_ns(xml_text)
    entry = _tag(text, "tableEntryTotal")
    value = _tag(text, "tableValueTotal")
    return int(entry or 0), int(value or 0)


def find_info_table_filename(index_json: dict) -> str | None:
    """Info-table filenames are NOT standardised across filings (observed:
    'form13fInfoTable.xml', 'salp13fq1xml.xml'). Pick the first .xml file
    that isn't the primary_doc."""
    for item in index_json["directory"]["item"]:
        name = item["name"]
        if name.endswith(".xml") and "primary" not in name.lower():
            return name
    return None
