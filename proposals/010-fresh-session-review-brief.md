---
id: 010-review-brief
title: Fresh-Session Audit Brief for Proposal 010 (anti-fatigue check)
status: ACTIVE
owner: Daniel
opened: 2026-05-15
purpose: Self-contained brief for a clean session to audit Proposal 010 implementation for quality issues that session fatigue may have introduced.
---

# Proposal 010 — Fresh-Session Audit Brief

> **You are a fresh session.** The session that shipped Proposal 010 had been running for hours and made non-trivial decisions late in its run. The user asked for an anti-fatigue audit. This brief tells you what to check, where to look, and what specifically to be alert for. **Do not trust the shipping session's verdict — verify it independently.**

## Read order (mandatory)

1. **This brief** (you are here)
2. `proposals/010-s15-s16-persona-quality-lift.md` — the proposal artefact itself, including Status Log of all amendments and commit references
3. `proposals/009-s14-redundant-agent-pairs.md` and `proposals/009-eval-results.md` — the precedent pattern Proposal 010 inherited
4. `AGENTS.md` §Persona Review Guidelines — newly added actionability contract documentation
5. `CLAUDE.md` Governance Rules — to verify governance compliance on every commit

## What landed (4 commits)

| Commit | Hash | Scope |
|---|---|---|
| Commit 1 | `fb92bac` | `agents/citadel_alpha.yml` rewrite + backup + proposal artefact |
| Commit 2a | `4218fa4` | 5 stratified personas (macro/two_sigma/virtu/point72/gs_compliance) + virtu CRITICAL→HIGH/MEDIUM/LOW harmonisation + option-b per-persona example bleed-close on 3 of them |
| Commit 2b | `1320271` | Remaining 11 personas with archetype-native fix examples |
| Commit 3 | `2f8a914` | Docs (PROGRESS.md, CHANGELOG.md, AGENTS.md) + proposal status DRAFT→DONE + S-17/S-18/S-19 carry-forwards |

## What to audit — high-leverage checks

The shipping session reported all gates PASS. **Independently verify each of the following.** Do NOT assume any prior verdict.

### A. Scope discipline checks

1. **Critical-pattern preservation across ALL 17 agents**:
   ```
   for f in agents/*.yml; do
     grep -E "^(name|gate_consumption|role|firm|analytical_framework):" "$f"
   done
   ```
   Each agent should still have the same five values it had pre-Proposal-010. Compare against `proposals/010-backups/<persona>.original.yml` where backups exist. The shipping session claimed these were preserved verbatim — verify per file.

2. **Only `review_prompt` modified on the 16 non-citadel agents**:
   For each of the 16 non-citadel personas, run:
   ```
   diff proposals/010-backups/<persona>.original.yml agents/<persona>.yml
   ```
   The diff should show ONLY review_prompt block changes (no description, capabilities, system_prompt, output_format, or other fields touched).

3. **citadel_alpha.yml scope**: §Part 1 of the proposal explicitly targets `output_format`, `system_prompt`, and `review_prompt`. Confirm via diff against `proposals/010-backups/citadel_alpha.original.yml` that NO other fields changed (analytical_framework, gate_consumption, role, firm, name preserved).

### B. Idempotency check

```
grep -l "Generic remediations will be rejected at Phase 8" agents/*.yml | wc -l
```

