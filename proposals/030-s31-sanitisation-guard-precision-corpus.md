---
id: 030
title: S-31 sanitisation-guard precision + corpus hardening
status: DONE
tier: MEDIUM
created: 2026-06-14
supersedes: []
superseded_by: []
related: [027, 029]
---

# PROPOSE: S-31 Sanitisation-Guard Precision + Corpus Hardening

**Tier: MEDIUM** (security-critical guard — 2 files: `scripts/hooks/sanitisation_guard.py` + `tests/test_sanitisation_guard.py`; within established patterns; no contract change to the hook shims.)

> **CARDINAL CONSTRAINT.** The guard's whole job is detection. Every precision/corpus narrowing REDUCES what blocks → the failure mode is a SILENT UNDER-BLOCK (a real investor-private literal slips into the now-PUBLIC repo). Each narrowing is PAIRED with a real-leak-STILL-blocks test. A loosening that does not prove detection-intact is a regression, not a fix.

## Pre-Flight Gate (results cited inline)

1. **Factual-claim verification.**
   - `find_leaks` uses a SINGLE shared `re.compile(r"(?<!\d)" + re.escape(pattern) + r"(?!\d)")` (line 361) for ISIN, ticker AND numeric — verified via Read. A boundary fix MUST branch on `record["kind"]`.
   - `ISIN_RE`/`TICKER_RE` carry `\b` at extraction (lines 44–45) but NOT at match — verified via Read.
   - `main()` line 410 `added = staged_added_text()` has NO try/except git-error branch — verified via `sed -n 409,411p`.
   - `main_prepush` rev-parse except (line 478) catches `(CalledProcessError, FileNotFoundError)` but NOT `OSError`; rev-list except (line 513) DOES catch `OSError` — verified via Read (asymmetry confirmed).
   - Corpus = `local_dir.rglob("*.md")` minus `_tracked_paths` (lines 169/172) — verified via Read.
   - Disk enumeration of `local/*.md` (15 untracked .md + 5 templates) matches the REAL/NOISE split — verified via `find local -name '*.md'` + `git ls-files local` (tracked-under-local = `.gitkeep` + `templates/*` only).
   - `git diff --cached` outside a repo exits non-zero (129) → `CalledProcessError` under `check=True` — verified via shell.
   - Test baseline 122 passed / 1 skipped — verified via `pytest -q`.
   - Subsumption counts (value-free, in-subprocess, PIN-1) — measured: see §ITEM 4.
2. **Downstream-artefact grep.** Consumers of the guard: `scripts/hooks/pre-commit` + `pre-push` (call `main`/`main_prepush`, return `int` — `GitInvocationError` caught INSIDE those functions → **no cascade**, shims unchanged); `tests/test_sanitisation_guard.py` (imports helpers — updated in this proposal; no existing test exercises an error path so the new `raise` breaks nothing → cascade addressed in §6); CHANGELOG/PROGRESS/`docs/retros/*`/proposals 027/029 are descriptive references → **no cascade**.
3. **Multi-surface walk.** 2 surfaces (guard module + test module). Guard: matcher branch (find_leaks), fail-closed (staged_added_text/range_added_text/main/main_prepush), corpus (extract_private_literals + new helper). Tests: paired detection-intact assertions per change. Walk outcome: each guard change has a paired real-leak-still-blocks test traversing a production entry-point (§3 SPECIFY).

## 1. DECOMPOSE

| # | Item / Sub-problem | Target scope | Type of change | DoD anchor |
|---|---|---|---|---|
| 1 | Ticker matching over-block (029 NOTE 1, **scoped to TICKERS by operator**) | `find_leaks` matcher (line 361) | Branch on `record["kind"]`; **TICKER ONLY** gets alpha-AND-digit boundary; **ISIN + numeric UNCHANGED** (digit-only) | (a1),(b),(f) |
| 1-cond | ISIN + hash-digit-substring FP on NUMERIC path | `find_leaks` ISIN/numeric branch | **NOT taken** — ISIN stays digit-only (12-char high-value, over-block-never-under-block); numeric untouched (glued-currency class). Named residuals. | (a2) residual |
| 2 | Fail-CLOSED on git error AND ledger-read error across BOTH entry-points | `staged_added_text`, `range_added_text`, `extract_private_literals`, `main`, `main_prepush` | New `GitInvocationError` + `LedgerReadError`; raise on git/OSError; catch → clean BLOCK + exit 1; empty-but-valid PASSES; UnicodeDecodeError → loud-skip | (c) |
| 3 | Doc-discipline convention | (no guard code) | NAMED RESIDUAL — placeholders + short SHAs in tracked docs | — |
| 4 | Corpus hardening — exclude process-noise | `extract_private_literals` + new `_is_process_noise` | Convention-glob exclusion of `.steering-`/`.issues-scratch`/`INDEX.md`/leading-`_`/`_draft`; subsumption gate (4iii) | (a3),(b-routing),(e) |

