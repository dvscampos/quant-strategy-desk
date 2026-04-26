"""SQLite persistence layer for backtest state."""

from __future__ import annotations

import json
import sqlite3
from datetime import date
from pathlib import Path

from .models import (
    AgentScore,
    PortfolioState,
    Position,
    Trade,
    TradeAction,
    Verdict,
    VerdictCategory,
    VerdictResult,
)

DB_PATH = Path(__file__).parent / "backtest.db"


class BacktestDB:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path))
        self._init_tables()

    def _init_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                session_number INTEGER PRIMARY KEY,
                date TEXT,
                state_json TEXT
            );
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_number INTEGER,
                action TEXT,
                ticker TEXT,
                shares INTEGER,
                price REAL,
                date TEXT,
                theme TEXT
            );
            CREATE TABLE IF NOT EXISTS rotation_history (
                session_number INTEGER,
                role TEXT,
                agent TEXT,
                PRIMARY KEY (session_number, role)
            );
            CREATE TABLE IF NOT EXISTS verdicts (
                session_number INTEGER,
                agent TEXT,
                result TEXT,
                note TEXT,
                category TEXT,
                PRIMARY KEY (session_number, agent)
            );
            CREATE TABLE IF NOT EXISTS instruments (
                ticker TEXT PRIMARY KEY,
                name TEXT,
                isin TEXT,
                ter REAL,
                theme TEXT,
                exchange TEXT,
                currency TEXT DEFAULT 'EUR',
                added_session INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS session_meta (
                session_number INTEGER PRIMARY KEY,
                session_date TEXT,
                execution_date TEXT,
                regime TEXT,
                geopolitical_status TEXT,
                notes TEXT
            );
        """)
        self.conn.commit()

    def save_snapshot(self, state: PortfolioState):
        """Save a portfolio snapshot."""
        positions_data = {
            ticker: {
                "shares": pos.shares,
                "avg_entry": pos.avg_entry,
                "theme": pos.theme,
            }
            for ticker, pos in state.positions.items()
        }
        state_json = json.dumps({
            "positions": positions_data,
            "cash": state.cash,
            "total_contributions": state.total_contributions,
        })
        self.conn.execute(
            "INSERT OR REPLACE INTO portfolio_snapshots (session_number, date, state_json) VALUES (?, ?, ?)",
            (state.session_number, state.date.isoformat(), state_json),
        )
        self.conn.commit()

    def load_snapshot(self, session_number: int) -> PortfolioState | None:
        """Load a portfolio snapshot."""
        row = self.conn.execute(
            "SELECT date, state_json FROM portfolio_snapshots WHERE session_number = ?",
            (session_number,),
        ).fetchone()
        if not row:
            return None
        d = date.fromisoformat(row[0])
        data = json.loads(row[1])
        positions = {}
        for ticker, pdata in data["positions"].items():
            positions[ticker] = Position(
                ticker=ticker,
                shares=pdata["shares"],
                avg_entry=pdata["avg_entry"],
                theme=pdata["theme"],
            )
        return PortfolioState(
            date=d,
            session_number=session_number,
            positions=positions,
            cash=data["cash"],
            total_contributions=data["total_contributions"],
        )

    def load_latest_snapshot(self) -> PortfolioState | None:
        """Load the most recent snapshot."""
        row = self.conn.execute(
            "SELECT session_number FROM portfolio_snapshots ORDER BY session_number DESC LIMIT 1"
        ).fetchone()
        if not row:
            return None
        return self.load_snapshot(row[0])

    def save_trades(self, trades: list[Trade], session_number: int):
        for t in trades:
            self.conn.execute(
                "INSERT INTO trades (session_number, action, ticker, shares, price, date, theme) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (session_number, t.action.value, t.ticker, t.shares, t.price, t.date.isoformat(), t.theme),
            )
        self.conn.commit()

    def load_trades(self, session_number: int) -> list[Trade]:
        rows = self.conn.execute(
            "SELECT action, ticker, shares, price, date, theme FROM trades WHERE session_number = ? ORDER BY id",
            (session_number,),
        ).fetchall()
        return [
            Trade(
                action=TradeAction(r[0]),
                ticker=r[1],
                shares=r[2],
                price=r[3],
                date=date.fromisoformat(r[4]),
                theme=r[5] or "",
            )
            for r in rows
        ]

    def save_verdicts(self, verdicts: list[Verdict], session_number: int):
        for v in verdicts:
            cat = v.category.value if v.category else ""
            self.conn.execute(
                "INSERT OR REPLACE INTO verdicts (session_number, agent, result, note, category) VALUES (?, ?, ?, ?, ?)",
                (session_number, v.agent, v.result.value, v.note, cat),
            )
        self.conn.commit()

    def load_verdicts(self, session_number: int | None = None) -> list[Verdict]:
        if session_number is not None:
            rows = self.conn.execute(
                "SELECT session_number, agent, result, note, category FROM verdicts WHERE session_number = ?",
                (session_number,),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT session_number, agent, result, note, category FROM verdicts ORDER BY session_number"
            ).fetchall()
        return [
            Verdict(
                session_number=r[0],
                agent=r[1],
                result=VerdictResult(r[2]),
                note=r[3],
                category=VerdictCategory(r[4]) if r[4] else None,
            )
            for r in rows
        ]

    def save_rotation(self, team: dict[str, str], session_number: int):
        for role, agent in team.items():
            self.conn.execute(
                "INSERT OR REPLACE INTO rotation_history (session_number, role, agent) VALUES (?, ?, ?)",
                (session_number, role, agent),
            )
        self.conn.commit()

    def load_rotation_history(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT session_number, role, agent FROM rotation_history ORDER BY session_number"
        ).fetchall()
        sessions: dict[int, dict] = {}
        for sn, role, agent in rows:
            if sn not in sessions:
                sessions[sn] = {"session": sn}
            sessions[sn][role] = agent
        return list(sessions.values())

    def save_instrument(self, ticker: str, name: str, isin: str, ter: float,
                        theme: str, exchange: str, currency: str = "EUR",
                        added_session: int = 0):
        self.conn.execute(
            "INSERT OR REPLACE INTO instruments (ticker, name, isin, ter, theme, exchange, currency, added_session) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (ticker, name, isin, ter, theme, exchange, currency, added_session),
        )
        self.conn.commit()

    def load_instruments(self) -> dict[str, dict]:
        rows = self.conn.execute(
            "SELECT ticker, name, isin, ter, theme, exchange, currency FROM instruments"
        ).fetchall()
        return {
            r[0]: {"name": r[1], "isin": r[2], "ter": r[3], "theme": r[4], "exchange": r[5], "currency": r[6]}
            for r in rows
        }

    def get_instrument_themes(self) -> dict[str, str]:
        instruments = self.load_instruments()
        return {ticker: info["theme"] for ticker, info in instruments.items()}

    def save_session_meta(self, session_number: int, session_date: str,
                          execution_date: str, regime: str = "",
                          geopolitical_status: str = "", notes: str = ""):
        self.conn.execute(
            "INSERT OR REPLACE INTO session_meta (session_number, session_date, execution_date, regime, geopolitical_status, notes) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (session_number, session_date, execution_date, regime, geopolitical_status, notes),
        )
        self.conn.commit()

    def seed_instruments_from_yaml(self):
        """Load seed instruments from config YAML into DB (only if not already present)."""
        import yaml
        config_path = Path(__file__).parent / "config" / "instruments.yml"
        with open(config_path) as f:
            config = yaml.safe_load(f)

        for ticker, info in config.get("instruments", {}).items():
            existing = self.conn.execute(
                "SELECT ticker FROM instruments WHERE ticker = ?", (ticker,)
            ).fetchone()
            if not existing:
                self.save_instrument(
                    ticker=ticker,
                    name=info.get("name", ""),
                    isin=info.get("isin", ""),
                    ter=info.get("ter", 0.0),
                    theme=info.get("theme", ""),
                    exchange=info.get("exchange", ""),
                    currency=info.get("currency", "EUR"),
                )

    def close(self):
        self.conn.close()
