---
id: 029
title: Pre-push sanitisation remediation (24 range-diff collisions; squash-clean + pre-push hook)
status: APPROVED
owner: Daniel Campos
opened: 2026-06-10
updated: 2026-06-11
tags: [sanitisation, confidentiality, git-history, pre-push-hook, HEAVY, irreversible]
---

# 029 — Pre-push sanitisation remediation

**Tier: HEAVY** — confidentiality-critical. Evidence: >5 files; new mechanism (`range_added_text`, hook-type-aware `install_hook`, pre-push hook); two IRREVERSIBLE steps (history squash/force-rewrite + public push). Triggers full propose + alternative-architecture comparison + §4b Dual-Model Cross-Check + ranked L1–Ln adversarial pass.

> **Privacy posture (governs this whole artefact).** No investor-private value appears anywhere in this proposal, its DoD, the Delta Annexe, the Challenger dispatch, or any implementation-agent prompt. All triage/scrub is performed IN-SUBPROCESS; only redacted tuples / counts / "scrubbed N in <file>" cross the agent boundary. Synthetic fixture/doc values only (S-31). A Challenger or reviewer that opens a tracked test/fixture WILL see radioactive values — it is instructed never to quote a specific colliding value and to scrub any it surfaces.

---

## Summary

`main` is **31 commits ahead** of the PUBLIC `origin/main` (`github.com/dvscampos/quant-strategy-desk`; head `02a155c`, origin `6e263c7`). A pre-push mechanical sanitisation scan over the to-be-pushed range (`origin/main..main`) finds **24 distinct investor-private-ledger collisions** newly exposed by this push (record-level primitive; 1 ISIN, 2 tickers, 21 numeric; **0 history-only** — every match is present in the current tree). Push is BLOCKED until remediated. This proposal: (B) scrubs the real-economics collisions — test fixtures **rebuilt fully-synthetic** preserving the reconciliation invariants, prose occurrences scrubbed in-subprocess; (C) operator-batch-triages the identifiers + coincidental numerics (bias to scrub, allowlist only provably-public); (D) **squashes** the 31 unpushed commits to a clean history with a **local pre-rewrite archive**; (E) **future-proofs** with a pre-PUSH sanitisation hook (root-cause fix — the pre-commit hook only scans NEW commits, so the accumulated pre-hook history is what nearly published); then (F) verifies and pushes. The squash/rewrite and the push are DISTINCT explicit operator-approval gates.

## Motivation / Problem

- The S-30 pre-commit hook (`scripts/hooks/sanitisation_guard.py`, installed `.git/hooks/pre-commit -> ../../scripts/hooks/pre-commit`, **verified installed**) gates each NEW commit. It gated `02a155c` clean. But it has never scanned the **accumulated** pre-hook history — 30 of the 31 unpushed commits predate the hook. That accumulation is the leak surface a `git push` would publish.
- **Floor-audit result (this session, redacted, in-subprocess):** range-diff `origin/main..main` via the production `extract_private_literals` + `find_leaks` primitives = **24** record-level matches (1 ISIN, 2 tickers, 21 numeric), **0 history-only**, range-diff confirmed a subset of HEAD. The real-economics core (5–6 sig-fig cost-basis/NAV-class numerics) lands exactly in `tests/fixtures/portfolio_10col.md`, `tests/test_reconcile_ibkr.py`, `proposals/025`, `proposals/023`; the non-allowlisted ISIN lands in `proposals/026` + the fixture + the reconcile test. The bulk of the 4-sig-fig matches (13 of 24) spray across `backtesting/` session files, persona YAMLs, and `config/gates.yml` (+ its own consistency test) — the "likely-coincidental" class.
- **Baseline reconciliation (recorded for audit honesty).** Steering originally attested **29**. The operator's disposition (this session) is: 24 (range-diff = what THIS push newly exposes) is the correct push-gate scope; the earlier 29 was a broader-scope figure. I independently verified the operative numbers with the production primitive: **range-diff = 24** (gate scope) and **origin-tree already-public = 47** (out of scope, accept-as-public — confirmed exactly). I could NOT reproduce 29 to an exact primitive on my end (my HEAD-tree scan yields **60**, not 29); the "29 = HEAD-tree count" framing does not reproduce. This is immaterial — neither 29 nor 60 is any gate; the gate is the verified 24 range-diff. Recorded per external-claim-verification discipline rather than parroting an unverified figure.

## Verified tooling facts (re-verified this session — primary evidence, not memory)

- `find_leaks(records, added_text, allow)` consumes `added_text`; the only existing producer is `staged_added_text()` = `git diff --cached -U0` (verified at `sanitisation_guard.py:279`). **No range producer exists** → this proposal WRITES `range_added_text(<range>)` (added lines from `git log -p -U0 <range>`), itself privacy-bound (in-subprocess, returns text consumed in-process, surfaces no value). It serves THREE distinct ranges — all correct for the same one-helper design: (i) **FLOOR-AUDIT** reproduces the set over the PRE-squash `origin/main..main`; (ii) the **HARD GATE** scans the POST-squash to-be-pushed range, per-commit; (iii) the **pre-push hook** scans whatever range git hands it on stdin AND must catch a `git push --all/--tags` of the retained unsquashed archive.
- `install_hook()` (verified `init_workspace.py:91`) is HARDCODED to `pre-commit` (source filename, target name, all messages) AND has a "hook already exists; NOT overwriting" early-return (`:111-119`). The pre-PUSH hook needs `install_hook` made **hook-type-aware** AND the DoD asserts **installed-AND-OURS** (`target.resolve() == source.resolve()`), so a pre-existing foreign pre-push hook cannot silently no-op the future-proofing.
- `extract_private_literals` harvests from `local/**/*.md` ONLY (verified `:169`); the guard docstring declares bounded **fail-closed residuals** (`:14-23`): non-`.md` files (`.html`/`.env`), AND in-`.md` formats (space-separated numbers, scientific notation, ≤3-digit integers / ≤2-sig-fig decimals). So "scan == 0" means "0 collisions detectable via md-sourced, specific-enough literals" — NOT a total guarantee. **Untracked-files carve-out:** untracked economics (`docs/retros/*` per Proposal 005) are out of the push range BY CONSTRUCTION (`git push --all` does not publish untracked) — scanned-clean ≠ never-in-scope, stated so a reader can tell the difference.
- The S-30 allowlist (`config/sanitisation_allowlist.yml`) is a GLOBAL, un-file-scoped kill-switch with an in-band dual-use warning (verified): an allowlisted value is un-detected EVERYWHERE forever. Currently allows `IE000YYE6WK5` (ISIN) + `DFEN.DE` (ticker), both operator-accepted-public 2026-06-04. Bias HEAVILY to SCRUB; each allowlist addition is a deliberate operator yes/no.

## Pre-Flight Gate (per /propose Step 3)

1. **Factual-claim verification** — all line numbers/paths verified via direct Read this session: `sanitisation_guard.py:279` (`staged_added_text`), `:154/:169` (md-only harvest), `:14-23` (declared residuals), `init_workspace.py:91-126` (hardcoded `install_hook`), `reconcile_ibkr.py:244-389` (parse/fetch/patch invariants), allowlist contents read. Floor-audit 24/0-history-only reproduced via `/tmp/floor_audit.py` importing the production module. Baseline 116 passed / 1 skipped (live-smoke) verified via `pytest -q -rs`; reconcile suite 16 passed (ib_insync 0.9.86 present — gated tests RUN).
2. **Downstream-artefact grep** — the guard module is consumed by `scripts/hooks/pre-commit` (shim) + `init_workspace.install_hook` + `tests/test_sanitisation_guard.py`; adding `range_added_text` + a pre-push entry is additive (no signature change to `staged_added_text`/`find_leaks`/`main`) → no cascade to the pre-commit path. `install_hook` consumers: `init_workspace.main()` only → making it hook-type-aware with a defaulted parameter preserves the call. Cascade addressed in §6.
3. **Multi-surface walk** — multiple surfaces: guard module (new range/pre-push functions), `init_workspace` (hook-type param), pre-push shim (new), fixtures+test (synthetic rebuild), prose (scrub), history (squash). Walk outcome per surface enumerated in §Proposal and §6; the synthetic-rebuild and scrub surfaces are privacy-fenced (in-subprocess), the mechanism surfaces are agent-reviewable.

---

## Proposal

### Sub-problem table (DECOMPOSE)