**Aggregate:** 4 substantive items (Item 1 + its conditional sub-decision = one matcher surface; Items 2, 3, 4) → `Item1 + Item2 + Item3 + Item4 = 4 ✓`. Item 3 is a convention-only named residual (no code). The 029-banked "hash-digit-substring" item is reconciled as a CONDITIONAL sub-decision of Item 1, NOT a 5th item (confirmed on disk: it lives on the same `find_leaks` matcher surface).

## 2. ARCHITECT

**Item 1 — TICKER-ONLY alpha-aware boundary (operator decision: tickers-only). Confidence 0.93.**
Branch the matcher on `record["kind"]`:
```python
if kind == "ticker":
    regex = re.compile(r"(?<![A-Za-z0-9])" + re.escape(pattern) + r"(?![A-Za-z0-9])")
else:  # ISIN and numeric value — digit-only lookaround UNCHANGED
    regex = re.compile(r"(?<!\d)" + re.escape(pattern) + r"(?!\d)")
```
Only the TICKER path gets the alpha boundary — tickers are low-information (5–7 chars), the realistic coincidental-substring FP class. **ISIN stays digit-only** (12-char high-value; keep maximal over-blocking detection, never under-block). The numeric branch is byte-for-byte unchanged.
**Named residual (operator-accepted):** a ticker glued to trailing letters with NO separator (e.g. `FAKE.DENotes`) no longer blocks. Every DELIMITED ticker shape (space / pipe / slash / table-cell — the realistic leak shape) STILL blocks (verified at steering + paired test §3 a1).

**Item 1-conditional — ISIN + numeric paths. Decision: DO NOT CHANGE. Confidence 0.92.**
ISIN stays on the digit-only matcher: a 12-char ISIN is high-confidence; keeping it over-blocking (it never under-blocks) is the cardinal-safe direction. The numeric path stays digit-only because a value glued to letters — e.g. a NAV `5142` appearing as `5142EUR` (glued currency code) — is the HIGHEST-STAKES leak class and MUST still block. **Named residuals:** (i) an ISIN that is a substring of a longer alphanumeric token in a tracked diff still over-blocks (safe, friction-only); (ii) a real ledger numeric that is a digit-substring of a SHA in a TRACKED doc still over-blocks (safe) — mitigated harvest-side by Item 4 (excludes SHA-bearing scratch logs from becoming spurious records) + Item 3 (short SHAs). Both residuals are in the SAFE (over-block) direction.

