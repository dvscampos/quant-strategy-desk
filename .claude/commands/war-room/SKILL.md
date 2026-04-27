---
name: war-room
description: Run the monthly War Room brainstorm session. Includes data preparation, Strike Team brainstorm, Phase 7 sign-off, and protocol audit. Use when the user requests a monthly brainstorm, War Room session, or says "/war-room".
allowed-tools: Bash(python3:*), Read, Write, Edit, Glob, Grep, Agent
---

# War Room — Monthly Brainstorm Session

Run all three phases sequentially. Do not skip any phase.

## Pre-Flight: First-Run Detection

> **Run this BEFORE Phase 0.** If the workspace has never been initialised, a War Room session cannot proceed — Phase 0 checkpoint recovery and Pre-Session Preparation both assume `local/` artefacts exist. Without this guard, the skill silently stalls at Step A (Portfolio Valuation) because there is no `local/PORTFOLIO.md` or `local/INVESTOR_PROFILE.md` to read.

```python
import pathlib
profile = pathlib.Path("local/INVESTOR_PROFILE.md")
# st_size > 0 catches partial-init failures that left a 0-byte file behind.
if not profile.exists() or profile.stat().st_size == 0:
    print("FIRST_RUN_DETECTED")
else:
    print("PROFILE_OK")
```

If the check prints `FIRST_RUN_DETECTED`:

1. **Stop the skill immediately. Do NOT enter Phase 0.**
2. Tell the user verbatim: *"Your investor profile hasn't been set up yet — `/war-room` can't run without it. Onboarding takes about 2 minutes (11 questions + a one-line setup script). Want me to run it now?"*
3. If the user confirms, follow the **First-Run Detection** flow in `CLAUDE.md` (the 11-question onboarding, then `scripts/init_workspace.py`, then hydration of `local/INVESTOR_PROFILE.md`, `docs/COMPLIANCE.md`, and `brainstorms/_TEMPLATE.md`). After hydration completes, ask the user whether to proceed with `/war-room` in a fresh session or continue now.
4. If the user declines, exit the skill cleanly. Do not write any files.

**User confirmation is required.** Do NOT auto-trigger onboarding — `scripts/init_workspace.py` writes to `local/`, modifies `docs/COMPLIANCE.md`, and edits `brainstorms/_TEMPLATE.md`. The user must explicitly opt in.

If the check prints `PROFILE_OK`, proceed to Phase 0.

---

## Phase 0: Checkpoint Recovery

Before starting any work, check for a session checkpoint from a previous (interrupted) run:

```python
import json, pathlib, datetime
today = datetime.date.today()
slug = today.strftime("%Y-%m")
# also check backtest path
for cp_path in [
    pathlib.Path(f"local/brainstorms/.checkpoint-{slug}.json"),
    pathlib.Path(f"backtesting/sessions/.checkpoint-{slug}.json"),
]:
    if cp_path.exists():
        cp = json.loads(cp_path.read_text())
        print(f"CHECKPOINT FOUND: {cp_path}")
        print(f"  Completed phases: {cp.get('completed_phases', [])}")
        print(f"  Session: {cp.get('session')}")
        print(f"  Saved at: {cp.get('saved_at')}")
        break
else:
    print("No checkpoint found — starting fresh.")
```

If a checkpoint exists:
- Tell the user: *"I found a checkpoint from a previous session run (saved at [time]). Phases completed: [list]. Shall I resume from where we left off, or start fresh?"*
- If resuming: load `prices`, `gates`, `nav`, `strike_team`, and `phase7_verdicts` from the checkpoint. Skip any phase listed in `completed_phases`.
- If starting fresh: delete the checkpoint file and proceed normally.

**Checkpoint write — after Phase 1 complete:**
```python
import json, pathlib, datetime
cp = {
    "session": "YYYY-MM",            # replace with actual session slug
    "session_type": "live",          # or "backtest"
    "saved_at": datetime.datetime.now().isoformat(),
    "completed_phases": ["prep", "phase_1"],
    # Valid completed_phases values (in order):
    # "prep", "phase_1", "phase_2", "phase_3", "phase_4", "phase_5",
    # "phase_6", "phase_7", "phase_8", "phase_9"
    "nav_eur": 0,                    # replace with actual NAV
    "prices": {},                    # dict of ticker → price (macro assets only; candidate tickers fetched in phase_2_5)
    "gates": {},                     # dict of gate → GREEN/AMBER/RED
    "strike_team": [],               # list of agent names with framework field, e.g. [{"name": "Bridgewater", "framework": "macro-narrative"}]
    # NOTE: carry_forward_brief is Orchestrator-only context — do NOT save here or reload into Strike Team prompts
}
cp_path = pathlib.Path("local/brainstorms/.checkpoint-YYYY-MM.json")  # adjust for backtest path
cp_path.write_text(json.dumps(cp, indent=2))
```