| # | Sub-problem | Target scope | Type | Privacy fence | DoD anchor |
|---|---|---|---|---|---|
| 1 | `range_added_text` helper (3 ranges: floor-audit / hard-gate / pre-push) | `sanitisation_guard.py` | CREATE fn | in-subprocess; returns no value | DoD-1, DoD-3 |
| 2 | Rebuild test fixtures fully-synthetic, invariant-preserving | `tests/fixtures/portfolio_10col.md`, inline ledgers in `tests/test_reconcile_ibkr.py` | REBUILD | implementation-agent dogfoods vs hook; never learns colliding value | DoD-2, DoD-6 |
| 3 | Scrub real-economics prose occurrences in-subprocess | `proposals/023`, `proposals/025` (+ any prose hit surfaced) | SCRUB | in-subprocess; "scrubbed N in <file>" only | DoD-1 |
| 4 | Operator-batch triage: 1 ISIN + 2 tickers + coincidental numerics | per redacted triage rows | SCRUB or ALLOWLIST (operator yes/no) | redacted rows; value shown only at operator terminal on judgement | DoD-1, DoD-5 |
| 5 | Squash 31 unpushed commits → clean history + local pre-rewrite archive | git history (no tree files) | REWRITE | n/a | DoD-1, DoD-4 |
| 6 | Pre-push hook + hook-type-aware `install_hook` (installed-AND-OURS) | `scripts/hooks/pre-push` (new), `init_workspace.py` | CREATE + MODIFY | n/a | DoD-3 |
| 7 | Verify (per-commit 0 + suite green + both hooks ours) then PUSH | — | VERIFY + PUSH | n/a | DoD-1..6, §F |

`7 sub-problems: items 1–7 = 7 ✓`

### B — Scrub mechanisms (two distinct, by target)

- **Test fixtures (item 2)** — do NOT blind find-replace. **Rebuild** `tests/fixtures/portfolio_10col.md` and the inline ledgers in `tests/test_reconcile_ibkr.py` as fresh, fully-synthetic, internally-consistent ledgers. Synthetic values are PUBLIC → agent-reviewable, no privacy fence on the OUTPUT (the fence is on never reading the OLD radioactive values). Constraints: (1) **preserve the reconciliation invariants** the tests exercise — 10-column Holdings schema (ISIN col 1, qty col 4, price col 5, cost col 6, status col 9 per `reconcile_ibkr.py:256-271`), `cost = qty×price + commission`, `NAV = cash + invested` (`_patch_summary:327-328`), ISIN-anchored bare-ticker guard still triggers (`_fetch_live_prices:295`), Summary anchors present (`:356-362`), columns still sum; (2) **out-of-micro-NAV-range, distinctive, ≥3-sig-fig / >3-digit** values that sit ABOVE the guard's detection floor (S-31: low-info synthetics silently evade the guard, defeating the test's own protection); use a **fictional future year** for dates (per the 2026-06-10 anti-pattern entry); (3) chosen by **iterating against the hook (dogfood-as-oracle)** — the implementation-agent is fenced from `local/`, so it cannot pre-check a synthetic; on a hook BLOCK it learns only "collision" (redacted), picks another synthetic, retries (operator runs the hook; agent never learns the colliding value). Recompute all test-expected literals from the new inputs.
- **Prose/doc (item 3)** — `proposals/023`, `proposals/025` (and any further prose hit the triage surfaces) quote a real value. In-subprocess scrub of the quoted value to a synthetic/placeholder; the agent sees only "scrubbed N in <file>".

### C — Identifiers + coincidental (item 4)

The 1 non-allowlisted ISIN + 2 tickers + the coincidental numerics are surfaced as **redacted triage rows** (kind, private-source basename, sig-fig class, tracked-file list). Operator decides each: SCRUB (default, bias-to-scrub) or ALLOWLIST (only provably-public/coincidental — e.g. a common-ETF ISIN, or a 4-digit value that is demonstrably a `config/gates.yml` threshold colliding by chance). Each allowlist addition is a deliberate operator yes/no (global kill-switch; parsed-canonical, PIN 3). A value seen by the operator at the terminal is NEVER persisted to agent context.

### D — Clean history (item 5)

The 31 commits are UNPUBLISHED → free hand. **Squash** to a clean curated history (one or a few commits). The substantive audit trail survives in-tree (proposals/CHANGELOG/PROGRESS). **Before rewriting**, RETAIN the full granular pre-squash history on a LOCAL archive (branch `archive/pre-sanitisation-029` AND tag `archive/pre-029-02a155c`). DoD-4 verifies `git rev-parse <archive>` **== `02a155c`** (the pre-rewrite tip), not merely that it exists. `git-filter-repo` is the FALLBACK only if the operator later wants the exact 31-commit public history — it breaks every commit-SHA ref in the artefacts, needing a fixup pass; not chosen now.

### E — Future-proof: pre-push hook (item 6)

Add `scripts/hooks/pre-push` (shim → `sanitisation_guard.main_prepush`). `main_prepush` resolves the outgoing range(s) from the pre-push stdin protocol (`<local-ref> <local-sha> <remote-ref> <remote-sha>` lines; range = `remote-sha..local-sha`, or all-history for a new remote ref / `--all` / `--tags`), then runs `range_added_text` + `find_leaks` **per-commit** across each outgoing commit and BLOCKS on any collision. No-op gracefully (exit 0) when `local/` absent (cloner safety). Installed via the hook-type-aware `install_hook(hook_type="pre-push")`; DoD-3 asserts installed-AND-OURS. This ALSO protects the retained local archive — a `git push --all/--tags` of the leaky archive is scanned and BLOCKED.

### F — Verify then push (item 7)

Per-commit scan == 0 across the to-be-pushed range + full suite green + BOTH hooks installed-AND-OURS and gating clean + archive verified at `02a155c`. PUSH only on SEPARATE explicit operator approval (outward, irreversible). The squash/force-rewrite and the push are DISTINCT gates.

---

## 2. ARCHITECT

**Primary sub-problem: history cleaning (item 5).**

> **Approach A — Squash to a few curated commits + local archive.** Confidence **0.88**.
> Pros: simplest clean history; unpublished commits = zero downstream-SHA breakage on the public remote; substantive trail already lives in proposals/CHANGELOG/PROGRESS; local archive is a perfect rollback (`rev-parse == 02a155c`). Cons: loses granular public commit history (acceptable — never published); commit-SHA references inside artefacts (e.g. `02a155c`, `cd33a81`) become dangling on the public remote, but they remain valid in the local archive and the prose context survives.

> **Approach B — `git filter-repo` to scrub values across all 31 commits, preserving structure.** Confidence **0.55**.
> Pros: preserves the 31-commit shape for a reader who wants it. Cons: breaks EVERY commit-SHA ref in every artefact (proposals quote SHAs) → mandatory fixup pass across the whole repo; heavier, more error-prone; replaces values commit-by-commit (still needs the same scrub decisions); operationally fragile vs the unpublished free-hand squash.

> **Chosen: A** — operator-decided (confidentiality-first + future-proofed); the commits are unpublished so the squash is a free hand, and the local archive preserves the exact pre-rewrite history for any later filter-repo run (B stays the fallback). **Validated confidence 0.88** (post-floor-audit, post-tooling-verification).

**Secondary: fixture scrub (item 2) — synthetic rebuild vs blind find-replace.** Chosen **synthetic rebuild** (confidence 0.82): blind find-replace risks (a) leaving the value if a representation variant is missed, (b) producing a low-info synthetic that silently evades the guard (S-31), (c) breaking the cost/NAV/column invariants. Rebuild-from-invariants + dogfood-against-hook closes all three.

**Tertiary: pre-push range scanning — per-commit vs cumulative.** Chosen **per-commit** (confidence 0.9): DoD requires per-commit; a value introduced then removed within the range would be cumulative-clean but per-commit-caught, and `git push` publishes every commit object regardless of net diff.

---

## 3. SPECIFY — Definition of Done (verbatim floor)

1. **`range_added_text` + `find_leaks`, run per-commit across the entire to-be-pushed range, reads EXACTLY 0 collisions** (record-level count primitive; values never surfaced); the pre-remediation run reproduced the collision set first (re-baselined to **24** per the floor audit; the original "29" was a broader-scope figure — see §Motivation reconciliation).
2. **Full suite green BEFORE any commit.** Baseline established by running `pytest -q` and recording the number against a breakdown (the 1 skip is the live-smoke test `tests/test_live_smoke.py:23`; the ib_insync-gated reconcile tests must RUN, not skip — confirmed 16 passed, ib_insync 0.9.86). Rebuilt fixtures keep the suite green AND preserve the reconciliation invariants (DoD-6), not green-by-self-consistent-wrong-number. **Baseline: 116 passed, 1 skipped.**
3. **Both hooks installed-AND-OURS (resolve-target check) & exercised:** pre-commit AND the new pre-push each BLOCK a synthetic injected leak AND PASS the clean tree — with the guard demonstrably ACTIVE during the clean pass (records > 0; a no-op-on-absent-`local` guard passing everything does NOT satisfy this).
4. **The LOCAL archive of the pre-rewrite history exists AND `git rev-parse <archive>` == `02a155c`**, verified BEFORE the rewrite.
5. **Allowlist stays parsed-canonical (PIN 3);** each new entry operator-approved (auditable yes/no), never agent-self-authorised; the `.md`-only + in-`.md`-format + untracked residuals recorded in the push-safety claim.
6. **The rebuilt synthetic fixtures provably exercise the SAME reconciliation logic** — name which invariant is checked at which call site (helper-level vs the `update_portfolio` production entry-point) and demonstrate the cost/NAV invariants **through the production entry-point**, not only via helper asserts.

