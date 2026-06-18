---
id: 031
title: S-24 brent fetch wire-up + S-25 stale-core-macro surfacing (Bundle A)
status: DONE
owner: Daniel Campos
opened: 2026-06-17
updated: 2026-06-17
tags: [data-layer, gates, S-24, S-25, pre-war-room-4]
---

# 031 — S-24 brent fetch wire-up + S-25 stale-core-macro surfacing (Bundle A)

## Summary
Two pre-War-Room-#4 data-layer fixes, bundled because both touch the gate evaluator's
staleness/Data-Confidence path. **S-24 (partial)**: wire the already-mapped `brent` gate's
FRED series (`DCOILBRENTEU`) into the fetch loop so brent scores from a live value instead of
the current `unavailable → RED-by-omission`. **S-25 (full)**: surface stale/ungated core-macro
series (e.g. euro-area HICP) in the `Data_Confidence_Tier` headline — today a months-stale core
series is invisible because it maps to no deployment gate. A live probe this session root-caused
the HICP staleness (genuine at source; recorded below) and captured the ECB monthly vintage
format the parse fix is built against. The cardinal invariant: **no fetched series — whether
moving `unavailable→fetched`, stale, or with an unparseable vintage — may ever silently score
GREEN; it fails toward the cautious tier.**

## Motivation / Problem
Observed in War Room Session #3 (2026-05) and confirmed by a live probe on 2026-06-17:

1. **brent never fetched.** `SERIES_TO_GATE` maps `DCOILBRENTEU → brent` (gate_eval.py:98) and
   `_GATE_STALENESS["brent"] = {amber:5, red:10}` already exists (gate_eval.py:107), but
   `DCOILBRENTEU` is absent from `config/gates.yml › data_staleness.series`. The fetch loop iterates
   `data_staleness.series` ONLY (`cli._build_providers` + `_fetch_all`), so brent is never fetched →
   `value is None` → `tier = RED` (gate_eval.py:371). The brent gate has read a permanently
   misleading RED, hand-sourced by the orchestrator each session.

2. **Stale core-macro is invisible.** `Data_Confidence_Tier` is built ONLY inside the
   `for gate_name in deployment_gates` loop (gate_eval.py:396-402). A *fetched-but-ungated* core
   series (HICP, CPI, UNRATE, DFR) never contributes to the headline. In #3 the euro-area inflation
   series read months-stale while only denting per-series staleness invisibly.

3. **Two cautious-fail gaps.** `_staleness_tier(None, …)` returns GREEN (gate_eval.py:157-159), and
   a vintage parse failure sets `staleness_days = None` (gate_eval.py:352-355). A FETCHED series whose
   vintage cannot be parsed therefore reads GREEN with a GREEN Data-Confidence contribution — a
   cautious-fail violation. Monthly ECB vintages (`YYYY-MM`, e.g. `2025-12`) are exactly such a case:
   `date.fromisoformat("2025-12")` raises `ValueError` (measured).

### Live probe findings (2026-06-17 — DoD #4, recorded verbatim)
Read-only probe, FRED key loaded from `.env` by the framework tool, key never echoed:

- **FRED `DCOILBRENTEU`** — serves OK: `value=97.46`, `as_of=2026-06-08`, `vintage=2026-06-11`.
  Units came back labelled `index` (no `_SERIES_META` entry → `_DEFAULT_META`); the fix adds the
  `USD_per_bbl` label (`units_param:"lin"` — DCOILBRENTEU is a daily price *level*, not a transform
  like PAYEMS's `chg`, L14). On the **value axis** `97.46` lands in the brent AMBER band (80–100),
  confirming the gate scores from a value once fetched, not None→RED; on the **staleness axis** the
  6-day vintage gap (2026-06-11 vs a 2026-06-17 read) is itself AMBER (amber=5).
- **ECB HICP `ICP.M.U2.N.000000.4.ANR`** — the months-stale read is **genuine at source, not a
  parse or cache artefact.** A live same-day probe (`header.prepared 2026-06-17T13:49…`) returns
  observations ending at `2025-12`; `lastNObservations=6` → `[2025-07 … 2025-12]`; both the `ANR`
  and `INX` suffixes confirm `2025-12` is the latest available; `startPeriod=2026-01` returns an
  empty body (no 2026 observations exist for this key). The series **as keyed** is ~6 months stale
  upstream. The monthly observation format is `YYYY-MM` (captured: `2025-12`), which
  `date.fromisoformat` cannot parse.
- **Root-cause verdict**: the upstream series-key is the problem, not our pipeline. **Correcting the
  key** (locating a currently-updating euro-area HICP flow or an alternative source) is a distinct
  investigation that would *expand* Bundle A → **deferred as named follow-up S-25c** (see Scope).
  Bundle A's surfacing fix (S-25a) makes this 6-month staleness **visible** (drives Data_Confidence
  RED) even without correcting the key — which is precisely S-25's goal.

