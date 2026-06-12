---
id: 011
title: Auto-load .env via python-dotenv (eliminate manual export step)
status: DONE
owner: Daniel
opened: 2026-05-15
updated: 2026-05-15
tags: [data-layer, ergonomics, secrets]
---

# 011 — python-dotenv Auto-Load

## Tier: LIGHT

**Evidence**: 3 files (`requirements.txt`, `scripts/data/__init__.py`, `scripts/init_workspace.py`), <10 net lines added, known pattern (standard dotenv idiom). No `critical_patterns` from `skill-config.yaml` touched (no skill-config exists). Within LIGHT ceiling.

## Summary

Add `python-dotenv` as a dependency and call `load_dotenv()` at the import-time entry points of `scripts.data` and `scripts.init_workspace`, so editing `.env` is sufficient — no manual `source .env`/`export FRED_API_KEY=…` step. The existing fail-fast blocker at `scripts/data/cli.py:100-103` (and its sibling at `scripts/data/gate_eval.py:511`) is preserved verbatim: a still-empty key after auto-load exits with a clear "FRED_API_KEY not set — add it to `.env`" message.

## Motivation

This session (2026-05-15) discovered that:
1. `.env` is byte-identical to `.env.example` (key never added).
2. There is **no dotenv loader anywhere** in the codebase (`grep -rn "load_dotenv\|dotenv" --include="*.py"` returns zero hits).
3. `scripts/data/cli.py:98` reads `os.environ.get("FRED_API_KEY", "")` directly — so even an edited `.env` has no effect without a separate `source .env` or `export` step in the same shell.
4. `README.md:42` and `SHARING.md:22` both tell the user *"edit `.env` and set `FRED_API_KEY=<your key>`"* with **no mention** of the `source`/`export` step — the docs imply auto-load that doesn't exist.
5. `local/snapshots/2026-04.json` has 0 observations → FRED has **never been successfully called**. The smoke (DoD #10b, 2026-05-16 trigger, 2026-06-20 rollback) has been silently blocked since `.env` was committed.

The "edited `.env` but forgot to source" foot-gun is real and live. Auto-load fixes it once.

## Proposal

### Decompose

1. Add `python-dotenv>=1.0.0` to `requirements.txt`.
2. Add `from dotenv import load_dotenv; load_dotenv()` at the top of `scripts/data/__init__.py` (BEFORE the existing provider/snapshot imports — those don't read env at import, but future ones might) and at the top of `scripts/init_workspace.py` (which validates the key during first-run setup).
3. Preserve the existing missing-key blockers verbatim (`scripts/data/cli.py:100-103` and `scripts/data/gate_eval.py:511` and `scripts/init_workspace.py:81-83`). They already exit cleanly on empty values after the `.split("#")[0].strip()` parser.

### File manifest

| Action | File | Reason |
|---|---|---|
| MODIFY | `requirements.txt` | Append `python-dotenv>=1.0.0` |
| MODIFY | `scripts/data/__init__.py` | Add `from dotenv import load_dotenv; load_dotenv()` after module docstring, before existing imports |
| MODIFY | `scripts/init_workspace.py` | Add `from dotenv import load_dotenv; load_dotenv()` after stdlib imports, before `os.environ` access at line 66 |

**Total**: 3 files, ~6 lines added (3 imports + 3 `load_dotenv()` calls, structured to fit existing style).

### Why `load_dotenv()` defaults are correct here

- **`override=False` (default)**: existing shell env vars are NOT clobbered. CI environments that inject `FRED_API_KEY` via a secret store keep working. Tests that `patch.dict(os.environ, …)` still get their patched values because patching happens AFTER import.
- **Search path**: `load_dotenv()` walks up from cwd to find `.env`. Both `scripts.data` and `scripts.init_workspace` are invoked from project root, so it finds `./.env`. No path override needed.

## Definition of Done

1. `python-dotenv>=1.0.0` listed in `requirements.txt`.
2. `from dotenv import load_dotenv; load_dotenv()` present at module top of `scripts/data/__init__.py` and `scripts/init_workspace.py`.
3. Smoke negative-path test: with an empty `.env`, `python3 -m scripts.data fetch --session 2026-05` still prints `"FRED_API_KEY not set — add it to .env before fetching live data."` and exits 1. (Confirms blocker preserved.)
4. Smoke positive-path test (deferred to user when they have a real key): `echo 'FRED_API_KEY=test123' >> /tmp/fake.env && cd /tmp && env FRED_API_KEY= python3 -c "from dotenv import load_dotenv; load_dotenv('/tmp/fake.env'); import os; assert os.environ['FRED_API_KEY']=='test123'"` (sanity that `load_dotenv` itself works). Optional — the negative-path test is what guards regression.
5. `python3 -m pytest tests/test_data_providers.py tests/test_gate_eval.py` still green (tests use `patch.dict` AFTER import, so behaviour unchanged).
6. `git status .env` after the change still shows nothing (still gitignored).

## Out of Scope

- No README/SHARING edits — current wording is already correct under the new auto-load behaviour ("edit `.env` and set FRED_API_KEY=…" becomes literally sufficient, no qualifier needed).
- No changes to `scripts/data/cli.py` or `scripts/data/gate_eval.py` — the missing-key blockers there already work and don't need touching.
- No changes to `scripts/data/providers/fred.py:45` (`os.environ["FRED_API_KEY"]` lookup at provider instantiation — runs AFTER `scripts/data/__init__.py` has already loaded dotenv).
- No version-pin tighter than `>=1.0.0` — dotenv 1.x is stable; conservative floor.
- Item #2 (the live FRED smoke itself) — still gated on user adding the real key. This proposal just removes the export step from the workflow.

## Reversibility

**FULLY REVERSIBLE.** `git revert` of the three edits restores prior behaviour. No external state, no data mutations, no API calls. Removing the dependency is `pip uninstall python-dotenv` if needed; the package has no migrations.

## Adversarial Pass (L1)

**L1 — load_dotenv overrides a deliberate shell-env value.** Risk: a user in a hardened env sets `FRED_API_KEY` via shell intentionally (e.g. CI secret manager) and a stale `.env` clobbers it. **Closed by** `load_dotenv()` default `override=False` — pre-existing shell env wins. Documented in §"Why defaults are correct."

**L2 — Import-time side effect surprises a future contributor.** Risk: `load_dotenv()` at module init is a non-local side effect; someone importing `scripts.data` for a non-CLI use (e.g. notebook) gets an env mutation they didn't ask for. **Closed by** acceptance: this is a standard 12-factor-app idiom; behaviour is `override=False` (additive, not mutative for existing vars); the alternative (every entry point calling `load_dotenv` itself) introduces a worse foot-gun (forgetting it).

## Core Team Verdict (LIGHT — inline, one-liner each)

- **A (Quant Architect)**: APPROVE. Single canonical load site, no duplication.
- **B (Portfolio Manager)**: APPROVE. Smallest scope that closes the foot-gun.
- **C (CTO)**: APPROVE WITH CONDITIONS — verify `override=False` default behaviour holds across `python-dotenv >=1.0`, and confirm `git check-ignore -v .env` still passes after the change (it must; we're not touching `.gitignore`).
- **D (Risk Officer)**: APPROVE. The existing fail-fast blocker is preserved; no risk-framework surface touched.

No REJECT; no unanimous-approval scrutiny needed (C has conditions).

## Status Log

> Append-only.

- 2026-05-15 — DRAFT created. LIGHT tier. Regression gate verified (proposal 010 idempotency marker = 17/17; proposal 009 firm-brand distinction intact). Awaiting user approval.
- 2026-05-15 — APPROVED by user (option a). Dispatched implementation-agent (Sonnet, single LIGHT dispatch).
- 2026-05-15 — Implementation LANDED. 3 files modified (+9 lines): `requirements.txt`, `scripts/data/__init__.py`, `scripts/init_workspace.py`. Opus verification gate PASS: diff matches scope; `override=False` default confirmed; 54 tests green; module imports clean. Implementation-agent's positive-path verification (`fetch --session 2026-99`) inadvertently revealed user had already added a real `FRED_API_KEY` to `.env` — confirming end-to-end auto-load works. Stray `local/snapshots/2026-99.json` cleaned up.
- 2026-05-15 — DoD #10b live smoke folded into same close-out (option a): `fetch --session 2026-05 && gate_eval --session 2026-05` ran clean. 7 live observations (4 FRED + 3 ECB), snapshot `sha256:83207ac933d7…`. Data-layer-integration rollback clock (2026-06-20) retracted. PROGRESS.md `Known issues to address` and Status Table both updated.
- 2026-05-15 — `/code-reviewer` verdict: **APPROVE WITH NOTES**. 2 NOTE items (optional inline comment on load_dotenv intent; optional pinned `dotenv_path`). No BLOCKs, no WARNs. Verification evidence cited (6 tool-call citations).
- 2026-05-15 — **PROPOSAL 011 CLOSED. STATUS: DONE.**