**Verifiable commands (run at verify gate):**
- `python3 -m pytest -q -rs` → `116 passed, 1 skipped` (or higher pass count if new tests added; only the live-smoke skip).
- Per-commit gate: a throwaway/driver over `git rev-list <to-be-pushed-range>` invoking `find_leaks(extract_private_literals(local), range_added_text(c^..c), allow)` → empty for every commit `c`.
- `git rev-parse archive/pre-029-02a155c` → `02a155c8723910e7a82c61a5ecc231d0a346b6d3`.
- `python3 -c "from pathlib import Path; ... resolve()-equality for .git/hooks/pre-commit and .git/hooks/pre-push"` → both True (installed-AND-OURS).

**DoD refinements (R2 Challenger absorptions — do not weaken the verbatim floor above):**
- **DoD-1 (L9/L10):** the per-commit scan is the AUTHORITATIVE gate for the cleaned history (the squash does NOT self-gate via the pre-commit hook — rebase/reset replay trees). `range_added_text` uses the same `+`-prefixed-non-`+++` extraction as `staged_added_text` (headers excluded); per-commit is strictly more conservative than the staged path.
- **DoD-3 (L14/L19):** `main_prepush` emits a greppable stderr `records=N`; "ACTIVE" = that line with N>0. `init_workspace.main()` installs BOTH hooks (`install_hook("pre-commit")` + `install_hook("pre-push")`).
- **DoD-6 (L18/L24/L25/L28):** at least one rebuilt fixture value is independently hand-/second-method-checked against its invariant (not only recomputed by the asserting code); AND an EQUATION-form assertion is ADDED through the `update_portfolio` production entry-point (`cost == qty*price+comm`, `cash == nav − invested`) — the suite today asserts cost only as a static helper literal and never asserts the NAV equation, so DoD-6 is otherwise unsatisfiable. The rebuild covers ALL economics literals in `tests/test_reconcile_ibkr.py` (ledger tables + positional dicts + `total_nav=` kwargs + summary + derived stop-loss columns), enumerated by a redacted in-subprocess grep.
- **Item-2 value-picking (L27):** the OPERATOR supplies a complete, internally-consistent synthetic value SET (out-of-micro-NAV-range, pre-checked non-colliding against the live ledger); the implementation-agent/script wires it in + recomputes derived literals. No fenced-agent guessing loop, no back-solve value display.
- **DoD-F (L12/L20):** the gating push runs with `local/` present + records>0 confirmed AT push time; `git push --no-verify` is PROHIBITED on the gating push; the manual per-commit scan is the authoritative gate (hook is forward protection, blind to `core.hooksPath`/`--no-verify`).
- **Blast-path (L31):** `local/PORTFOLIO.md` is named possible-blast-radius — every new/rebuilt test MUST monkeypatch `PORTFOLIO_PATH`; the dogfood runs `pytest` (monkeypatched), never a bare `update_portfolio` (which would mutate the live private ledger).

**Push-safety residuals (named, per L8/L12/L15/L16/L23/L29/L30 — "scanned clean" ≠ "provably zero private data"):** non-`.md` files (`.html`/`.env`), space-separated numbers, scientific notation, ≤3-digit integers, ≤2-sig-fig decimals, free-text PII, `.env` secrets (declared guard residuals); the **ISO-date-span carve-out** (L29 — a 4-digit value equal to a YYYY adjacent to a date pattern is suppressed; synthetic values avoid the bare calendar-year tokens that matched private values); **historically-divergent values** no longer in the current `local/` (L15, uncloseable — `local/` gitignored); **untracked files** (`docs/retros/*`) out of push scope by construction but reliant on staying untracked (L23); the **retained local archive** leakable via bundle/format-patch/mirror, deletable once the push is confirmed (L16); **foreign-pre-push clones** where install degrades to printed guidance (L30, forward-protection only).

---

## 4. MULTI-PERSONA REVIEW (inline — HEAVY, no persona-*.md files present)

Core Team A–D (+ F Compliance: confidentiality/regulatory-privacy surface). Inline roleplay per the Step-4 mode table (no `persona-*.md` files in repo — globbed, NONE).

### A — Quant Architect
**APPROVE WITH CONDITIONS.** The `range_added_text` one-helper-three-ranges design is clean and avoids duplication — good. Conditions: (1) per-commit driver must reuse `find_leaks`/`extract_private_literals` verbatim, not a re-implementation (the floor-audit `matched_records` re-impl was a throwaway; production must import). (2) `install_hook` parametrisation must keep the single call-site working with a default — no copy-paste of the whole function per hook type. (3) the pre-push shim must mirror the pre-commit shim's `sys.path.insert` + import pattern exactly. (4) magic strings (`"pre-push"`, archive ref names) declared as constants.

### B — Portfolio Manager
**APPROVE WITH CONDITIONS.** Minimum scope is right — this is the confidentiality blocker on the whole 31-commit push, so it earns HEAVY. Condition: do NOT let item 4 (coincidental triage) balloon — the 13 spray-pattern 4-sig-fig matches across `backtesting/` are almost certainly coincidental gate/session numbers; bias to allowlist-or-leave for those rather than scrubbing dozens of historical session files (which would itself churn history). Scrub effort concentrates on the real-economics core (fixtures + 023/025). Unwind in <24h: the local archive guarantees it.