## Proposal

### File-level manifest
| File | Change | Type |
|---|---|---|
| `config/gates.yml` | add `DCOILBRENTEU` to `data_staleness.series` (`source: FRED`, `amber_age_days: 5`, `red_age_days: 10`) | modified |
| `scripts/data/providers/fred.py` | add `_SERIES_META["DCOILBRENTEU"] = {units_param:"lin", units_label:"USD_per_bbl"}` | modified |
| `scripts/data/gate_eval.py` | (a) `_parse_vintage_to_date` helper (YYYY-MM-DD + YYYY-MM); (b) `_data_confidence_contribution` helper (cautious-fail for live+None; preserves `_GATE_STALENESS` as gated threshold source); (c) route both Data-Confidence appends through the helper; (d) ungated fetched-series Data-Confidence fold-in. **NOT touched: the gated staleness-computation site (gate_eval:352) keeps `date.fromisoformat` — gated vintages are daily and parse fine (L2/L6 absorption — scope-narrowing).** | modified |
| `backtesting/REPLAY_DELTA.md` | add current-SHA note (preserve "at replay" SHA) | modified |
| `proposals/003-phase-1b-data-integration.md` | append Status-Log cross-ref entry citing new SHA | modified (append-only) |
| `tests/test_gate_eval.py` | new tests: brent-scores-from-value; monthly-vintage parse; ungated fold-in (2 stale + 1 fresh); live-None cautious-fail; D4 manual-None-not-regressed; cached-non-None-stale→real-tier (L5); _GATE_STALENESS↔gates.yml consistency | modified |
| `tests/test_gates_schema.py` | add `DCOILBRENTEU` to `REQUIRED_STALENESS_SERIES` so a future drop is caught (L7) | modified |

### Mechanism design (from the closed #28 delta re-pass — D1–D4)
- **D1** — ungated series have NO `_GATE_STALENESS` entry, so the S-25(a) fold-in MUST source its
  thresholds from `gates.yml › data_staleness.series` (`amber_age_days`/`red_age_days`), NOT
  `_GATE_STALENESS.get` (which returns `None → GREEN-always` for ungated series = the exact silent-GREEN
  this bundle closes). Thresholds are remapped to the `{amber, red}` shape `_staleness_tier` expects.
- **D2** — the negative test (fresh→GREEN) passes for a broken impl too; only the *positive* test
  discriminates, and only if its fixture wires staleness through the REAL threshold source. The
  positive-test fixture pins thresholds in `data_staleness.series` for series that are absent from
  `_GATE_STALENESS` — a broken impl reading `_GATE_STALENESS` would stay GREEN and FAIL the test.
- **D3** — the None-staleness cautious-fail is enforced on the NEW ungated path (the live-relevant
  locus for monthly HICP). The same `_data_confidence_contribution` helper also wraps the gated
  Data-Confidence append (defensive — closes the theoretical gated parse-fail gap), but the gated
  *staleness-computation* site (gate_eval:352) is left untouched and the gated *threshold source*
  stays `_GATE_STALENESS` (no behaviour change, no dual-source drift — L2/L6/L13 absorption).
