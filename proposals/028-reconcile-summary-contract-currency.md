---
id: 028
title: Reconcile Summary canonical contract (S-27) + currency-aware pricing (S-28)
status: DONE
owner: Daniel
opened: 2026-06-10
updated: 2026-06-10
tags: [reconcile, S-27, S-28, summary-contract, currency, fx]
---

# 028 — Reconcile Summary canonical contract (S-27) + currency-aware pricing (S-28)

**Tier: MEDIUM** — 4 MODIFY + 1 CREATE = 5 files (`scripts/reconcile_ibkr.py`, `local/templates/PORTFOLIO.template.md`, `tests/test_reconcile_ibkr.py`, `proposals/README.md`, this artefact). Within established patterns; built on the sound post-025/026 10-column ISIN foundation. No new architecture, no irreversible step.

## Summary

Two coupled defects in `scripts/reconcile_ibkr.py`, both surfaced as Challenger L-items during the 025 close-out and both on the now-sound 10-column foundation:

- **S-27** — `_patch_summary`'s five label anchors carry a `(post-fill)` suffix that matches **neither** the tracked template **nor** the live ledger labels. Floor audit (2026-06-10) refines the PROGRESS wording: against the **template** it is a *full* mismatch (0/5); against the **live ledger** it is a *partial* mismatch (3/5 match, Cash + Invested miss) → a real reconcile today produces a **partial** patch (3 fresh rows + 2 stale rows in one table) while the 025 warning misreports it as "Summary not updated". Fix = a **canonical Summary contract** reconciled across four surfaces: script anchors ↔ template ↔ live ledger ↔ test fixture.
- **S-28** — `_fetch_live_prices` feeds a native-venue price straight into a base-currency (EUR) unrealised-P&L computation in `_patch_summary`; a holding on a non-EUR venue yields a wrong-magnitude P&L. Dormant today (all current holdings on EUR venues). Fix = venue-currency check (`fast_info.currency`); a non-base-currency venue is **flagged and its P&L mark omitted** (loud WARNING), **not** FX-converted — see §B5 / Risk L9: converting the live mark while the entry-cost leg is currency-unaware (banked F2, write-side) produces a *worse* P&L than omitting it, so convert-mode is deferred to a bundle that also fixes F2 (changed from convert-or-flag after Challenger R1 L7/L8/L9).

**Floor-audit headline (de-risks the design):** the live ledger Summary is **already fully conformant** with the canonical anchor set — all six core anchors match exactly once file-wide (verified via a digit-redacting labels-only subprocess, 2026-06-10). Aligning the script anchors to the live labels therefore requires **no live-ledger edit at all**; only the script and the tracked template change, and the fixture already conforms. The high-risk live-edit subprocess machinery collapses to a redacted *verification*.

## Motivation / Problem

Evidence (all disk-verified at floor audit, 2026-06-10):

- `_patch_summary` (`scripts/reconcile_ibkr.py:305-371`) anchors on five labels — `**Cash (post-fill)**`, `**Invested (post-fill)**`, `**Unrealised P&L**`, `**Number of open positions**`, `**Equity exposure[^|]*\*\*`. Each `_sub` is `count=1` and **not section-scoped** (patches the first matching occurrence anywhere in the file).
- **Live ledger Summary** (read via redacted subprocess) = 7 labels: `Total NAV`, `Cash`, `Invested (MTM)`, `Unrealised P&L`, `Realised P&L (YTD)`, `Number of open positions`, `Equity exposure (% NAV)`. File-wide match counts for the canonical anchors: **all = 1** (Total NAV READ, Cash, Invested (MTM), Unrealised P&L, Number of open positions, Equity exposure each match exactly once).
- **Tracked template** (`local/templates/PORTFOLIO.template.md:24-32`) = 4 labels: `Total NAV (entry)`, `Cash Reserve`, `Invested`, `Sessions completed` → 0/5 script anchors match.
- **Test fixture** (`tests/fixtures/portfolio_10col.md:24-32`) = 6 labels (the live set minus `Realised P&L (YTD)`) → already matches the canonical core set.
- `_parse_total_nav` (`:274-277`, regex `\*\*Total NAV[^|]*\*\*`) is a READ anchor matching **both** `**Total NAV (entry)**` and `**Total NAV**`; it gates the entire Summary branch (`:398 if positions and total_nav:`). A broken NAV match silently skips all Summary patching.
- The 025 loud-warning (`:402-406`) hardcodes `/5`, references a stale `pending L14`, and says "Summary not updated" even when 3 rows were patched.
- `_fetch_live_prices` (`:280-302`) returns `fast_info.last_price` with no currency check; `_patch_summary:320` computes `prices[t]*qty − entry_cost` where `entry_cost` is EUR. The 026 bare-ticker guard (`:294-297`) is adjacent and must not regress.

## Proposal

### A. Canonical Summary Contract (S-27) — FIXED at approval

This table is the contract. **Reclassifying any row later to dodge a gate is a scope change requiring re-approval.** "CORE" rows (1–6) appear on all three document surfaces and are DoD-1-enforced; rows 7–8 are documented per-surface manual divergences (permitted for the two audiences — onboarding template vs running ledger).