**Item 2 — fail-closed via sentinel exceptions (git error + ledger-read error). Confidence 0.88.**
`staged_added_text`/`range_added_text` raise `GitInvocationError` on `(CalledProcessError, FileNotFoundError, OSError)` — distinguishing a genuine git error (raise → caller fails CLOSED) from a legitimately empty added-text set (return `""` → caller PASSES). `extract_private_literals` raises a new `LedgerReadError` on `OSError` (a real file that cannot be read must not silently drop its protection; `is_file()` already pre-filters dirs/broken-symlinks so the residual OSError is a genuine unreadable file). A `UnicodeDecodeError` is handled by a **best-effort `latin-1` fallback re-read** + a loud stderr warning — latin-1 never raises and preserves 100 % of ASCII content (ISINs/tickers/digits), so a non-UTF-8 ledger (e.g. a Latin-1 broker-statement paste) is STILL harvested and STILL blocks (resolves the Challenger-R2 dL4 under-block), while a stray binary `.md` yields at-worst harmless over-blocking noise — neither silent under-block nor DoS. `source` is computed BEFORE the read so it is defined in the read-error branches; `_is_process_noise` is checked BEFORE the read so an excluded file cannot trigger a read error. **This refines the operator's `loud-skip` directive (Real-time Execution Stop flag — headlined at the steering checkpoint).** `main()`/`main_prepush()` wrap `extract_private_literals()` → clean BLOCK + `return 1` on `LedgerReadError`, and `main()` wraps `staged_added_text()` → clean BLOCK + `return 1` on `GitInvocationError`. `main_prepush`: (a) no-stdin rev-parse except widened to catch `OSError` and fail CLOSED (cannot establish a range = unsafe); (b) malformed pre-push stdin line (`len(parts)!=4`) → fail CLOSED (a real pre-push always emits 4 fields; the empty-line filter at line 464 runs first, so blanks never reach this check); (c) rev-list fallback `range_added_text` wrapped → fail CLOSED on `GitInvocationError`; (d) git-show per-commit error → fail CLOSED. rev-list's own except is PRESERVED (still catches + falls back — never weakened to crash). A branch delete (`local_sha` all-zeros) and an empty range remain legitimate PASSES.

**Item 4 — corpus convention-glob. Confidence 0.85.**
New `_is_process_noise(path)` excludes process/meta artefacts by **convention glob** (not an enumerated list): `name == "INDEX.md"`, `stem.startswith("_")`, `"_draft" in stem`, or any of `(".steering-", ".issues-scratch")` as a name infix.
- *Chosen: convention glob over enumerated list* — a future `2026-07.steering-*.md` is auto-excluded, directly closing the self-poisoning root cause (banked in PROGRESS 029 line). An enumerated list would re-introduce the self-poison for any new steering log.
- *Risk (over-matching a real source) closed* by a no-swallow test asserting none of the 11 current retained sources match `_is_process_noise`. Rooted at `_local_dir()` (the `path.name`/`path.stem` predicate is path-agnostic). `_tracked_paths` subtraction PRESERVED (templates stay un-harvested); composes with the git-failure fallback (templates-only) consistent with the Item-2 fail-closed posture (more harvesting on git failure = fail-safe for detection).

## 3. SPECIFY (success criteria — paired, traversing production entry-points)

All new tests use SYNTHETIC out-of-ledger-range values via `SANITISATION_LOCAL_DIR` → tmp corpus; NEVER the real `local/` ledger.

- **(a1) ticker FP fixed:** `find_leaks` — ticker `FAKE.XX` in `"FAKE.XXY"` (glued-no-separator) → no leak.
- **(a1-pair) ticker detection intact — ALL delimited shapes block:** ticker `FAKE.XX` in `"FAKE.XX listed"` (space), `"|FAKE.XX|"` (pipe/table), `"/FAKE.XX/"` (slash), standalone → STILL BLOCKS.
- **(a1-isin) ISIN unchanged (over-blocks, never under-blocks):** ISIN `XX0000FAKE01` in `"XX0000FAKE01Notes"` → STILL BLOCKS (digit-only path untouched); standalone → STILL BLOCKS.
- **(a2 residual) numeric glued-to-letters STILL BLOCKS:** `find_leaks` — value `5142` in `"5142EUR"` → STILL leaks (numeric path unchanged; highest-stakes class).
- **(a3) corpus FP:** a synthetic value living ONLY in a tmp EXCLUDED file → not harvested → PASSES (extract-level + production).
- **(b-routing) production routing:** plant value V1 in a tmp RETAINED source (tmp `SESSIONS.md`) and a DIFFERENT value V2 ONLY in a tmp EXCLUDED file (`2026-07.steering-foo.md`); `main_prepush` over a commit adding V1 → BLOCKS; over a commit adding V2 → PASSES.
- **(c) git-error CLEAN fail-closed:**
  - `main()` with non-git `REPO_ROOT` + records → `return 1`, stderr contains `COMMIT BLOCKED` + `failing CLOSED` (NOT a traceback).
  - `main()` with valid git repo + EMPTY staged diff + records → `return 0` (empty-but-valid PASSES).
  - `main_prepush` malformed stdin → `return 1` (`PUSH BLOCKED`); delete-only stdin → `return 0`; no-stdin + no origin/main → `return 1`; git-show error (monkeypatched) → `return 1`.
  - **(c-read) ledger-read fail-closed + latin-1 fallback:** `main()` with a synthetic local file that raises `OSError` on read (monkeypatched `read_text`) → `return 1` (`LedgerReadError` BLOCK); a synthetic non-UTF-8 `.md` containing an ASCII-shaped synthetic value → loud warning AND the value is STILL harvested and BLOCKS (latin-1 fallback preserves detection; does NOT DoS).