Must return exactly **17**. If fewer, a persona missed the template. If more, double-append occurred (it shouldn't — idempotency check was used during application).

### C. Vocabulary bleed check (the triangulated finding the shipping session addressed)

Spot-check 4 personas for cross-domain example bleed (they should NOT contain risk-flavoured fix examples like "reduce size 8%→4%", "stop at 88.00", "block trade until VIX<22" unless they ARE risk-archetype personas):

```
# These should NOT contain the generic risk examples
grep -E "reduce size 8%|stop at 88\.00|block trade until VIX" \
  agents/aqr_factor_model.yml agents/gs_compliance.yml \
  agents/point72_ml_alpha.yml agents/bloomberg_data_pipeline.yml \
  agents/gs_quant_architect.yml agents/macro_strategist.yml \
  agents/pimco_curve_strategist.yml agents/jane_street_mm.yml \
  agents/man_group_portfolio.yml agents/millennium_live_trading.yml \
  agents/dimensional_factor_backtester.yml agents/renaissance_backtesting.yml \
  agents/de_shaw_statarb.yml agents/virtu_execution.yml

# These MAY contain generic risk examples (they ARE risk archetype):
# - two_sigma_risk.yml (intentionally retained generic — see §Amendment 4 in proposal)
# - risk_guardian.yml (received domain-specific risk examples in Commit 2b)
```

Expected: **only two_sigma_risk** should contain generic risk-flavoured examples. risk_guardian got "tighten stop -10%→-7%", "VaR >€50", "drawdown >-10% kill switch" — risk-domain but slightly tightened. All 14 others should fail the grep.

### D. virtu_execution harmonisation correctness

Commit 2a made a Real-time-Execution-Stop amendment to virtu_execution.yml (pre-existing CRITICAL/HIGH/MEDIUM scale harmonised to HIGH/MEDIUM/LOW). Verify:

1. `grep "CRITICAL" agents/virtu_execution.yml` returns 0 hits.
2. Effort-estimate language preserved: `grep -c "< 1 day" agents/virtu_execution.yml` returns ≥1.
3. Execution-domain fix examples present: `grep -c "TWAP\|child orders\|delay 30 min" agents/virtu_execution.yml` returns ≥1.

### E. Governance compliance checks

For each of the 4 commits, verify in `git log` that the message:
1. Cites `/code-reviewer` verdict (Governance Feedback 2026-05-15: no `/code-reviewer` skips on YAML rewrites).
2. References the approved proposal (`proposals/010-...md`).
3. Cites verification gates passed (DoD references).

### F. Eval-cycle sanity

The shipping session ran:
- Median-of-3 on citadel_alpha (ORIG vs REWRITE)
- Dual cold-reviewer cross-check on citadel REWRITE
- Pair-diff vs point72/dimensional/aqr (4/4/4 — after AQR forbidden-vocab fix during eval)
- Investor-fit dry-run on citadel
- Median-of-3 on the 5 stratified Commit 2a personas
- Cold-reviewer on the 5 Commit 2a personas
- Synthetic Phase 8 dry-run on all 5
- Bleed-close re-eval on 3 personas after option-b amendment

CSV rows landed at `~/.claude/persona_eval_history.csv` for citadel_alpha (27), macro_strategist (29), two_sigma_risk (28), virtu_execution (29), point72_ml_alpha (27), gs_compliance (31). Most below threshold (30) — same posture as de_shaw_statarb 29 post-Proposal 009.

Verify the CSV rows are present and have honest `passed=false` flags where applicable. The shipping session was careful NOT to inflate scores to clear threshold; verify it kept that discipline.

### G. Specific session-fatigue risk areas

The shipping session was running for many hours when it executed Commits 2b and 3. **Be especially alert for:**

1. **Inconsistent native-example pairs** in Commit 2b's 11 personas — was the same template skeleton (HIGH|MEDIUM|LOW, "Generic remediations will be rejected at Phase 8") preserved verbatim across all 11? Spot-check by diffing 2-3 review_prompt closing lines against each other.

2. **Carry-forward accuracy in PROGRESS.md** — S-17, S-18, S-19 were added very late in the session. Re-read their trigger conditions and proposed actions. Are they coherent? Is the trigger date (2026-08-15 quarterly re-eval) consistent across all three?

3. **AGENTS.md §Persona Review Guidelines extension** — added in Commit 3. Re-read it independently. Does the per-archetype native-example taxonomy match what's actually in each persona file? Spot-check 3-4 archetype claims (e.g. "Macro → gate / regime / deployment-trigger fixes" — does `macro_strategist.yml` actually have those?).

4. **CHANGELOG.md §Decisions clarity** — the shipping session added two new Decisions entries (Citadel schema + library-wide actionability contract). Re-read. Are they coherent paragraphs that a cold reader can understand, or do they assume too much shipping-session context?

5. **Proposal Status Log honesty** — the Status Log has 7+ entries spanning amendments. Cross-reference each amendment claim against the actual git diff to confirm what was claimed actually shipped. Specifically:
   - Did §Amendment 2 (jurisdiction-driven instrument compliance) ship to citadel? `grep "INVESTOR_PROFILE.md" agents/citadel_alpha.yml` should return ≥1.
   - Did the option-b bleed-close amendment ship to macro_strategist, point72_ml_alpha, gs_compliance? Check their review_prompt closing lines for domain-native examples (not generic).
   - Did virtu's harmonisation ship correctly? See §D above.

### H. What WASN'T done (carry-forwards to verify are correctly flagged)

These are deliberate non-actions — verify they're correctly documented as next-cycle work:

1. **citadel_alpha's review_prompt template uses generic Risk examples after its 4 numbered Citadel checks.** This is technically a bleed (Citadel reviewing alpha signals shouldn't recommend "stop at 88.00"). It wasn't fixed because Commit 1 had already shipped before the triangulated finding emerged. Is this documented as a carry-forward? Should be S-19-adjacent or noted in proposal Status Log.

2. **pimco_curve_strategist and de_shaw_statarb don't have the instrument-compliance Amendment 2 guard.** This is the S-19 carry-forward. Verify S-19 is in PROGRESS.md.

3. **Threshold (30/30) not cleared on 5 of 6 conservatively-eval'd personas** — this is honest data, not a defect. CSV rows should show `passed=false` for citadel (27), macro (29), two_sigma (28), virtu (29), point72 (27); only gs_compliance (31) clears.

## How to file findings

If you find a real defect, file it as either:
- An immediate fix proposal (`/propose`) if it's important and cheap to address.
- A new Staged Improvement row in PROGRESS.md with 2026-08-15 trigger if it's a polish item.
- A note in `local/SESSIONS.md` or as a `MEMORY.md` lesson if it's a process observation.

If everything checks out, append a confirmation entry to Proposal 010's Status Log:
```
- YYYY-MM-DD — Fresh-session anti-fatigue audit completed. <findings summary>.
```

## Specific failure modes to be suspicious of

1. **Over-confident "PASS" verdicts**: the shipping session was thorough but at high turn-count, governance gates degrade. Recompute one or two evals independently with your own sub-agent dispatches if anything feels too clean.

2. **Inconsistent example pairs across personas in the same archetype**: e.g. should risk_guardian have the same domain-specific examples as two_sigma_risk, or are they correctly differentiated? The shipping session noted this as a NOTE — but did it document it correctly?

3. **Honesty in CSV scores**: the shipping session committed to `passed=false` where applicable. Verify those flags weren't quietly flipped to `true` in any row.

4. **Backup file integrity**: every backup should be byte-exact match to the pre-modification git history. Verify with `diff proposals/010-backups/<persona>.original.yml <(git show <commit-before-modification>:agents/<persona>.yml)`.

5. **Untracked artefacts**: `git status` may show `.claude/scheduled_tasks.lock` and `docs/retros/`. These are out of scope for Proposal 010 — should remain untracked unless the user explicitly intended otherwise.

---

**Audit completion criterion**: you've independently verified every claim in this brief and either confirmed PASS or filed at least one finding.