- **D4 (highest risk — regression)** — the None-staleness cautious-fail is conditioned on
  `data_source == "live"`. Manual_gates series (`data_source == "cached"`: hormuz/ecb/tariff/stoxx600)
  legitimately carry `staleness_days = None` and are fresh-by-design; an unconditional flip would drag
  Data_Confidence cautious when those are fine. Helper contract:
  `if data_source=="unavailable": RED; elif staleness_days is None and data_source=="live": AMBER;
  else: _staleness_tier(staleness_days, thresholds)`. So `cached+None → GREEN` (fresh-by-design),
  `live+None → AMBER` (cautious-fail), and **`cached+non-None-stale → real tier via _staleness_tier`**
  (L5 — no GREEN bypass for a genuinely stale manual gate).

### Ungated-set derivation (generic, no hardcoded list)
`ungated_fetched = (snapshot.series ∩ data_staleness.series.keys()) − SERIES_TO_GATE.keys()`.
After adding brent, fetched-ungated = `{CPIAUCSL, UNRATE, DFR, ICP.M.U2.N.000000.4.ANR}`. Each is
staleness-scored via `_parse_vintage_to_date(obs.vintage)` + its `data_staleness.series` thresholds,
and its tier folds into `data_staleness_tiers` → `Data_Confidence_Tier`. `gates_config.get("data_staleness", {})`
is read defensively so inline test fixtures lacking that key are unaffected.

### Monthly-vintage parse (S-25b)
`_parse_vintage_to_date`: try `date.fromisoformat(v[:10])`; on failure, match `^(\d{4})-(\d{2})$`
and anchor monthly to the **first of month** (the most conservative anchor for staleness — slightly
overstates age, which is the cautious direction). Unparseable → `None` → cautious via D3/D4. Used
**only on the new ungated fold-in path** — the gated `staleness_days` site (gate_eval:352) is not
mutated (its members are daily-vintage series; first-of-month overstatement against tight gated
thresholds + the L23 stale-penalty is avoided by not touching it — L6 absorption).

## Scope & Out-of-Scope
**In scope (Bundle A):** brent fetch wire-up; monthly-vintage parse; generic ungated Data-Confidence
fold-in; live+None cautious-fail close; SHA cascade; consistency test; runtime observation.

**Out of scope (deferred, named):**
- **S-24 remainder** — equity-vs-50wMA gate (new equity-provider archetype, own proposal); the 3
  categorical/geopolitical manual-input gates (hormuz/ecb/tariff need a structured manual-input slot).
- **S-25c (new follow-up)** — correct the upstream HICP series key / alternative source. Probe-driven;
  expands scope; deferred per the STOP rule. The surfacing fix makes the staleness visible meanwhile.
- Explicitly NOT pulled in: S-21, S-29, S-32, S-33, S-26, atomic-cache writes.

## Definition of Done
1. `gates.yml › data_staleness.series` contains `DCOILBRENTEU` with EXACTLY `{source: FRED,
   amber_age_days: 5, red_age_days: 10}` (no extra fields — the pre-computed SHA depends on this set);
   `fred.py _SERIES_META["DCOILBRENTEU"] == {units_param:"lin", units_label:"USD_per_bbl"}` and a test
   asserts `units_label == "USD_per_bbl"` (L1); a test asserts the brent gate scores its real tier
   from a fetched `DCOILBRENTEU` value (NOT None→RED); `DCOILBRENTEU` is added to
   `test_gates_schema.REQUIRED_STALENESS_SERIES` so a future drop is caught (L7).
