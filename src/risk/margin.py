"""Gross/net exposure identity and a maintenance-margin simulator.

Definitions (stated once, used everywhere):
  equity           = investor capital (NAV)
  gross_leverage   = (long + |short|) / equity
  net_leverage     = (long - |short|) / equity
  maintenance_pct  = minimum equity / gross the prime broker requires
"""
from dataclasses import dataclass


@dataclass
class Book:
    equity: float
    long_usd: float
    short_usd: float

    @property
    def gross(self) -> float:
        return self.long_usd + abs(self.short_usd)

    @property
    def net(self) -> float:
        return self.long_usd - abs(self.short_usd)

    @property
    def gross_leverage(self) -> float:
        return self.gross / self.equity if self.equity else float("inf")

    @property
    def net_leverage(self) -> float:
        return self.net / self.equity if self.equity else float("inf")

    def equity_after_move(self, long_return: float, short_return: float) -> float:
        """New equity after the long book moves `long_return` and the short
        book's underlying moves `short_return` (a positive short_return means
        the shorted names rose, i.e. a loss on the short leg)."""
        pnl = self.long_usd * long_return - self.short_usd * short_return
        return self.equity + pnl

    def implied_book_move_for_equity_loss(self, equity_loss_pct: float) -> float:
        """Solve: at this net leverage, what book-level move produces the
        given percentage loss of equity? (single-driver approximation —
        ignores the separate long/short split; use for sanity-checking only)"""
        if self.net_leverage == 0:
            return float("inf")
        return equity_loss_pct / self.net_leverage


def maintenance_call_threshold(equity: float, gross: float, maintenance_pct: float) -> float:
    """Equity level at which the prime broker issues a margin call."""
    return gross * maintenance_pct


def days_to_margin_call(book: Book, maintenance_pct: float, daily_drawdown_pct: float) -> float:
    """Simple iterative simulator: shrink equity by daily_drawdown_pct of the
    CURRENT gross exposure each day (gross held constant — no de-risking),
    stop when equity <= maintenance threshold."""
    equity = book.equity
    gross = book.gross
    threshold = maintenance_call_threshold(equity, gross, maintenance_pct)
    days = 0
    while equity > threshold and days < 60:
        equity -= gross * daily_drawdown_pct
        days += 1
    return days