| # | Canonical label | Class | Source of value | Template | Live | Fixture |
|---|---|---|---|---|---|---|
| 1 | `**Total NAV**` | MANUAL (READ anchor — gates Summary branch) | manually maintained NAV input | ✓ placeholder `€` | ✓ | ✓ |
| 2 | `**Cash**` | SCRIPT-PATCHED | `total_nav − Σ entry_cost` | ✓ placeholder `€` | ✓ | ✓ |
| 3 | `**Invested (MTM)**` | SCRIPT-PATCHED | `Σ entry_cost` (cost-basis — see Risk L3) | ✓ placeholder `€` | ✓ | ✓ |
| 4 | `**Unrealised P&L**` | SCRIPT-PATCHED | `Σ (live_px·qty − entry_cost)`, base-ccy | ✓ placeholder `—` | ✓ | ✓ |
| 5 | `**Number of open positions**` | SCRIPT-PATCHED | `len(open positions)` | ✓ placeholder `0` | ✓ | ✓ |
| 6 | `**Equity exposure (% NAV)**` | SCRIPT-PATCHED | invested % + per-position breakdown | ✓ placeholder `0%` | ✓ | ✓ |
| 7 | `**Realised P&L (YTD)**` | MANUAL | uncomputable here (SELL parsing out of scope) | ✗ | ✓ | ✗ |
| 8 | `**Sessions completed**` | MANUAL | onboarding context | ✓ | ✗ | ✗ |

SCRIPT-PATCHED anchor count = **5** (rows 2–6). Total NAV (row 1) is the READ anchor.

**Realised P&L (YTD) stays MANUAL — populating it is a banned scope expansion.** Fills enter the ledger BUY-side only (`side != "BOT"` skipped, `:83/:130`); SELLs never reach the ledger via this script, so realised P&L is uncomputable without SELL parsing. Banked as a follow-up (Out-of-Scope §F1).

### B. Script changes (`scripts/reconcile_ibkr.py`)