2. The monthly-vintage parse handles the captured `YYYY-MM` format (fixture derived from the live
   capture `2025-12`); `staleness_days` computes to a real int for a monthly series flowing through
   `evaluate_gates`, asserted by a test. (If the probe had been impossible, the parse fix would defer
   and DoD#5 alone would close the exposure — probe succeeded, so it ships.)
3. The Data_Confidence fold-in iterates the ungated fetched set GENERICALLY (no hardcoded list) and
   sources thresholds from `data_staleness.series` (D1); a test asserts TWO distinct months-stale
   ungated series each move `Data_Confidence_Tier` off GREEN (positive test wired through the real
   threshold source, D2), and a fresh ungated series leaves it GREEN.
4. The live ECB probe outcome (root-cause finding) is recorded verbatim in this proposal (done above);
   the warranted key-correction fix is deferred as named follow-up S-25c.
5. No path lets a bad/stale/None-staleness fetched series score falsely GREEN: `unavailable → RED`,
   the L23 stale-penalty, and `cli sys.exit(1)`-on-fetch-failure remain intact; AND a fetched
   (`data_source == "live"`) series whose vintage cannot be parsed reads cautious (AMBER+), asserted
   by a test through `evaluate_gates` on the ungated path (D3); the manual_gates fresh-None path is
   NOT regressed (D4 test).
6. Cross-artefact cascade closed: every live artefact embedding the canonical gates-content-SHA
   (`REPLAY_DELTA.md`, `proposals/003`) carries the new live-config SHA (estimated
   `a8d90addea00c75cfe114859707353b3483a24e1d1220321cbc84a744ef5e542` — **RECOMPUTED against the
   actual edited bytes at implementation before seeding the artefacts**, L4), `tests/test_gate_eval.py
   TestArtefactSync` passes; a `_GATE_STALENESS ↔ gates.yml data_staleness.series` consistency test is
   added and passes. (`backtesting/engine/config/gates.yml` is a different-schema frozen backtest-era
   config — top-level `gates:`, no `data_staleness`/`brent`, no canonical-SHA computed over it — and is
   verified OUT of the cascade, L3.)
7. Runtime observation — TWO independent halves so an ECB-leg fetch failure cannot mask the brent
   demonstration (L9): (a) brent FETCH path — a live `python -m scripts.data fetch` showing
   `DCOILBRENTEU` fetched (FRED key present); if the ECB leg aborts the combined fetch, fall back to a
   `_build_providers` routing assertion (`DCOILBRENTEU → FredProvider`, present in `_fetch_all`); (b)
   stale-core headline — `python -m scripts.data gate_eval` over a snapshot containing the 2025-12 HICP
   (existing `2026-05.json` suffices) showing brent scoring from a value AND HICP reading STALE in the
   Data_Confidence headline.
8. Full suite green: `python3 -m pytest -q` passes with the expected NEW total `141 + N passed / 1
   skipped` (N = count of tests added this proposal; collection failure of a new test is therefore
   observable, not masked by "≥141"), no regression vs the FIRST-MOVE baseline (L10).

## Risks & Mitigations
See the L-pass below.

## Adversarial Loophole Pass (L1–Ln)

**L1 — SHA cascade falsifies the replay record.** Overwriting `REPLAY_DELTA.md:4` "at replay" SHA
would claim the historical backtest used the post-brent config. **Closed by** adding a *separate*
current-SHA note line and preserving the "at replay" value; the brent addition is additive to
`data_staleness` and changes no replayed deployment-gate threshold, so replay outcomes are unaffected
— only the canonical SHA label changes, and that is documented truthfully.

**L2 — append-only Status Log violation on proposal 003.** Editing 003's line-300 historical entry
in place breaks the append-only invariant. **Closed by** appending a new dated Status-Log entry to
003 citing the new SHA and naming Proposal 031 as the cause; the historical entry stays byte-intact.

**L3 — D4 regression: manual gates dragged cautious.** An unconditional `None→AMBER` flip would push
Data_Confidence cautious for the 4 fresh-by-design manual gates. **Closed by** conditioning the
cautious-fail on `data_source == "live"`; a dedicated D4 test asserts a fresh manual-None gate stays
GREEN.

**L4 — positive test green on a broken impl (D2).** A fold-in that wrongly reads `_GATE_STALENESS`
would leave ungated series GREEN-always; a weak fixture might still pass. **Closed by** pinning the
positive-test thresholds ONLY in `data_staleness.series` for series absent from `_GATE_STALENESS`, so
a broken impl FAILS the positive test.

**L5 — monthly anchor direction wrong.** Anchoring `YYYY-MM` to a wrong day could understate age.
**Closed by** anchoring to first-of-month (conservative — overstates age slightly, the cautious
direction); documented in the helper docstring.

**L6 — inline test fixtures lack `data_staleness`.** The existing `GATES_FIXTURE` has no
`data_staleness` key; a naive `gates_config["data_staleness"]` would `KeyError` and break ~20 tests.
**Closed by** `gates_config.get("data_staleness", {}).get("series", {})` → empty → zero ungated series
→ existing tests unchanged (verified against the baseline pre/post).

**L7 — new full SHA self-poisons the sanitisation guard at push.** A 64-char hex SHA carries digit
runs the harvest can treat as private numerics; a gitignored scratch echoing it would FP. **Closed by**
the SHA being a deterministic hash of *public* config (not a private numeric), no scratch file echoing
it (probe scripts live in `/tmp`, outside the repo), and the pre-existing full SHAs in the same two
files already pass the guard. Re-checked at /commemorate via `/process-sheriff`.

**L8 — brent fetch failure aborts the whole snapshot.** `_fetch_all` does `sys.exit(1)` on ANY fetch
failure; adding brent adds a new failure surface that could block the monthly snapshot if FRED drops
`DCOILBRENTEU`. **Accepted, not closed** — this is the existing fail-closed contract (cautious by
design); brent is a standard long-history FRED daily series (probe confirmed live). If it became a
recurring problem the DDP stale-cache fallback already covers a transient miss.

## Core Team Review (A–D)

**A — Quant Architect.** APPROVE. Two new pure helpers (`_parse_vintage_to_date`,
`_data_confidence_contribution`), no logic duplicated — the ungated fold reuses the same staleness
primitive as the gated path. The threshold-source split (gated → `_GATE_STALENESS`; ungated →
`gates.yml`) is the one wart; the new consistency test pins them so drift breaks the build. Not
touching gate_eval:352 keeps the change surgical. Magic numbers all live in gates.yml.

**B — Portfolio Manager.** APPROVE. Minimum scope — brent fetch + a headline-surfacing change, no
new strategy surface. The real win is cheap: a 6-month-stale inflation read becomes *visible* without
chasing the upstream key fix (correctly deferred to S-25c). Fully unwindable (additive config + a
reporting fold). Ships inside the 3-day window before #4.

**C — CTO.** APPROVE WITH NOTES. FRED key stays in `.env`, read by the framework tool, never in
context (probe respected this). Pipeline idempotent — fold-in is read-only over the snapshot. NOTE:
brent adds a new `_fetch_all` failure surface (`sys.exit(1)` on miss) — accepted as the existing
fail-closed contract (L-pass L8). NOTE: recompute the canonical SHA against real bytes before seeding
artefacts (L4) and re-run the sanitisation dogfood for the full SHA at commit (L7/L12).

**D — Risk Officer.** APPROVE. The cardinal invariant holds: `unavailable→RED`, L23 stale-penalty,
and `cli sys.exit(1)` all preserved; the live+None cautious-fail closes the silent-GREEN gap; D4
conditioning prevents fresh manual gates being dragged cautious. Confirm the positive ungated test
discriminates a broken impl (D2) — that is the one test that actually guards the headline.

## Delta Annexe — Round 1 (Core Team)
- **Absorbed**: CTO L4 SHA-recompute gate and L7/L12 dogfood re-run → folded into DoD #6 and the
  L-pass. D's D2-discrimination demand → pinned in DoD #3 (positive test wired through the real
  threshold source).