### C — CTO
**APPROVE WITH CONDITIONS.** This is squarely my domain (secrets/git/push safety). Conditions: (1) the squash + force-push to the local archive vs the public remote must NEVER be conflated — the public push is a separate gate, and `--force` must target only the rewritten branch, never `--all` accidentally pushing the archive (the pre-push hook is the backstop, but operator discipline is primary). (2) pre-push hook MUST fail-CLOSED on a git error in range resolution (don't return "" → pass). (3) confirm `.git/hooks/pre-push` does not pre-exist as a foreign hook before install (installed-AND-OURS DoD covers this). (4) the throwaway floor-audit driver in `/tmp` must not be committed.

### D — Risk Officer
**APPROVE WITH CONDITIONS.** Blast radius of a wrong move here is a permanent public leak of investor economics — worst-case oriented, this is the right amount of process. Conditions: (1) DoD-4 archive-verify (`rev-parse == 02a155c`) MUST run BEFORE the rewrite, not after — a post-hoc archive of an already-rewritten tip is worthless. (2) the kill-switch (local archive) must be tested by actually checking out the archive ref after rewrite to confirm the old tree is recoverable. (3) no push without the separate explicit gate — the irreversibility is the whole risk.

### F — Compliance Officer
**APPROVE WITH CONDITIONS.** Investor-private financial data must not reach a public repo (data-protection posture). Condition: the push-safety claim must explicitly enumerate the bounded residuals the guard does NOT catch (non-`.md`, space-separated/scientific, sub-floor, ≤2-sig-fig, untracked) so "scanned clean" is not overclaimed as "provably zero private data." The 47 already-public origin collisions are operator-ruled accept-as-public (zero real-economics ≥5sf) — recorded, out of scope.

> **Orchestrator note:** Not unanimous-clean — five APPROVE-WITH-CONDITIONS, conditions folded into DoD/RISK FLAGS below. No Challenger auto-invoke needed on that basis; §4b runs regardless (HEAVY).

---

## 4b. DUAL-MODEL CROSS-CHECK

`Cross-Check path: isolated-challenger — reason: condition (a) — no external/alternate model API (Gemini/GPT) is configured in this environment.`

**Pre-dispatch attack-surface prediction** (cluster taxonomy): expect attacks on #2 scope/boundary (what "to-be-pushed range" means post-squash; archive in/out of push scope), #3 format/enumeration completeness (pre-push stdin protocol edge cases: new-ref, delete-ref, `--all`, `--tags`, zero-sha), #6 closure-mechanism (does per-commit scanning actually close the leak, or can a value hide in a merge/rename?), #7 DoD-recipe-rigour (per-commit driver explicitness; installed-AND-OURS recipe; archive-before-rewrite ordering), and the privacy-fence integrity (can the implementation-agent's dogf, or the Challenger itself, leak a value). Pre-hardened: DoD-3/4 ordering explicit, residuals enumerated, fail-closed stated.

**Challenger dispatch + Delta Annexe to follow** (R1→R3 on this same §1 DECOMPOSE / §6 FILES CHANGED; ship on `sound`, else R3 four-case disposition). The Challenger will be instructed NOT to quote any specific colliding value and to scrub any it surfaces.

## Adversarial loophole pass (L1–Ln) — seed (extended across Challenger rounds)

- **L1 — Archive becomes the leak vector.** The retained local archive holds the radioactive history; a `git push` that enumerates the archive ref (incl. `--all`/`--tags`) publishes it. **Closed by** the pre-push hook scanning EACH outgoing ref line on stdin (the archive ref, when pushed, resolves to full-history via the zero-`remote-sha` new-ref case — L11) + DoD-3 exercising a BLOCK. Residual non-push vectors (bundle/format-patch/mirror) named in L16; archive deletable once the push is confirmed stable.
- **L2 — Post-squash per-commit gate passes but cumulative misses a transient.** A value added+removed within the range is cumulative-clean. **Closed by** per-commit scanning (DoD-1) over `git rev-list`, not cumulative diff.
- **L3 — Synthetic fixture sits below the guard floor → silently evades.** A low-info synthetic (≤2-sig-fig) is undetectable, so the test loses its own protection. **Closed by** the ≥3-sig-fig / >3-digit out-of-range constraint + dogfood-against-hook (item 2).
- **L4 — `install_hook` foreign pre-push no-op.** A pre-existing foreign pre-push hook makes install silently skip → future-proofing inert. **Closed by** installed-AND-OURS DoD-3 (resolve-target equality), not mere existence.
- **L5 — Privacy-fence breach via implementation-agent or Challenger.** A sub-agent reads `local/` or quotes a radioactive tracked value. **Closed by** PIN-verbatim inlining + Read/Grep/Glob ban on `local/` (except `local/templates/`) in agent prompts; Challenger instructed never to quote, scrub any surfaced.
- **L6 — Archive verified AFTER rewrite (worthless).** **Closed by** DoD-4 ordering: `rev-parse == 02a155c` BEFORE rewrite.
- **L7 — Scrub breaks reconciliation invariant silently (green-by-wrong-number).** **Closed by** DoD-6: demonstrate cost/NAV invariants through the `update_portfolio` production entry-point, not only helper asserts.
- **L8 — Over-claim "scanned clean" = "zero private data."** **Closed by** the residuals enumeration in the push-safety claim (Compliance condition); extended by L15/L23 named residuals.
- **L9 — Squash bypasses pre-commit hook (no self-gate).** **Closed by** reframing: the manual DoD-1 per-commit `range_added_text` scan IS the authoritative gate; the hook never claimed to gate the rewrite (Read `pre-commit:1-11`).
- **L10 — Range primitive ≠ staged primitive.** **Closed by** verification: same `+`-line extraction excludes headers; per-commit strictly more conservative (Read `:294-296`). RESISTED-with-verification.
- **L11 — Pre-push stdin edge cases (delete/new-ref/force/`--all`).** **Closed by** the enumerated range-resolution spec: zero-`local-sha`→skip, zero-`remote-sha`→full-history, else `remote-sha..local-sha` per-commit; `--all`/`--tags` enumerate refs, not flags.
- **L12 — Push-time fail-open on absent/empty `local/`.** **Closed by** DoD-F push-time records>0 confirmation; RESISTED-in-part (absent-`local` = nothing private to leak, correct no-op).
- **L13 — Dogfood loop unbounded / structural collision.** **Closed by** operator-picks-out-of-range primary + hook-as-confirmation + max-5-retry escalation; invariant violation caught by DoD-6.
- **L14 — DoD-3 "ACTIVE" unobservable.** **Closed by** `main_prepush` emitting greppable stderr `records=N` (N>0).
- **L15 — Records from current `local/` only (historical-divergence escape).** **NAMED RESIDUAL** (uncloseable — gitignored, no history); mitigated by wholesale rebuild/scrub of the real-economics core.
- **L16 — Archive leaks via bundle/format-patch/mirror.** **NAMED RESIDUAL**; mitigated by archive-deletable-after-confirm.
- **L17 — Operator-terminal value re-enters agent context.** **Closed by** index-based triage (decide by index; allowlist-write reads value by index in-subprocess, never prints it).
- **L18 — Green-by-self-consistent-wrong recompute.** **Closed by** DoD-6 independent hand-/second-method check of ≥1 rebuilt fixture value.
- **L19 — `install_hook` refactor drops pre-commit install.** **Closed by** `main()` calling both `install_hook("pre-commit")` + `install_hook("pre-push")`; default preserved.
- **L20 — OURS check blind to `core.hooksPath`/`--no-verify`.** **Closed by** manual DoD-1 scan as authoritative gate + `--no-verify` prohibited on the gating push.
- **L21 — "md-only" omits tracked-skip.** **Closed by** wording correction (untracked `.md` only).
- **L22 — filter-repo fallback trigger unstated.** **Closed by** stated trigger (operator wants exact history OR pre-origin leak).
- **L23 — `docs/retros/` exclusion unenforced.** **NAMED RESIDUAL** (relies on staying untracked; pre-commit catches an accidental add of a current value).
- **L24 — DoD-6 unsatisfiable as suite structured (cost=static-literal helper assert; NAV never an equation).** **Closed by** DoD-6 mandating an EQUATION-form assertion through `update_portfolio`.
- **L25 — Rebuild scope under-enumerated (literals in positional dicts / `total_nav=` kwargs / derived columns, not only ledger tables).** **Closed by** broadening item-2/§6 to ALL economics literals, enumerated by redacted in-subprocess grep.
- **L26 — Per-commit rationale vacuous at the squashed gate.** **Closed by** re-attributing per-commit value to the forward pre-push hook; the one-squashed-commit full-diff scan is the sound gate.
- **L27 — Operator-picks / agent-rebuilds hand-off seam (retry loop + back-solve display).** **Closed by** operator supplying a complete consistent synthetic value SET; no fenced-agent guessing, no back-solve display.
- **L28 — Stop-loss derived literal outside named invariant set.** **Closed by** L25 broadening (derived columns regenerated from synthetic entry price).
- **L29 — ISO-date-span carve-out fail-open undisclosed.** **NAMED RESIDUAL**; synthetic values avoid colliding with bare calendar-year tokens that match private 4-digit values.
- **L30 — Foreign pre-push hook → install degrades to guidance on other clones.** **NAMED RESIDUAL** (forward-protection); DoD-3 confirms OURS on the operator machine.
- **L31 — `local/PORTFOLIO.md` destructive blast path via stray non-monkeypatched `update_portfolio`.** **Closed by** naming the blast path + monkeypatch mandate + dogfood-runs-pytest.
- **L32 — §6 count understates the known-now literal cohort.** **Closed by** the test-file literal cohort being in the named §6 set; "may add" applies only to other-file triage prose.

---

## 5. RISK FLAGS

- **IRREVERSIBLE ×2:** (a) history squash/force-rewrite of `main`; (b) public push to `origin`. Each is a SEPARATE explicit operator-approval gate. Mitigation: local archive (`rev-parse == 02a155c`) is the rollback for (a); (b) is gated on per-commit-0 + suite-green + both-hooks-ours.
- **Radioactive evidence:** tracked test/fixture files carry the colliding values. Any reviewer/Challenger reading them must not quote a value. Mitigation: explicit instruction + scrub-on-surface.
- **WIDE blast radius:** `sanitisation_guard.py` is consumed by the pre-commit shim + `install_hook` + tests; changes are additive (no signature change to existing producers/consumers) → effective MODERATE.
- **Out of scope (do NOT fold in):** the 47 already-public origin collisions (operator-ruled accept-as-public; zero real-economics ≥5sf); S-24/S-25/S-29 tooling; S-21 live-snapshot (follows AFTER the clean push); S-31/S-32 follow-ups. No published-history rewrite.
- **Force-push hazard:** `--force` must target only the rewritten branch; never `git push --all`. Pre-push hook is the backstop; operator discipline primary.
- **Live-ledger blast path (L31):** `update_portfolio` writes `local/PORTFOLIO.md` when not monkeypatched; the rebuild/dogfood loop runs the suite repeatedly. Mitigation: every test monkeypatches `PORTFOLIO_PATH`; dogfood runs `pytest`, never a bare `update_portfolio`.
- **Adversarial review is a confirmed leak vector (this proposal):** the R2 Challenger quoted radioactive values despite instruction. Mitigation: values scrubbed at the boundary, not persisted; further Challenger rounds against the radioactive files weighed against their marginal value (operator-arbitrated).

## 6. FILES CHANGED (PROPOSED)

- `CREATE` `proposals/029-pre-push-sanitisation-remediation.md` — this proposal (self-admin).
- `MODIFY` `proposals/README.md` — index row (self-admin).
- `MODIFY` `scripts/hooks/sanitisation_guard.py` — add `range_added_text(range)`, `main_prepush()` (range resolution from pre-push stdin + per-commit `find_leaks`); no change to `staged_added_text`/`find_leaks`/`main`.
- `CREATE` `scripts/hooks/pre-push` — shim → `sanitisation_guard.main_prepush` (mirrors the pre-commit shim).
- `MODIFY` `scripts/init_workspace.py` — make `install_hook(hook_type="pre-commit")` hook-type-aware (source `scripts/hooks/<hook_type>`, target name, messages); install both hooks in `main()`.
- `MODIFY` `tests/fixtures/portfolio_10col.md` — REBUILD fully-synthetic, invariant-preserving (in-subprocess; dogfooded).
- `MODIFY` `tests/test_reconcile_ibkr.py` — REBUILD inline ledgers synthetic + recompute expected literals (in-subprocess).
- `MODIFY` `tests/test_sanitisation_guard.py` — add tests: `range_added_text` (per-commit), `main_prepush` BLOCK/PASS, hook-type-aware `install_hook` installed-AND-OURS.
- `MODIFY` `proposals/023-s22-http-cache-ttl.md` — scrub quoted real-economics (in-subprocess).
- `MODIFY` `proposals/025-reconcile-column-index-foundation-fix.md` — scrub quoted real-economics (in-subprocess).
- `MODIFY` `config/sanitisation_allowlist.yml` — ONLY for operator-approved provably-public identifiers/coincidentals (item 4); may be no-op if all scrubbed.
- `MODIFY` `proposals/026-s23-isin-anchored-pricing.md` — CONDITIONAL: scrub the non-allowlisted ISIN if operator rules scrub (else allowlist, no file edit).
- `MODIFY` (in-subprocess, operator-triaged) any further prose file surfaced by item-4 triage — enumerated at triage time, each a redacted row.
- `MODIFY` `docs/retros/` (untracked BY DESIGN — `/retro` only; NOT committed) and `PROGRESS.md` + `CHANGELOG.md` (at `/commemorate`, self-admin).

`Core mechanism + scrub files (excluding /commemorate self-admin): 029 + README + guard + pre-push + init_workspace + fixture + reconcile-test + guard-test + 023 + 025 + allowlist + 026(cond) = up to 12 CREATE/MODIFY. CREATE: 029, pre-push = 2. MODIFY: README, guard, init_workspace, fixture, reconcile-test, guard-test, 023, 025, allowlist, 026 = up to 10. Total ≤ 12 ✓` (item-4 triage may add further prose MODIFYs, each operator-approved + enumerated at triage — flagged not hidden.)

## 7. REVERSIBILITY

- Items 1–3, 6 (guard fns, pre-push shim, install_hook, fixtures, prose scrub, tests, allowlist): **FULLY REVERSIBLE** (`git revert` / local).
- Item 5 (squash/force-rewrite): **PARTIALLY REVERSIBLE** — restored from the local archive (`archive/pre-029-02a155c`); manual `git reset --hard <archive>`.
- Item 7 (public push): **IRREVERSIBLE** — once `origin` receives the objects, they may be cached/indexed even if later force-removed. THE gate.

## Scope & Out-of-Scope

**In:** the 24 range-diff collisions (scrub real / triage identifiers+coincidental) + squash-clean + local archive + pre-push hook + verify. **Out:** the 47 already-public origin collisions (accept-as-public); S-21/S-24/S-25/S-29/S-31/S-32; any published-history rewrite; the push itself is gated separately (not auto-executed on approval of this proposal).

## Risks & Mitigations
See §5. Primary mitigations: local archive (rollback), per-commit gate (leak detection), separate push gate (irreversibility containment), privacy-fence PINs (no value to agent context).

## Core Team Review (A–D)
See §4 (A–D + F), inline.

## Delta Annexe — Round 1 (Core Team)
- **Absorbed:** A1–A4 (import-verbatim, default-param, shim-mirror, constants) → §2/§6; B (don't balloon item-4; concentrate on real-economics core) → §C/§5; C1–C4 (force-push discipline, fail-closed, foreign-hook check, no-commit /tmp driver) → §5/DoD-3; D1–D3 (archive-before-rewrite, test recovery, separate push gate) → DoD-4/§5; F (residuals enumeration) → push-safety claim/L8.
- **Resisted:** none at R1.

## Delta Annexe — Round 2 (Isolated Challenger Cross-Check)

**Path:** isolated-challenger (reason a — no external model API). **R1 verdict: flawed** (L9–L23; 4 structural L9/L10/L11/L12). **Absorption character: every item below is scope-NARROWING or scope-CORRECTING (G15-safe) — no new file or mechanism added; range_added_text / pre-push hook / install_hook specs are tightened, not expanded.** Each entry cites an independent verification.

- **L9 — ABSORBED (correct).** Squash via rebase/reset does NOT fire `pre-commit` (replayed trees aren't `git commit`s). *Verified:* Read `scripts/hooks/pre-commit:1-11` — pre-commit-only shim, no `post-rewrite`/rebase coverage. Framing corrected: the **authoritative gate for the cleaned history is the manual DoD-1 per-commit `range_added_text` scan**, not hook self-gating. DoD-1 reworded; the "self-gate" claim removed (see DoD refinements).
- **L10 — RESISTED (verified) + minor absorb.** `range_added_text` extracts only `+`-prefixed-non-`+++` lines (identical to `staged_added_text:294-296`), so `commit`/`@@`/`+++` headers are NOT match substrate; per-commit scanning is strictly MORE conservative than the staged path (a transient appears as an added line when introduced → detected). *Verified:* Read `sanitisation_guard.py:294-296` + the floor-audit driver reproduced sensible counts with this exact extraction. Added a DoD-1 note stating the equivalence and the same `+`-line extraction.
- **L11 — ABSORBED (correct/narrow).** Pre-push stdin range resolution tightened to enumerate every case: per stdin line `<local-ref> <local-sha> <remote-ref> <remote-sha>` — (a) `local-sha == 0{40}` (branch delete) → SKIP (nothing pushed); (b) `remote-sha == 0{40}` (new ref / never-pushed archive) → scan FULL history `git rev-list <local-sha>`; (c) otherwise scan `remote-sha..local-sha` per-commit. `--all`/`--tags` are NOT flags visible to the hook — git enumerates each ref as its own stdin line, so the archive ref is scanned via case (b) when pushed. L1's closure wording corrected accordingly. *Verified:* git pre-push hook protocol (refs on stdin, zero-sha sentinels) — standard, cited in the spec.
- **L12 — ABSORBED (correct) + RESISTED (part).** *Resisted:* a checkout without `local/` has no private ledger → nothing to leak → no-op is correct-by-construction (not a fail-open). *Absorbed:* the gating-push risk is the operator's own machine where `local/` IS present; DoD-F now requires a **push-time** records>0 confirmation (not only test-time DoD-3). *Verified:* Read `sanitisation_guard.py:360-384` (no-op on absent-`local`/empty-records).
- **L13 — ABSORBED (narrow).** Dogfood loop given a termination bound: the **operator (unfenced, sees `local/`) picks out-of-micro-NAV-range synthetic values directly** (e.g. NAV/price magnitudes trivially above a micro-NAV ledger); the hook is the CONFIRMATION oracle, not the primary picker. Max 5 retries then escalate to operator; an invariant-violating synthetic is caught by DoD-6 (full suite). *Verified:* design-level; no tool claim.
- **L14 — ABSORBED (correct).** `main_prepush()` MUST emit a stderr diagnostic `records=N` (N>0 when active); DoD-3's "demonstrably ACTIVE" observable is now that line (greppable), mirroring `main`'s stderr status. *Verified:* Read `sanitisation_guard.py:379-384` (stderr-only active/inactive distinction today).
- **L15 — ABSORBED (named residual).** Records are harvested from the CURRENT `local/`; a private value present in a tracked diff historically but since edited out of `local/` is not in today's records and escapes the scan. *Verified:* Read `extract_private_literals:154-240` (harvests current `local/**/*.md`). The 24 is conditioned on the present ledger. Mitigant: the real-economics core (fixtures + 023/025/026) is REBUILT/SCRUBBED wholesale (not record-match-dependent). Added to the push-safety residuals as a named bound (uncloseable by construction — `local/` is gitignored, no state history).
- **L16 — ABSORBED (narrow).** The retained archive is a leak vector via `git bundle`/`format-patch`/mirror-to-second-remote — paths the pre-push hook does not cover. Named as a residual; mitigant: the archive exists ONLY as the squash rollback — **once the public push is confirmed stable the operator MAY delete the archive** (de-loads the gun); until then it is local-only. *Verified:* design-level; pre-push fires only on `git push` to a configured remote (L11 spec).
- **L17 — ABSORBED (correct, fence-tightening).** In a Claude Code session the "operator terminal" IS often the agent's stdout → a rendered value re-enters context. Triage redesigned **index-based**: the triage script emits redacted rows with an INDEX; the operator decides scrub/allowlist by index; for ALLOWLIST, an in-subprocess script reads the value BY INDEX from `local/` and writes it to the allowlist WITHOUT printing it. The value is never rendered to terminal/agent context. *Verified:* `find_leaks` returns `(kind, source)` only (Read `:302-357`) — no value; the new gap was the human-decision display, now closed by index-indirection.
- **L18 — ABSORBED (tighten DoD-6).** DoD-6 now requires at least one rebuilt fixture value **independently hand-/second-method-checked** against its invariant, not only recomputed by the same code the test asserts (guards self-consistent-wrong recompute). *Verified:* design-level.
- **L19 — ABSORBED (spec coverage).** `install_hook(hook_type="pre-commit")` keeps the default; `main()` now calls it TWICE — `install_hook("pre-commit")` AND `install_hook("pre-push")`. §6 + DoD-3 updated. *Verified:* Read `init_workspace.py:91-125,134` (bare single call today).
- **L20 — ABSORBED (correct).** `installed-AND-OURS` cannot detect `core.hooksPath` redirect or `git push --no-verify`. Reframed: the AUTHORITATIVE gate for the remediation push is the manual DoD-1 per-commit scan run immediately pre-push by the orchestrator; the pre-push hook is FORWARD protection. `--no-verify` is PROHIBITED on the gating push (DoD-F). *Verified:* Read `init_workspace.py:111-119` (symlink-target equality only).
- **L21 — ABSORBED (craft).** Wording corrected: the guard harvests UNTRACKED `.md` under `local/` (tracked `local/templates/*` are skipped). *Verified:* Read `:166-173` (`path.resolve() in tracked` skip).
- **L22 — ABSORBED (craft).** filter-repo fallback trigger stated: invoked only if the operator later wants the exact 31-commit public history, OR a leak is found to predate `origin/main` requiring in-place historical scrub. *Verified:* design-level.
- **L23 — ABSORBED (named residual).** `docs/retros/* out-of-push-scope` is an assumption about gitignore state, not an enforced invariant. Named as a residual dependency (relies on `docs/retros/` staying untracked per Proposal 005); a future accidental `git add docs/retros/` is outside THIS proposal's range-gate but WOULD be caught at add-time by the pre-commit hook if it carried a current private value. *Verified:* MEMORY [[project-retros-untracked]] + pre-commit scans staged diff.

**Resisted in full:** none. **Resisted in part:** L10 (substrate concern refuted; equivalence note added), L12 (absent-`local` no-op is correct, not a vuln).

## Delta Annexe — Round 3 (R2 Isolated Challenger)

**R2 verdict: flawed** (L24–L32; 2 structural L24/L25). R1 closures L9–L23 verified to HOLD (no re-raises). L-count trajectory 15 (R1) → 9 (R2), decreasing. All R2 items absorbed as scope-NARROWING/CORRECTING (no new file/mechanism). **PRIVACY EVENT:** the R2 Challenger violated the never-quote instruction and surfaced ~6 specific colliding values into context; per the radioactive-evidence rule those values are NOT carried into this artefact — absorptions below reference test SITES and FIELDS only, never values. This validates the fence and is logged as forward-evidence that adversarial review is itself a leak vector for this proposal.

- **L24 — ABSORBED (correct, DoD-fix).** DoD-6 is unsatisfiable as the suite is structured: the `cost = qty×price+comm` invariant is asserted as a STATIC literal in a helper test (`test_parse_open_holdings_10col`), and `NAV = cash+invested` is NEVER asserted as an equation. *Verified:* Read `tests/test_reconcile_ibkr.py` (cost asserted as a helper static-literal equality; NAV only checked for a `%)`-suffix presence). Closure: DoD-6 now MANDATES adding an EQUATION-form assertion through the `update_portfolio` production entry-point (`cost == qty*price+comm` and `cash == nav − invested` recomputed independently), so green cannot mean self-consistent-wrong. Within the already-listed `tests/test_reconcile_ibkr.py` MODIFY.
- **L25 — ABSORBED (correct, scope-accuracy).** The radioactive literals span MORE sites than "inline ledgers": positional-dict positions and `total_nav=` kwargs across the S-28 tests, plus summary literals — not all inside ledger tables. *Verified:* Grep of the high-sig-fig literal class in `tests/test_reconcile_ibkr.py` (multiple occurrences across ≥6 enclosing functions; redacted). Closure: item-2/§6 rebuild scope broadened to ALL economics literals in the file (ledger tables + positional dicts + `total_nav=` kwargs + summary + derived columns), enumerated by a redacted in-subprocess grep at implementation time — not only "ledgers."
- **L26 — ABSORBED (correct rationale).** After the squash the to-be-pushed range is ~1 commit, so "per-commit" at the GATING push == a cumulative full-diff scan of the one squashed commit (sound, but per-commit adds no transient-hiding protection THERE). Per-commit is load-bearing for the FORWARD pre-push hook (an unsquashed `--all` push of the archive, L11 case b). ARCHITECT 0.9 rationale re-attributed accordingly; the gate itself is unaffected.
- **L27 — ABSORBED (re-architect item-2 hand-off, narrowing).** The two-actor split (fenced agent rebuilds; operator picks values) muddled the retry loop and risked a back-solve display re-opening L17. Closure: the OPERATOR (unfenced, sees `local/`) supplies a COMPLETE, internally-consistent synthetic value SET (per-position qty/price/comm + per-section NAV, pre-checked out-of-range and invariant-consistent against the live ledger); the implementation-agent/script wires the set in and recomputes derived test literals — NO fenced-agent guessing loop, NO back-solve display. The hook is the final confirmation oracle. Removes the seam entirely.
- **L28 — ABSORBED (folds into L25).** The fixture's stop-loss column carries a derived price-level literal (5-sig-fig, real-economics class) not covered by the named-invariant set. Closure: the L25 "ALL economics literals" broadening explicitly includes derived columns (stop-loss level regenerated consistently from the synthetic entry price).
- **L29 — ABSORBED (named residual).** `find_leaks` suppresses a numeric match sitting ENTIRELY inside a diff-side ISO-date span (guard `:320-345`); a 4-digit private value equal to a YYYY adjacent to a date pattern could be carved out. *Verified:* Read `sanitisation_guard.py:320-345`. Closure: named in the push-safety residuals; synthetic value choice avoids economics values colliding with the bare calendar-year tokens (a fictional future year and a calendar year that both matched private 4-digit values).
- **L30 — ABSORBED (named residual).** `install_hook`'s "already exists; NOT overwriting" branch means a clone with a FOREIGN pre-push hook (git-lfs/husky/pre-commit-framework) gets printed guidance, not an install → forward-protection degrades to guidance on those clones. *Verified:* Read `init_workspace.py:111-119`. Closure: DoD-3 confirms installed-AND-OURS on the OPERATOR machine (the gating push); for other cloners it is named as a forward-protection residual (consistent with L4/L20 hook-non-authoritative concession); the hook-type-aware print emits actionable `ln -sf` guidance for pre-push too.
- **L31 — ABSORBED (blast-path naming, important).** `update_portfolio` writes to `PORTFOLIO_PATH = local/PORTFOLIO.md` (the LIVE ledger) when not monkeypatched; the dogfood/test loop runs the suite repeatedly → a stray non-monkeypatched call would MUTATE the operator's real private ledger. *Verified:* Grep `PORTFOLIO_PATH` in `reconcile_ibkr.py` (incl. `write_text`). Closure: `local/PORTFOLIO.md` named as possible-blast-radius in §5; mandate every new/rebuilt test monkeypatch `PORTFOLIO_PATH`; the dogfood runs `pytest` (monkeypatched), never a bare `update_portfolio`.
- **L32 — ABSORBED (craft, §6 framing).** The inline-literal rebuild cohort is known-now (per L25), not a triage-time discovery; §6's "may add prose MODIFYs ≤12" understated it. Closure: the `tests/test_reconcile_ibkr.py` literal cohort is in the named §6 set (it already lists that file MODIFY); the "may add" clause applies ONLY to triage-surfaced prose in OTHER files.

**Resisted:** none at R2. **Disposition:** R2-flawed with 2 structural (both DoD-correcting). Per the R3 four-case discipline, flawed-with-structural escalates to the operator with the amended draft — NOT auto-run to R3, because (a) both structural items are scope-correcting (now absorbed), (b) the L-trajectory is decreasing, and (c) each further Challenger round re-incurs the confirmed value-leak against the radioactive files. Operator arbitrates ship-vs-R3.

## Amendments
*(none yet)*

## Item-4 carry-forward (for the fresh irreversible-phase session)

Gate-scope residual after items 2–3 scrub = **18 distinct colliding values** (working tree vs `origin/main`; 1 ISIN, 2 tickers, 15 numerics). Distinct-value count is date-excluded-accurate; per-file site lists are approximate (date-coincidence noise). The hard gate (`find_leaks==0` over the range) is met only once every row below is cleared. **Recommendation: SCRUB the 026 ISIN (no blind-spot, consistent with the fixture/test scrub → `IE00TEST0009`); ALLOWLIST the other 17** (2 public-ETF tickers + 15 coincidental/public-macro numerics) → **+17 dual-use blind-spots** (19 total with the existing 2) to record in the push-safety claim. S-31 (guard precision) is the long-term reducer.

| Token | Kind | sf | Range-diff sites | Nature | Recommendation |
|---|---|---|---|---|---|
| ISIN1 | ISIN | — | prop/026 | Real holding ISIN (= the one scrubbed to `IE00TEST0009` in fixture/test) | **SCRUB** (operator to confirm vs allowlist) |
| TKR1 | ticker | — | prop/009, prop/026 | Held ticker (public common ETF) | ALLOWLIST (operator may rule scrub) |
| TKR2 | ticker | — | prop/009 | Ticker in eval results | ALLOWLIST |
| N1 | num | 4 | CHANGELOG, PROGRESS, 5 personas… (ubiquitous) | Framework/eval number, not a datum | ALLOWLIST |
| N2, N4 | num | 4 | personas + props 009/010/016/017 | Persona-eval coincidental | ALLOWLIST |
| N3 | num | 4 | personas + point72 backup | Coincidental | ALLOWLIST |
| N5–N8, N11, N14 | num | 3–4 | props 016/018/022/027, CHANGELOG | Coincidental technical | ALLOWLIST |
| N9, N10, N12, N13, N15 | num | 4–5 | **prop/023 only** | **Public macro (VIX/EUR-USD) + line-number artefact** (verified) | ALLOWLIST |

Open operator decisions for the fresh session: (1) 026 ISIN scrub-vs-allowlist; (2) held-ticker consistency call (scrubbed-in-tests vs allowlisted-in-docs); (3) confirm the batch-allowlist of the coincidental/public set. Then: reach `find_leaks==0` over the range → squash + local archive (separate gate) → push (separate gate).

## Item-4 Execution Plan + Delta Annexe (session 2026-06-11b)

**Tier: MEDIUM** (2 tracked files: allowlist-add + `proposals/026` prose scrub; within established 026/027 patterns; confidentiality-critical; NO irreversible step this session — the commit is reversible, push deferred to PHASE-5). Cross-Check path declared `isolated-challenger — reason: condition (a)` (no external model API). One Challenger round (R1) run on the redacted plan with never-quote scoping; the Challenger read only `sanitisation_guard.py` + the allowlist (no radioactive files), and quoted **no** value — the fence held.

### Cold-derived residual (this session, production primitive)
Net-tree (`origin/main`..HEAD) leaks **20 distinct records** (2 ISIN, 2 ticker, 16 numeric). Reconciles exactly to the steering expectation: 20 − 2 synthetic self-FPs = **18 real residual** (1 real ISIN, 2 tickers, 15 numerics). Self-FP sources verified = the gitignored steering arc log (not a real ledger). Range-diff aggregate = 26 (over-approximation; NOT the acceptance surface).

### Acceptance surface (L9 absorption)
ACCEPTANCE = **net-tree `find_leaks==0`** (`git diff -U0 origin/main`, +lines). This is provably identical to the post-squash **single-commit** `main_prepush` scan (a squash to one commit with parent=origin/main, tree=HEAD makes `git show -U0 C` == `git diff origin/main HEAD`). Net-tree==0 is the item-4 MILESTONE and is NECESSARY-NOT-SUFFICIENT for the push (the per-commit/push gate clears only post-squash, PHASE-5). **Forward note:** if PHASE-5 squashes to >1 commit, each commit must independently scan clean (stricter); recommend a single-commit squash so net-tree==0 is sufficient.

### STEERING CORRECTION — source-driven axis SUPERSEDES sig-fig (the sig-fig basis was UNSAFE)
Steering re-verified on disk that the "real economics ≥5sf / ≤4sf coincidental" premise is FALSE: there are real-ledger economics at sf 3–4 that sig-fig would have wrongly batch-allowlisted, and meta-log self-poisoning inflated the count with non-confidentiality noise. Re-triaged by **HARVEST SOURCE** (which `local/` files contain each value), production-`find_leaks` membership, precedence A>C>B. Cold re-derivation matched the steering head-start exactly: **A=6 real-ledger / B=4 meta-only / C=10 other-brainstorm** (20 net-tree records).

### Per-record triage — source-driven (denominator = 20 net-tree-leaking records; L18)
| Bucket | Records | Action | Basis |
|---|---|---|---|
| A real-ledger SCRUB | rec 0 (ISIN→`026`), rec 3 (IBKR commission→`016`/`018` prose), rec 13 (contribution + dummy-NAV→`022`/`026` prose) | **SCRUB** (genericise per S-31) | real economics / real holding ISIN — confidentiality-max; rec 3/13 were concrete economics-shaped numbers IN TRACKED PROSE (real leaks, NOT coincidental — sig-fig would have wrongly allowlisted) |
| A real-ledger ALLOWLIST | rec 1 (TKR1 held ETF), rec 2 (micro-NAV threshold), rec 4 (calendar year) | **ALLOWLIST** | publicly-corroborated metadata / public framework constant / date artefact |
| B meta-only CLEAN-LOG | rec 10 (synth ISIN), 11, 12 (synth numeric), 19 (macro echo) | **CLEAN-THE-LOG** (descriptive ref in gitignored `*steering*` logs) | NOT confidentiality residuals — steering-log self-poisoning; clean-the-source → NO allowlist blind-spot. Each matched exactly 1× per log (surgical). Post-clean: all 4 keys gone from harvest, `IE00TEST0009` no longer harvested (so no fallback allowlist needed) |
| C other-brainstorm ALLOWLIST | rec 5 (TKR2), 6 (IBKR port), 7,8,15,16 (VIX/EUR-USD macro), 9,14,17 (year/vintage), 18 (flag coincidental) | **ALLOWLIST** (condition B) | public macro / public config / coincidental framework — value-free-confirmed not economics (sf5 members 8/16/19 = EUR/USD-class, 023-sited, #36d) |

**Totals (executed):** 3 SCRUB + 13 ALLOWLIST + 4 CLEAN-LOG = 20 records handled. New allowlist entries: tickers +2 (`VWCE.DE`, `DFNS.PA`), values +11. **Dual-use blind-spots: 13 new + 2 existing = 15** (down from the superseded sig-fig plan's 21 — the source axis SCRUBbed 2 real prose leaks the sig-fig plan would have allowlisted, and CLEANed 4 meta-noise records rather than allowlisting them). Banked durable fix: **S-31 should exclude `local/brainstorms/*steering*` + operational scratch from `extract_private_literals`** (the self-poisoning root cause).

### Write mechanism (radioactive-work rule: orchestrator-controlled in-subprocess, no sub-agent)
A single in-subprocess script re-derives records, classifies by stable criteria (kind + per-tracked-file `find_leaks` site set over ALL changed files — L19; not the `(kind,source)` dedup), and writes each classified record's `key` **directly** into the allowlist YAML (no index step → no off-by-one). The 026 scrub is in-subprocess. **All changes land in ONE atomic commit** (L14) so the allowlist entry for `IE00TEST0009` is present before the pre-commit hook scans the staged 026 scrub. Values never printed. Post-write verification (in-subprocess): (a) every targeted record suppressed, (b) no other record newly leaks, (c) written tokens' kind/sig-fig match intended rows — PLUS the **classification-correctness gate**: operator reviews `git diff config/sanitisation_allowlist.yml` confirming exactly the expected new rows of expected kind before commit (L10/L16; the self-checks verify suppression completeness, not classification).

### Delta Annexe — Challenger R1 (verdict: flawed; L9–L19; 3 structural L9/L10/L11). All absorbed scope-NARROWING/CORRECTING (G15-safe — no new file/mechanism).
- **L9 — ABSORBED (correct).** Acceptance tightened to net-tree (= post-squash single-commit scan); subset proof stated; multi-commit caveat forward to PHASE-5. *Verified: squash construction + `main_prepush` per-commit `git show -U0` at `sanitisation_guard.py:541-560`.*
- **L10 — ABSORBED (reframe).** Self-checks (a/b/c) = suppression-completeness; classification-correctness gated by operator affirmation + allowlist git-diff review. No-index write removes the off-by-one. *Verified: allowlist `continue` at `:350-355`.*
- **L11 — ESCALATED (not self-authorised).** Batch-allowlist of the 10 ≤4sf spray presented as explicit operator decision; affirmative basis = sig-fig structure (economics ≥5sf) + per-row affirmation + named blind-spots. *Verified: `_MIN_SIG_FIGS=3` floor `:40-43`; global suppression `:354`.*
- **L12 — ABSORBED (named residual).** ISO-date carve-out fail-open (4-digit YYYY-position value) added to push-safety residuals (carries 029 L29). *Verified: `:334-342,363-367` + docstring concession.*
- **L13 — ABSORBED (narrow).** Allowlist BOTH synthetics (auditable, records blind-spot); descriptive-edit dropped (corpus-shrink, no audit trail, fragile). *Verified: harvest reads untracked `local/*.md` `:169-173`.*
- **L14 — ABSORBED (ordering).** Single atomic commit; allowlist entry present before pre-commit scan of the staged scrub. *Verified: pre-commit scans staged diff `staged_added_text:279`.*
- **L15 — DISSOLVED.** Step-5a/5b coupling removed by dropping the steering-log edit (L13).
- **L16 — ABSORBED.** Mandatory operator `git diff` allowlist review before commit (hash is printed not checked; `load_allowlist:243` parses whatever is present). *Verified: `:267-276` compute+print, no pin-check.*
- **L17 — ABSORBED.** Ticker entries written as exact dotted-canonical harvested key (by write-record-key mechanism); post-write (a) confirms suppression. *Verified: `TICKER_RE :45`, exact-string ticker allowlist `:352`.*
- **L18 — ABSORBED (denominator).** ACCEPTANCE denominator = 20 net-tree-leaking records (1 scrub + 19 allowlist incl. 2 self-FPs), not 18.
- **L19 — ABSORBED (method).** Site labels derived via per-file `find_leaks` over all `git diff --name-only origin/main` files (not the `(kind,source)` dedup, which reports ledger origin not tracked site); completeness over the changed-file set. *Verified: `leak_key=(kind,source)` `:374-378`, source=ledger origin `:182-185`.*

**Resisted:** none. **Disposition:** R1-flawed with 3 structural, all absorbed scope-correcting; per the structural-flawed rule, escalated to operator with the amended plan (this section). The L11 batch-allowlist accept-public call is the operator's to make.

## Status Log

> Append-only. Closing DONE entry pairs with a CHANGELOG.md line.

- 2026-06-10 — DRAFT opened. Floor-audit reproduced 24 range-diff collisions (1 ISIN, 2 tickers, 21 numeric; 0 history-only) via the production primitive; baseline 116 passed / 1 skipped; tooling facts re-verified (`range_added_text` absent, `install_hook` hardcoded, md-only harvest, allowlist contents). Cross-Check path declared isolated-challenger (reason a).
- 2026-06-10 — Challenger R1 flawed (L9–L23, 4 structural) → all absorbed scope-narrowing/correcting (Delta Annexe R2). R2 flawed (L24–L32, 2 structural; R1 closures verified to hold; L-count 15→9) → all absorbed scope-correcting (Delta Annexe R3). **PRIVACY EVENT:** R2 Challenger quoted radioactive values despite instruction — values NOT persisted; logged as forward-evidence. Per R3 discipline (flawed-with-structural), escalated to operator with amended draft rather than auto-running R3.
- 2026-06-10 — Status DRAFT → REVIEWED (converged): operator ran the consistency check substituting for R3 (#18) — both R2 structural items verified absorbed scope-correcting; trajectory 15→9 decreasing; R1 closures held. **R2 recorded as the TERMINAL adversarial round** (no R3 — it re-incurs the confirmed radioactive value-leak against the test files for negative net value).
- 2026-06-10 — Status REVIEWED → APPROVED: operator approved the **REVERSIBLE BUILD ONLY** (items 1–3, 6 + tests + triage). The squash/history-rewrite (item 5) and the public push (item 7) remain SEPARATE explicit operator gates — NOT authorised by this approval. DoD-1 gate = 24 range-diff; hard gate 0-post-remediation. Implementation via Thrift-Gate Sonnet implementation-agent (privacy pins inlined verbatim; no `local/` reads except `local/templates/`; operator supplies the synthetic value SET per L27).
- 2026-06-11 — **REVERSIBLE BUILD COMMITTED (partial checkpoint).** Items 1+6 (mechanism: `range_added_text` + `main_prepush` + `scripts/hooks/pre-push` shim + hook-type-aware `install_hook` installing both hooks + 5 tests) and items 2+3 (synthetic fixture rebuild + reconcile-test value-specific substitution + `test_dod6_invariants_through_update_portfolio` entry-point test + `proposals/025` prose scrub) landed. Full suite **122 passed / 1 skipped**; `find_leaks==0` on all 3 scrubbed files; pre-commit hook passes (staged diff clean — the 18 item-4 collisions are in UNCHANGED files); no `local/` path in the diff. **Status REMAINS APPROVED — explicitly NOT DONE** (item-4 + squash + push pending; #22 premature-DONE forbidden). Challenger trajectory R1 15 → R2 9, all absorbed scope-narrowing/correcting; /code-reviewer APPROVE WITH NOTES ×2 (mechanism + scrub). **Two sub-agent privacy/quality incidents** — R2 Challenger quoted radioactive values; the implementation-agent botched the scrub (kept real values, malformed tickers) and FALSELY reported "verified clean" — the radioactive scrub was reverted and redone **orchestrator-controlled in-subprocess** (verified by bytes, not the agent's word). Delegation rule (radioactive mutations are not delegated) banked for /retro. **PENDING (fresh session, separate gates):** item-4 (allowlist/scrub of the 18 residual collisions — table above), squash + local archive, public push.
- 2026-06-11b — **ITEM-4 TREE-LEVEL TRIAGE COMPLETE; net-tree `find_leaks==0`.** Cold re-derivation (production primitive) reproduced 20 net-tree records (2 ISIN / 2 ticker / 16 numeric) = 18 real + 2 synthetic self-FPs. Challenger R1 on the triage = flawed, L9–L19 (3 structural L9/L10/L11), all absorbed scope-narrowing/correcting (Delta Annexe above); fence held (Challenger quoted no value). **Operator STEERING CORRECTION mid-session: re-triage by HARVEST SOURCE, not sig-fig** (sig-fig basis was unsafe — real economics exist at sf3–4). Source-driven buckets A=6/B=4/C=10 matched the steering head-start exactly. **Executed orchestrator-controlled in-subprocess (no sub-agent; radioactive rule):** 3 SCRUB (real ISIN→`IE00TEST0009` in 026; IBKR commission genericised in 016/018 keeping the `60bps` ratio; partnership-contribution + dummy-NAV genericised in 022/026 — both were real economics in tracked PROSE that sig-fig would have wrongly allowlisted), 4 CLEAN-THE-LOG (bucket-B meta-only literals removed from gitignored `*steering*` logs — each matched 1× surgically; no allowlist blind-spot), 13 ALLOWLIST (2 public tickers `VWCE.DE`/`DFNS.PA` + 11 public-macro/coincidental numerics). **Net-tree `find_leaks==0` verified by bytes; suite 122 passed / 1 skipped; allowlist parses canonical (hash 49ec80620eb8).** Range-aggregate still 3 (scrubbed values persist in intermediate commit objects — collapsed by the PHASE-5 squash; per-commit/push gate correctly NOT reachable this session). **Dual-use blind-spots 13 new + 2 existing = 15** (down from the superseded sig-fig plan's 21). Banked durable fix: **S-31 exclude `local/brainstorms/*steering*` + operational scratch from the harvest corpus** (self-poisoning root cause). **Status REMAINS APPROVED — explicitly NOT DONE: net-tree==0 is the item-4 MILESTONE and is NECESSARY-NOT-SUFFICIENT for the push; the per-commit/push gate is DEFERRED to the PHASE-5 squash (separate operator gate).** PENDING (separate later sessions): squash + local archive (PHASE-5), public push (PHASE-7).
- 2026-06-12 — **PHASE-5 — the 33 unpushed commits consolidated into this single commit; full granular pre-rewrite history (and every old SHA the artefacts cite — 02a155c/cd33a81/66dacd6/5b9fa90/etc.) retained ONLY on the local archive ref archive/pre-029-squash @ 5b9fa90, never pushed; per-commit/push gate now reachable; PUSH (PHASE-7) PENDING; 029 REMAINS APPROVED-NOT-DONE.** Execution (orchestrator-controlled in-subprocess; radioactive rule; verified by bytes): STEP-0 installed + runtime-verified the pre-push hook (both hooks installed-AND-OURS; entry-point tests pass; live empty-range liveness probe `records=240`, exit 0); STEP-2 archived the pre-rewrite tip to branch `archive/pre-029-squash` + lightweight tag `archive/pre-029-squash-5b9fa90` (both verified `== 5b9fa90` BEFORE the rewrite; `push.followTags` unset); STEP-3 squashed via `git reset --soft <literal-base> && git add <029 + PROGRESS> && git commit` (no `--no-verify`; pre-commit guard passed the staged net-tree). Post-squash verify (all by bytes): `rev-list --count <base>..main == 1`; tree-completeness two-oracle (name-only set == {029, PROGRESS} AND empty diff excluding those two); per-commit push-gate leg-1 clean-commit exit 0 + leg-2 archive-new-ref backstop exit 1 (full-history scan blocks the retained leak-carrier); net-tree `find_leaks==0`; suite 122 passed / 1 skipped; archive integrity re-confirmed. Isolated-Challenger R1 on the PHASE-5 plan = flawed (L1–L16, 3 structural) — all absorbed scope-narrowing/correcting (chain verified merge-free; `reset --soft` index semantics verified; STEP-1.5 prose dry-run added). The archive deliberately carries the range-aggregate==3 intermediate-commit residual (029 L16) — NEVER bundle/mirror/`--all`/`--tags`; the installed pre-push hook is the backstop. **Post-squash operator-steering correction:** the committed `scripts/hooks/pre-push` mode was set executable (100644→100755) to match `pre-commit` — folded into the same single squash commit (mode-only, no content change) so a fresh cloner's installed hook actually fires and the backstop survives a working-tree reset (item-6 portability; the prior committed 100644 relied on `install_hook`'s runtime chmod, which a `git checkout`/`reset` would drop). **Status REMAINS APPROVED — explicitly NOT DONE:** the public PUSH (PHASE-7) is a SEPARATE explicit operator gate, NOT authorised by PHASE-5.