**Checkpoint write — after Phase 3 (Counter-Regime) complete:**
Load existing checkpoint, add `"phase_3"` to `completed_phases`, and add:
```json
{
  "counter_regime": {
    "alternative_regime": "...",
    "confidence": "HIGH / MEDIUM / LOW",
    "invalidators": "..."
  }
}
```

**Checkpoint write — after Phase 5 (Instrument Verification) complete:**
Load existing checkpoint, add `"phase_5"` to `completed_phases`, and add:
```json
{
  "verified_tickers": {},
  "failed_tickers": {}
}
```

**Checkpoint write — after Phase 9 (Full Desk Sign-Off) complete:**
Load the existing checkpoint, add `"phase_7"` to `completed_phases`, and add:
```json
{
  "phase7_verdicts": [{"agent": "...", "verdict": "APPROVE/FLAG/BLOCK", "note": "..."}],
  "trade_plan": [{"ticker": "...", "action": "BUY", "notional_eur": 0}]
}
```

**Checkpoint delete — after session file written and protocol audit complete:**
```python
cp_path.unlink(missing_ok=True)
```

---

## Pre-Session Preparation (Steps A–F, automated)

> **Principle.** Preparation is "state of the world" only — existing holdings, macro gates, portfolio state. It MUST NOT pre-fetch data for candidate instruments. Candidate instrument verification happens in Phase 5 (post-Signal-Generator) so that the Signal Generator's universe is not silently narrowed by Yahoo Finance's coverage quality. **Data availability does not gate thesis formation.**

### A0. IBKR Reconciliation (live sessions only)

Before valuation, sync any fills and commission reports since the last session:

```bash
python3 scripts/reconcile_ibkr.py --since <last_session_date>
```

- Read `local/PORTFOLIO.md` for the last session's execution date to determine `--since`.
- If TWS is not running or the connection is refused, skip and note "IBKR offline — reconciliation skipped" in the pre-session log. Do not block the session.
- If new fills are found, re-read `local/PORTFOLIO.md` before proceeding to Step A.
- If only commission updates are found (positions already OPEN), update the Trade History commission column and note the change.

### A. Portfolio Valuation
Pull current/historical prices via yfinance for all **currently held positions only**. Calculate:
- Current NAV (portfolio mark-to-market + cash + new contribution)
- Position-level P&L (unrealised gains/losses)
- Month low prices for each position (stop-loss tracking)

### B. Deployment Gate Check (gate_eval powered)

Evaluate all 8 deployment gates using the locked snapshot. Do NOT hand-derive
tiers: no training-data guesses, no cached prints, no threshold re-computation.
The snapshot is the authoritative data source; gate_eval is the authoritative evaluator.

**Step B.1 — Resolve snapshot**
```python
import pathlib
session = "YYYY-MM"  # replace with actual session slug
snapshot_path = pathlib.Path(f"local/snapshots/{session}.json")
if not snapshot_path.exists():
    print(f"Snapshot missing: {snapshot_path}")
    print("Run: python -m scripts.data fetch --session {session}")
    # If fetch fails after all retries → Data Failure Protocol (docs/RISK_FRAMEWORK.md §DDP)
```

**Step B.2 — Run gate_eval and capture output**
```bash
python -m scripts.data gate_eval --session YYYY-MM --format markdown
```
Capture stdout into the pre-session live log (Step F) BEFORE launching any Strike Team
Task() call. This is the tamper-resistant T=0 record.

**Step B.3 — Write pre-session live log checkpoint**
```python
import json, pathlib, hashlib
gate_output = "<stdout from step B.2>"
cp_path = pathlib.Path(f"local/brainstorms/.checkpoint-{session}.json")
cp = json.loads(cp_path.read_text()) if cp_path.exists() else {}
cp["gate_table_sha256"] = hashlib.sha256(gate_output.encode()).hexdigest()
cp_path.write_text(json.dumps(cp, indent=2))
```