- **Resisted**: none (Core Team raised no blocking items).

## Delta Annexe — Round 2 (Cross-Model Critique)
Cross-Check path: [isolated-challenger] — reason: no external/alternate model API configured; MEDIUM
proposal requires the dual-model cross-check, so the Isolated Challenger Sub-Agent fallback applies.
Verdict returned: **FLAWED** (14 items). Each structural claim independently verified against the
bytes before absorbing/resisting (FATAL-claim independent verification).

- **L1 (units label undertested) — ABSORBED** (correcting): DoD #1 now asserts
  `units_label == "USD_per_bbl"`.
- **L2 (gated parse-site mutation untested/outside surgical scope) — ABSORBED** (scope-narrowing):
  the gated staleness-computation site (gate_eval:352) is NOT mutated; `_parse_vintage_to_date` is used
  only on the new ungated path. Dissolves L2 and L6.
- **L3 (second gates.yml in SHA blast radius) — RESISTED, claim verified FALSE-as-blocker**:
  `backtesting/engine/config/gates.yml` is a different-schema frozen file (top-level `gates:`, no
  `data_staleness`/`brent`); no `compute_gates_content_sha` is computed over it; it is not in the
  cascade. Recorded in DoD #6 for transparency. (The file's *existence* was a real catch — the
  blast-radius *claim* was not.)
