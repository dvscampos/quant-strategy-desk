---
id: 024
title: ISIN-anchored pricing + read-only IBKR --snapshot (S-21 + S-23 bundle)
status: SUPERSEDED
owner: Daniel
opened: 2026-06-04
updated: 2026-06-04
tags: [data-layer, ibkr, isin, pricing, war-room-3-followup]
---

# 024 — ISIN-anchored pricing + read-only IBKR `--snapshot` (S-21 + S-23 bundle)

**Tier: MEDIUM** — 4 code/data/doc files + 2 self-admin. Bundled because S-21 and S-23 share the IBKR/ISIN surface (PROGRESS S-23 "Extends S-21"). Within established patterns (additive script mode + helper hardening); external read-only call surface elevates effective blast radius → full L1–Ln Challenger pass.

## Summary

Close the two open data-layer items from War Room #3. **S-23**: fix the bare-ticker valuation trap (`reconcile_ibkr.py::_fetch_live_prices:287` calls `yf.Ticker("DFEN")` → US Direxion 3× fund, not the held VanEck Defense UCITS — a ~€40 NAV overstatement caught only by IBKR cross-check in #3) by making the **tracked framework** carry the portable identity contract: exchange-qualified tickers + ISIN in the ledger and its tracked template, with a structural code guard. **S-21**: add a read-only `--snapshot` mode to `reconcile_ibkr.py` that pulls live positions + cash from IBKR and cross-checks the ledger against the broker (the local-authoritative enhancement that *caught* the #3 trap).

## The central design tension (resolved, not assumed away)

This is a **public** GitHub repo; `local/PORTFOLIO.md` is **gitignored**. A fresh cloner has **no ledger and no IBKR account** — yet must still get correct, non-colliding instrument identity. Therefore the **portable correctness contract cannot live behind IBKR or in the local ledger**. Resolution:

- **Canonical (portable) path — key-free, stands alone:** the tracked `local/templates/PORTFOLIO.template.md` mandates an **exchange-qualified Ticker** (`DFEN.DE`, not `DFEN`) plus a populated **ISIN** column; the tracked framework price path (`_fetch_live_prices`) keys off the exchange-qualified ticker, so `yf.Ticker("DFEN.DE")` resolves the correct XETRA fund. The bare-symbol collision is made **structurally impossible** by a code guard, not by convention alone. Works for **any** cloner with only `yfinance` — no IBKR, no account, no live ledger required to be correct.
- **Local-authoritative enhancement — layers on when present:** IBKR `reqContractDetails` ISIN resolution (the `--snapshot` cross-check) verifies the ledger against the broker and would have flagged the #3 trap. It is **never the sole path** to correct identity.

**Canonical for the public repo = the portable path (a).** IBKR is an enhancement (b).

## 1. DECOMPOSE

| # | Sub-problem | Target / scope | Type of change | DoD anchor |
|---|---|---|---|---|
| 1 | S-21 read-only `--snapshot` subcommand | `reconcile_ibkr.py` (new `snapshot` arg + `print_snapshot()` + soft-connect) | New script mode (additive) | DoD #1, #6 |
| 2 | S-23 bare-ticker guard | `reconcile_ibkr.py::_fetch_live_prices` + `_parse_open_holdings` (thread ISIN) | Helper hardening | DoD #2, #4 |
| 3 | Portable identity contract | `local/templates/PORTFOLIO.template.md` (TRACKED) — format doc | Doc / contract | DoD #3 |
| 4 | Live-ledger data fix | `local/PORTFOLIO.md` (UNTRACKED) — `DFEN` → `DFEN.DE` ×2 | Data correction | DoD #5 |
| 5 | Test coverage | `tests/test_reconcile_ibkr.py` (TRACKED, new) | New tests | DoD #4 |
| — | Self-admin | proposal artefact + `proposals/README.md` row | Governance | — |

`6 files: 1 CREATE test + 1 CREATE proposal + 4 MODIFY (script + template + ledger + README) = 6 ✓` (PROGRESS.md + CHANGELOG.md deferred to `/commemorate`; memory nuance + retro deferred to `/retro`.)

## 2. ARCHITECT

