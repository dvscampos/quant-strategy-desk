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

## When to write a proposal

- Any change the `/propose` skill would gate (strategy code, risk framework, new data source, agent roster change).
- Any architectural decision that touches more than one subsystem.
- Any intelligence document flagged HEAVY under the global Intelligence Document Governance rule.

One-line config tweaks, typo fixes, and session-file edits do **not** need a proposal.
