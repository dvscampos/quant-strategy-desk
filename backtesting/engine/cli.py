"""CLI entry point — orchestrates a backtest session.

Usage:
    # Prepare a session (fetch data, generate skeleton, print briefs)
    python -m backtesting.engine.cli prepare --session 7

    # Record trades after conversation
    python -m backtesting.engine.cli record-trades --session 7 --trades trades.yml

    # Record Phase 7 verdicts
    python -m backtesting.engine.cli record-verdicts --session 7 --verdicts verdicts.yml

    # Compute EOM marks and finalise
    python -m backtesting.engine.cli finalise --session 7

    # Replay historical sessions (backfill from existing data)
    python -m backtesting.engine.cli replay --session 1 --trades trades.yml --verdicts verdicts.yml

    # Show portfolio state
    python -m backtesting.engine.cli status

    # Show agent scores
    python -m backtesting.engine.cli scores

    # Add a new instrument
    python -m backtesting.engine.cli add-instrument --ticker XDWD.DE --name "..." --theme "Global Equity" --isin "..." --ter 0.12
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import yaml

from . import data, gates, portfolio, rotation, scoring, session
from .briefs import strike_team_brief, phase7_brief
from .db import BacktestDB
from .models import (
    PortfolioState,
    Trade,
    TradeAction,
    Verdict,
    VerdictCategory,
    VerdictResult,
)


ENGINE_DIR = Path(__file__).parent
SESSIONS_DIR = ENGINE_DIR.parent / "sessions"


def _load_portfolio_config() -> dict:
    with open(ENGINE_DIR / "config" / "portfolio.yml") as f:
        return yaml.safe_load(f)


def cmd_prepare(args):
    """Prepare a session: fetch data, check gates, generate skeleton."""
    db = BacktestDB()
    db.seed_instruments_from_yaml()
    config = _load_portfolio_config()

    session_number = args.session
    month = args.month  # Format: YYYY-MM
    year, mon = int(month.split("-")[0]), int(month.split("-")[1])

    # Compute dates
    session_date = data.third_saturday(year, mon)
    exec_date = data.execution_date(session_date)

    print(f"Session #{session_number}: {session_date} (exec: {exec_date})")

    # Load previous state or initialise
    prev = db.load_snapshot(session_number - 1)
    if prev:
        state = portfolio.add_contribution(prev, config["monthly_contribution"], session_date)
        print(f"Loaded session #{session_number - 1} state. Added €{config['monthly_contribution']} contribution.")
    else:
        if session_number == 1:
            state = PortfolioState(
                date=session_date,
                session_number=0,
                cash=config["initial_cash"],
                total_contributions=config["initial_cash"],
            )
            print(f"Initialised new portfolio with €{config['initial_cash']}.")
        else:
            print(f"Error: No snapshot for session #{session_number - 1}. Run previous sessions first.")
            return

    state.session_number = session_number
    state.date = session_date

    # Fetch prices
    tickers = list(state.positions.keys())
    instruments = db.load_instruments()
    all_tickers = list(set(tickers) | set(instruments.keys()))
    prices = data.get_execution_prices(all_tickers, exec_date) if all_tickers else {}

    # Fetch macro
    macro = data.fetch_macro(exec_date)
    print(f"\nMacro: STOXX {macro.stoxx}, VIX {macro.vix}, ECB {macro.ecb_rate}%, Brent ${macro.brent}, EUR/USD {macro.eurusd}")

    # Previous macro for delta
    prev_macro = None
    if session_number > 1:
        prev_meta = db.conn.execute(
            "SELECT execution_date FROM session_meta WHERE session_number = ?",
            (session_number - 1,)
        ).fetchone()
        if prev_meta:
            try:
                prev_macro = data.fetch_macro(date.fromisoformat(prev_meta[0]))
            except Exception:
                pass

    # Gate check — prompt for geopolitical status
    if args.geopolitical:
        geo_status = args.geopolitical
    else:
        geo_status = input("Geopolitical gate status [GREEN/AMBER/RED]: ").strip().upper() or "GREEN"

    gate_results = gates.check_gates(
        macro=macro,
        portfolio=state,
        prices=prices,
        geopolitical_status=geo_status,
        trigger_pct=config.get("trigger_default_pct", -0.08),
        cash_floor_pct=config.get("cash_floor_pct", 0.30),
    )

    print(f"\nGates: {gates.count_by_status(gate_results)}")
    print(gates.format_gates_table(gate_results))

    # Rotation candidates
    history = db.load_rotation_history()
    print("\nRotation candidates:")
    for role in ["macro", "signal", "architect", "challenger"]:
        candidates = rotation.valid_candidates(role, history)
        print(f"  {role}: {candidates}")

    # Generate session skeleton
    team = {}
    if args.team:
        # Parse team from --team "macro:AQR Factor Model,signal:Citadel Alpha,..."
        for pair in args.team.split(","):
            role, agent = pair.split(":", 1)
            team[role.strip()] = agent.strip()
    team.setdefault("risk", "Two Sigma Risk")

    regime = args.regime or "TBD"

    skeleton = session.generate_session_skeleton(
        session_number=session_number,
        session_date=session_date.isoformat(),
        execution_date=exec_date.isoformat(),
        regime=regime,
        portfolio=state,
        prices=prices,
        macro=macro,
        gates=gate_results,
        team=team,
        rotation_history=history,
        previous_macro=prev_macro,
        instrument_config=instruments,
    )

    # Write skeleton
    out_path = SESSIONS_DIR / f"{year}-{mon:02d}.md"
    out_path.write_text(skeleton)
    print(f"\nSkeleton written to {out_path}")

    # Save session meta
    db.save_session_meta(
        session_number=session_number,
        session_date=session_date.isoformat(),
        execution_date=exec_date.isoformat(),
        regime=regime,
        geopolitical_status=geo_status,
    )

    # Print Strike Team briefs
    instrument_themes = db.get_instrument_themes()
    if args.briefs:
        for role in ["macro", "signal", "architect", "challenger"]:
            if role in team:
                brief = strike_team_brief(
                    role=role,
                    agent_name=team[role],
                    portfolio=state,
                    prices=prices,
                    macro=macro,
                    gates=gate_results,
                    session_number=session_number,
                    session_date=session_date.isoformat(),
                    execution_date=exec_date.isoformat(),
                    instrument_config=instruments,
                )
                print(f"\n{'='*60}")
                print(f"BRIEF: {team[role]} ({role})")
                print(f"{'='*60}")
                print(brief)

    db.close()
    print(f"\nReady for Strike Team conversation.")


def cmd_record_trades(args):
    """Record trades from a YAML/JSON file."""
    db = BacktestDB()
    config = _load_portfolio_config()

    session_number = args.session

    # Load trades
    trades_path = Path(args.trades)
    with open(trades_path) as f:
        if trades_path.suffix in (".yml", ".yaml"):
            trades_data = yaml.safe_load(f)
        else:
            trades_data = json.load(f)

    # Get state
    prev = db.load_snapshot(session_number - 1)
    if not prev:
        if session_number == 1:
            prev = PortfolioState(
                date=date.today(), session_number=0,
                cash=config["initial_cash"],
                total_contributions=config["initial_cash"],
            )
        else:
            print(f"Error: No snapshot for session #{session_number - 1}")
            return

    meta = db.conn.execute(
        "SELECT execution_date FROM session_meta WHERE session_number = ?",
        (session_number,)
    ).fetchone()
    exec_date = date.fromisoformat(meta[0]) if meta else date.today()

    state = portfolio.add_contribution(prev, config["monthly_contribution"], exec_date)
    state.session_number = session_number

    instruments = db.load_instruments()
    instrument_themes = {t: i["theme"] for t, i in instruments.items()}
    tickers = list(set(state.positions.keys()) | set(instruments.keys()))
    prices = data.get_execution_prices(tickers, exec_date)

    # Parse trades
    trades = []
    for td in trades_data.get("trades", []):
        trades.append(Trade(
            action=TradeAction(td["action"]),
            ticker=td["ticker"],
            shares=td["shares"],
            price=prices.get(td["ticker"], td.get("price", 0)),
            date=exec_date,
            theme=instrument_themes.get(td["ticker"], td.get("theme", "")),
        ))

    # Execute
    try:
        new_state = portfolio.execute_trades(
            state, trades, prices, instrument_themes,
            cash_floor_pct=config.get("cash_floor_pct", 0.30),
            affordability_cap_pct=config.get("affordability_cap_pct", 0.25),
        )
    except (portfolio.CashFloorBreachError, portfolio.AffordabilityCapError) as e:
        print(f"REJECTED: {e}")
        return

    # Save
    db.save_trades(trades, session_number)
    db.save_snapshot(new_state)

    mtm = portfolio.mark_to_market(new_state, prices)
    print(f"Trades recorded. Post-trade NAV: €{mtm['nav']:.2f}, Cash: {mtm['cash_pct']:.1f}%")
    for t in trades:
        print(f"  {t.action.value} {t.shares}× {t.ticker} @ €{t.price:.3f} = €{t.cost:.2f}")

    db.close()


def cmd_record_verdicts(args):
    """Record Phase 7 verdicts."""
    db = BacktestDB()

    verdicts_path = Path(args.verdicts)
    with open(verdicts_path) as f:
        if verdicts_path.suffix in (".yml", ".yaml"):
            vdata = yaml.safe_load(f)
        else:
            vdata = json.load(f)

    verdicts = []
    for vd in vdata.get("verdicts", []):
        verdicts.append(Verdict(
            agent=vd["agent"],
            result=VerdictResult(vd["result"]),
            note=vd.get("note", ""),
            category=VerdictCategory(vd["category"]) if vd.get("category") else None,
            session_number=args.session,
        ))

    db.save_verdicts(verdicts, args.session)

    # Compute scores
    all_verdicts = db.load_verdicts()
    scores = scoring.compute_cumulative(all_verdicts)
    print(scoring.format_scores_table(scores, args.session))

    db.close()


def cmd_finalise(args):
    """Compute EOM marks and finalise a session."""
    db = BacktestDB()

    session_number = args.session
    state = db.load_snapshot(session_number)
    if not state:
        print(f"No snapshot for session #{session_number}. Record trades first.")
        return

    meta = db.conn.execute(
        "SELECT execution_date FROM session_meta WHERE session_number = ?",
        (session_number,)
    ).fetchone()
    exec_date = date.fromisoformat(meta[0])
    year, month = exec_date.year, exec_date.month

    # EOM prices
    tickers = list(state.positions.keys())
    eom_prices = data.get_eom_prices(tickers, year, month)

    mtm = portfolio.mark_to_market(state, eom_prices)

    print(f"\n=== End-of-Month Mark ({year}-{month:02d}) ===")
    print(f"NAV: €{mtm['nav']:.2f}")
    print(f"Cash: €{mtm['cash']:.2f} ({mtm['cash_pct']:.1f}%)")
    print(f"Invested: €{mtm['invested']:.2f} ({mtm['invested_pct']:.1f}%)")
    print(f"Gain: €{mtm['gain']:+.2f} ({mtm['gain_pct']:+.1f}% on €{mtm['contributions']:.0f} contributed)")
    print()
    for p in mtm["positions"]:
        print(f"  {p['ticker']}: {p['shares']}× €{p['price']:.3f} = €{p['value']:.2f} (P&L: €{p['pnl_eur']:+.2f}, {p['pnl_pct']:+.1f}%)")

    # Update the snapshot with EOM date
    state.date = data.last_trading_day_of_month(year, month)
    db.save_snapshot(state)

    db.close()


def cmd_status(args):
    """Show current portfolio state."""
    db = BacktestDB()
    state = db.load_latest_snapshot()
    if not state:
        print("No portfolio state. Run a session first.")
        return

    instruments = db.load_instruments()
    tickers = list(state.positions.keys())
    if not tickers:
        print(f"Session #{state.session_number}: NAV €{state.cash:.2f} (all cash)")
        return

    # Use latest available prices
    from datetime import date as d
    prices = data.get_execution_prices(tickers, d.today())
    mtm = portfolio.mark_to_market(state, prices)

    print(f"Session #{state.session_number} | Date: {state.date}")
    print(f"NAV: €{mtm['nav']:.2f} | Cash: €{mtm['cash']:.2f} ({mtm['cash_pct']:.1f}%) | Gain: €{mtm['gain']:+.2f} ({mtm['gain_pct']:+.1f}%)")
    print()
    for p in mtm["positions"]:
        print(f"  {p['ticker']}: {p['shares']}× @ €{p['avg_entry']:.3f} → €{p['price']:.3f} = €{p['value']:.2f} ({p['pnl_pct']:+.1f}%)")

    db.close()


def cmd_scores(args):
    """Show agent performance scores."""
    db = BacktestDB()
    all_verdicts = db.load_verdicts()
    if not all_verdicts:
        print("No verdicts recorded.")
        return

    max_session = max(v.session_number for v in all_verdicts)
    scores = scoring.compute_cumulative(all_verdicts)
    print(scoring.format_scores_table(scores, max_session))
    db.close()


def cmd_add_instrument(args):
    """Register a new instrument."""
    db = BacktestDB()
    db.save_instrument(
        ticker=args.ticker,
        name=args.name or "",
        isin=args.isin or "",
        ter=args.ter or 0.0,
        theme=args.theme or "",
        exchange=args.exchange or "",
    )
    print(f"Registered {args.ticker} ({args.theme})")
    db.close()


def main():
    parser = argparse.ArgumentParser(description="Backtesting engine CLI")
    sub = parser.add_subparsers(dest="command")

    # prepare
    p = sub.add_parser("prepare", help="Prepare a session")
    p.add_argument("--session", type=int, required=True)
    p.add_argument("--month", required=True, help="YYYY-MM")
    p.add_argument("--regime", default="")
    p.add_argument("--geopolitical", default="")
    p.add_argument("--team", default="", help="role:agent,role:agent,...")
    p.add_argument("--briefs", action="store_true", help="Print Strike Team briefs")

    # record-trades
    p = sub.add_parser("record-trades", help="Record executed trades")
    p.add_argument("--session", type=int, required=True)
    p.add_argument("--trades", required=True, help="YAML/JSON file with trades")

    # record-verdicts
    p = sub.add_parser("record-verdicts", help="Record Phase 7 verdicts")
    p.add_argument("--session", type=int, required=True)
    p.add_argument("--verdicts", required=True, help="YAML/JSON file with verdicts")

    # finalise
    p = sub.add_parser("finalise", help="Compute EOM marks")
    p.add_argument("--session", type=int, required=True)

    # status
    sub.add_parser("status", help="Show portfolio state")

    # scores
    sub.add_parser("scores", help="Show agent scores")

    # add-instrument
    p = sub.add_parser("add-instrument", help="Register a new instrument")
    p.add_argument("--ticker", required=True)
    p.add_argument("--name", default="")
    p.add_argument("--isin", default="")
    p.add_argument("--ter", type=float, default=0.0)
    p.add_argument("--theme", default="")
    p.add_argument("--exchange", default="")

    args = parser.parse_args()

    commands = {
        "prepare": cmd_prepare,
        "record-trades": cmd_record_trades,
        "record-verdicts": cmd_record_verdicts,
        "finalise": cmd_finalise,
        "status": cmd_status,
        "scores": cmd_scores,
        "add-instrument": cmd_add_instrument,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