1. **Anchor rename + exact regex forms (S-27).** Anchors held as a data list so the count is derived, not hardcoded. Exact regex forms (all literal parens/percent escaped — an unescaped `(MTM)` would become a regex capture group and shift the `\g<1>` back-reference, corrupting the substitution; Challenger L14):
   - `\*\*Cash \(post-fill\)\*\*` → `\*\*Cash\*\*`
   - `\*\*Invested \(post-fill\)\*\*` → `\*\*Invested \(MTM\)\*\*`
   - `\*\*Unrealised P&L\*\*` — unchanged (already matches live/fixture).
   - `\*\*Number of open positions\*\*` — unchanged.
   - `\*\*Equity exposure[^|]*\*\*` → **tightened** to the literal `\*\*Equity exposure \(% NAV\)\*\*` (Challenger L5: the `[^|]*` wildcard matches any `**Equity exposure …**` sibling, diverging from DoD-1's literal-label count; the literal reconciles script anchor ↔ contract label ↔ audit predicate). Each anchor's first group is the label-prefix capture for `\g<1>`.
2. **Section-scope the patching (RULING).** `_patch_summary` patches only within the `## Portfolio Summary` section (header line → next `## ` or EOF), mirroring the existing `in_holdings` idiom in `_parse_open_holdings`/`_pending_tickers`. **Rationale:** the canonical labels (`**Cash**`, `**Total NAV**`) are generic enough that first-occurrence-anywhere is fragile against future prose drift; section-scoping removes the fragility and matches the file's existing idiom.
   - **Header match is precise, not prefix (Challenger L1).** The header is detected by `re.match(r"##\s+Portfolio Summary\s*(\(.*\))?\s*$", line)` — matches the bare template header AND the live `## Portfolio Summary (post Session #3 …)` parenthetical form, but **not** a `## Portfolio Summary Notes`-style sibling (`startswith` would prefix-collide). The header is the natural anchor and is **inside** Summary-scope. DoD-1 additionally asserts exactly one matching header per surface.
   - **No-section semantics (Challenger L12).** If no header matches, `_patch_summary` returns `(text_unchanged, n_total, n_total)` — all anchors missed → the full-no-op warning fires. It **never** falls back to whole-text patching (which would silently restore the old file-wide behaviour). An empty slice yields all-missed, not a vacuous all-matched.
   - **Splice mechanic (Challenger R2 L14).** The slice is taken by *line index* (header-line index → next `## `/EOF), the five `_sub` calls run on the joined slice, `misses` is counted over the slice, and the result is reassembled positionally (`head_lines + patched_slice + tail_lines`) — **never** via `text.replace(old_slice, new_slice)` (which could false-match a recurring separator row elsewhere).
   - The current live header ends in `)` with no trailing prose (confirmed: the digit-redacted floor-audit read preserved structure, only digits masked), so the `\s*$` anchor holds; a *future* header with trailing prose after the parenthetical would fail the match → full-no-op + loud warning (fail-loud, never a silent mis-patch — Challenger R2 L4).
   - All *other* live↔template section drift (Dividends/Notes naming) is **out of scope** (observation only, §E).
3. **`_parse_total_nav` stays file-wide (CONSCIOUS RULING).** Its contract is kept intact; the DoD-1 exactly-once guarantee (Total NAV matches once file-wide on every surface — verified) makes the file-wide read unambiguous. Not section-scoped to keep the change surgical.
4. **Warning rework (025 / S-27).** `_patch_summary` returns `(text, n_missed, n_total)` where `n_total = len(anchors)` = **5 script-patched anchors** (derived). The two existing 2-tuple unpack sites MUST update in lockstep (Challenger L3): the caller `scripts/reconcile_ibkr.py:401` (`text, n_missed = …`) and the direct-call test `tests/test_reconcile_ibkr.py:151` (`patched, _ = …`). The `_patch_summary` docstring (`:306-310`) is updated to describe the 3-tuple return, and the stale `pending L14` reference there is removed (Challenger L15). `update_portfolio` emits:
   - `n_missed == 0` → no warning; print `Portfolio Summary updated ({n_total}/{n_total} labels)`.
   - `0 < n_missed < n_total` → warning `Summary partially updated — {n_total-n_missed}/{n_total} script-patched labels matched; {n_missed} label(s) missing from the Portfolio Summary section (check for label drift)`.
   - `n_missed == n_total` → warning `Summary not updated — 0/{n_total} script-patched labels matched in the Portfolio Summary section (template/ledger label drift)`.
   Drops the hardcoded `/5` and the stale `pending L14`; distinguishes full no-op from partial patch. **Terminology (Challenger L16):** `n_total` counts the **5 script-patched** anchors; DoD-1 audits **6** anchors (those 5 PLUS the Total NAV READ anchor). The warning says "script-patched labels" (not "canonical labels") to avoid colliding with the §A "CORE 6" framing (Challenger L20).
5. **Currency-aware pricing (S-28) — FLAG-ONLY ruling.**
   - New module constant `BASE_CURRENCY = "EUR"` (the ledger denomination; matches the existing `€` convention and the `"EUR"` fill-currency defaults at `:75/:122`).
   - `_fetch_live_prices` binds `fi = yf.Ticker(ticker).fast_info` **once** (Challenger L18 — no double network fetch), reads `native = float(fi.last_price)` and `ccy = getattr(fi, "currency", None)`.
     - **Confirmed-base only (Challenger R2 L6).** The mark is stored `round(native, 2)` **only when `ccy` is a non-empty string equal (case-insensitive) to `BASE_CURRENCY`**. An empty / `None` / unrecognised currency is *not* confirmed-base → skipped (we cannot confirm the live mark is in EUR; skip-don't-misprice, 026 philosophy).
     - Any non-base or unconfirmable venue (non-EUR ISO code, minor-unit code like `GBp`, or empty/`None`) → **skip the mark with a loud, plain-language WARNING** — `{ticker} priced in {ccy or 'unknown currency'} — P&L mark omitted (non-EUR pricing not yet supported)` (no internal proposal/roadmap codes in operator output — Challenger R2 L10). The position is absent from `prices`.
   - **Why flag, not convert (Challenger L7/L8/L9 — the deciding constraint).** FX-converting only the live mark is *unsound while F2 is open*: a non-EUR holding's `entry_cost` is parsed from the ledger as a native-magnitude number wearing a `€` sign (`_patch_holdings_row:207` writes `f"€{all_in}"` for a native fill; `_parse_open_holdings:261` strips the `€` and reads the native magnitude as EUR). `_patch_summary:320` computes `live_mark·qty − entry_cost`; converting only the live leg to EUR while the cost leg stays native-magnitude yields a *mismatched-unit* P&L — **worse** than the unconverted number. Converting also re-introduces wrong-magnitude bugs convert-mode is meant to fix: a NaN FX `last_price` is truthy in Python → `€nan` silently written (L7); `GBp` pence `.upper()`→`GBP` → 100× error (L8). Flag-only sidesteps all three by never converting. **FX source ruling: none this bundle** — no new network dependency, no `_fetch_fx_rate`, Wallet-Bleed surface eliminated. Convert-mode + F2 write-side currency persistence ship together in a future bundle (banked F4).
   - The 026 bare-ticker guard and the `import yfinance` guard are preserved byte-for-byte; the currency check sits *after* them, inside the existing per-position `try/except`.
   - A skipped (non-base-venue) position is absent from `prices`, so `_patch_summary`'s existing `(partial: n/m marks)` annotation (026) surfaces the reduced mark count; the printed WARNING makes the currency skip visible in the console. **Note (Challenger L6):** the partial-mark *count* is aggregate — it does not itself distinguish a currency skip from the silent generic-fetch failure at `:300-301`; the console WARNING is the distinguishing signal. The generic-fetch-failure silence is pre-existing 026 behaviour, untouched.
   - **All-skipped message fix (Challenger R2 L5).** When *every* position is skipped (an all-non-EUR portfolio under flag-only), `prices == {}` and `_patch_summary` falls to its `else` branch (`:328-329`), which today prints the misleading `n/a (yfinance unavailable)`. That message is changed to a reason-neutral `n/a (no live marks — see warnings above)` so an all-non-EUR portfolio is not mislabelled as a yfinance outage. **Two-state messaging is intentional (Challenger R3 L2):** the mixed case shows `(partial: n/m marks)` and the all-skipped case shows `no live marks` — two distinct true states. The per-position currency WARNING prints inside `_fetch_live_prices` for *each* skipped position in **both** cases, so the operator always sees the currency reason above the Summary line; the two Summary strings are deliberately not unified.
   - **Orthogonality with the 026 carve-out (Challenger R2 L1/L2 — a deliberate consequence, not a regression).** The currency check is *downstream of and orthogonal to* the 026 bare-ticker collision guard. The 026 guard decides WHICH instrument resolves (collision avoidance); flag-only decides WHETHER its mark enters the base-currency P&L. A genuinely-USD holding (e.g. a US-ISIN bare ticker the 026 carve-out admits — `fast_info.currency == "USD"`) resolves correctly but its mark is **omitted** for the same currency-soundness reason as any non-EUR venue. This is the safer posture: today such a holding yields a silently currency-confused P&L *magnitude* (the sign may still be directionally informative, but the magnitude is unsound under a `€` label — Challenger R3 L5); flag-only converts that into an honest flagged gap. The 026 carve-out still does its job (it prevents the DFEN-class mis-resolution); flag-only simply declines to mark a non-EUR result.

### C. Template (`local/templates/PORTFOLIO.template.md`) — tracked carve-out, placeholders only

Replace the 4-label day-zero Summary with the canonical CORE 6 + the manual `Sessions completed`, all with day-zero placeholder values (`€`, `—`, `0`, `0%`) — **no economics-shaped literals** (S-30 hook gate + S-31 rule). `Total NAV (entry)` → `Total NAV`; `Cash Reserve` → `Cash`; `Invested` → `Invested (MTM)`; add `Unrealised P&L`, `Number of open positions`, `Equity exposure (% NAV)`; keep `Sessions completed`. **Row order (Challenger R2 L15):** Total NAV, Cash, Invested (MTM), Unrealised P&L, Number of open positions, Equity exposure (% NAV), then Sessions completed last. Only the `## Portfolio Summary` section is touched; Dividend/Notes sections untouched.

### D. Live ledger + fixture — VERIFY ONLY, no edit

- `local/PORTFOLIO.md`: already conformant (all six anchors match exactly once — verified). **No edit.** DoD-1 live-side re-verified via the digit-redacting labels-only subprocess (output = per-anchor match counts only; values never enter context).
- `tests/fixtures/portfolio_10col.md`: already carries the canonical CORE 6. **No edit** (verified by DoD-1 direct grep).

### E. Out-of-scope drift (observation, not fixed)

Live↔template section-name drift beyond Summary (`Ownership Tracking` / `Dividends Received` / `Notes for Agents` vs template `Dividend & Income Log` / `Notes`) is **named here as an observation** and deliberately not touched (S-27 is Summary-scope only).

## Scope & Out-of-Scope

**In scope:** script anchor rename, section-scoping, warning rework, **S-28 currency check + flag-only** (non-base venues flagged, marks omitted; **no** FX conversion this bundle — see §B5), template canonical alignment, test updates, live/fixture verification.

**Out of scope (banked follow-ups):**
- **F1 — Realised P&L (YTD) population** — needs SELL-side fill parsing; scope expansion, banned this bundle.
- **F2 — Write-side currency-unawareness** — `_patch_holdings_row:207` writes `f"€{all_in}"` unconditionally; the fill captures `fill.contract.currency` (`:96/:143`) but never uses it. Same currency-unaware class as S-28 but on the WRITE side. Surfaced for the operator to rule on; **NOT folded in** (G15 — avoid scope-expanding absorption).
- **F3 — `Invested (MTM)` semantic relabel** — the script writes cost-basis under an "(MTM)" label. Pre-existing live-ledger label; the contract adopts it to avoid a live-ledger edit. Relabel or recompute = future follow-up.
- **F4 — S-28 convert-mode + minor-unit currencies** — true FX conversion of non-base marks (a guarded `_fetch_fx_rate` with NaN/finiteness checks, plus minor-unit handling such as `GBp` pence→pounds) ships **together** with F2 (currency-aware entry-cost persistence) so both P&L legs convert consistently. Connects to S-29 (multi-source pricing). Deferred — convert-mode is unsound while F2 is open (Challenger L7/L8/L9). **Recorded as a new roadmap item (candidate S-32) at close-out** so it has a tracked home (Challenger R2 L7). Flag-only is an *improvement* for a non-EUR (e.g. `GBp`/LSE) holding — today the P&L is silently currency-confused (pence magnitude under a `€` label); flag-only makes it an honest flagged gap pending S-32.
- **S-21 / S-24 / S-25 / S-29 / S-31** — explicitly excluded (stop rule).

## Definition of Done

> The four floor gates below are quoted verbatim from the session brief and are the binding DoD floor.

1. **Post-alignment mechanical label-match check:** every anchor classified SCRIPT-PATCHED on a given surface per the approved contract table, PLUS the Total NAV READ anchor, matches EXACTLY ONCE — counted FILE-WIDE — on each of the three document surfaces (template, live ledger, fixture; the script is the anchor-source side). File-wide counting is the safe default under first-occurrence semantics; because this proposal rules section-scoped patching it ADDS an in-section check, never replacing the file-wide count. Live side runs via the redacted subprocess; output = per-anchor match counts only. This is the S-27 success predicate — a typo'd or partial live edit must fail it.
2. **Runtime observation through the production entry-point:** call `update_portfolio` with a synthetic fills dict (fills is a parameter — nothing to monkeypatch there) against a tmp-copy synthetic ledger, monkeypatching `PORTFOLIO_PATH` and `_fetch_live_prices` (NOT a live IBKR call). CLI output shown: full-match Summary patch, the reworked partial/no-op warning, and the S-28 currency flag path.
3. **Full suite green BEFORE the commit is presented:** compare against the 110 passed / 1 skipped baseline AND show the reconcile tests PASSED rather than skipped (`tests/test_reconcile_ibkr.py:10 importorskip("ib_insync")` can silently skip all 10).
4. **Test the guard at the entry-point:** new currency/label guards exercised through `update_portfolio`, not only helper-level asserts.

**DoD-2 reconciliation (Challenger L2/L17).** DoD-2's `_fetch_live_prices` monkeypatch covers the *label / partial-no-op* demo (deterministic prices, no network). The *S-28 currency-flag* demo is shown separately by **injecting a fake `yfinance`** (via `sys.modules`, the existing `:96-97` idiom) so the **real** `_fetch_live_prices` runs through `update_portfolio` and the currency guard is traversed at its production call site — satisfying DoD-4 (guard at the entry-point, not the helper). Both demos appear in the DoD-2 CLI output. **No live confirmatory run (Challenger R2 L13):** the runtime observation runs ONLY against the synthetic tmp ledger — running `reconcile_ibkr.py` against the real `local/PORTFOLIO.md` (its default `PORTFOLIO_PATH`) is FORBIDDEN; its console echo would print live Cash/Invested/P&L into context, breaching the privacy fence.

**Implementation-specific binary checks:**
5. **DoD-1 concrete commands (privacy-pinned, Challenger L13/L19).** For each CORE anchor, `grep -cE '<anchored regex>'` on template + fixture == 1 (anchored regex, e.g. `\*\*Cash\*\*` — never a bare `Cash` substring, so no false-match inside `**Cash Reserve**`); exactly one `## Portfolio Summary` header per surface; in-section count within that section == 1 on all three. **Live side ONLY via the digit-redacting labels-only subprocess emitting per-anchor integer match-counts** — never `grep -n`/matched content; every printed string digit-redacted (`re.sub(r"\d","#",s)`), headers included. All counts == 1 (re-confirmed at close).
6. **`test_update_portfolio_end_to_end` Cash assertion FLIPS** (Challenger R2 L3): pre-alignment the Cash row was a no-op (the fixture value, unpatched); post-alignment the Summary patches, so Cash becomes `total_nav − Σ entry_cost` with a `({cash_pct}%)` suffix. The implementer MUST replace the old no-op assertion (and delete the stale `# Summary unchanged (L14 no-op)` comment) with one that proves the flip. Asserted **structurally** — the patched Cash row carries a `(NN.N%)` suffix the pre-patch no-op value lacks — **not** by hardcoding the computed economics literal: the fixture carries accepted-exposure real-colliding values (2026-06-04 sanitisation audit note), so a fixture-derived literal in the tracked test would trip the S-30 hook (S-31, confirmed at this proposal's own close-out). Falsifiable: a Summary that failed to patch shows no `(%)` suffix.
7. **`test_summary_mismatch_warns` split into two** (Challenger L4 / R2 L11 concrete names), each with a bespoke in-memory ledger carrying a real `## Portfolio Summary` section: (a) `test_summary_partial_patch_warns` — drift ONE script-patched label → asserts the `partially updated — N/M` string; (b) `test_summary_full_noop_warns` — a section with none of the script-patched labels → asserts the `Summary not updated — 0/M` string. The aligned fixture now yields `n_missed == 0` (no warning), so the old single-test premise is gone. NEW asserts on the reworked strings. **The old `test_summary_mismatch_warns` is removed/replaced by these two** (Challenger R3 L4): its `"… label mismatch"` substring no longer fires (the reworked message drops that phrase). This is NOT a DoD-10 "coverage deleted" violation — the warning-path *behaviour* coverage is preserved and *extended* (partial + full-no-op); DoD-10's no-delete rule governs behaviour coverage, not function names.
8. **`test_patch_summary_partial_mark_annotation`** wrapped in a `## Portfolio Summary` section (section-scoping requires one) AND its `patched, _ = …` unpack updated to the 3-tuple (Challenger L3).
9. **New S-28 tests (flag-only), through the production entry-point** (Challenger L2/L17): inject a fake `yfinance` whose `fast_info` carries a `currency` field, then call `update_portfolio` (real `_fetch_live_prices` runs): (a) EUR venue → priced; (b) non-EUR venue (`USD`) **alongside ≥1 EUR position** (so `prices != {}`) → the USD mark omitted + WARNING, surfaced as `(partial: n/m marks)` in the patched Summary (Challenger R3 L1: the partial annotation requires ≥1 other priced position; a single-USD ledger instead hits the all-skipped `no live marks` message — assert that separately); (c) minor-unit (`GBp`) → treated as non-base → **asserts the position is absent from `prices` AND the WARNING fired** (not a vacuous "NOT 100×-converted" check against a non-existent path — Challenger R2 L9); (d) unconfirmable currency (`None`/empty) → also skipped (Challenger R2 L6). `_FakeFastInfo` gains a `currency` field defaulting to `"EUR"` so existing `test_guard_*` stay green (a real USD holding reports `USD` → would skip; the EUR default isolates the *guard* test from the *currency* rule — see §B5 orthogonality). Coverage UPDATED, never deleted.
10. **No regression / suite (Challenger L10):** 026 bare-ticker guard tests + `import yfinance` guard preserved byte-for-byte and green. The DoD-3 "110 passed / 1 skipped" baseline is a **floor, not a ceiling** — all 110 prior tests still green + the new S-28/label tests green (post-change total > 110); reconcile tests PASS, not skip. **Residual-marker sweep (Challenger R3 L3):** `grep -rn 'L14' scripts/reconcile_ibkr.py tests/test_reconcile_ibkr.py` returns 0 at close (both the docstring `pending L14` at `:309` and the test comment `# Summary unchanged (L14 no-op)` at `:62` removed).

## Risks & Mitigations

- **Wallet Bleed (review-patterns vector):** ELIMINATED — flag-only S-28 adds **no** FX fetches (no `_fetch_fx_rate`); `_fetch_live_prices` binds `fast_info` once per position (no double fetch, Challenger L18). Script runs monthly, read-only.
- **Non-base-venue P&L omission (S-28 flag-only):** a non-EUR holding gets no unrealised-P&L mark (`partial: n/m`) until convert-mode + F2 land. This is the correct conservative behaviour (Challenger L9: converting one leg while the cost leg is native-magnitude is *worse* than omitting). Loud WARNING + partial-mark annotation make it visible — never a silent wrong-magnitude number.
- **Section-scoping ripple:** inverts the line-62 Cash assertion, requires section-wrapping the line-149 bare-text test, and splits the mismatch test in two. *Mitigation:* DoD 6–9 update coverage explicitly; no coverage deleted.
- **Return-arity change:** the 2→3-tuple breaks the `:401` caller and `:151` test unpack. *Mitigation:* both enumerated in §B4; DoD-8 covers the test.
- **`_parse_total_nav` file-wide read retained:** relies on Total NAV appearing once file-wide. *Mitigation:* verified == 1 on all surfaces (anchored regex, not bare substring — Challenger L13); DoD-1 re-asserts it.
- **No live-ledger edit needed:** the highest-risk operation (live-economics edit) is eliminated by the floor-audit finding; only a digit-redacting count-only read remains (Challenger L19 — never `grep -n`/content on the live ledger).
- **Template change blast (init_workspace):** `init_workspace.py:31` copies the template at onboarding → new ledgers inherit the canonical labels. This is the intended forward-correctness effect; placeholders only, no economics.

## Core Team Review (A–D) — inline (no `persona-*.md` files present)

> **Note:** these A–D verdicts were rendered on the *convert-mode* draft. The Cross-Check (below) subsequently changed S-28 to **flag-only** (strictly safer). Where a review mentions FX machinery (FX cache, FX-fetch wrapping), read it as superseded — there is no FX call in the shipped design. §Scope and the DoD reflect flag-only.

### A — Quant Architect
Anchors-as-data + section-scoping reuse the established `in_holdings` idiom — no duplication, no magic `/5`. `BASE_CURRENCY` extracts the implicit EUR. One concern: `Invested (MTM)` labels a cost-basis figure — flag the semantic gap (Risk L3) rather than silently enshrining it. **APPROVE WITH CONDITIONS** — (1) anchor list is the single source for the count; (2) the `(MTM)` semantic imperfection is explicitly banked, not hidden.

### B — Portfolio Manager
Minimum scope that fixes a real silent-no-op the investor would otherwise trust. No live-ledger edit is the right call — capital-data integrity preserved. Resist F1/F2 firmly. **APPROVE** — scope is tight; banked follow-ups are correctly deferred.

### C — CTO
yfinance-native FX = no new key, no secret, idempotent (read-only). FX cache bounds the call count. Degrade-to-flag is the correct failure posture. Confirm the `import yfinance` guard and 026 bare-ticker guard are byte-preserved. **APPROVE WITH CONDITIONS** — (1) FX fetch wrapped so a network failure flags, never crashes; (2) 026 guard regression test stays green.

### D — Risk Officer
The currency bug is dormant but real — a non-EUR venue today silently misreports P&L magnitude, which corrupts the risk dashboard. Flag-not-crash is correct: a missing mark is safer than a wrong one (consistent with 026's skip-don't-misprice philosophy). The partial-vs-no-op warning distinction matters — a half-stale Summary read as "not updated" is a risk-reporting blind spot. **APPROVE WITH CONDITIONS** — the FX-skip must be loud (printed WARNING + partial-mark annotation), never a silent omission.

**Consolidated conditions** (all absorbed into the plan): anchor-list-derived count; `(MTM)` semantic gap banked (F3); 026 guard byte-preserved + tested; non-base-venue skip is loud (plain-language WARNING + partial-mark annotation). *(Post-R1 the design changed to flag-only — there is no FX call; the CTO "FX failure must flag not crash" and Risk "FX-skip loud" conditions are satisfied a fortiori.)*

## Delta Annexe — Round 1 (Core Team)
- **Absorbed:** A's anchor-list-source-of-count (already in §B1); A+architecture's `(MTM)` semantic-gap → banked as F3 + Risk L3 (scope-correcting, not expanding). C's FX-failure-flags + 026-byte-preservation → §B5. D's loud-FX-skip → §B5 (WARNING + partial mark).
- **Resisted:** none — all conditions narrow or clarify the existing surface; none expand scope.

## Delta Annexe — Round 2 (Dual-Model Cross-Check)

`Cross-Check path: isolated-challenger — reason: no external/alternate model API is configured in this Claude Code session (CLAUDE.md §3 condition a).`

**R1 verdict: `flawed`, 20 L-items (5 structural).** Every claim leaned upon was independently verified (CLAUDE.md §2 External-agent-claim + FATAL-claim verification) against the actual files before absorption. **All 20 absorbed; none resisted; none required scope EXPANSION** (the single large delta — S-28 convert→flag-only — is scope-REDUCING, G15-safe). The deciding delta is L7/L8/L9 → the flag-only redesign.

## Adversarial Loophole Pass (L1–L20)

| L | Severity | Disposition |
|---|---|---|
| **L1 — Header prefix-collision** | structural | **ABSORBED** — header detection changed from `startswith` to `re.match(r"##\s+Portfolio Summary\s*(\(.*\))?\s*$")` (§B2); DoD-1 asserts exactly-one header/surface. Verified: live header form via redacted floor-audit read; template/fixture bare headers via direct Read. |
| **L2 — DoD-2 stubs out the S-28 path** | structural | **ABSORBED** — DoD-2 reconciliation note + DoD-9: the currency-flag demo injects a fake `yfinance` so the real `_fetch_live_prices` runs through `update_portfolio` (DoD-4 entry-point). Verified `_fetch_live_prices` houses the guard (`:280-302`). |
| **L3 — Return-arity breaks `:401`/`:151` unpack** | structural | **ABSORBED** — both unpack sites enumerated in §B4; DoD-8 covers the test. Verified `:401 text, n_missed = …` and `:151 patched, _ = …`. |
| **L4 — Repurposed test can't reach both branches on the aligned fixture** | structural | **ABSORBED** — split into two bespoke-ledger tests (DoD-7). Verified the fixture's 6 labels make `n_missed==0` post-rename. |
| **L5 — Equity wildcard `[^|]*` ≠ DoD-1 literal count** | structural/substantive | **ABSORBED** — anchor tightened to literal `\*\*Equity exposure \(% NAV\)\*\*` (§B1). Verified wildcard at `:367`. |
| **L6 — Skip reasons indistinguishable in the partial-mark count** | substantive | **ABSORBED (claim corrected)** — §B5 now states the count is aggregate; the console WARNING is the distinguishing signal; generic-fetch silence is pre-existing 026. Verified silent `except` at `:300-301`. |
| **L7 — NaN FX rate → `€nan`** | substantive | **ABSORBED by redesign** — flag-only removes FX conversion entirely; no rate to validate. (Would have needed `math.isfinite`; now moot, banked into F4.) |
| **L8 — `GBp` pence `.upper()`→`GBP` → 100×** | substantive | **ABSORBED by redesign** — any non-EUR code (incl. minor units) is flagged+skipped, never converted; the 100× path cannot arise. Minor-unit handling banked F4. |
| **L9 — Convert only the live leg while cost leg is native-magnitude → worse P&L** | substantive | **ABSORBED — the deciding constraint** → flag-only (§B5). Verified `_patch_holdings_row:207 f"€{all_in}"` + `_parse_open_holdings:261` strip-€. |
| **L10 — DoD-3 "110 passed" is stale after adding tests** | substantive | **ABSORBED** — DoD-10 frames the baseline as a floor (≥110 prior green + new green), not an exact post-count. DoD-3 text kept verbatim (brief floor). |
| **L11 — DoD-6 asserts an unstated Cash literal** | substantive | **ABSORBED** — DoD-6: exact literal lives in the test (S-31), proposal states the formula. |
| **L12 — No-section case n_missed semantics undefined** | substantive | **ABSORBED** — §B2 no-section ruling: returns `(text, n_total, n_total)` (full-no-op), never whole-text fallback. |
| **L13 — Floor-audit count unverifiable / method unaudited** | substantive | **ABSORBED (method pinned)** — DoD-5 pins anchored-regex count-only; `\*\*Cash\*\*` cannot match inside `**Cash Reserve**` (verified my floor-audit subprocess used the anchored form). Challenger fenced this by privacy; flagged not asserted-false. |
| **L14 — Unescaped `(MTM)` regex group shifts `\g<1>`** | substantive | **ABSORBED** — exact escaped regex forms fixed in §B1. Verified current anchors escape parens (`:347/:352`). |
| **L15 — Docstring still says 2-tuple / "pending L14"** | craft | **ABSORBED** — §B4 mandates the docstring update. Verified `:306-309`. |
| **L16 — "anchor count" means 5 vs 6** | craft | **ABSORBED** — §B4 disambiguates: 5 script-patched (n_total) vs 6 audited (DoD-1). |
| **L17 — DoD-9(c) FX-unavailable path unconstructible from `_FakeYF`** | substantive | **ABSORBED** — moot under flag-only (no FX branch); DoD-9 fake carries a `currency` field for the non-EUR-skip path. Verified `_FakeYF` returns a fixed price for all tickers (`:85-93`). |
| **L18 — Double `fast_info` fetch risk** | craft | **ABSORBED** — §B5 binds `fi` once. |
| **L19 — Live-side audit could leak a value via `grep -n`** | substantive | **ABSORBED** — DoD-5 pins count-only digit-redacted subprocess; never content on the live ledger. |
| **L20 — Warning "canonical" vs §A CORE-6 wording** | craft | **ABSORBED** — warning reworded to "script-patched labels" (§B4). |

**Core Team note:** the A–D review (above) was conducted on the convert-mode draft; the flag-only redesign is *strictly safer* than what they reviewed (CTO's "FX failure must flag not crash" and Risk's "FX-skip must be loud" are satisfied a fortiori — there is no FX call to fail, and the non-base skip is loud). No condition is invalidated.

### Round 2 (delta cross-check on the flag-only redesign) — `flawed`, 15 L-items (3 structural); trajectory 20→15 (strictly decreasing)

All 15 verified and absorbed; none resisted; none scope-expanding. The 3 "structural" items (R2-L1/L2 carve-out interaction, R2-L3 Cash flip) are **artefact-completeness/clarity gaps, not design FATALs** — flag-only *correctly* skips USD marks (consistent with L9); absorbed as documentation + test-clarity + a reason-neutral message fix.

| L (R2) | Sev | Disposition |
|---|---|---|
| L1 — flag-only skips USD marks / 026 carve-out | structural | **ABSORBED (doc)** — §B5 orthogonality note: 026 guard resolves the instrument; flag-only declines its mark (sound, consistent with L9). Honest gap, not regression. |
| L2 — `test_guard_us_isin..._priced` false-green | structural | **ABSORBED** — DoD-9 note: the fake-EUR default isolates the *guard* test from the *currency* rule; a real USD holding would skip. |
| L3 — DoD-6 Cash literal stale/unfalsifiable | structural | **ABSORBED** — DoD-6 mandates the no-op→patched FLIP + stale-comment removal; asserted structurally (`(NN.N%)` suffix present), no economics literal (S-31). |
| L4 — header regex greedy / trailing prose | substantive | **ABSORBED** — §B2: current header verified to end in `)`; a future trailing-prose header fails-loud (full-no-op), never silent. |
| L5 — all-skipped → "yfinance unavailable" lie | substantive | **ABSORBED (code)** — §B5: `else` (`:328`) message → reason-neutral "no live marks — see warnings". |
| L6 — empty/None currency priced-as-EUR | substantive | **ABSORBED (code)** — §B5 confirmed-base-only: only a non-empty `==EUR` prices; empty/None → skip. |
| L7 — GBp no mark indefinitely / F4 untracked | substantive | **ABSORBED** — §F4 → roadmap candidate S-32; flag-only is an improvement (honest gap > silent pence-confusion). |
| L8 — stale convert-mode refs (§Scope/CTO) | substantive | **ABSORBED (sweep)** — §Scope flag-only; Core Team note + Consolidated conditions corrected. |
| L9 — DoD-9(c) "NOT 100×" tautology | substantive | **ABSORBED** — DoD-9(c) asserts absence-from-`prices` + WARNING fired. |
| L10 — WARNING leaks "F2" to console | craft | **ABSORBED** — plain-language message, no internal codes (§B5). |
| L11 — DoD-7 ellipsis test names | craft | **ABSORBED** — concrete names `test_summary_partial_patch_warns` / `_full_noop_warns`. |
| L12 — G15 scope-coherence (§Scope contradiction) | substantive | **ABSORBED** — same sweep as L8; §Scope now states flag-only. |
| L13 — no-live-run prohibition for DoD-2 | substantive | **ABSORBED** — DoD-2 reconciliation forbids a confirmatory live run (privacy). |
| L14 — section-splice spec thin | substantive | **ABSORBED** — §B2 index-based splice (`head+patched-slice+tail`), not `.replace()`; misses counted on the slice. |
| L15 — template row order unpinned | craft | **ABSORBED** — §C pins the 7-row order. |

R2 confirmed R1-L3/L5/L7/L8/L14/L15 closed.

### Round 3 (convergence confirmation) — `sound`, 5 L-items (0 structural; 3 substantive, 2 craft); trajectory 20→15→5

**STRUCTURAL: sound → authoritative for ship.** R3 confirmed PROBE-1/2/4/5/6/7 closed (confirmed-base-only consistent; all-skipped fix in a disjoint branch; no R1↔R2 contradiction; no stale convert-mode scope claim; DoDs jointly falsifiable; no new code defect). All 5 residual items absorbed as DoD-falsifiability + wording refinements — **no design change**:

| L (R3) | Sev | Disposition |
|---|---|---|
| L1 — DoD-9(b) partial annotation needs ≥1 priced peer | substantive | **ABSORBED** — DoD-9(b) states the mixed-ledger precondition; single-USD hits the all-skipped path (asserted separately). |
| L2 — two-message regime (partial vs all-skipped) | substantive | **ABSORBED** — §B5: intentional two-state messaging documented; per-position WARNING prints in both cases (operator always sees the reason). |
| L3 — no residual-"L14" sweep across both sites | craft | **ABSORBED** — DoD-10 grep gate `grep -rn 'L14' …` == 0. |
| L4 — DoD-7 "split" vs DoD-10 "no delete" tension | substantive | **ABSORBED** — DoD-7: old test removed/replaced; behaviour coverage preserved+extended (DoD-10 governs behaviour, not names). |
| L5 — orthogonality "improvement" overstates | craft | **ABSORBED** — §B5 softened to "safer posture; magnitude unsound (sign may be directional)". |

**Ship decision:** R3 `sound` is authoritative (iteration discipline). Converged 20→15→5. Proceeding to the operator approval gate.

## Amendments
None yet.

## Status Log

- 2026-06-10 — DRAFT opened. Floor audit complete (no pre-existing FATAL beyond S-27/S-28; foundation sound). Cross-Check path declared isolated-challenger.
- 2026-06-10 — Challenger R1 = `flawed`, 20 L-items (5 structural). All claims verified; all 20 absorbed (none resisted, none scope-expanding). Key delta: S-28 convert→**flag-only** (L7/L8/L9). Proposal amended (§B1/B2/B4/B5, §F4, DoD-2 reconciliation + DoD 5–10, Risks, Delta Annexe R2 + L-pass).
- 2026-06-10 — Challenger R2 = `flawed`, 15 L-items (3 structural), trajectory 20→15 (strictly decreasing). All 15 verified + absorbed (docs + minor code-spec; none scope-expanding). Structural items adjudicated as artefact-clarity gaps, not design FATALs. Amended §Scope/§B2/§B5/§C/§F4/Core-Team-note/DoD-2/6/7/9 + R2 L-pass table.
- 2026-06-10 — Challenger R3 = `sound`, 5 L-items (0 structural; 3 substantive, 2 craft). Trajectory 20→15→5 (converged). STRUCTURAL `sound` = authoritative for ship. All 5 absorbed (DoD/wording refinements; no design change). Status → REVIEWED. Awaiting operator approval.
- 2026-06-10 — Operator GO (steering-verified bytes on disk). Implemented via Sonnet implementation-agent; orchestrator verified the diff against §FILES CHANGED (3 impl files, no out-of-scope hunks, live ledger UNMODIFIED). /code-reviewer APPROVE WITH NOTES (2 NOTEs — `:312` silent-except, `:307` NaN-on-confirmed-EUR — both pre-existing, flag-only neither adds nor worsens, banked to S-32; not fixed this commit). DoD-1 PASS (all 6 anchors == 1 + 1 Summary header on template/fixture direct + live via redacted count-only subprocess). DoD-2 runtime observation PASS through `update_portfolio` (full-match / partial / no-op / S-28 currency-flag, synthetic tmp ledger, no live run). DoD-3 full suite 116 passed / 1 skipped (110 baseline + 6 new; reconcile tests ran, not skipped). Status → DONE. No push (main 30 ahead of origin).
