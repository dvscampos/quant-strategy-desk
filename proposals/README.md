# Proposals Archive

> **Purpose**: persist every material PROPOSE so it survives `/clear`, `/compact`, and session changes. A proposal that only lives in transcript is a proposal that dies at the next context boundary.

## Convention

- One file per proposal, numbered sequentially: `NNN-short-slug.md` (e.g. `001-data-layer-upgrade.md`).
- Copy `_TEMPLATE.md` to start. Fill every section — if a section does not apply, write "n/a" with one line of reasoning.
- Status lifecycle: `DRAFT` → `REVIEWED` (Core Team A–D done) → `APPROVED` (user sign-off) → `IN PROGRESS` → `DONE` / `SUPERSEDED` / `ABANDONED`.
- Update the status and the **Status Log** section whenever state changes. Do not rewrite history — append.
- When a proposal is executed, link back from `PROGRESS.md` by ID so the roadmap and the proposal stay in sync.
- **Closing a proposal appends a [CHANGELOG.md](../CHANGELOG.md) entry** (under `[Unreleased]` or a new dated section). Architectural decisions go under `### Decisions` with persona attribution. Entry-or-it-didn't-happen.
- Delta Annexes (absorbed / resisted log from dual-model cross-check) are **mandatory** for HEAVY proposals and foundational intelligence documents, per global CLAUDE.md.

## Index

| ID  | Title                    | Status    | Owner  | Opened     | Last Update |
|-----|--------------------------|-----------|--------|------------|-------------|
| 001 | Data Layer Upgrade       | DONE      | Daniel | 2026-04-21 | 2026-04-23  |
| 002 | Project Portability & Structural Segregation | DONE  | Daniel | 2026-04-24 | 2026-04-25  |
| 003 | Data Layer Integration   | DONE      | Daniel | 2026-04-25 | 2026-04-26  |
| 004 | Sanitisation Sweep & CHANGELOG Introduction | DONE | Daniel | 2026-04-26 | 2026-04-26  |
| 005 | P-09 Cold-Reader Reword + Public Release Sanitisation Sweep | DONE | Daniel | 2026-04-26 | 2026-04-26  |
| 006 | Add Windows Git prerequisite to README | DONE  | Daniel | 2026-04-27 | 2026-04-27  |
| 007 | First-run pre-flight guard for /war-room skill | DONE  | Daniel | 2026-04-27 | 2026-04-27  |
| 008 | Phantom skills cleanup (first deferral) | DONE  | Daniel | 2026-04-27 | 2026-04-27  |
| 009 | S-14 Resolve redundant agent pairs (persona-eval differentiation) | APPROVED | Daniel | 2026-05-15 | 2026-05-15  |
| 010 | S-15 citadel_alpha lift + S-16 D3 Actionability batch across persona library | DONE | Daniel | 2026-05-15 | 2026-05-15  |
| 011 | python-dotenv auto-load (eliminate manual `export` step) | DONE | Daniel | 2026-05-15 | 2026-05-15  |
| 012 | Citadel + Two-Sigma review_prompt example-trio domain polish | DONE | Daniel | 2026-05-16 | 2026-05-16  |
| 013 | Port `/skill-audit` from Gemini → Claude Code (global; archived at `~/.claude/governance-overhaul/proposals/013-skill-audit-port.md`) | DRAFT (global) | Daniel | 2026-05-16 | 2026-05-16  |
| 014 | S-19 — Carry-forward instrument-compliance guard to pimco + de_shaw | DONE | Daniel | 2026-05-16 | 2026-05-16  |
| 015 | Roadmap housekeeping — de-date War Room header, refresh S-17/S-18 rationale, record FRED-key decision | DONE | Daniel | 2026-05-20 | 2026-05-20  |
| 016 | S-17 renaissance_backtesting lift + S-18 virtu_execution lift (bundle) | SUPERSEDED | Daniel | 2026-05-20 | 2026-05-21  |
| 017 | S-17 — renaissance_backtesting persona quality lift (standalone) | DONE | Daniel | 2026-05-21 | 2026-05-21  |
| 018 | S-18 — virtu_execution persona re-architecture (standalone) | DONE | Daniel | 2026-05-21 | 2026-05-22  |
| 019 | S-20 — AGENTS.md archetype-line correction + gs_compliance EN/PT example tidy | DONE | Daniel | 2026-05-22 | 2026-05-22  |
| 020 | Surface HYPOTHESIS_LOG.md read in /war-room SKILL.md Phase 4 (pointer to template) | SUPERSEDED | Daniel | 2026-06-02 | 2026-06-02  |
| 021 | Hypothesis-log lifecycle — pointer + plain anti-bias line + stamp-in-place close-out | DONE | Daniel | 2026-06-02 | 2026-06-02  |
| 022 | PORTFOLIO partner-name correction (Sofia→PPDC) + S-21 IBKR read-only snapshot roadmap item | DONE | Daniel | 2026-06-02 | 2026-06-02  |
| 023 | S-22 — HTTP-cache per-series TTL (amber-keyed) + `--no-cache` on macro fetch | DONE | Daniel | 2026-06-03 | 2026-06-03  |
| 024 | S-21+S-23 — ISIN-anchored pricing + read-only IBKR `--snapshot` (bare-ticker trap fix) | SUPERSEDED | Daniel | 2026-06-04 | 2026-06-04  |
| 025 | `reconcile_ibkr.py` column-index foundation fix (10-column ISIN schema) | DONE | Daniel | 2026-06-04 | 2026-06-04  |
| 026 | S-23 ISIN-anchored pricing — bare-ticker guard + portable identity contract (S-21 `--snapshot` split out) | DONE | Daniel | 2026-06-04 | 2026-06-04  |
| 027 | S-30 Mechanical pre-commit sanitisation guard — blocks private-literal leaks into tracked diffs; cloner-portable | DONE | Daniel | 2026-06-04 | 2026-06-09  |
| 028 | Reconcile Summary canonical contract (S-27) + currency-aware pricing (S-28) | DONE | Daniel | 2026-06-10 | 2026-06-10  |
| 029 | Pre-push sanitisation remediation — scrub range-diff collisions (20 net-tree = 18 real + 2 synthetic self-FP: 3 SCRUB / 13 ALLOWLIST / 4 CLEAN-LOG) + squash-clean + local archive + pre-push hook | DONE | Daniel | 2026-06-10 | 2026-06-13 |
| 030 | S-31 sanitisation-guard precision (ticker-only alpha-boundary) + fail-closed both entry-points (git + ledger-read) + corpus process-noise exclusion (convention-glob) | DONE | Daniel | 2026-06-14 | 2026-06-14 |
| 031 | S-24 brent fetch wire-up (PARTIAL) + S-25 stale-core-macro surfacing into Data_Confidence_Tier (DONE; per-series render row → S-25d) | DONE | Daniel | 2026-06-17 | 2026-06-17 |
| 032 | S-25c — replace dead ECB euro-area HICP key with a Eurostat ei_cphi_m provider (new EUROSTAT archetype; thresholds 55/90) | DONE | Daniel | 2026-06-18 | 2026-06-20 |

## When to write a proposal

- Any change the `/propose` skill would gate (strategy code, risk framework, new data source, agent roster change).
- Any architectural decision that touches more than one subsystem.
- Any intelligence document flagged HEAVY under the global Intelligence Document Governance rule.

One-line config tweaks, typo fixes, and session-file edits do **not** need a proposal.
