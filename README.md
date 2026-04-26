# Quant Strategy Desk

> A structured monthly investment process powered by 15 AI agent personas — macro strategist, risk officer, compliance, execution, and more. Run one command, get specific trade instructions tailored to your investor profile and the current macro regime.

**This is not automated trading.** You place every trade manually through your own broker. The framework helps you decide *what* to buy and *why*, with proper risk controls, stop-losses, and a documented audit trail.

> ⚠️ **Disclaimer**: Nothing in this repository constitutes financial, tax, or investment advice. It is a personal framework tool. Always consult a qualified advisor for your jurisdiction.

---

## What you get

- **Monthly War Room** — a single `/war-room` command runs a 5-agent Strike Team plus a 15-agent sign-off panel and outputs 3 ranked trade ideas with ISINs, sizing, entry, stop-loss, and plain-language rationale.
- **Personalised by one file** — `local/INVESTOR_PROFILE.md` (jurisdiction, broker, budget, constraints) is read by every agent. No code changes required to make it yours.
- **Risk framework built in** — VIX gates, cash floor, drawdown limits, ATR-based stops, concentration caps. See `docs/RISK_FRAMEWORK.md`.
- **Privacy by construction** — your portfolio, profile, and session files live under `local/`, which is gitignored. The framework files are shared; your data never leaves your machine.
- **Auditable** — every session is archived to `local/brainstorms/YYYY-MM.md` with full Strike Team output, sign-off table, and trade log.

---

## Requirements

- **Claude Code** (desktop app or CLI) with **Claude Pro or Max** — start every session in **Opus**.
- **A brokerage account** — IBKR, Degiro, Trading212, and XTB are all supported.
- **A free FRED API key** — sign up at [fred.stlouisfed.org](https://fred.stlouisfed.org) (2 minutes).
- **Python 3.11+** — only needed if you later run the backtesting engine; not required for the monthly War Room.

---

## Quick start

```bash
# 1. Clone the repo
git clone https://github.com/dvscampos/quant-strategy-desk.git my-investments
cd my-investments

# 2. Copy the env template and add your FRED key
cp .env.example .env
# then edit .env and set FRED_API_KEY=<your key>

# 3. Open the folder in Claude Code (desktop app or CLI)
claude
```

In your Claude Code session:

```
/model opus
```

On first run, Claude detects that `local/INVESTOR_PROFILE.md` is missing and walks you through an 11-question onboarding (country, currency, broker, contributions, risk tolerance, exclusions, etc.). It then runs:

```bash
python scripts/init_workspace.py
```

…to create your `local/` workspace from the templates. After that you're ready to run your first session:

```
/war-room
```

The session takes ~15–30 minutes of AI processing. The output is saved to `local/brainstorms/YYYY-MM.md`. Read the trade plan, place the trades through your broker (set GTC stop-losses immediately), then tell Claude what you executed — it will update `local/PORTFOLIO.md` for you so the next session sees your current holdings.

---

## Cadence

The framework is built around a **monthly review** by default, but your actual cadence is set during onboarding — fixed monthly contributions, irregular top-ups, or a quarterly review can all be accommodated.

A common pattern is to run the session once the month's key macro inputs (e.g. US CPI/PPI, central-bank decisions) have been released, on a weekend when markets are closed. Exact release dates fluctuate — check an economic calendar and pick a day that works for you.

Typical time commitment: ~2–3 hours per session.

---

## Repository layout

| Path | Purpose |
|---|---|
| `AGENTS.md` | Governance rules and the 15 agent personas |
| `agents/*.yml` | Individual agent persona configurations |
| `docs/STRATEGY_LOGIC.md` | Signal rules, asset-class targets, backtesting standards |
| `docs/RISK_FRAMEWORK.md` | Position sizing, stop-loss rules, cash floor, VIX protocol |
| `docs/COMPLIANCE.md` | Tax and regulatory guidance (jurisdiction-specific) |
| `backtesting/` | Event-driven backtest engine and tear sheets |
| `scripts/` | Setup and maintenance utilities (e.g. `init_workspace.py`) |
| `proposals/` | Architectural change proposals (audit trail) |
| `brainstorms/_TEMPLATE.md` | Master War Room template |
| `local/` | **Your personal workspace — gitignored** (profile, portfolio, sessions) |

---

## Documentation

- **[USER_INSTRUCTIONS.md](USER_INSTRUCTIONS.md)** — full user guide: setup, monthly process, stop-loss rules, FAQ
- **[SHARING.md](SHARING.md)** — how to share the framework safely without leaking personal data
- **[CLAUDE.md](CLAUDE.md)** — agent-facing init file (read order, governance, model selection)
- **[PROGRESS.md](PROGRESS.md)** — roadmap and state of play
- **[CHANGELOG.md](CHANGELOG.md)** — release notes

---

## What this system is *not*

- Not a robo-advisor — no broker connection, no auto-execution.
- Not financial advice — you own every trade you place.
- Not for day trading, options, or shorting — long-only, monthly cadence, ETF-focused.
- Not a guarantee of returns — markets are unpredictable; the framework is a discipline tool, not an oracle.

---

## Contributing

Framework improvements (agents, scripts, docs, templates — anything outside `local/`) are welcome via PR. Your portfolio and session history will never appear in the diff because `local/` is gitignored. See [SHARING.md](SHARING.md#how-to-contribute-framework-improvements-back) for the workflow and pre-push checklist.

---

## License

Personal use framework. See repository for any license file added at the root.
