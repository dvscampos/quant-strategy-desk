---
id: 025
title: reconcile_ibkr column-index foundation fix (10-column ISIN schema)
status: DONE
owner: Daniel
opened: 2026-06-04
updated: 2026-06-04
tags: [data-layer, ibkr, reconcile, bugfix, foundation]
---

# 025 — `reconcile_ibkr.py` column-index foundation fix (10-column ISIN schema)

**Tier: MEDIUM** — 3 code/test/fixture files + 2 self-admin. Corrects a pre-existing index drift in the **Holdings** parse/patch path; no new API surface, no external/broker calls, no `local/` writes. Successor to the SUPERSEDED [Proposal 024](024-isin-anchored-pricing-ibkr-snapshot.md) under the foundation-first ruling.

> **Behaviour-change honesty (Challenger R1 L5/L13 + steering loud-guard absorption).** This is *not* "no new behaviour at the system level." Pre-fix, `_parse_open_holdings` returns `[]`, so `update_portfolio`'s `if positions and total_nav:` branch (`:373`) never runs — the Summary-patch and live-price P&L paths are **dormant**. Restoring the parser **re-activates** them, surfacing two latent defects on live data: **L14** (`_patch_summary` regex anchors match neither template nor live ledger → Summary stays stale while Holdings updates) and **L6** (non-EUR-venue currency mismatch — dormant today since both held instruments are `.DE`/EUR). Because 025 **owns the branch it activates**, it must not ship a *silent* Holdings-fresh/Summary-stale inconsistency: the now-active `_patch_summary` no-op is made **LOUD** (operator-authorised scope-correcting absorption — see Delta Annexe). The fix delivers its **primary** job (flip `PENDING FILL`→`OPEN`, fill the Trade-History row — end-to-end tested); the **secondary** Summary path stays stale **but now warns** until L14 lands.

## Summary

`scripts/reconcile_ibkr.py` parses and patches the ledger's **Current Holdings** table using **9-column** indices, but that table has carried a 10th column (**ISIN at index 1**) since the initial commit. The ISIN insert shifted every subsequent column right by one, so `_parse_open_holdings` and `_patch_holdings_row` read/write the wrong cells: the parser returns `[]` for every position and the patcher's match guard never fires. This proposal corrects the two drifted functions to the 10-column schema and adds a **tracked 10-column fixture** + tests that traverse the real parse → patch → re-parse path — so the bug is caught by CI without the gitignored live ledger. It restores a sound foundation on which S-21 (read-only `--snapshot`) and S-23 (ISIN-anchored pricing guard) can be re-proposed cleanly.

## Motivation / Problem

Surfaced by the Isolated-Challenger pass on Proposal 024 (L1), independently verified on disk:

- **Verified column map** (`local/PORTFOLIO.md:8` / `local/templates/PORTFOLIO.template.md:8`, after `line.strip("|").split("|")`): `[0]Ticker [1]ISIN [2]Name [3]EntryDate [4]Quantity [5]EntryPrice [6]EntryCost [7]Strategy [8]StopLoss [9]CurrentStatus`.
- **`_parse_open_holdings`** (`:255-260`) tests `cols[8] != "OPEN"` — `cols[8]` is **Stop-Loss** (`"Mental -7% (€783.53)"`), never `"OPEN"` → every row `continue`-skipped; `float(cols[3])` would also raise on the Entry-Date string. Returns `[]`.
- **`_patch_holdings_row`** (`:202-208`) matches `"PENDING FILL" in cols[8]` (Stop-Loss) → **never fires** (silent no-op — the live ledger is therefore intact, **not** corrupted; verified: both Holdings rows well-formed with `OPEN` at col 9). If it ever matched, its writes (`cols[2..5]`, `cols[8]`) would land in Name/EntryDate/Quantity/EntryPrice/Stop-Loss.

Consequence: the post-execution reconcile path silently does nothing against the live ledger, and any consumer of `_parse_open_holdings` (Portfolio Summary patch; the future ISIN guard and snapshot cross-check) sits on a parser that returns nothing.

## Proposal

Correct the **two** drifted Holdings-table functions to the 10-column schema. **Surgical scope** — the other two functions Challenger/steering enumerated were audited and are **already correct**, so they are left untouched:

- `_pending_tickers` (`:179`) reads only `cols[0]` (Ticker, still index 0) — correct, no change.
- `_patch_trade_row` (`:228-237`) targets the **Trade History** table, which has **no ISIN column** (9 columns: `[0]Date [1]Action [2]Ticker …`) — its indices are correct, no change.

### Fix manifest

`_parse_open_holdings`:
- `len(cols) < 9` → `len(cols) < 10`; `cols[8] != "OPEN"` → `cols[9] != "OPEN"`.
- `qty = float(cols[3])` → `float(cols[4])`; `price = float(cols[4])` → `float(cols[5])`; `cost = float(cols[5].lstrip("€~").replace(",", ""))` → **`float(cols[6].lstrip("€~").replace(",", ""))`** (the `€`/comma sanitisation moves **with** the index — dropping it makes `float("€5899.00")` raise and silently re-skip the row; Challenger R1 L4).
- `"ticker": cols[0]` unchanged.
- Add an inline comment recording the column-count contract (`# Holdings table is 10-column: ISIN at index 1, status at index 9`) per the ghost-contract discipline (Challenger R1 L7 — comment, not new guard logic; the strict `len < 10` skip is retained surgically).

`_patch_holdings_row`:
- `len(cols) >= 9` → `len(cols) >= 10` (also prevents an `IndexError` on `cols[9]` against 9-column Trade-History rows, since this function scans all lines); `"PENDING FILL" in cols[8]` → `cols[9]`.
- write remap: `cols[2]=date` → `cols[3]`; `cols[3]=shares` → `cols[4]`; `cols[4]=price` → `cols[5]`; `cols[5]=€all_in` → `cols[6]`; `cols[8]="OPEN"` → `cols[9]`.

ISIN (col 1), Name (col 2), Strategy (col 7), Stop-Loss (col 8) are preserved untouched by both functions.