**Step B.4 — User-facing checkpoint**
> "Pre-session gate table captured. Market_Risk_Tier = [X], Data_Confidence_Tier = [Y].
> Proceeding to Strike Team? (confirm to continue)"

**Do NOT proceed past this step until the user confirms.**
If Data_Confidence_Tier = RED: recommend halting and re-fetching before Strike Team launches.

**Step B.5 — Paste gate table into Phase 2 of session file verbatim**
The orchestrator pastes the markdown table output exactly as printed by gate_eval.
The Macro Strategist may *interpret* tiers but must cite the tier label verbatim.

**Verification (DoD #7):**
After session: run `pytest tests/test_skill_invariants.py` — it greps watched files for
forbidden recall patterns and must exit 0.

### C. Price Affordability Filter
Calculate: **max affordable share price = 25% of current NAV**
Include this in the Signal Generator's prompt to prevent suggesting unaffordable instruments.

> **Do NOT** pre-fetch prices for specific candidate tickers here, even if they were carried forward from the previous session's trade plan. If the previous session flagged a ticker (e.g. "DFNS.PA returned no data"), that flag is stale context, not a verdict — treat it as open for re-verification in Phase 5 below.

### D. Rotation Check
Read the appropriate rotation log (see **Path Convention** below). Identify:
- Agents who MUST rotate out (hit 2-session consecutive limit)
- Agents who have NEVER served on Strike Team (prioritise for Challenger slot)
- Proposed Strike Team with rationale

**Framework diversity rule**: The Strike Team must include at least 2 distinct `analytical_framework` values from the agent YAMLs (macro-narrative / quantitative / fundamental / behavioural / flow-based). If the proposed team is all-quantitative, swap one for a macro-narrative or fundamental agent. Record the framework breakdown in the Rotation Check table.

### E. Carry-Forward Context (Orchestrator only)
Read the previous session's "Handoff to Next Session" section. **This context is for the Orchestrator's synthesis stage only.** Do NOT inject it into individual Strike Team sub-agent prompts — the Strike Team must form independent views from market data and portfolio state, not inherit last session's regime call, signals, or framing.

The one exception: explicit outstanding user-action items (e.g. "confirm IGLN Cat G/B with contabilista") that concern the Compliance agent may be surfaced to that specific agent only.

### F. Pre-Session Live Log (tamper-resistant)
Before the Strike Team launches, write a short timestamped file capturing the "view at T=0" — the raw portfolio state, prices, gates, and each sub-agent's first-draft output *before* orchestrator synthesis. This creates an auditable record separate from the retrospective session file.

Path: `local/brainstorms/YYYY-MM.pre-session.md` (live) or `backtesting/sessions/YYYY-MM.pre-session.md` (backtest).

Structure:
```markdown
# Pre-Session Live Log — YYYY-MM
Timestamp (UTC): ...

## Portfolio State
[holdings + NAV + cash, as pulled by Phase 1a]

## Gate Readings
[raw gate data from Phase 1b, no colour coding yet]

## Strike Team Raw Drafts (before Orchestrator synthesis)
### Macro Agent — first-draft regime call
[verbatim]
### Counter-Regime Agent — first-draft alternative call
[verbatim]
### Signal Generator — first-draft signals
[verbatim]
### Strategy Architect — first-draft allocation
[verbatim]
### Risk Guardian — first-draft stress result
[verbatim]
### Challenger — first-draft challenge
[verbatim]
```

This file is append-only during the session and must NOT be edited retrospectively. It is the ground truth for the "Regime Accuracy Retrospective" in next month's session.

Present all Phase 1 results to the user before proceeding.

---

## Phase 5: Instrument Verification (post-Signal-Generator)

> **Owner**: Strategy Architect sub-agent (or Orchestrator if Architect is absent).
>
> **Runs AFTER** the Signal Generator has proposed instruments, never before.

For each candidate ticker proposed by the Signal Generator:

### Data Failure Protocol (MANDATORY)
If the initial yfinance call fails, you MUST execute this escalation sequence before declaring the instrument structurally unavailable:

1. **Retry** after 10 seconds (yfinance rate-limits throw 404s that resolve on retry).
2. **Alternative ticker format** — try `.PA`, `.AS`, `.DE`, `.L`, `.MI`, `.SW` variants of the same ISIN.
3. **Alternative exchange** — if DFNS.PA fails, try DFNS.AS or DFNS.DE; if NATO.L fails, try NATO.MI. Use the ISIN as the anchor, not the ticker.
4. **Alternative data source** — consult EODHD, Alpha Vantage, or IBKR's API if the ISIN is known to trade.
5. **Only after all four fail**, flag the instrument as "structurally unavailable" with the specific failure mode documented.

A single yfinance 404 is NEVER a valid basis for rejecting a candidate instrument. Document the retry sequence in the session file.

---

## Brainstorm Session

Follow the full War Room template at `brainstorms/_TEMPLATE.md`:
- Phase 1: Portfolio Review
- Phase 2: Macro Context (Sonnet sub-agent)
- Phase 3: **Counter-Regime Analysis** (Sonnet sub-agent — MANDATORY, see below)
- Phase 4: Signal & Opportunity (Sonnet sub-agent)
- Phase 5: Instrument Verification (runs here, post-Signal-Generator)
- Phase 6: Strategy Architecture (Sonnet sub-agent)
- Phase 7: Risk Stress Test (Sonnet sub-agent)
- Phase 8: Challenger Review (Sonnet sub-agent)
- Orchestrator synthesis and conflict resolution
- Phase 9: Full Desk Sign-Off (15 Haiku sub-agents)

### Counter-Regime Analysis (Phase 3 — MANDATORY)
Launch a second Sonnet sub-agent in **parallel** with the Macro agent. Both receive identical market data and portfolio state. The Counter-Regime agent's prompt MUST explicitly instruct:

> "Argue the strongest alternative regime call to the one a naive reading of current data would produce. You are not a devil's advocate — you are a serious analyst presenting the second-most-plausible macro frame. Produce: (a) named alternative regime, (b) specific evidence supporting it that the consensus would dismiss or under-weight, (c) invalidators that would force you back to the consensus call, (d) one or two sizing implications that differ from the consensus."

The Orchestrator reads BOTH the Macro agent's call and the Counter-Regime agent's call before synthesising. If the Counter-Regime view would materially change sizing (>20% allocation shift on any position), the Orchestrator must explicitly resolve the conflict in the session's Conflict Resolution table — a soft-pedal "noted and dismissed" is not acceptable.

Use any macro-capable persona for this role (Bridgewater, Man Group, AQR Factor) — rotation rules apply independently from the Macro slot. The Counter-Regime agent must be a different persona from the Macro agent in the same session.

**Critical rules:**
- Launch real sub-agents (Sonnet for Strike Team, Haiku for Phase 7). Never fake results inline.
- All prices must be from yfinance. No estimates.
- **Phase 7 Context Brief is deliberately minimal** — see rule below.
- **Strike Team sub-agent prompts do NOT include the previous session's Carry-Forward Brief.** The Orchestrator holds that context for its own synthesis only. Each sub-agent forms an independent view from market data + portfolio state.
- For backtests: enforce information cutoff strictly in every agent prompt.
- Write the complete session file to `local/brainstorms/YYYY-MM.md` (live) or `backtesting/sessions/YYYY-MM.md` (backtest).

### Phase 7 Context Brief — What the 15 Agents See

> [!IMPORTANT] Phase 7 sign-off agents are intentionally kept cold.
> Do NOT include Strike Team resolutions, Orchestrator synthesis, conflict resolution outcomes, or rationale for the chosen path in the Phase 7 Context Brief.

Phase 7 agents receive **only**:
- Session type (live / backtest + cutoff date)
- NAV and tier (Micro / Standard / Full)
- Current holdings (so N/A judgments are coherent)
- The trade plan (ticker, action, size, brief one-line thesis)

They do NOT receive:
- Which alternatives were considered and rejected
- Why specific sizing was chosen over alternatives
- Strike Team debate outcomes
- Challenger's assessment
- Counter-Regime agent's view

If an agent "re-flags" something the Strike Team already debated, that's fine — the absence of a blocking third flag (the 3+ threshold) is what resolves it, not pre-loaded context. This change is deliberate: the Phase 9 gate only works if the agents are genuinely independent of the synthesis.

### Path Convention — Live vs Backtest

Determine session type from the user's request (e.g. "run the June 2025 backtest" → backtest; "monthly brainstorm" with no historical date → live).

| File | Live path | Backtest path |
|---|---|---|
| Session file | `local/brainstorms/YYYY-MM.md` | `backtesting/sessions/YYYY-MM.md` |
| Rotation log | `local/ROTATION_LOG.md` | `backtesting/ROTATION_LOG.md` |
| Agent performance | `local/AGENT_PERFORMANCE.md` | `backtesting/AGENT_PERFORMANCE.md` |
| Portfolio history | `local/PORTFOLIO.md` (existing ledger) | `backtesting/PORTFOLIO_HISTORY.md` |

Use the correct path set throughout all phases. The two sets are independent — live sessions do not update backtest files and vice versa.

---

## Protocol Audit (Post-Session — Process Sheriff)

After the session is complete, verify all of the following:

| Check | How to Verify | Pass/Fail |
|---|---|---|
| Strike Team >= 5 agents? | Count launched Sonnet agents | |
| Counter-Regime agent launched (distinct persona from Macro)? | Check Phase 3 section of session file | |
| Framework diversity: ≥2 distinct frameworks on Strike Team? | Check Rotation table for `analytical_framework` values | |
| Rotation rules followed? | Compare against `local/ROTATION_LOG.md` | |
| Phase 9 run with 15 real agents? | Count Haiku agent results in session file | |
| Prices verified via yfinance? | Check for yfinance calls | |
| Phase 9 Context Brief **minimal** (no Strike Team resolutions)? | Verify brief contains only session type, NAV, holdings, trade plan | |
| Deployment gates checked? | Check for gate table in session file | |
| PORTFOLIO_HISTORY updated? | Compare session date vs last entry | |
| Carry-forward brief held by Orchestrator only (not in Strike Team prompts)? | Review prompt templates used for sub-agents | |
| Price affordability filter applied? | Check Signal Generator prompt for max price | |
| Pre-session live log written and unchanged after synthesis? | Compare `local/brainstorms/YYYY-MM.pre-session.md` timestamps | |
| Candidate tickers verified via Phase 5 (post-Signal-Generator) with retry protocol if any failed? | Check session file's Phase 5 section | |

Report the compliance score (e.g., 9/9) and flag any failures.

### 3a. Post-Session Updates
Update the files matching the session type (see **Path Convention** above):
- Update `local/ROTATION_LOG.md` with this session's Strike Team
- Update `local/AGENT_PERFORMANCE.md` with Phase 7 verdicts
- Update portfolio history (`local/PORTFOLIO.md` for live, `backtesting/PORTFOLIO_HISTORY.md` for backtest) with session results

### 3b. Append CHANGELOG entry (if framework changed)

**Trigger condition**: any file path that does **not** begin with `local/` was modified during this session (i.e., any framework, doc, agent YAML, script, proposal, skill, or root-level file).

If triggered, append an entry to [`CHANGELOG.md`](../../../CHANGELOG.md) under `[Unreleased]` (or a new dated section for today). Use the appropriate subsection: `### Added` / `### Changed` / `### Removed` / `### Fixed` / `### Process`. Architectural decisions go under `### Decisions` with persona attribution (`- (X, Persona Name) <decision> — <rationale>`).

If no file outside `local/` changed, skip this step.

### 3c. Schedule Next Session Reminder
Calculate the **third Saturday of next month**. Exception: if the ECB decision falls after that date, use the following Saturday instead.

Create a macOS Calendar reminder:
```bash
python3 -c "
import subprocess, datetime

# Calculate third Saturday of next month
today = datetime.date.today()
if today.month == 12:
    next_month = datetime.date(today.year + 1, 1, 1)
else:
    next_month = datetime.date(today.year, today.month + 1, 1)

# Find third Saturday
day = next_month
saturdays = 0
while saturdays < 3:
    if day.weekday() == 5:  # Saturday
        saturdays += 1
        if saturdays == 3:
            break
    day += datetime.timedelta(days=1)

third_sat = day
date_str = third_sat.strftime('%Y-%m-%d')
month_name = third_sat.strftime('%B %Y')

script = f'''
tell application \"Calendar\"
    tell calendar \"Calendar\"
        make new event with properties {{summary:\"War Room - {month_name}\", start date:date \"{date_str} 10:00:00\", end date:date \"{date_str} 12:00:00\", description:\"Monthly War Room brainstorm session. Run /war-room in Claude Code.\"}}
    end tell
end tell
'''
subprocess.run(['osascript', '-e', script])
print(f'Calendar reminder created for {date_str} ({month_name})')
"
```

Add the next session date to the session file's "Session Scheduling" section and to PORTFOLIO_HISTORY.md.