**Sub-problem 1 — `--snapshot` (Confidence 0.86).** Add `argparse` flag `--snapshot`; when set, connect read-only and call `print_snapshot(ib)` instead of the reconcile flow. Data source (verified against installed `ib_insync` source):
- Primary: `ib.portfolio()` → `List[PortfolioItem(contract, position, marketPrice, marketValue, averageCost, unrealizedPNL, …)]` — carries live marks directly, no `reqMktData` subscription. (Populated by `reqAccountUpdates`, auto-issued on `connect()` for a single auto-detected account — verified `ib.py:connectAsync` lines 1760/1765-1770.)
- Fallback: if `portfolio()` is empty (multi-account, no `account` auto-set) → `ib.positions()` (always populated; `reqPositionsAsync` issued unconditionally on connect) + `ib.accountValues()` for cash/NAV.
- ISIN per position: `reqContractDetails(contract)` → `ContractDetails.secIdList: List[TagValue]`, read the `TagValue(tag="ISIN")` value (ISIN is **not** on the bare `Position.contract` — verified `objects.py:309`, `contract.py:473-496`).
- Cash / NAV: `ib.accountValues()` → filter `tag in {"TotalCashValue","NetLiquidation"}`, base currency; `value` is a **string** (verified `objects.py:214-219`) → cast to float.
- Ledger cross-check: reuse `_parse_open_holdings` (+ISIN) and join on `_base_symbol`; flag ISIN-mismatch / qty-mismatch / not-in-broker rows.
- **No file writes** — snapshot is pure read + print.

**Sub-problem 2 — bare-ticker guard (Confidence 0.9).** Thread `isin` (ledger col 2) through `_parse_open_holdings` into the position dict. In `_fetch_live_prices`, before the `yf.Ticker` call: if `isin` present, **not** US-prefixed (`isin[:2] != "US"`), and the ticker carries **no exchange suffix** (`"." not in ticker`) → skip with a loud warning naming the DFEN→Direxion collision. Precise (keyed to the ISIN country prefix already in the ledger), not an arbitrary allowlist; a legitimate US bare ticker (`US…` ISIN) is unaffected.

**Sub-problem 3 — portable contract (Confidence 0.88).** Add a `## Ticker & ISIN format` note block to the tracked template documenting: Ticker column **must** be exchange-qualified; ISIN column **must** be populated; one-line "why" (bare `DFEN` = US Direxion 3× ≠ held UCITS). This is the canonical key-free correctness contract.

**Sub-problem 4 — soft-connect (Confidence 0.85).** Existing `connect()` does `sys.exit(1)` on failure (correct for reconcile — you need the fills). Snapshot is advisory/read-only → add `connect(paper, *, required=True)`; snapshot passes `required=False` → on failure print `TWS/Gateway unavailable on {ports} — snapshot skipped (ledger unchanged)` and `sys.exit(0)`. Reconcile path unchanged (default `required=True`).

## 3. SPECIFY

- `pytest tests/test_reconcile_ibkr.py -q` → all pass.
- Guard test: a position with `isin="IE000YYE6WK5"`, `ticker="DFEN"` (bare) traverses `_fetch_live_prices` (monkeypatched `yfinance`) → ticker is **absent** from the returned prices dict and a warning is emitted; with `ticker="DFEN.DE"` → present.
- ISIN-threading test: `_parse_open_holdings` returns `isin` for each row.
- `python3 scripts/reconcile_ibkr.py --snapshot` (live, per-session operator approval) → prints positions + ISIN + marks + cash/NAV + ledger-vs-broker diff; with TWS down → soft-skip message + exit 0.
- `python3 scripts/reconcile_ibkr.py --help` lists `--snapshot`.

## 5. RISK FLAGS

- **Live IBKR read-only calls (IRREVERSIBLE-class surface, though non-mutating).** `--snapshot` opens a socket to TWS and issues `reqContractDetails`/account reads. Read-only (`readonly=True`, non-default `clientId=10`); no broker mutation. **Requires separate explicit per-session operator approval** before firing — never auto-run.
- **Wallet Bleed**: `reqContractDetails` is one call per position (N=2 today); no retry loop, no pagination, no model invocation. Bounded.
- **Secrets**: IBKR connects to a local TWS socket; no API key in code or agent context. The Challenger must not echo `.env`.
- **`portfolio()` empty on multi-account** → fallback to `positions()`+`accountValues()` (handled).
- **PROGRESS.md framework-only rule (AGENTS.md:194)**: the S-21/S-23 DONE rows (at `/commemorate`) must carry **no ticker-shape tokens** (`DFEN.DE`) — `/code-reviewer` flags them. Mitigation: keep the DONE prose generic ("exchange-qualified ticker"), tickers live in CHANGELOG only if needed.
- **yfinance `.DE` coverage is patchy** (known) — guard skips rather than mis-prices; a skipped mark shows "n/a", not a wrong number.

## 6. FILES CHANGED (PROPOSED)