- **L4 (pre-computed SHA asserted, not measured) — ABSORBED** (correcting): SHA labelled estimated +
  RECOMPUTE-at-implementation gate; exact DCOILBRENTEU field set pinned in DoD #1.
- **L5 (cached + non-None stale could bypass to GREEN) — ABSORBED** (correcting): helper contract
  routes all non-None staleness through `_staleness_tier`; new test asserts a stale cached gate scores
  its real tier.
- **L6 (monthly anchor overstates gated age) — DISSOLVED** by the L2 absorption (gated site untouched).
- **L7 (DCOILBRENTEU not pinned in REQUIRED_STALENESS_SERIES) — ABSORBED** (correcting): added to the
  schema test so a future drop is caught.
- **L8 (snapshot-present, config-absent series silently uncounted) — RESISTED, with reasoning**: the
  fetch loop is config-driven, so `snapshot.series ⊆ data_staleness.series` by construction; the ∩ is
  belt-and-braces and snapshot-hash verification guards hand-edits. No code change.
- **L9 (combined runtime obs masks brent if ECB aborts) — ABSORBED**: DoD #7 split into two
  independent halves with a routing-assertion fallback.
- **L10 (DoD #8 target unfalsifiable) — ABSORBED**: expected NEW total stated as `141 + N`.
- **L11 (value-band vs staleness-band ambiguity) — ABSORBED** (craft): probe finding now names both axes.
- **L12 (full SHA self-poison risk) — ACCEPTED/MANAGED**: `TestArtefactSync` requires the full 64-char
  SHA (cannot shorten per the 7-char anti-pattern without changing the test = scope expansion + weakened
  lock); pre-existing full SHAs already pass; re-verify no gitignored scratch echoes the new SHA via the
  sanitisation dogfood at /commemorate.
- **L13 (dual threshold-source drift) — ABSORBED** (correcting): gated path keeps `_GATE_STALENESS` as
  its threshold source; the helper only adds the cautious-fail wrapper. The new consistency test guards
  the two sources against drift.
- **L14 (no `lin` rationale) — ABSORBED** (craft): one-line rationale added to the probe finding.

No absorption expanded scope (G15): every absorption narrowed (L2/L6), corrected (L1/L4/L5/L7/L9/L10/
L11/L13/L14), or was resisted (L3/L8) / accepted-as-constraint (L12). No re-escalation required.

## Amendments
- 2026-06-17 — post-Challenger: gated parse site (gate_eval:352) removed from scope (L2); helper
  contract pinned (L5/L13); DoD #1/#3/#6/#7/#8 tightened; `test_gates_schema` + units-label tests added.

## Status Log

> Append-only. The closing entry (status flips to DONE) MUST be paired with a corresponding line in
> the project root [`CHANGELOG.md`](../CHANGELOG.md).

- 2026-06-17 — DRAFT opened. FIRST-MOVE baseline 141 passed / 1 skipped @ `e76c6f6`. Live probe
  recorded (DoD#4). Pre-computed post-edit canonical SHA `a8d90add…ef5e542`.
- 2026-06-17 — Challenger (isolated, FLAWED/14) absorbed/resisted; Core Team A–D reviewed.
- 2026-06-17 — **APPROVED** (operator, steering-relayed verdict SOUND). Five carry-forward conditions
  bound to /commemorate (do not let any evaporate):
  1. **SHA recompute gate (L4/CTO):** recompute `compute_gates_content_sha` against the ACTUAL edited
     `config/gates.yml` bytes before seeding `REPLAY_DELTA.md` + `proposals/003`; MUST equal
     `a8d90addea00c75cfe114859707353b3483a24e1d1220321cbc84a744ef5e542` — valid ONLY if the
     `DCOILBRENTEU` field set is EXACTLY `{source: FRED, amber_age_days: 5, red_age_days: 10}` (no
     stray field). `TestArtefactSync` green.
  2. **Sanitisation dogfood (L7/L12):** at /commemorate re-run the pre-commit sanitisation hook /
     `/process-sheriff` MECHANICALLY over the staged diff carrying the new full 64-char SHA; confirm no
     gitignored scratch echoes it (S-31 self-poison FP guard). Verify mechanically, not by eye.
  3. **Status discipline (#22):** verify → flip-DONE → commit; never pre-flip/pre-write a passing
     verdict. Reconcile S-24 = PARTIAL (brent done; equity gate + 3 categorical manual-input gates
     remain) and S-25 = DONE across **FIVE** artefacts: proposal frontmatter, proposal Status Log,
     PROGRESS row, CHANGELOG, AND `proposals/README` index row.
  4. **Append-only (L1/L2):** APPEND a new dated Status-Log entry to `proposals/003` citing the new
     SHA + naming 031 as cause — do NOT edit the historical entry. `REPLAY_DELTA.md` preserves the
     "at replay" SHA and adds a SEPARATE current-SHA note.
  5. **Full-suite gate (#25a):** run the FULL `python3 -m pytest -q` (expect `141 + N passed / 1
     skipped`) before the staged-blob endorsement — not a subset, not just the new tests.
- 2026-06-17 — Implementation complete (7 files; orchestrator-direct — implementation-agent dispatch
  hit a session limit, never ran). Full suite **152 passed / 1 skipped** (141 + 11 new). SHA recompute
  gate #1 verified: edited `config/gates.yml` → `a8d90addea00c75cfe114859707353b3483a24e1d1220321cbc84a744ef5e542`
  (== expected). `/code-reviewer`: APPROVE WITH NOTES (3 NOTEs; the one logic NOTE — None-valued
  thresholds → TypeError in the ungated fold — is unreachable under the `test_gates_schema` int-threshold
  guard and fails loud, not silent). Runtime obs BOTH halves: (a) live fetch `DCOILBRENTEU=97.46
  vintage 2026-06-11`; (b) `gate_eval` shows brent AMBER-from-value + stale HICP (2025-12) drives
  Data_Confidence AMBER→RED (counterfactual: GREEN-leg confirmed via evaluate_gates).
- 2026-06-17 — **S-25 done-line scope decision (operator/steering, Option 1):** aggregate-tier fold is
  sufficient for S-25 = DONE. Per-series visible stale-row in `render_table` deferred. **Precise wording
  REQUIRED across all five artefacts** (not a bare "S-25 DONE"): *"S-25 DONE — stale ungated core-macro
  series now drive the Data_Confidence_Tier headline (aggregate surfacing); per-series visible stale-row
  in render_table deferred as S-25d."* — mirrors the S-24 PARTIAL precision; prevents a reader assuming
  the rendered table shows per-series staleness (it shows the 8 gates + the aggregate tier only).
- 2026-06-17 — **S-25d banked (new follow-up):** surface each stale ungated core-macro series as a
  visible row/note in `render_table`. Carries a render_table consumer-check (`backtesting/.../parity_check.py`
  parses the table; War Room SKILL.md + agent table-consumption path consume it) + its own test +
  `/code-reviewer`. NOT this bundle.
- 2026-06-17 — **DONE.** All carry-forwards honoured: #1 SHA recompute == `a8d90add…ef5e542` (verified
  against edited bytes); #2 sanitisation dogfood guard exit 0 over the staged diff (incl. new full SHA);
  #3 status reconciled across five artefacts (this frontmatter + Status Log + PROGRESS S-24=PARTIAL /
  S-25=DONE + CHANGELOG + proposals/README); #4 `proposals/003` append-only (historical entry intact) +
  `REPLAY_DELTA.md` "at replay" SHA preserved with a separate current-SHA note; #5 full suite 152 passed
  / 1 skipped. `/process-sheriff` CLEAR; `/code-reviewer` APPROVE WITH NOTES. **S-24 = PARTIAL** (brent
  done; equity gate + 3 categorical manual-input gates remain). **S-25 = DONE — stale ungated core-macro
  series now drive the Data_Confidence_Tier headline (aggregate surfacing); per-series visible stale-row
  in render_table deferred as S-25d.** New follow-ups banked: S-25c (upstream HICP key), S-25d (per-series
  render row). Paired CHANGELOG entry under [Unreleased] § Added.
