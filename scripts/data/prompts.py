"""Prompt formatters for War Room Strike Team agents (A-C2, L14).

These are the SOLE constructors of macro_strategist and risk_guardian prompts.
Templates are module-level string constants — no logic scattered across callers.

DoD #22: functions named format_macro_prompt / format_risk_prompt (not build_).
L14: gate table injected here; orchestrator does not paraphrase between gate_eval
     and Strike Team prompt construction.
"""

from __future__ import annotations

_MACRO_TEMPLATE = """\
## Pre-Evaluated Deployment Gate Table

{gate_table}

---

You are the Macro Strategist for this War Room session. The gate table above was
produced by `gate_eval` from the locked snapshot at `local/snapshots/{session}.json`.

**You must cite gate tiers verbatim** when referencing macro conditions.
You may interpret the tiers (e.g. explain *why* VIX = AMBER matters today), but
you must NOT re-derive thresholds from memory or recall the latest data independently.
The table is the ground truth for this session.

Your task:
1. Classify the current macro regime (named regime: e.g. Stagflation, Risk-On, Late-Cycle).
2. Identify the 2–3 forces most likely to move the portfolio in the next 4–6 weeks.
3. State one named alternative regime (input for the Counter-Regime agent).

## Portfolio State

{portfolio_state}

## Prior Session Handoff (Orchestrator context — not for independent regime derivation)

{carry_forward}
"""

_RISK_TEMPLATE = """\
## Pre-Evaluated Deployment Gate Table

{gate_table}

---

You are the Risk Guardian for this War Room session. The gate table above was
produced by `gate_eval` from the locked snapshot at `local/snapshots/{session}.json`.

**You must cite gate tiers verbatim.** You may ESCALATE a tier (AMBER → RED) only
if you name a specific trigger from `docs/RISK_FRAMEWORK.md` that justifies it —
and record the escalation in the `Tier_Override` field in Phase 7 of the session file.
You may NOT de-escalate (GREEN → AMBER, AMBER → RED reversed) without a human edit
to the threshold config, a `gate_eval` re-run, and a one-line Phase 7 receipt.

Your task:
1. Assess the Market_Risk_Tier and Data_Confidence_Tier from the table above.
2. If Data_Confidence_Tier = RED: recommend halting the session pending a re-fetch
   (Data Failure Protocol).
3. Run a stress test: simulate a -10% equity correction against current holdings.
4. Flag any position breaching its risk limit under stress.

## Portfolio State

{portfolio_state}

## Current Holdings

{holdings}
"""


def format_macro_prompt(
    gate_table: str,
    session: str,
    portfolio_state: str,
    carry_forward: str = "(no carry-forward)",
) -> str:
    """Format the macro strategist prompt.

    Args:
        gate_table: Markdown string output of render_table(..., fmt='markdown').
        session: Session slug (YYYY-MM) used for snapshot path reference.
        portfolio_state: Plain-text portfolio NAV + positions summary.
        carry_forward: Prior session handoff text (Orchestrator-only context).
    """
    return _MACRO_TEMPLATE.format(
        gate_table=gate_table,
        session=session,
        portfolio_state=portfolio_state,
        carry_forward=carry_forward,
    )


def format_risk_prompt(
    gate_table: str,
    session: str,
    portfolio_state: str,
    holdings: str,
) -> str:
    """Format the risk guardian prompt.

    Args:
        gate_table: Markdown string output of render_table(..., fmt='markdown').
        session: Session slug (YYYY-MM) used for snapshot path reference.
        portfolio_state: Plain-text portfolio NAV + positions summary.
        holdings: Current holdings table (ticker, size, P&L).
    """
    return _RISK_TEMPLATE.format(
        gate_table=gate_table,
        session=session,
        portfolio_state=portfolio_state,
        holdings=holdings,
    )