- **(d) allowlist honoured:** allowlisted ISIN/value → PASSES; non-allowlisted → BLOCKS (existing tests retained).
- **(e) tracked-path invariant:** a tmp `templates/*` value (via monkeypatched `_tracked_paths`) → NOT harvested.
- **(f) date-span no-op (numeric untouched):** an ISIN match adjacent to an ISO date still BLOCKS (a full ISIN/ticker match is longer than any ISO-date span so `inside_date` cannot fire on it — verified by construction + test); existing numeric date-exclusion tests still pass.
- **Whole suite:** `python3 -m pytest -q` → all pass (≥122 + new).
- **Runtime observation (at /commemorate):** installed `.git/hooks/pre-commit` + `pre-push` invoked end-to-end against a synthetic corpus demonstrating FP-passes, real-leak-blocks, AND clean-fail-closed.

## 4. MULTI-PERSONA REVIEW (inline — no persona-*.md files; Core Team A–D)

- **A — Quant Architect:** APPROVE. The `kind`-branch is the minimal change; the `GitInvocationError` sentinel removes the empty-vs-error conflation cleanly; `_is_process_noise` is a single-responsibility helper. No duplication (a shared `_print_push_block_git_error` helper folds the 3 repeated fail-closed messages).
- **B — Portfolio Manager:** APPROVE. Minimum scope — S-31 only; no chaining into S-32/S-21. Fully unwound by `git revert`.
- **C — CTO:** APPROVE WITH CONDITIONS. Fail-closed is the correct posture for a security gate. Condition: prove the empty-but-valid path still PASSES (else the guard blocks its own clean commit on the public self-gating repo). Condition met by SPECIFY (c) empty-diff test.
- **D — Risk Officer:** APPROVE WITH CONDITIONS. The detection-not-weakened constraint is the tail risk. Condition: EVERY narrowing has a paired real-leak-still-blocks test through a production entry-point, and the numeric-path residual (a2) is named not silently closed. Conditions met by §3 + §2 Item-1-conditional.

## 5. RISK FLAGS

- **R1 — Silent under-block (CARDINAL).** Any narrowing could drop real detection. Closed by paired tests per narrowing + the Challenger pass.
- **R2 — Self-gating public repo.** A broken guard change could BLOCK its own commit. Closed by exhaustive testing BEFORE staging + the empty-but-valid PASS test.
- **R3 — Over-exclusion (corpus).** Dropping a real source is the cardinal corpus sin. Closed by the no-swallow test + the value-free subsumption count + operator-accept gate (4iii).
- **R4 — Numeric SHA residual (a2).** Named, accepted, mitigated by Items 3+4 (not fully closed on the diff side). Documented.
- **R5 — PIN-1.** Private ledger economics never enter agent/Challenger/test context; the subsumption analysis returns COUNTS only; value-visibility (if needed) is OPERATOR-ONLY in their own terminal.

## ITEM 4(iii) — Subsumption safety (value-free counts + operator gate)

Value-free per-file analysis (counts only returned to agent context; in-subprocess; PIN-1):

| Excluded file | total_keys | non_subsumed | disposition |
|---|---|---|---|
| `brainstorms/INDEX.md` | 4 | **0** | trivially safe (excluding loses nothing) |
| `brainstorms/_phase4_working_prompt_draft.md` | 0 | **0** | trivially safe |
| `brainstorms/2026-05.issues-scratch.md` | 12 | **3** | **ACCEPT exclusion** (operator-attested 2026-06-14) |
| `brainstorms/2026-06.steering-data-layer.md` | 15 | **14** | **ACCEPT exclusion** (operator-attested 2026-06-14) |
| `brainstorms/2026-06.steering-tooling-remainder.md` | 24 | **20** | **ACCEPT exclusion** (operator-attested 2026-06-14) |

