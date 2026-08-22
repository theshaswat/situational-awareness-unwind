"""Thin, rate-limited SEC EDGAR fetcher. Every request carries a real
User-Agent with a contact email, per SEC's access policy — requests without
one are blocked with a 403 'undeclared automated tool' page."""
import json
import time
import urllib.parse
import urllib.request

from src.utils.config import SEC_UA

_LAST_REQUEST = 0.0
_MIN_INTERVAL = 0.15  # keeps us under 10 req/sec


def _throttle():
    global _LAST_REQUEST
    elapsed = time.time() - _LAST_REQUEST
    if elapsed < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - elapsed)
    _LAST_REQUEST = time.time()


def get_text(url: str) -> str:
    _throttle()
    req = urllib.request.Request(url, headers={"User-Agent": SEC_UA})
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")


def get_json(url: str) -> dict:
    return json.loads(get_text(url))


def submissions(cik: str) -> dict:
    cik_padded = cik.zfill(10)
    return get_json(f"https://data.sec.gov/submissions/CIK{cik_padded}.json")


def filing_index(cik: str, accession: str) -> dict:
    acc_nodash = accession.replace("-", "")
    cik_int = str(int(cik))
    return get_json(f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_nodash}/index.json")


def filing_file(cik: str, accession: str, filename: str) -> str:
    acc_nodash = accession.replace("-", "")
    cik_int = str(int(cik))
    return get_text(f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_nodash}/{filename}")


def full_text_search(query: str, forms: str = "", dateb_range: tuple = None) -> dict:
    """SEC EDGAR full-text search (efts.sec.gov). Only indexes filings from 2001+."""
    url = f"https://efts.sec.gov/LATEST/search-index?q={urllib.parse.quote(query)}"
    if forms:
        url += f"&forms={forms}"
    if dateb_range:
        url += f"&dateRange=custom&startdt={dateb_range[0]}&enddt={dateb_range[1]}"
    return get_json(url)