`_patch_summary` + `update_portfolio` (**operator-authorised loud-guard absorption** — 025 owns the branch it re-activates; Challenger R1 L5):
- `_patch_summary`'s nested `_sub` helper switches `re.sub(...)` → `re.subn(...)` (returns `(text, n)`); track how many of the 5 label substitutions matched 0 times.
- `_patch_summary` returns `(text, n_missed)` instead of bare `text`; `update_portfolio` (`:376`) unpacks and, if `n_missed > 0`, appends **one** warning to its existing `warnings` list: `"Summary not updated — label mismatch ({n_missed}/5 labels); Holdings fresh / Summary stale, pending L14"`.
- `main` already prints `warnings` (`:435-436`) — verified, so the guard is not inert. A test asserts the warning fires (DoD#8).

### Tracked fixture + tests

- `CREATE tests/fixtures/portfolio_10col.md` — a minimal 10-column ledger: one `OPEN` row, one `PENDING FILL` row, a matching `(planned)` Trade-History row, and a Summary/NAV block. The Holdings **header line is copied byte-verbatim from the live `local/PORTFOLIO.md:8`** (Challenger R1 L2 — a re-typed header could share the bug's mental model and self-confirm). This closes Challenger **L13** (the live ledger is gitignored, so without a tracked fixture the index bug is invisible to CI). The fixture Summary uses the **live ledger's** labels (`Cash`, `Invested (MTM)`), not the script's `(post-fill)` anchors — so test (3) does **not** silently mask L14 with a synthetic label (Challenger R1 L6).
- `CREATE tests/test_reconcile_ibkr.py` — top-level `pytest.importorskip("ib_insync")` so a broker-SDK-less env **skips** rather than aborting collection (the module `sys.exit(1)`s on missing `ib_insync` at import — Challenger R1 L12):
  1. `test_parse_open_holdings_10col` — parse the fixture → exactly the `OPEN` positions with correct ticker/qty/price/cost (fails pre-fix: returns `[]`).
  2. `test_patch_holdings_row_pending_to_open` — patch the `PENDING FILL` row → status cell (col 9) becomes `OPEN`; qty/price/cost land in cols 4/5/6; ISIN/Name/Strategy/Stop-Loss unchanged.
  3. `test_update_portfolio_end_to_end` — monkeypatch module `PORTFOLIO_PATH` → a tmp copy of the fixture and `_fetch_live_prices` → `{}` (no network); call the production `update_portfolio(fills, date)`; assert the `PENDING FILL` row reaches `OPEN` with correct columns, the `(planned)` Trade-History row is filled, and ISIN is preserved. **This traverses the real entry-point**, not a helper predicate. The test also asserts the Summary block is **unchanged** (documenting the L14 no-op explicitly — Challenger R1 L5).
  4. `test_summary_mismatch_warns` — the same end-to-end run returns a warning containing `"Summary not updated — label mismatch"` (proves the loud-guard fires; the fixture's live-style labels don't match the script's `(post-fill)` anchors).

## Scope & Out-of-Scope

**In scope:** the two drifted Holdings functions; tracked fixture; tests.

**Out of scope (banked, not silently deferred):**
- **S-23 ISIN threading + bare-ticker guard, S-21 `--snapshot`** — re-proposed clean on this committed base in a future session (carries the verified `ib_insync` pre-flight: ISIN in `ContractDetails.secIdList`; `portfolio()` carries live marks; auto-populated on `connect()`; `reqContractDetails` returns a **List**). Absorbs Challenger L5 (case-normalise), L7 (join on ISIN, not base symbol), L10 (List-guard).
- **L6 — currency mismatch.** A correctly exchange-qualified ticker on a non-EUR venue (`.L` GBp, `.SW` CHF) still feeds a native-currency `fast_info.last_price` straight into EUR P&L (`_patch_summary`). New tracked PROGRESS S-item.
- **L14 — `_patch_summary` label divergence.** Its regex anchors (`Cash (post-fill)`, `Invested (post-fill)`) match neither the tracked template (`Cash Reserve`, `Invested`) nor the live ledger (`Cash`, `Invested (MTM)`) → summary patch is a silent no-op. A 3-way label reconciliation (script + template + live ledger), not a column-index fix. New tracked PROGRESS S-item.

## Definition of Done

1. `_parse_open_holdings` returns the `OPEN` positions from the 10-column fixture with correct qty/price/cost.
2. `_patch_holdings_row` flips a `PENDING FILL` row to `OPEN` writing qty/price/cost into cols 4/5/6 and status into col 9; ISIN/Name/Strategy/Stop-Loss unchanged.
3. `test_update_portfolio_end_to_end` passes through the production `update_portfolio` entry-point (monkeypatched path + no-network prices).
4. `tests/fixtures/portfolio_10col.md` is tracked and is the data source for the parse/patch tests.
5. `_patch_trade_row` and `_pending_tickers` are unchanged (verified-correct against the maps below; surgical scope).
6. Full regression: `pytest -q` green — **77 existing** (`grep -c def test_`: 6+5+9+1+5+2+48+1 across 8 files = 77 ✓; Challenger R1 L1 corrected the draft's "11") **+ 4 new = 81**. `tests/test_reconcile_ibkr.py` carries `pytest.importorskip("ib_insync")` so a broker-SDK-less env skips cleanly.
7. Live `local/PORTFOLIO.md` is **not** modified by this proposal (foundation fix is code-only; the ledger is already intact).
8. The re-activated `_patch_summary` no-op is **loud**: `update_portfolio` appends a "Summary not updated — label mismatch … pending L14" warning when labels don't match, and `main` prints it (`:435`). `test_summary_mismatch_warns` asserts it.

### Surgical-scope evidence (Challenger R1 L8 — claim audited, not asserted)

- `_patch_trade_row` (`:227-238`) writes `cols[0]=date, cols[1]=BUY, cols[3]=shares, cols[4]=price, cols[5]=total, cols[6]=comm, cols[7]=strip("(planned)")` against Trade-History map `[0]Date [1]Action [2]Ticker [3]Qty [4]Price [5]Total [6]Commission [7]Reason [8]Strategy` — every cell correct; `cols[7]` is **Reason** (where "(planned)" lives), not Strategy. No ISIN column in Trade History → no drift. **Unchanged.**
- `_pending_tickers` (`:177-180`) gates on whole-line `"PENDING FILL" in line` then appends `cols[0]` (Ticker, index 0 in both tables) — correct. **Unchanged.** (Whole-line vs `_patch_holdings_row`'s cell-specific match is a pre-existing asymmetry, safe today since "PENDING FILL" only ever occupies the status cell — Challenger R1 L15, noted, out of surgical scope.)

## Risks & Mitigations

- **Over-broad `_patch_holdings_row` scan** (iterates all lines): the new `len(cols) >= 10` guard excludes 9-column Trade-History rows, preventing an `IndexError` on `cols[9]`. Covered by `test_update_portfolio_end_to_end` (fixture contains both tables).
- **Hidden 9-column consumers**: exhaustive `grep "cols\["` audit (8 clusters) confirms only the two Holdings functions are drifted; `_pending_tickers`/`_patch_trade_row` verified correct.
- **Fixture realism**: the fixture mirrors the live ledger's exact 10-column header so the test exercises the production schema, not a simplified one (single-source-fixture blind-spot avoided).
- **No external/broker calls, no `local/` writes** — FULLY REVERSIBLE (`git revert`).

## Reversibility

All changes (`reconcile_ibkr.py`, new test, new fixture, proposal, README) — **FULLY REVERSIBLE** via `git revert`. No external state, no broker calls, no `local/` ledger mutation.

## FILES CHANGED (PROPOSED)

- `MODIFY` `scripts/reconcile_ibkr.py` — correct `_parse_open_holdings` + `_patch_holdings_row` indices to the 10-column ISIN schema; loud-guard the re-activated `_patch_summary` no-op (`re.subn` miss-count → `update_portfolio` warning).
- `CREATE` `tests/test_reconcile_ibkr.py` — parse / patch / end-to-end `update_portfolio` tests.
- `CREATE` `tests/fixtures/portfolio_10col.md` — tracked 10-column ledger fixture (closes L13).
- `CREATE` `proposals/025-reconcile-column-index-foundation-fix.md` — this artefact (self-admin).
- `MODIFY` `proposals/README.md` — index row (self-admin).
- *(deferred to `/commemorate`)* `MODIFY` `PROGRESS.md` — new tracked S-items: **L14 summary-label reconciliation (IMMEDIATE-NEXT, prioritised)** + L6 currency mismatch (lower priority); `MODIFY` `CHANGELOG.md` `[Unreleased] ### Fixed`.

`5 files: 3 CREATE (test + fixture + proposal) + 2 MODIFY (script + README) = 5 ✓` (PROGRESS + CHANGELOG at `/commemorate`).

## Delta Annexe (Cross-Check)

**Cross-Check path: isolated-challenger — reason: no external/alternate model API is configured in this environment (CLAUDE.md §3 condition a).** R1 verdict `flawed`, 15 L-items → **10 absorbed** (9 inline + the operator-authorised loud-guard) + **5 resisted** (pre-existing / out-of-surgical-scope) + L7 part-(a) absorbed / part-(b) resisted. Every absorbed/resisted item independently verified on disk before disposition. **No absorption expands the §6 file list**; the loud-guard adds two functions (`_patch_summary`, `update_portfolio`) *within the already-modified `reconcile_ibkr.py`* and is **scope-correcting** (025 owns the branch it re-activates), operator-authorised via steering — not a scope expansion. The adversarial-sequence stop-rule fires on scope expansion; none occurred, so no further Challenger round is triggered.

| L | Severity | Verified | Disposition |
|---|---|---|---|
| L1 | substantive | `grep -c def test_` = 77, not 11 | **Absorbed** — DoD#6 corrected to 77+3=80 with per-file breakdown. |
| L2 | structural | live ledger header line 8 (10-col) | **Absorbed** — fixture Holdings header copied **byte-verbatim** from live `:8`. |
| L3 | structural | `_patch_holdings_row` is un-fenced (scans all lines) | **Resisted** — the `len≥10` change *narrows* the match surface (excludes 9-col rows); adding a section-fence is behaviour change beyond surgical scope. Noted as pre-existing property. |
| L4 | substantive | `:260` carries `.lstrip("€~").replace(",","")` | **Absorbed** — manifest made explicit: sanitisation moves with the index. |
| L5 | substantive | `:373` `if positions and total_nav` | **Absorbed (loud-guard, operator-authorised)** — behaviour-honesty note added; the re-activated `_patch_summary` no-op is made **loud** (`re.subn` miss-count → `update_portfolio` warning, printed by `main`); end-to-end test asserts Summary **unchanged** + `test_summary_mismatch_warns` asserts the warning fires. Scope-correcting (025 owns the activated branch), not expanding. |
| L6 | substantive | template/live label divergence | **Absorbed** — fixture Summary uses live labels (`Cash`/`Invested (MTM)`), not synthetic `(post-fill)`. |
| L7 | substantive | parser hard-codes column count | **Partial — explicit per-part:** part (a) inline column-count comment (`# Holdings table is 10-column…`) **absorbed** (ghost-contract discipline, comment not logic); part (b) broader `len(cols)!=10 → warn` shape-guard **resisted** as new behaviour beyond surgical scope. |
| L8 | substantive | `_patch_trade_row` cell-by-cell | **Absorbed** — surgical-scope claim now shows the audited cell map (not asserted). |
| L9 | substantive | `_patch_trade_row` `len≥6` + `cols[2]` discriminator | **Resisted** — safe today (`cols[2]`=Name≠ticker); pre-existing, untouched. |
| L10 | substantive | `_patch_holdings_row` writes `str(price)` | **Resisted** — pre-existing formatting behaviour, **unchanged** by the index fix; not introduced here. |
| L11 | craft | live ledger 0 PENDING rows (`grep -c`) | **Absorbed** — "intact" note now cites both reasons (no-op guard + zero PENDING rows). |
| L12 | substantive | `:30-34` import-time `sys.exit(1)`; ib_insync installed here | **Absorbed** — test carries `pytest.importorskip("ib_insync")` for portability. |
| L13 | substantive | dormant→active P&L path | **Absorbed** — folded into the L5 behaviour-honesty note (currency L6 dormant: both holdings `.DE`/EUR). |
| L14 | craft | aggregate-count discipline | **Absorbed** — DoD#6 now carries the breakdown-sum check. |
| L15 | substantive | `_pending_tickers` whole-line vs cell match | **Resisted** — pre-existing asymmetry, safe today; noted in surgical-scope evidence. |

**Banked to PROGRESS (tracked S-items, not silent defers; steering-sequenced):**
- **IMMEDIATE-NEXT (prioritised):** the L14 defect — `_patch_summary` 3-way label reconciliation across script + tracked template + live ledger. 025's loud-guard makes the no-op *visible* but does not *fix* it; this is the prioritised follow-up.
- **Lower priority:** L6 currency mismatch (dormant — no non-EUR-venue holdings today).

**Deferred to future clean re-propose (fresh session):** S-21 `--snapshot` + S-23 ISIN guard/threading (absorb L5-normalise / L7-join / L10-List from the 024 pass).

## Status Log

- 2026-06-04 — DRAFT written. Successor to SUPERSEDED 024 (foundation-first, operator-ruled via steering). Pre-flight verified on disk: live ledger intact (no corruption); column map `[1]=ISIN`; exhaustive `cols[` audit → only `_parse_open_holdings` + `_patch_holdings_row` drifted; next-number 025 confirmed against dir + README.
- 2026-06-04 — Isolated-Challenger R1 `flawed` (15 L-items); all verified on disk; 9 absorbed inline (no scope expansion) + 5 resisted (pre-existing/out-of-surgical-scope) + L7 partial. Delta Annexe above. Reported to steering.
- 2026-06-04 — **APPROVED** by operator (via steering): anchors verified on disk; one scope-correcting absorption added — make the re-activated `_patch_summary` no-op **loud** (`re.subn` → `update_portfolio` warning, confirmed printed by `main`). L7 partial split made explicit (a-absorbed / b-resisted). L14 banked as IMMEDIATE-NEXT S-item, L6 lower. 10 absorbed + 5 resisted; no scope expansion → no further round. → implement via Sonnet implementation-agent (049 guardrail live).
- 2026-06-04 — **DONE.** Implemented via Sonnet implementation-agent (diff verified against §6: `scripts/reconcile_ibkr.py` 2 drifted functions corrected + loud-guard; new `tests/test_reconcile_ibkr.py` + `tests/fixtures/portfolio_10col.md`; agent correctly returned `[OUT OF SCOPE]` on the orchestrator's own pre-existing `proposals/README.md` edit and left it untouched — 049 guardrail working). Runtime observation shown: real parse→patch→re-parse (`WRLD.DE`+`TSTX.DE` both OPEN), Holdings/Trade-History rows correct, loud Summary-mismatch warning fired. `/code-reviewer` APPROVE WITH NOTES (1 NOTE — print-says-"updated"-while-stale — folded inline: print now reads `stale (label mismatch)`). Full suite 91 passed / 1 skipped (4 new). PROGRESS S-27 (immediate-next) + S-28 banked + Foundation note on S-21/S-23; CHANGELOG `[Unreleased] ### Fixed`. Status DONE across frontmatter / README / this log.