- **CLASS-LEVEL safety (named residual):** all 5 are process/meta artefacts (steering logs / scratch / INDEX / working-prompt draft) — NON-LEDGER by construction. Paired with the forward "steering/scratch stays figure-free" discipline.
- **NO-GATE files (`INDEX.md` + `_phase4_working_prompt_draft.md`) — value-free justification.** Both have a non-subsumed count of **0** (every private-literal they carry is already present in a retained source, so excluding them removes ZERO unique detection signal — trivially safe). They were therefore excluded WITHOUT an operator value-visibility gate; the count==0 result is itself the value-free proof. Steering verified this on the bytes at byte-verification.
- **OPERATOR-ACCEPT — CLEARED (value-free record, PIN-1 held).** The operator ran the value-visible triage in a SEPARATE terminal; the non-subsumed tokens reached the OPERATOR ONLY (never agent / Challenger / test context). Operator confirmed every non-subsumed token benign: byte-counts / SHA-fragments, plus one public-macro index reference (not a holding) in `issues-scratch`. Decision (operator-attested, value-free): **all three files → ACCEPT exclusion.** No values recorded here per PIN-1.

## 6. FILES CHANGED (PROPOSED)

- `MODIFY` `scripts/hooks/sanitisation_guard.py` — `GitInvocationError` + `LedgerReadError` classes; `find_leaks` **ticker-only** kind-branch matcher (ISIN+numeric untouched); `staged_added_text`/`range_added_text` raise-on-git-error; `extract_private_literals` raise `LedgerReadError` on OSError + loud-skip UnicodeDecodeError + `_is_process_noise` exclusion call; `main`/`main_prepush` fail-closed catches (git + ledger-read); `main_prepush` 4 fail-closed branches + `_print_push_block_git_error` helper; `_is_process_noise` helper.
- `MODIFY` `tests/test_sanitisation_guard.py` — ~13 new tests per §3 (paired FP-fixed/detection-intact, fail-closed both entry-points, corpus routing + no-swallow, tracked-path invariant, date no-op).
- `CREATE` `proposals/030-s31-sanitisation-guard-precision-corpus.md` — this proposal.
- `MODIFY` `proposals/README.md` — index row for 030.
- `MODIFY` `PROGRESS.md` — consolidate the S-31 row to the reconciled sub-items + mark DONE (at /commemorate).
- `MODIFY` `CHANGELOG.md` — `[Unreleased]` entry (at /commemorate).
- `CREATE` `docs/retros/2026-06-14.md` — session retro (at /retro; untracked by design).

**Aggregate:** 7 surfaces: 4 MODIFY (guard, tests, README, PROGRESS) + 1 MODIFY (CHANGELOG) + 2 CREATE (proposal, retro) → core code+test = 2 MODIFY; self-admin = 2 CREATE + 3 MODIFY = 5. `2 + 5 = 7 ✓`.

## 7. REVERSIBILITY

