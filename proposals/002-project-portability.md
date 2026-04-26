---
id: 002
title: Project Portability & Structural Segregation
status: DONE
owner: Daniel
opened: 2026-04-24
updated: 2026-04-24
tags: [infrastructure, governance, sharing, onboarding, segregation]
---

# 002 — Project Portability & Structural Segregation

## Summary
The repo today conflates the reusable **framework** (CLAUDE.md, AGENTS.md, docs/, agents/, scripts/, config/, tests/, proposals/, brainstorms/_TEMPLATE.md) with **personal data** (Daniel's portfolio, investor profile, real session files, hypothesis log, macro snapshots, dashboard output, agent/rotation logs). `PORTFOLIO.md` and `INVESTOR_PROFILE.md` live at the repo root alongside framework files. If the directory is `git init`-ed and pushed today, personal financial data ships with it.

This proposal applies **structural segregation** as the primary mechanism: all personal, runtime, or session-generated artefacts move into a single `/local/` directory. `.gitignore` contains one relevant line (`local/`) instead of eight scattered patterns. A deterministic `scripts/init_workspace.py` handles first-run plumbing without ingesting secrets. Onboarding follows a pre-flight flow: announce → Q1–Q11 dialogue → plumbing → hydrate. A new `SHARING.md` documents the clone-per-user model and backup posture.

**Critical risk flagged upfront**: `PORTFOLIO.md`, `INVESTOR_PROFILE.md`, `HYPOTHESIS_LOG.md`, real `brainstorms/YYYY-MM.md` files, `data/snapshots/*.json`, `dashboard.html`, `AGENT_PERFORMANCE.md`, and `ROTATION_LOG.md` are currently root-level and untracked-by-gitignore. The directory is **not** yet under git (verified 2026-04-24: no `.git/` present), so there is no history to rewrite — but the structural move must land before any `git init` / push.

## Motivation / Problem
- Pattern-based `.gitignore` entries are brittle against future file-name variants. If an agent or user creates `PORTFOLIO_BACKUP.md`, `Q3-SESSION.md`, or `investor-profile-v2.md`, a regex list misses it and personal data ships with the next push. Security by containment (single directory rule) is strictly more robust than security by pattern matching.
- `PROGRESS.md` mixes a **framework roadmap** (architecture, staged improvements, backlog — shareable) with **personal session history** (real trades, NAV, session-by-session log — not shareable). LLM agents updating PROGRESS.md during sessions will re-contaminate it with ticker/NAV references unless the rule is explicit.
- CLAUDE.md's first-run flow generates `INVESTOR_PROFILE.md` and tax-specific sections of `docs/COMPLIANCE.md` but never tells the user they need a FRED API key. A new user hits the first live snapshot fetch with no key and a bare traceback.
- There is no documented repo model — clone vs fork vs template is ambiguous. Others will assume incorrectly.
- Proposal 001 is DONE; snapshots are now being generated against live data. This is the last clean moment to lock segregation before session artefacts accrete personal timing metadata.

## Proposal

### File manifest

**Moved into `/local/`** (all runtime / personal state)
```
INVESTOR_PROFILE.md              → local/INVESTOR_PROFILE.md
PORTFOLIO.md                     → local/PORTFOLIO.md
HYPOTHESIS_LOG.md                → local/HYPOTHESIS_LOG.md
AGENT_PERFORMANCE.md             → local/AGENT_PERFORMANCE.md
ROTATION_LOG.md                  → local/ROTATION_LOG.md
brainstorms/2026-*.md            → local/brainstorms/2026-*.md
brainstorms/*.pre-session.md     → local/brainstorms/*.pre-session.md
brainstorms/.checkpoint-*.json   → local/brainstorms/.checkpoint-*.json
data/snapshots/*.json            → local/snapshots/*.json
dashboard.html                   → local/dashboard.html
```

**New files (framework-shared, committed)**
```
local/.gitkeep                               # directory marker
local/retros/.gitkeep                        # retro archive directory marker (replaces docs/retros/ default)
local/templates/PORTFOLIO.template.md        # header skeleton + column legend
local/templates/HYPOTHESIS_LOG.template.md   # schema comment block
local/templates/SESSIONS.template.md         # seed entry format
local/templates/AGENT_PERFORMANCE.template.md
local/templates/ROTATION_LOG.template.md
scripts/init_workspace.py                    # deterministic plumbing (~40 LOC)
SHARING.md                                   # repo model + backup posture + pre-push checklist
```

**New file (personal, gitignored — created by SESSIONS split)**
```
local/SESSIONS.md                # personal session log extracted from PROGRESS.md
```

**New files (framework-shared, committed) — continued**
```
skill-config.yaml                            # override retro archive_dir: local/retros/ (and any future skill path overrides)
```

**Modified files**
```
.gitignore                                   # replace 1 pattern (data/.http_cache/ stays), add: local/ (except local/templates/ and local/.gitkeep), tighten .env* glob, add .obsidian/
CLAUDE.md                                    # first-run flow: pre-flight announcement → Q1–Q11 → init_workspace.py → hydrate; update every path reference (PORTFOLIO.md → local/PORTFOLIO.md, etc.)
AGENTS.md                                    # new governance rule: PROGRESS.md references sessions by ID only; no ticker / NAV / outcome content
.claude/commands/war-room/SKILL.md           # update path references if any (audit required)
scripts/generate_dashboard.py                # output path: local/dashboard.html; input paths: local/PORTFOLIO.md, local/brainstorms/
scripts/data/cli.py                          # default snapshot out_dir: local/snapshots/; friendly error on missing FRED_API_KEY
config/gates.yml                             # consumer list: update any path references
.env.example                                 # one-line comment per key; FRED signup URL reference
PROGRESS.md                                  # remove Session Log section; one-line pointer to local/SESSIONS.md; audit remaining entries for ticker/NAV leakage
proposals/README.md                          # index row for 002; policy note on owner attribution
requirements.txt                             # unchanged (confirmed)
```

### `.gitignore` — consolidated

```gitignore
# Secrets
.env*
!.env.example

# Personal / runtime state — structural segregation
local/*
!local/.gitkeep
!local/templates/

# Tier 1 HTTP response cache (not in local/ because it's repo-scoped infra)
data/.http_cache/

# OS / editor / Python (unchanged from current)
.DS_Store
Thumbs.db
.obsidian/
__pycache__/
*.py[cod]
*.so
*.egg-info/
dist/
build/
.venv/
venv/
env/
.vscode/
.idea/
*.swp
.pytest_cache/
.coverage
htmlcov/
*.log
.ipynb_checkpoints/
```

One rule (`local/*` + targeted allow-list) replaces the 8-pattern scattered approach.

### `scripts/init_workspace.py` — deterministic plumbing

Responsibilities (narrow, testable):
1. Create `local/` and `local/brainstorms/`, `local/snapshots/` subdirs if missing.
2. Copy every file in `local/templates/*.template.md` → `local/<name>.md` **iff the target does not already exist**. Never overwrites.
3. Check `.env` exists; if not, `cp .env.example .env`.
4. Detect `FRED_API_KEY` in `.env`; if empty or missing, print exactly:

    ```
    FRED_API_KEY not set in .env — live fetches will fail until you add it.
    Sign up: https://fred.stlouisfed.org/docs/api/api_key.html
    Then add FRED_API_KEY=<your_key> to .env. Continuing setup.
    ```

    Script exits 0. **Never prompts for the key, never ingests the key.**
5. Idempotent: running twice is a no-op on a provisioned workspace.

### Onboarding pre-flight flow (CLAUDE.md first-run)

**Step 0 — Announce** (new):
> "We'll do an 11-question onboarding to build your profile, then I'll run a one-line setup script to prepare your local workspace. Heads up: you'll need a free FRED API key (fred.stlouisfed.org, 2 minutes) before your first live macro fetch — you can add it after onboarding. Ready?"

**Step 1 — Dialogue**: Q1–Q11 as today, answers held in conversation state.

**Step 2 — Plumbing**: `python scripts/init_workspace.py` (Bash tool). Output confirms `local/` created and FRED status.

**Step 3 — Hydrate**: Write generated `local/INVESTOR_PROFILE.md` from Q1–Q11 answers (fully generated, no template merge). Update `docs/COMPLIANCE.md` tax section. Update `brainstorms/_TEMPLATE.md` home-bias line.

This order prevents the script from overwriting agent-generated content (`INVESTOR_PROFILE.md` is *not* in `local/templates/` — it is fully generated). Partially-filled files (`PORTFOLIO.md`, `HYPOTHESIS_LOG.md`) use templates copied by the script.

### AGENTS.md governance rule (new)

Add under §Governance:

> **PROGRESS.md content rule.** PROGRESS.md is framework-only. When updating it, do not reference tickers, specific dates, NAV, deployment amounts, P&L, or trade outcomes. Refer to sessions by ID only (e.g. "2026-04 session closed"). Personal session content belongs in `local/SESSIONS.md`. The `/code-reviewer` skill flags any PROGRESS.md diff containing currency symbols, ticker-shape tokens, or session-specific numeric claims.

### SHARING.md (new, ≤150 lines)

Content outline:
1. **What's shared vs what's yours** — framework in repo, personal data in `local/` (gitignored).
2. **How to use this repo for your own investing** — clone → run Claude Code → onboarding generates `local/` → your data stays local by default.
3. **How to contribute framework improvements back** — PR against upstream; `local/` is gitignored so your diff is clean by construction.
4. **Backup posture** — `local/` is not under git. Enable Time Machine (macOS) / File History (Windows) / restic or similar (Linux) before first live session. Alternative: `cd local && git init` for git-as-backup (optional; not required by the framework).
5. **Pre-push checklist** — `git status` clean + `git ls-files | grep -E '^local/'` returns empty + `.env` not tracked.
6. **Security reminder** — `.env`, `local/*` never leave your machine unless you explicitly override `.gitignore`.

## Scope & Out-of-Scope

**In scope**
- `/local/` directory creation and migration of 11 personal/runtime artefacts
- `.gitignore` consolidation (single `local/*` rule + allow-list)
- `scripts/init_workspace.py` deterministic plumbing
- CLAUDE.md pre-flight onboarding flow + all path-reference updates
- AGENTS.md PROGRESS.md content rule
- `SHARING.md` (new)
- PROGRESS.md → PROGRESS.md (framework) + `local/SESSIONS.md` (personal) split with **per-entry triage**, not section-level move
- `scripts/data/cli.py` friendly error on missing `FRED_API_KEY`
- Path updates in `scripts/generate_dashboard.py`
- `.env.example` comments
- Proposal 001 audit for personal leakage (findings recorded in Status Log)

**Out of scope (explicit to prevent drift)**
- `git init` and first commit — user decides timing
- Dual-repo with `git init` inside `local/` — offered as user option in SHARING.md, not mandated
- Upstream-sync tooling for forks
- Sanitised reference / mock session under `docs/examples/` — deferred to Backlog (see Delta Annexe Round 2)
- Multi-platform guides (Gemini, Codex, Cursor) — Staged Improvement S-8
- Secrets management beyond `.env`
- Rewriting any pre-existing git history (none exists today)

## Definition of Done (binary)

1. `local/` directory exists at repo root with `.gitkeep` and `templates/` subdirectory. All 11 artefacts listed in the file manifest are moved (not copied) from their old locations. Old paths return `not found`.
2. `.gitignore` contains `local/*` + allow-list + `.env*` + `!.env.example` + `.obsidian/`. Verification: after `git init` dry-run, `git check-ignore local/PORTFOLIO.md local/INVESTOR_PROFILE.md local/snapshots/2026-05.json local/brainstorms/2026-04.md .env` returns ignored for all; `git check-ignore local/templates/PORTFOLIO.template.md .env.example local/.gitkeep` returns **not ignored** for all.
3. `git ls-files` (after a hypothetical `git init && git add .`) returns **zero** files matching `^local/(?!templates/|\.gitkeep)`. Verified by dry-run script committed in `tests/` or executed inline.
4. `scripts/init_workspace.py` is idempotent: running twice on a provisioned workspace produces zero file changes and exits 0 both times. Running on a bare clone creates all expected directories and template-copied files, and never prompts for or echoes the FRED key.
5. CLAUDE.md first-run flow follows the four-step pre-flight order (announce → Q1–Q11 → plumbing → hydrate) explicitly. Every reference to moved files uses the `local/` path.
6. AGENTS.md contains the PROGRESS.md content rule. `/code-reviewer` skill instructions include the PROGRESS.md scan pattern.
7. `SHARING.md` exists, ≤150 lines, covers all six outline sections.
8. PROGRESS.md contains zero ticker references, zero NAV/currency amounts, zero trade outcomes. `local/SESSIONS.md` contains the extracted personal history with no content loss (line-count + heading parity check against the pre-split PROGRESS.md Session Log section).
9. `scripts/data/cli.py` exits with a friendly one-line error and a signup URL when `FRED_API_KEY` is missing. No traceback.
10. Proposal 001 audit complete; findings (expected clean) recorded in this proposal's Status Log.
11. Zero regression in existing tests: `python3 -m pytest` passes all 54 offline tests after migration. Path updates in `scripts/generate_dashboard.py` and `scripts/data/cli.py` verified by running each.

## Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Path updates miss a framework-file reference to a moved artefact | Exhaustive grep before completion: `grep -rEn '(PORTFOLIO\|INVESTOR_PROFILE\|HYPOTHESIS_LOG\|AGENT_PERFORMANCE\|ROTATION_LOG\|dashboard\.html\|data/snapshots)' --include='*.md' --include='*.py' --include='*.yml'` returns only intended references. Documented in Status Log at close. |
| PROGRESS.md / SESSIONS.md split loses framework decisions buried in session entries | DoD #8 requires per-entry triage. Architecture/staged-improvement markers (e.g. "S-11 ACTIVE — implemented YYYY-MM-DD") stay in PROGRESS.md Architecture Decisions Log; trade/NAV/per-session observations move. Line-count + heading-parity check catches silent drops. |
| `init_workspace.py` overwrites user-edited files | DoD #4 requires idempotence via existence-check before copy. Never overwrites. |
| FRED key leaks through `init_workspace.py` | Script never reads the key from stdin, never echoes the key, never accepts it as an argument. Key handling is 100% manual file edit by user. Architectural guarantee, not convention. |
| User pushes repo before migration lands | DoD #1–#3 are the critical path. `.git/` confirmed absent 2026-04-24. SHARING.md pre-push checklist (DoD #7) provides secondary defense. |
| Obsidian vault breaks after move | `.obsidian/` is workspace-scoped; moving files invalidates internal links but Obsidian re-indexes. Acceptable cost. Mitigation: user performs Obsidian "Search and replace" for moved paths post-migration (documented in SHARING.md §Migration). |
| `/code-reviewer` false positives on PROGRESS.md | Scan pattern is specific (currency symbols + ticker-shape regex + NAV-shape numerics). First few runs tuned against real diffs. |
| Agent future-session creates a personal file outside `local/` | AGENTS.md rule extended: runtime/personal artefacts land in `local/`. Reinforced by structural default — scripts write to `local/` by default. Not eliminated, but pattern-based gitignore had the same failure mode. |
| Templates drift from actual file schema | Templates committed as schema-of-record. Any field change to PORTFOLIO.md schema etc. requires matching template update — enforced by `/code-reviewer`. |

## Core Team Review (A–D)

### Quant Architect
Approve. Structural segregation is the correct primitive for a framework intended to be forked. One observation: `data/snapshots/*.json` moving to `local/snapshots/*.json` is a path change that `scripts/data/cli.py` and `scripts/data/snapshot.py` both hit. Verify via the live smoke test after migration — if the hash computation is independent of path (it is, per Proposal 001 canonical JSON spec), regression is purely path-plumbing. No cognitive-layer impact.

### Portfolio Manager
Approve. The critical items (DoD #1–#3) prevent the single real risk — accidental push of personal financial data. SHARING.md backup paragraph is load-bearing; Time Machine / Dropbox is the right primitive for a solo investor. Do not market this proposal as a capability upgrade — it is plumbing + security hygiene, which is what 1A was.

### CTO
Approve with conditions. (1) Idempotence of `init_workspace.py` must be tested, not asserted — DoD #4 requires a test fixture or inline verification. (2) `.gitignore` allow-list syntax is subtle: `local/*` followed by `!local/templates/` works only with git's path-level negation rules; verify `git check-ignore` behaviour explicitly per DoD #2 before closing. (3) The migration is destructive-adjacent (file moves) — perform in a clearly demarcated block with diff review before committing any subsequent work. (4) Running `init_workspace.py` on the *current* (already-populated) repo must not clobber existing `local/` files — DoD #4 existence-check covers this but worth re-emphasising.

### Risk Officer
Approve. The FRED key handling is the decisive improvement over Proposal 002's previous draft — no LLM layer ever sees the secret. PROGRESS.md content rule + `/code-reviewer` scan provides durable defence against session-to-session contamination, which is the real long-term leakage vector. Two additions: (a) SHARING.md pre-push checklist must be a *literal checklist* users tick, not prose — prose gets skimmed. (b) Consider a pre-commit hook (future work, not this proposal) that blocks commits where `git diff --cached` touches tracked paths matching the forbidden patterns. Deferred to Backlog.

## Delta Annexe — Round 1 (Core Team)
- **Absorbed**: CTO's idempotence-as-test requirement folded into DoD #4. CTO's `.gitignore` negation verification folded into DoD #2. CTO's emphasis on destructive-adjacent file moves handled via Status Log block demarcation. Risk Officer's literal-checklist requirement for SHARING.md pre-push section adopted. Quant Architect's live smoke test verification added as DoD #11 implicit requirement. Portfolio Manager's "do not market as capability upgrade" framing carried into Summary.
- **Resisted**: Risk Officer's pre-commit hook — deferred to Backlog per Simplicity First; value accrues only after repo is git-tracked and multiple contributors exist. Premature today.

## Delta Annexe — Round 2 (Cross-Model Critique — Gemini)
Dual-model pass captured verbatim in session log; condensed here.

- **Absorbed**:
  - **Structural segregation via `/local/`** — Gemini's Challenge 1/2. Strictly more robust than 8-pattern gitignore against future file-name variants. Adopted as the primary mechanism of this proposal.
  - **Governance rule against PROGRESS.md contamination** — Gemini's Challenge 3. Added to AGENTS.md; `/code-reviewer` scan pattern defined in DoD #6.
  - **Deterministic onboarding plumbing as code** — Gemini's Challenge 4, scoped to plumbing only. `scripts/init_workspace.py` handles directory creation, template copy, and FRED key check. Conversational Q1–Q11 remains in CLAUDE.md prose.
  - **Pre-flight onboarding flow** — Gemini's dependency-trap correction. Four-step order (announce → dialogue → plumbing → hydrate) prevents script-clobbers-agent-output and UX-blocked-at-end-by-missing-key failures.
  - **Rewrite Proposal 002 rather than stage sibling 003** — Gemini's "no git history to rewrite, zero refactor cost" argument. Accepted; manufacturing debt to pay it off next cycle violates Simplicity First and Surgical Changes.

- **Resisted**:
  - **Dual-repo with `git init` inside `/local/` as mandated backup** — Gemini's Challenge 1 prescription. Diagnosis correct (no undo on agent overwrite); prescription wrong for user profile (solo investor, not a team). Git-as-backup for financial ledgers requires manual commit discipline after every trade — exactly when the user is least thinking about it. Continuous background sync (Time Machine / Dropbox / restic) is the correct primitive. Offered as optional user choice in SHARING.md §Backup, not mandated.
  - **`init_workspace.py` prompting for FRED key via stdin** — Gemini's Step 2 in revised flow. Even `getpass.getpass()` still routes through Bash tool output to the model. Adopted stricter rule: script never ingests the key, user edits `.env` manually. Architectural guarantee > UX convenience.
  - **Sanitised mock session under `docs/examples/`** — Gemini's Challenge 5. Real value is speculative; mock data rots as macro conditions change; constructing an internally-consistent fake portfolio with valid snapshot hash is non-trivial. Deferred to Backlog as Staged Improvement candidate.

- **Resisted framing**: "Do not proceed with L1–L10 tweaks" implied L1–L10 were wasted work. They are not — L1 (tracked-file check), L3 (transcript safety), L7 (CLI friendly error) apply regardless of layout and are folded into DoD. The segregation pivot is additive.

## Amendments
None at draft.

## Confidence
0.88. Scope is structural but blast radius is bounded (no cognitive-layer touch, no data-layer touch, no agent-roster change). The judgment calls — PROGRESS.md split cut-line, templates vs generated files, backup posture — are all recoverable if wrong.

## Status Log
- 2026-04-24 — DRAFT opened after user request following Proposal 001 close. Triggered by portability question during 1A wrap-up.
- 2026-04-24 — Adversarial self-review produced L1–L10 loopholes; folded into proposal structure.
- 2026-04-24 — Gemini cross-model critique: five challenges returned (structural segregation, scattergun gitignore, PROGRESS.md contamination, onboarding as code, mock session).
- 2026-04-24 — Counter-analysis of Gemini returned: accepted segregation / governance rule / deterministic plumbing / pre-flight flow / rewrite-over-sibling. Resisted dual-repo mandate / mock session / stdin key prompt.
- 2026-04-24 — Gemini ack + pre-flight UX refinement absorbed. Rewrite adopted. Proposal renamed "Project Portability & Structural Segregation."
- 2026-04-25 — APPROVED → EXECUTING. All 11 artefact moves confirmed, templates created, init_workspace.py written and tested (idempotent, FRED detection verified). Grep-clean standard applied across all 44 files. PROGRESS.md → local/SESSIONS.md split complete (per-entry triage). SHARING.md, skill-config.yaml created. Proposal 001 audit: no personal leakage found (expected clean). All DoD items passed. Status: DONE.