- `MODIFY` `scripts/reconcile_ibkr.py` — S-21 `--snapshot` mode + `print_snapshot()` + soft-connect; S-23 ISIN-threaded `_parse_open_holdings` + `_fetch_live_prices` guard.
- `MODIFY` `local/templates/PORTFOLIO.template.md` (TRACKED) — portable identity contract (exchange-qualified ticker + ISIN mandatory).
- `MODIFY` `local/PORTFOLIO.md` (UNTRACKED) — `DFEN` → `DFEN.DE` in Holdings (line 11) + Trade History (line 22).
- `CREATE` `tests/test_reconcile_ibkr.py` (TRACKED) — guard + ISIN-threading + snapshot-format unit tests.
- `CREATE` `proposals/024-isin-anchored-pricing-ibkr-snapshot.md` — this artefact (self-admin).
- `MODIFY` `proposals/README.md` — index row (self-admin).
- *(deferred to `/commemorate`)* `MODIFY` `PROGRESS.md` (S-21+S-23 → DONE), `MODIFY` `CHANGELOG.md` (`[Unreleased]`).
- *(deferred to `/retro`)* memory `feedback_isin_anchor_pricing.md` nuance ("IBKR = local-authoritative, not portable/sole").

## 7. REVERSIBILITY

- `reconcile_ibkr.py`, `PORTFOLIO.template.md`, `tests/…`, proposal, README — **FULLY REVERSIBLE** (`git revert`).
- `local/PORTFOLIO.md` — local untracked data edit, reversible by hand (2 token changes).
- Live `--snapshot` calls — read-only, **no external state mutated**; nothing to reverse. (Listed in RISK FLAGS as a call-surface, not a state change.)

## Definition of Done

1. `--snapshot` mode prints broker positions (symbol/ISIN/qty/mark/mktValue/unrealisedPnL) + cash/NAV + ledger-vs-broker diff; writes nothing.
2. `_fetch_live_prices` skips a non-US-ISIN bare ticker with a warning; prices an exchange-qualified ticker normally.
3. Tracked `PORTFOLIO.template.md` documents the exchange-qualified-ticker + ISIN contract.
4. `tests/test_reconcile_ibkr.py` passes; the guard test traverses the real `_fetch_live_prices` entry-point (monkeypatched yfinance), not a helper predicate.
5. Live ledger `DFEN` → `DFEN.DE` (Holdings + Trade History); `_base_symbol("DFEN.DE")=="DFEN"` so IBKR fill-matching is unregressed.
6. TWS-down `--snapshot` soft-skips (exit 0), does not hard-error.
7. Full regression: `pytest -q` green (existing 11 + new).

## Status Log

- 2026-06-04 — DRAFT written. Pre-flight: S-22 regression PASS (5/5 `test_http_client`); `reconcile_ibkr.py` ISOLATED (no importers); `ib_insync` surface verified on installed source (connect auto-populates positions/portfolio/accountValues; ISIN in `ContractDetails.secIdList`). Cross-Check path: isolated-challenger pending (Step 4b).
- 2026-06-04 — **SUPERSEDED (foundation-first reset).** Isolated-Challenger pass (Cross-Check path: isolated-challenger — reason: no external/alternate model API configured, CLAUDE.md §3 condition a) returned `flawed` with a structural FATAL (L1), independently verified on disk: `reconcile_ibkr.py`'s `_parse_open_holdings`/`_patch_holdings_row` use **9-column** indices, but the ledger/template Holdings table has been **10 columns** (ISIN inserted at index 1) since the initial commit — `cols[8]` is Stop-Loss (never `=="OPEN"`) so the parser returns `[]` (silent no-op, **not** corruption — patch guard `"PENDING FILL" in cols[8]` also never fires; live ledger intact). This proposal's premise ("thread ISIN from col 2"; ISIN is col **1**) and DoD#2/#4 (guard test `DFEN.DE → present`) are unreachable on a broken parse foundation. Per G15, this FATAL is corrected by **fixing the existing surface first**, not by expanding 024. Operator (via steering) ruled foundation-first. Superseded by **Proposal 025** (pure column-index drift correction + tracked 10-column fixture, absorbing Challenger L13). S-21+S-23 (ISIN guard + read-only `--snapshot`, absorbing L5/L7/L10) to be re-proposed clean on the committed sound base in a future session. Banked from this pass: **L6** (currency-mismatch — a `.L`/`.SW` qualified ticker still feeds wrong-currency price into EUR P&L) and **L14** (`_patch_summary` regex anchors match neither template nor live ledger) → tracked PROGRESS S-items.