**FULLY REVERSIBLE** — all changes are local code/config/docs. `git revert` restores all state. No external state, no API calls, no data sent anywhere. (The guard's *purpose* relates to an irreversible public push, but this proposal makes no push — it hardens the gate.)

## 8. Delta Annexe (Isolated Challenger R1 — `isolated-challenger`, no external model configured)

R1 verdict: **flawed**, L1–L16 (6 structural). Each structural claim independently verified against the bytes before absorb/resist (CLAUDE.md §2).

| L | Severity | Disposition | Verification |
|---|---|---|---|
| L1 | structural | **ABSORBED (narrow)** — drop `stem.startswith("_")` clause; keep `_draft`+infixes+`INDEX.md`. | Verified: all 5 noise files still excluded, all 11 retained sources kept (python run). Scope-narrowing (G15-a). |
| L2 | structural | **RESISTED → named residual + operator-accept gate (4iii).** Permanent-exclusion-vs-snapshot gap is the operator-arbitrated residual. | Verified vs boot ITEM 4(iii): per-literal value-free proof is explicitly WITHDRAWN as unachievable; operator-accept is the gate. |
| L3 | structural/subst. | **ESCALATED to operator** — fold read-error fail-closed into ITEM 2, or carry-forward? | Verified lines 175–178: `except (OSError, UnicodeDecodeError): continue` is a real harvest-side fail-open. |
| L4 | structural | **RESISTED** — mitigated by no-swallow test + L1 narrowing (real ledger files never match the glob) + L3 (if folded). | Verified: real sources never excluded; only zero-out path is L3 read-error or genuinely-no-literals. |
| L5 | substantive | **CARRY-FORWARD (S-31 successor)** — merge-commit empty-diff under-scan is pre-existing, outside the 4-item scope. | Verified lines 541–558: `git show` default shows no merge diff. Named follow-up. |
| L6 | structural | **ESCALATED to operator** — alpha-boundary under-blocks a real ISIN/ticker glued to trailing letters. | Verified: `XX0000FAKE01Notes` cur=BLOCK new=pass; delimited shapes block under both. Cardinal tension. |
| L7 | substantive | **ABSORBED** — add ≥2 production-path corpus-routing tests; (a1) documents the boundary as designed (pending L6). | — |
| L8 | substantive | **ABSORBED (clarify)** — empty-line filter precedes the `len!=4` check → malformed→fail-closed is safe. | Verified line 464 filter runs before the loop. Add code comment. |
| L9 | substantive | **ABSORBED (critical)** — dogfood ran: proposal 030 + README CLEAN vs real ledger; re-run before final staging. | Verified via in-subprocess find_leaks (value-redacted). |
| L10 | substantive | **RESISTED** — git-fallback (templates-only) + ITEM 4 exclusion compose correctly; real ledger files are neither. | Verified lines 146–151 + exclusion logic. Benign interaction. |
| L11 | substantive | **ABSORBED (clarify framing)** — Item 4 removes spurious SCRATCH-sourced records (cuts FALSE blocks), never a real ledger source; numeric real-SHA-substring residual remains named. | — |
| L12 | craft | **ABSORBED** — label R3 (under-block, cardinal-fatal) vs R4 (over-block, safe) by direction. | — |
| L13 | substantive | **RESISTED → named** — unreachable `remote_sha` → range error → fail-closed is the SAFE direction; `--no-verify` escape. | Verified lines 489–498 + ITEM 2c. |
| L14 | substantive | **RESISTED → named** — numeric-in-ISO-date skip is pre-existing (docstring 339–342); numeric path untouched. | Verified. |
| L15 | craft | **ABSORBED** — SPECIFY relabel for 1:1 item traceability. | — |
| L16 | substantive | **ABSORBED (clarify)** — PIN-1 intact: counts computed via throwaway in-subprocess script printing `len()` only; values never returned to agent context. | Verified: `/tmp/subsumption_count.py` prints only counts. |

**Net:** 9 absorbed, 5 resisted/named, 2 escalated (L3, L6) — plus the mandatory 4iii operator-accept gate (L2). No absorption expands scope except the L3 candidate, which is escalated per G15.

### Delta Re-pass (Challenger R2 — L3 read-error addition only; operator-mandated per adversarial-sequence-stop-rule)

R2 verdict on the added surface: **flawed**, dL1–dL10 (2 structural). Each verified against the bytes.

| dL | Severity | Disposition | Verification |
|---|---|---|---|
| dL1 | structural | **ABSORBED** — compute `source` BEFORE the read so it is defined in the except branches. | Verified lines 180–185: `source` is computed AFTER the read (would `NameError`). |
| dL2 | structural | **ABSORBED** — `source` two-branch `relative_to` block moved above the read intact; its own `ValueError` handling stays self-contained. | Verified lines 181–185. |
| dL3 | substantive | **RESISTED → confirmed safe** — UnicodeDecodeError (a `ValueError`) and OSError are disjoint; specific-first arm order; no other exception type can arise from `read_text(encoding="utf-8")`. | Verified line 177 catch taxonomy. |
| dL4 | substantive (cardinal) | **ABSORBED — best-effort latin-1 fallback (supersedes loud-skip).** A non-UTF-8 ledger (Latin-1 broker-paste) is re-read with `latin-1` (never raises; preserves all ASCII content → ISIN/ticker/numeric still harvested → STILL BLOCKS) + a loud warning. Resolves the under-block AND avoids the DoS. **Real-time Execution Stop flag: refines the operator's `loud-skip` directive; headlined at the steering checkpoint.** | Verified: latin-1 maps all 256 bytes; ASCII subset is identity. |
| dL5 | substantive | **RESISTED** — `is_file()` (line 170) pre-filters dirs/broken-symlinks; residual OSError after it is a genuine unreadable file → fail-closed is the operator directive. | Verified line 170. |
| dL6 | substantive | **RESISTED** — fresh-clone guarantee intact via `local_dir.exists()` no-op (line 387/442); a half-onboarded unreadable file correctly fails closed. | Verified lines 387/442 before the extract call. |
| dL7 | substantive | **RESISTED → dissolved by dL4** — best-effort decode means no skip, so no boy-who-cried-wolf protection-loss. | — |
| dL8 | craft | **ABSORBED** — message reads "local/ private file" not "ledger file" (scan covers all local `.md`). | Verified docstring line 155. |
| dL9 | structural-adjacent | **ABSORBED** — `_is_process_noise` skip placed BEFORE the read so an unreadable excluded file cannot DoS. | Verified loop order lines 169–178. |
| dL10 | craft | **ABSORBED** — block message + a note that the harvest aborts on first unreadable file (re-run after fixing perms). | — |

**Delta net:** 6 absorbed, 4 resisted. dL4 is the only cardinal item; resolved by best-effort decode (strictly safer than both loud-skip and block). No further scope added.

## 9. Status Log

- 2026-06-14 — DRAFT created. Floor-audit complete; baseline 122/1; subsumption counts measured.
- 2026-06-14 — Challenger R1 (isolated-challenger): flawed, 16 L-items; all structurals byte-verified; Delta Annexe authored. Escalated L3 + L6 + 4iii operator-accept to user.
- 2026-06-14 — Operator steering decisions: L6 → **tickers-only** (ISIN+numeric stay digit-only); L3 → **fold in** (OSError fail-closed, UnicodeDecodeError loud-skip); 4iii → **CLEARED, all 3 files ACCEPT exclusion** (operator-attested, PIN-1 held, value-free). Proposal status → APPROVED pending L3-delta Challenger re-pass (operator-mandated, scope-adding absorption per adversarial-sequence-stop-rule).
- 2026-06-14 — **L3-delta Challenger re-pass COMPLETE** (discharges the "pending" above): R2 on the read-error addition only — flawed, 10 dL-items, all byte-verified; 6 absorbed, 4 resisted/named. No further scope added. Delta Re-pass Annexe recorded in §8.
- 2026-06-14 — **dL4: directed `loud-skip` SUPERSEDED by best-effort `latin-1` fallback** (operator-endorsed at steering byte-verification). A Challenger-verified under-block (a Latin-1 ledger would be skipped, dropping protection) made loud-skip cardinal-unsafe; latin-1 preserves all ASCII content (still harvests, still blocks) with a loud warning — no under-block, no DoS. The byte-state changed accordingly; verified through the installed hook (latin-1 ledger still BLOCKS).
- 2026-06-14 — NOTE 1 FIXED (malformed-stdin message names the real cause, clean fail-closed PUSH BLOCK); NOTE 2 ACCEPTED as named residual (`INDEX.md` exact-match). Full suite 141/1; staged 6 files by name; self-gate exit 0. HANDED TO STEERING for the #32 hook re-run + four-artefact byte-verification. Status → DONE atomically with the commit (pending steering clearance).
- 2026-06-14 (steering) — #32 byte-verification PASSED. Re-ran .git/hooks/pre-commit on the staged set (exit 0); full suite 141/1; four artefacts read DONE on the staged blobs (git show :); Status Log §9 append-only confirmed; no fabricated SHA; gate-coverage gap (INDEX.md + _phase4_draft) verified non-subsumed count==0 value-free; dL4 latin-1 fallback endorsed (replaces directed loud-skip). Cleared for commit.
