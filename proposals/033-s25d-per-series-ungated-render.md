---
id: 033
title: S-25d — per-series ungated core-macro visibility in render_table
status: DONE
owner: Daniel Campos
opened: 2026-06-21
updated: 2026-06-22
tags: [data-layer, gate-eval, render, S-25d, visibility]
---

# 033 — S-25d — per-series ungated core-macro visibility in render_table

**Tier: MEDIUM** — 5 code/doc files + 2 self-admin (proposal + README); ~25 net lines in `gate_eval.py` plus new tests (>30 net code lines → exceeds the LIGHT ceiling). Known pattern (additive TypedDict field + fold capture + render block). FULLY REVERSIBLE; no irreversible step; no SHA cascade; no `config/gates.yml` change. *(Scope expanded 2026-06-22, operator-approved: + `scripts/data/parity_check.py` MODIFY — see Amendments + the parity-map Delta Annexe.)*

## Summary
Surface each fetched-but-ungated core-macro series (CPI / unemployment / ECB deposit rate / euro-area HICP) as a **visible per-series note block** appended to `gate_eval`'s markdown render, so a War Room operator who sees `Data_Confidence_Tier: RED` (or AMBER) can also see WHICH ungated series drove it. This completes the S-25 (031) / S-25c (032) surfacing story: 031 made the ungated series move the *aggregate* tier; this makes each contributor *visible*. **Visibility only — it must not re-tier anything.**

## Motivation / Problem
The S-25 fold (`gate_eval.py:451-463`, verified by Read) folds fetched-but-ungated core-macro series into `Data_Confidence_Tier` but appends **only the contribution tier** to the flat `data_staleness_tiers` list — it has `series_id` and `ungated_staleness` in scope and **discards both**. The rendered markdown table (`render_table`, `gate_eval.py:492-528`, verified) shows only the 8 deployment gates plus the two aggregate tiers. So an operator sees `Data_Confidence_Tier: RED` with no indication of which ungated series is stale (PROGRESS.md:100, S-25d row, verified). S-25d closes that visibility gap.

## Proposal

### Design decisions
*(All code paths below are under `scripts/data/` unless otherwise stated — corrected post-Challenger L8.)*

- **Form: NON-PIPE note block (mandatory, not pipe-table).** `parity_check.extract_prose_tiers` (`scripts/data/parity_check.py:84-132`, verified) parses every `startswith("|")` line as a gate row and maps col-0 labels via `_PROSE_LABEL_TO_GATE_ID` (`scripts/data/parity_check.py:57-77`, verified). That map contains `"ecb deposit rate" → ecb` **and** `"ecb" → ecb`. DFR — one of the four ungated series — **is** the ECB deposit-facility rate, so a pipe row labelled "ECB deposit rate" would inject a spurious `ecb` tier into the 8-gate parity dict (silent corruption — the **F8 label-collision trap**). A non-pipe block (lines starting `**`/`-`, never `|`) is never seen by the `startswith("|")` filter → zero parity_check interaction, zero collision exposure, lower blast radius.
- **Human-readable labels (F8).** No id→label map exists today. Add a small explicit dict `_UNGATED_SERIES_LABEL` so the raw opaque id `ei_cphi_m.TOTAL.RT12.EA` does not ship; fall back to the raw id for any unmapped series (defensive, non-crashing).
- **Carrier field.** `GateReport` (TypedDict, `gate_eval.py:80-85`, verified) has no per-series field and `render_table` receives only a `GateReport` (`:492`, `:566`). Add a new JSON-serialisable field `data_confidence_series: list[dict]` (records of `{series_id, label, staleness_days, tier}`; all `str`/`int`/`None`). Constructed at the single `GateReport(...)` call site (`:478`, verified sole constructor).
- **Agent-visibility (F3b).** The new block rides the existing paste path (operator pastes `gate_eval --format markdown` output into the session file; `brainstorms/_TEMPLATE.md:304-318`, verified), so War Room Macro/Risk agents see the per-series breakdown at T=0. This is an **intended additive** transparency change aligned with S-25d's purpose — stated explicitly here, not riding silently.

### Rendered block — shape exemplar (R2-L7/L8: ages illustrative, NOT pinned digits)
The block is appended after the aggregate-tier lines. Every line begins with `**` or `- `; after `str.strip()` no line begins with `|` (the labels in `_UNGATED_SERIES_LABEL` and the tier/age tokens contain no `|`), so `parity_check`'s `line.strip()` → `startswith("|")` branch (`scripts/data/parity_check.py:97-98`, verified) never sees it. **Pinnable** = heading text, `- {label} — {TIER} ({age})` line format, and **sort order by `series_id`** (verified `sorted([CPIAUCSL, UNRATE, DFR, ei_cphi_m…]) = [CPIAUCSL, DFR, UNRATE, ei_cphi_m…]`). **Not pinnable** = the age digits (runtime-derived from `snap_date − vintage`). Exemplar (ages shown as `NNd` placeholders so no test author pins them — post-Challenger R3-L4; real digits appear only in runtime-obs §DoD#7):
```
**Data Confidence — ungated core series:**
- US CPI — GREEN (NNd)
- ECB deposit rate — GREEN (NNd)
- US unemployment — GREEN (NNd)
- Euro-area HICP — GREEN (NNd)
```
A `None` staleness (unparseable vintage → cautious-fail AMBER+) renders as `age unknown` in place of `(Nd)`. Sort is by `series_id` (post-Challenger R1-L5/R2-L8) so output is canonical regardless of snapshot array order; the aggregate is a count → order-independent, so the sort cannot affect tiers. DoD#3 asserts the format/heading/sort, NOT literal age digits.

### File-level manifest
1. `scripts/data/gate_eval.py`: (a) `_UNGATED_SERIES_LABEL` dict; (b) **strictly inside the second (ungated) fold loop** (`:451-463`, verified — the gated leg appends at `:439` in the first loop and is NOT captured), compute the contribution once: `tier = _data_confidence_contribution(ungated_staleness, thresholds, "live")` (a bare `Tier` string, verified `:190-205`). That **same scalar `tier` value** is then both `.append`-ed to `data_staleness_tiers` (the existing `list[Tier]` the aggregate `.count()`s) AND stored as the `tier` field of a new `data_confidence_series` record (`dict`). One computation, value reused in two places — so the aggregate input is unchanged and `data_confidence_series` holds the ungated subset only (post-Challenger R2-L2: the two sinks hold different *shapes* — `list[Tier]` vs `list[dict]` — but share the one tier *value*, which is the no-drift invariant). (c) add the field to the `GateReport` TypedDict and the `GateReport(...)` return (`:478`, sole constructor); (d) `render_table` emits the non-pipe block (sorted by `series_id`, `None`→`age unknown`) via `report.get("data_confidence_series", [])` when non-empty.
2. `tests/test_gate_eval.py`: new tests — fold-capture (≥2 distinct ungated series, distinct individual tiers, defeats a hardcode), render-block content, field shape (in-memory types + json round-trip).
3. `tests/test_parity_check.py` (NEW): consumer-safety — a prose file containing the new block yields exactly the 8 deployment gates (and the block alone yields zero gates).
4. `.claude/commands/war-room/SKILL.md`: one-line Step B.5 clarification so "paste the markdown table output" reads as "paste the full gate_eval output (table + ungated core-series block)" — the new block makes the old narrow wording ambiguous (DoD #8).
5. `scripts/data/parity_check.py` (MODIFY — scope expansion, operator-approved 2026-06-22): add `"us_payrolls": "us_payrolls"` to `_PROSE_LABEL_TO_GATE_ID`. **Pre-existing gap** (S-25d touched neither the gate-row label nor parity_check): `render_table` emits the gate-**id** as col-0 (e.g. `us_payrolls`, underscore), but the map only had the human aliases `"us payrolls"`/`"payrolls"` (spaces) → the verbatim render parsed to **7** gates, not 8. The S-25d block is genuinely inert; but the "exactly 8" DoD/CHANGELOG claim had been verified via a human-label fixture, not the real render. The operator chose to make it true. Verified post-fix: all 8 deployment gate-ids round-trip from the real render. The other 7 already self-mapped (`vix`/`brent`/`ecb`/`tariff`/`eur_usd`/`stoxx600_vs_50wk_ma` exact + `hormuz`); `us_payrolls` was the sole gap.

### Downstream consumer surfaces of the rendered output (post-Challenger R1-L3/R2-L4 cascade audit)
- `parity_check.extract_prose_tiers` (markdown pipe-parse) — **no cascade** (non-pipe block invisible; DoD#4 locks it).
- War Room agents via the paste path — **intended additive** visibility (§Design agent-visibility).
- `gate_eval` CLI `print` (`scripts/data/gate_eval.py:566`) — renders the block to stdout; the only consumer of `render_table(fmt="json")` too (grep-verified — no programmatic JSON consumer).
- SKILL.md Step B.2/B.3 pre-session checkpoint: `gate_table_sha256 = sha256(gate_output)` (`SKILL.md:178`, verified) hashes the **full** captured stdout → the SHA now covers the block. **Benign — no change needed**: the SHA is computed live from whatever stdout is (no pinned value to update); the block is deterministic (sorted), so the checkpoint stays reproducible.

## Scope & Out-of-Scope
**In:** the four work items above; non-pipe render; per-series capture; consumer-safety + render + fold tests; SKILL.md wording.
**Out (STOP RULE — S-25d only):** S-24 remainder (equity-vs-50wMA gate + manual-input slot — the item that actually moves the aggregate off RED), S-21/S-26/S-29/S-32/S-33, any governance lift. **No push** — the end-of-arc commit is a separate operator-gated public push.

## Definition of Done
- **#1** The fold captures per-ungated-series `(series_id, staleness_days, tier)` for every fetched-but-ungated series in `data_staleness.series`; a test asserts ≥2 distinct ungated series appear with their correct individual tiers, AND a **negative assertion** that a gated series (e.g. `VIXCLS`, which is in both `SERIES_TO_GATE` and `data_staleness.series`) is **absent** from `data_confidence_series` — defeats a regression that moved the capture into the gated leg (`:439`) or read the shared list post-hoc (post-Challenger R3-L7).
- **#2** `GateReport` carries the records in a new JSON-serialisable field. A test **guards against future shape drift** (e.g. a `date` or tuple slipping in, which `default=str` would silently stringify) by asserting the **in-memory shape positively**: the field is `list[dict]` with keys `{series_id, label, staleness_days, tier}`, value types `str`/`str`/`int|None`/`Tier`, and `json.loads(render_table(fmt="json"))["data_confidence_series"]` round-trips equal to the in-memory value. *(Post-Challenger R1-L1/R2-L9: the field is fully JSON-native today so `default=str` cannot fire on it now — the assertion is forward-protection, not a present-day failure guard.)*
- **#3** `render_table` emits a per-series ungated block with each series' human-readable label + tier + staleness age, in the **non-pipe** collision-safe form. The block tier tokens are **bare** (`GREEN`, not `**GREEN**`) — a *second* inertness layer (post-Challenger R3-L2): even if a line were ever pipe-formatted, `parity_check._TIER_PATTERN` (`scripts/data/parity_check.py:79`, verified — `r"\*\*(GREEN|AMBER|RED)\*\*"`) matches only **bold** tiers, so a bare token would not register. A test also exercises the **raw-id fallback** label path (a series in `data_staleness.series` absent from `_UNGATED_SERIES_LABEL` renders its raw id, not a crash — post-Challenger R3-L1). Test asserts format/heading/sort, NOT literal age digits.
- **#4** Consumer-safety (post-Challenger R1-L4 corrected oracle; R2-L1 corrected mechanism — `extract_prose_tiers(prose_path: Path)` reads a file via `.read_text()`, so the test **writes each fixture to a `tmp_path` file** and passes the `Path`, never a string): `extract_prose_tiers(<table+block file>) == extract_prose_tiers(<table-alone file>)` — the block is **inert** (adds no gate_id, overwrites no tier; this is the true collision oracle, since `tiers[gate_id]=tier` overwrites on duplicate so a bare count of 8 would mask a same-key collision). AND `extract_prose_tiers(<block-alone file>) == {}`. **Real-render reality check (post-2026-06-22 scope expansion):** the authoritative "exactly 8" assertion parses the **VERBATIM** `render_table(report, fmt="markdown")` bytes (gate-**id** row labels like `us_payrolls`, plus the populated ungated block) and asserts the extracted gate-id set == exactly the 8 deployment gate-ids (`test_real_render_with_block_round_trips_to_exactly_eight`). The hand-written `_TABLE` (human-prose-label) fixture is retained as an alias-path check but is NOT the proof of "exactly 8" — the real-render test is. The test also includes an **adversarial** case (R1-L9/L10): a block line with leading whitespace must still not parse as a gate row. **Ownership** (post-Challenger R3-L8): the table+block integration fixtures live in `tests/test_parity_check.py` (which imports `render_table` to build the real block), so parity fixtures are not duplicated/orphaned across files. **Class invariant (delta-L4):** a guard test derives the deployment-gate set from `config/gates.yml` and asserts every gate-id self-maps in `_PROSE_LABEL_TO_GATE_ID` (with a non-vacuity pre-check) — so a future gate with an underscore/multi-word id cannot silently re-open the 8-vs-7 miscount.
- **#5** Aggregate `Data_Confidence_Tier` + `Market_Risk_Tier` math UNCHANGED (`TestUngatedFoldIn` green); cautious-fail invariant intact. The per-series captured tiers == the ungated subset of contributions (same `_data_confidence_contribution` values the fold appends); aggregate fed by gated + ungated over one shared `data_staleness_tiers` list.
- **#6** Full suite green (`pytest -q`): **passed count == 163 (measured baseline) + N=10 (measured)** = **173 passed** (achieved 2026-06-22). N decomposes as 5 in `tests/test_gate_eval.py` (`TestS25dPerSeriesRender`: fold-capture+negative, render-block, field-shape+json, age-unknown/cautious, raw-id-fallback) + 5 in `tests/test_parity_check.py` (table-alone=8, inert-equality, block-alone={}, real-rendered={}, adversarial-whitespace). Exact integer floor — no `~`/open `≥` (post-Challenger R3-L6). Skip count environment-dependent, excluded from floor (R1-L13). `tests/test_skill_invariants.py`, `test_json_render_is_deterministic`, `test_markdown_render_is_deterministic` all green; `/code-reviewer` APPROVE / APPROVE WITH NOTES.
- **#7** Runtime-observation: `python3 -m scripts.data gate_eval --session 2026-06 --format markdown` renders the block. The gate is the **invariant** "every series in `(snapshot.series ∩ data_staleness.series − gated)` appears with its tier + age (or `age unknown` for an unparseable vintage)" — NOT a hardcoded count (post-Challenger R1-L6/R2-L6). For today's `2026-06` snapshot that invariant resolves to the 4 series {US CPI, US unemployment, ECB deposit rate, Euro-area HICP} (illustrative of the invariant, not the criterion); `parity_check` yields exactly the 8 gates **from the VERBATIM render** (post-2026-06-22 fix: `us_payrolls` gate-id label now maps), asserted by `test_real_render_with_block_round_trips_to_exactly_eight` — not merely by the human-label fixture.
- **#8** War Room SKILL.md consumer-check: `tests/test_skill_invariants.py` GREEN (forbidden strings are recall-phrases, not tier tokens — a per-series block does not trip it); SKILL.md Step B.5 paste wording reviewed for coherence with the new output shape, updated as in §6.4.

## Risks & Mitigations
- **R1 — pipe-form collision (F8).** Mitigated by mandating the non-pipe form (DoD #3/#4) + a consumer-safety test.
- **R2 — re-tiering regression.** Mitigated by reusing the same `tier` value for capture and aggregate append (one computation, two sinks); `TestUngatedFoldIn` (DoD #5) locks aggregate behaviour.
- **R3 — json shape masked by `default=str`.** `render_table(fmt="json")` uses `default=str` (`:499`, verified) which silently stringifies malformed objects → DoD #2 inspects in-memory types, not json bytes.
- **R4 — render non-determinism.** The block iterates the captured list in fold order (snapshot order) — deterministic per report; markdown idempotence test stays green.
- **R5 — SKILL.md invariant trip.** New wording contains none of `FORBIDDEN_STRINGS` (`from memory`, `recall the latest`, `fallback to recall`, `re-derive the tier`, verified `test_skill_invariants.py:34-39`).
- **R6 — SHA cascade (post-Challenger L12).** None. `compute_gates_content_sha` hashes `gates_config` (`scripts/data/gate_eval.py:305-322`, verified — not the report); `snapshot_sha256` is `snapshot.get("snapshot_hash", "")` (`:477`, verified — the snapshot's own hash, not the report). The new field lives only on the in-memory `GateReport`, so neither SHA's inputs change. `config/gates.yml` is untouched → `TestArtefactSync` / `REPLAY_DELTA.md` / proposal 003 unaffected.

## Core Team Review (A–D)
*(Inline roleplay — no `persona-*.md` files in project; MEDIUM tier.)*

### Quant Architect (A)
APPROVE. The capture reuses the existing `_data_confidence_contribution` result rather than recomputing — no duplicated math, no dual-source drift. The `_UNGATED_SERIES_LABEL` dict is the right home for the id→label mapping (no magic strings scattered in render). One condition: the render block must use `.get("data_confidence_series", [])` so a `GateReport` built without the field (older callers, fixtures) does not `KeyError`.
**VERDICT: APPROVE WITH CONDITIONS** — defensive `.get` on the render read.

### Portfolio Manager (B)
APPROVE. Minimum scope: visibility only, no aggregate change, fully unwindable via `git revert`. Does not expand the data pipeline or add API calls. Good discipline keeping S-24-remainder out.
**VERDICT: APPROVE**

### CTO (C)
APPROVE. No new env vars, no secrets, no API calls, idempotent (pure render of an in-memory report). New field is JSON-serialisable. No SHA cascade (`config/gates.yml` untouched → `compute_gates_content_sha` unchanged → `TestArtefactSync` unaffected). Condition: confirm the json determinism test still holds with the new field (it asserts run-to-run equality, which a new field preserves).
**VERDICT: APPROVE WITH CONDITIONS** — re-run `test_json_render_is_deterministic` post-change.

### Risk Officer (D)
APPROVE. This is a transparency improvement to the risk surface — it makes the Data_Confidence driver legible without relaxing any threshold. The cautious-fail invariant (live+None→AMBER) is untouched; the block surfaces it rather than hiding it. Condition: the render must show "age unknown" (not a blank or `0`) for a `None` staleness, so a cautious-fail series is visibly flagged, not silently rendered as fresh.
**VERDICT: APPROVE WITH CONDITIONS** — `None` staleness renders as "age unknown".

## Delta Annexe — Round 1 (Core Team)
- **Absorbed**: A's defensive `.get("data_confidence_series", [])` on the render read → folded into §6.1(d). C's json-determinism re-run → added to DoD #6 verification. D's "age unknown" for `None` staleness → folded into §6.1(d) render spec.
- **Resisted**: none.

## Delta Annexe — Round 2 (Cross-Model Cross-Check)
**Cross-Check path: isolated-challenger** — reason: no external/alternate model API is configured in this environment (CLAUDE.md §3 condition (a)), consistent with the whole data-layer arc's cross-check path.

Challenger R1 verdict: **flawed** (13 L-items; structural: L2, L7, L8). Every load-bearing claim independently re-verified on disk before disposition (CLAUDE.md §2).

**Absorbed (all scope-narrowing/correcting per G15 — no new files, no new mechanisms; FILES CHANGED + DECOMPOSE unchanged):**
- **L8 (structural) — code citations omitted `scripts/data/` prefix.** Verified via `ls scripts/data/{gate_eval,parity_check,prompts}.py`. → path-prefix note added to §Design; manifest item 1 re-pathed.
- **L2 (structural) — capture-vs-append "same tier" under-demonstrated; shared list with gated leg.** Verified via grep: gated append `:439` (1st loop), ungated append `:461` (2nd loop). → manifest item 1(b) now shows the exact one-computation-two-sinks refactor strictly inside the ungated loop; the gated leg is never captured.
- **L1 (substantive) — DoD#2 "not default=str bytes" tests a difference that cannot manifest for a JSON-native field.** Verified (`default=str` only fires on non-native types). → DoD#2 reframed to a positive in-memory shape+round-trip assertion, with the guard reframed as future-drift protection.
- **L4 (substantive) — "exactly 8" count is the wrong collision oracle; `tiers[gate_id]=tier` overwrites on duplicate.** Verified `scripts/data/parity_check.py:128-130`. → DoD#4 corrected to `extract(table+block) == extract(table-alone)` (inertness) + block-alone `== {}`.
- **L5 (substantive) — block order rests on snapshot array order.** Verified `series_map` built in array order (`:357-359`). → block sorted by `series_id` at render (count-based aggregate is order-independent → sort is display-only).
- **L9 + L10 (substantive) — non-pipe safety unproven until the test lands; `line.strip()` runs before `startswith("|")`.** Verified `:97-98`. → §Design now pins the literal rendered block bytes (no line strips to a leading `|`); DoD#4 adds an adversarial leading-whitespace case.
- **L6 (substantive) — DoD#7 hardcoded 4-series.** → reworded to the set-invariant; the 4 are illustrative.
- **L12 (substantive) — REVERSIBILITY asserted "no SHA cascade" without citing inputs.** Verified `compute_gates_content_sha` hashes `gates_config` (`:305-322`), `snapshot_sha256 = snapshot.snapshot_hash` (`:477`). → added as R6.
- **L13 (craft) — baseline asserted, "1 skipped" env-dependent.** → DoD#6 floor reworded to "passed ≥ 163 + new tests"; skip excluded from the floor.

**Resisted (verified):**
- **L7 (structural) — claim that `brainstorms/_TEMPLATE.md` also needs the paste-wording fix.** RESISTED. Verified `_TEMPLATE.md:304` ("Paste the output of `gate_eval` **verbatim** here") + `:311` ("byte-identical to **CLI stdout**") already unambiguously cover the full output incl. the block. The narrow-"table" wording is **only** in SKILL.md B.5, which is already in FILES CHANGED §6.4. No template change.
- **L3 (substantive) — a JSON consumer keyed on label could collide.** RESISTED. Verified via grep: no consumer parses `render_table(fmt="json")` output beyond the CLI `print` — the field is additive and no code iterates `data_confidence_series` by label. The DFR/"ECB deposit rate" collision is exclusively a `parity_check` markdown pipe-parse concern, sidestepped by the non-pipe form.
- **L11 (craft) — "age unknown" inconsistent with the table's `—` null convention.** RESISTED. The block is a plain-language operator note (user preference: plain language); `age unknown` is clearer than the terse `—` for a non-quant reader, and the two surfaces have different audiences. Non-blocking craft tag.

**Round 2 (fresh Isolated Challenger on amended draft):** verdict **flawed** (11 L-items; structural L1, L2). Count decreasing R1→R2 (13→11; structural 3→2). All load-bearing claims re-verified on disk. Approach unchanged throughout (same FILES CHANGED, same DECOMPOSE — no scope expansion).

**R2 absorbed (corrections/clarifications):**
- **L1 (structural) — DoD#4 test passed strings to `extract_prose_tiers(prose_path: Path)`** which does `.read_text()`. Verified `scripts/data/parity_check.py:84,91`. → DoD#4 now writes fixtures to `tmp_path` files and passes `Path`.
- **L2 (structural) — "same object to both sinks" is type-incoherent** (`data_staleness_tiers: list[Tier]` vs `data_confidence_series: list[dict]`). Verified `_data_confidence_contribution` returns a bare `Tier` (`:190-205`). → manifest 1(b) reworded to "same scalar tier *value* reused in two places" (the no-drift invariant), not "same object."
- **L3 (substantive) — DoD#6 "≥163 + new tests" unfalsifiable.** → floor set to **≥169** with the component breakdown (163 + ~3 + ~3).
- **L4 (substantive) — B.2/B.3 checkpoint `gate_table_sha256` inherits the block, undeclared.** Verified `SKILL.md:178`. → added to §Downstream consumer surfaces as benign (live-computed SHA, deterministic block).
- **L6 (substantive) — DoD#7 "tier+age" falsified for None-staleness.** → reworded to "tier + age (or `age unknown`)".
- **L7 (substantive) — pinned age digits won't match a real run.** → block relabelled "shape exemplar"; pinnable = heading/line-format/sort, NOT digits; DoD#3 asserts format not digits.
- **L8 (substantive) — sort-by-series_id contradicted the pinned block order.** Verified `sorted([CPIAUCSL,UNRATE,DFR,ei_cphi_m…]) = [CPIAUCSL,DFR,UNRATE,ei_cphi_m…]`. → pinned exemplar reordered to series_id order.
- **L9 (craft) — DoD#2 buried the guard rationale.** → reworded to lead with the future-drift-guard purpose (safe-form-leads).
- **L10 (craft) — `extract_prose_tiers` cited `:96-130`; real span `:84-132`.** → citation corrected.

**R2 resisted (verified):**
- **L5 (substantive) — claim the B.5 edit is unnecessary scope (in tension with the L7 template-resist).** RESISTED with clarification: the two are NOT in tension. `_TEMPLATE.md:304` says "the **output** of gate_eval verbatim" (no narrowing noun) — already covers the block, hence resisted. SKILL.md B.5 (`:189-190`) says "the markdown **table** output" — the noun "table" is the specific ambiguity-source absent from the template, so the one-line B.5 clarification is warranted (DoD#8). The distinguishing factor is the "table" noun.
- **L11 (substantive) — L3 resist lacked auditable grep evidence.** RESISTED→now cited: `render_table(fmt="json")` output is consumed only at `scripts/data/gate_eval.py:566` (`print(render_table(report, fmt=fmt))`); grep of `scripts/ --include='*.py'` returns no other caller. Recorded in §Downstream consumer surfaces.

**Round 3 (fresh Isolated Challenger on R2-amended draft):** verdict **STRUCTURAL: sound** (confidence delta −0.30, 8 substantive/craft residuals; **zero structural**). Per iteration discipline (CLAUDE.md §IDG / `/propose` Step 4b): *STRUCTURAL: sound is authoritative for shipping* → **the cross-check sequence CLOSES at R3** (terminal, no grind). The Challenger independently verified on disk that R1+R2's structural defects are genuinely closed: manifest 1(b) preserves the aggregate (tier computed once, reused; `data_staleness_tiers` is `.count()`-ed → order-independent), the gated/ungated leg separation (`:439` vs `:461`) is real, DoD#4's `tmp_path`/`Path` mechanism is executable, the sort/exemplar is self-consistent.

**R3 absorbed (test/DoD hardening — no design change, FILES CHANGED unchanged):**
- **L7 (substantive) — no negative assertion that a gated series is excluded from the captured list.** → DoD#1 gains a negative assertion (`VIXCLS` absent from `data_confidence_series`).
- **L1 (substantive) — `_UNGATED_SERIES_LABEL` 4-key enum vs config-driven loop; raw-id fallback untested.** → DoD#3 gains a fallback-label test.
- **L2 (substantive) — DoD#4 inertness omitted the `_TIER_PATTERN` bold-wrap layer.** Verified `:79` matches only `**TIER**`; block emits bare tiers → second inertness layer. → noted in DoD#3.
- **L6 (craft) — `≥169` + `~` floor unfalsifiable.** → DoD#6 reworded to exact `163 + N`, N counted at implementation, no `~`/open `≥`.
- **L4 (craft) — exemplar real-looking digits invite pinning.** → exemplar ages changed to `NNd` placeholders.
- **L8 (craft) — cross-file test ownership unstated.** → DoD#4 names `tests/test_parity_check.py` as owner of the table+block fixtures.

**R3 noted (not absorbed — low value / already covered):**
- **L3 (substantive) — JSON round-trip equality only enumerates current keys; a genuinely non-native future field would need its own test.** Acknowledged as a known limitation of the forward-protection (the test guards the *current* shape + flags the *mechanism*; a new non-native field is a future proposal's DoD). No present-day gap.
- **L5 (substantive) — no runtime-obs for the degenerate no-`snap_date` all-`age unknown` render.** The DoD#7 invariant already admits the "(or `age unknown`)" case; the cautious-fail invariant (DoD#5) covers the tier. A dedicated degenerate-snapshot obs is low value for a visibility-only change — **carry-forward note**, not a blocker.

**Cross-check CLOSED: R1 (flawed, 3 struct) → R2 (flawed, 2 struct) → R3 (sound, 0 struct).** Monotonic structural convergence 3→2→0; L-count 13→11→8. Ready for user approval.

## Amendments
- **Amendment 1 (2026-06-22, operator-approved scope expansion).** Steering's staged-set verification found the verbatim `gate_eval` render parses to **7** gates, not 8: `render_table` emits gate-**ids** as col-0 labels (`us_payrolls`, underscore), but `_PROSE_LABEL_TO_GATE_ID` only had the human aliases `"us payrolls"`/`"payrolls"`. Pre-existing (S-25d touched neither surface); the S-25d block is inert. But the DoD/CHANGELOG "exactly 8" was verified via a human-label fixture, not the real render — false for the actual output. **Operator chose to make it true.** Added `scripts/data/parity_check.py` (MODIFY) to §6; added `"us_payrolls": "us_payrolls"` to the map; added a real-render test; reworded DoD #4/#7. Fresh ≥L1 Challenger pass on the delta below.

## Delta Annexe — Parity-map fix (2026-06-22, operator-approved scope expansion)
**Cross-Check path: isolated-challenger** — reason: no external/alternate model API configured (CLAUDE.md §3 (a)). Fresh ≥L1 pass on the DELTA (the new map key + the new real-render test) per CLAUDE.md L52 (scope-expansion delta cross-check), BEFORE re-staging.

FATAL-claim verification (CLAUDE.md §2): independently confirmed on disk before changing anything — real render → `extract_prose_tiers` → 7 gate-ids; `us_payrolls` the sole unmapped gate-id (other 7 map). Post-fix: all 8 round-trip (verified via live gates.yml + 2026-06 snapshot through `evaluate_gates`→`render_table`→`extract_prose_tiers`).

Challenger verdict on the delta: **STRUCTURAL: sound** (6 L-items, all substantive/craft; zero structural). Verified: exact-match lookup (`_PROSE_LABEL_TO_GATE_ID.get(label)`) → no collision with the per-series block labels or any prose row; the new key is not over-broad; inertness is enforced by the `startswith("|")` filter *upstream* of the lookup, so the delta cannot touch it; all 8 gate-id render labels now resolve.

- **L4 (substantive) — CLOSED by class-guard test (operator-approved 2026-06-22, Option 1).** Added `test_every_deployment_gate_id_self_maps_in_prose_label_table` to `tests/test_parity_check.py`: derives the gate set from `config/gates.yml` (the authoritative source `evaluate_gates`/`render_table` use — NOT a hardcoded literal, so a FUTURE gate is covered, closing the class not the instance), with a non-vacuity guard (`assert gate_ids >= _EIGHT` before the loop so an empty/misderived set can't pass trivially), then asserts each gate-id self-maps. Non-vacuity proven: simulating the map with `us_payrolls` removed reds the guard on exactly `['us_payrolls']`.
- **L1/L2 (substantive) — CLOSED (overlap with L4).** L4's class-guard derives the gate set from `gates.yml` (the same set `evaluate_gates` keys its report by), closing the "render→parse asserts only a hand-built set" gap; the evaluate-side is additionally covered by `TestArtefactSync` + `test_live_smoke.py`.
- **L3 (craft) — CLOSED.** The cross-module emission contract asserted by the `parity_check.py` map-key comment is now bound by the L4 class-guard test (a `render_table` change that stopped emitting gate-ids verbatim would red it).
- **L5 (substantive→coverage) / L6 (craft) — noted, no action.** Inertness derives from non-pipe-ness (holds structurally regardless of label text); the bare-tier second layer guards a non-existent pipe-form code path. Neither is a live defect.

## Status Log

> Append-only. The closing DONE entry MUST be paired with a [`CHANGELOG.md`](../CHANGELOG.md) line.

- 2026-06-21 — DRAFT opened. FIRST-MOVE disk re-derivation: HEAD `9ddb9fa`, origin/main == HEAD (0/0), `git status` clean except `?? docs/retros/`; pytest baseline **163 passed, 1 skipped** (DoD #6 floor). All FLOOR FACTS (F1–F8) re-verified on disk.
- 2026-06-21 — Cross-check (isolated-challenger) CLOSED: R1 flawed (3 struct) → R2 flawed (2 struct) → R3 **sound** (0 struct); all L-items byte-verified before absorb/resist. Operator APPROVED.
- 2026-06-22 — status → **APPROVED**. Implemented via Sonnet implementation-agent (2 dispatches; each diff verified vs FILES CHANGED): `scripts/data/gate_eval.py` (label dict + fold capture + `data_confidence_series` field + non-pipe render block), `tests/test_gate_eval.py` (+5 tests), `tests/test_parity_check.py` (NEW, +5 tests), `.claude/commands/war-room/SKILL.md` (B.5 wording). Full suite **173 passed / 1 skipped** (163 + 10). `/code-reviewer` **APPROVE WITH NOTES** (3 NOTEs, non-blocking). `/process-sheriff` CLEAR. Runtime-obs confirmed (all 4 ungated series rendered; parity yields exactly 8). All 8 DoD satisfied. **COMMIT HELD** — awaiting steering staged-set byte-verification + explicit operator commit approval; no push this arc. NOT pre-flipped to DONE per steering checkpoint instruction.
- 2026-06-22 — **Operator-approved scope expansion (Amendment 1): parity-map `us_payrolls` fix.** Steering staged-set verification found the verbatim render parses to 7 (not 8): `us_payrolls` gate-id label absent from `_PROSE_LABEL_TO_GATE_ID`. FATAL-claim independently verified on disk (7→post-fix 8). Added `scripts/data/parity_check.py` (`"us_payrolls": "us_payrolls"`) + a real-render test; reworded DoD #4/#7; CHANGELOG/PROGRESS reconciled. Fresh ≥L1 Challenger pass on the delta (CLAUDE.md L52) → **sound** (6 L-items, 0 structural); L4 (instance-not-class) FLAGGED for operator decision, not self-absorbed. Full suite **174 passed / 1 skipped**. Re-staged 9 files by explicit name. **COMMIT STILL HELD** — awaiting steering staged-set RE-verification + operator commit approval. Steering's verdict NOT pre-written here.
- 2026-06-22 — **Challenger delta-L4 CLOSED (operator-approved Option 1):** folded the class-guard test into `tests/test_parity_check.py` — derives the deployment-gate set from `config/gates.yml` (authoritative, not a literal → covers future gates) + non-vacuity guard (`>= _EIGHT` pre-loop) + per-gate self-map assertion. Non-vacuity proven (simulated `us_payrolls` removal reds the guard). Closes L1/L2/L3 by overlap. No source change, no new file (test-only, same file). No fresh full Challenger round (folding the L52 delta-pass's own remedy — #18 proportionality). Full suite **175 passed / 1 skipped** (prior 174 + 1). Re-staged 9 files by explicit name; pre-commit hook exit 0. **COMMIT STILL HELD** — awaiting steering staged-set re-verification + operator commit approval; no push. Steering verdict NOT pre-written.
- STEERING STAGED-SET VERDICT (2026-06-22, authored by the steering session): PASS. Independently re-verified on the staged blobs — 9-file set exact (by-name, no concurrent bleed); full suite 175 passed/1 skipped (163+12); verbatim render→extract_prose_tiers == exactly 8 gate-ids incl. us_payrolls (real render, end-to-end); class-guard sources deployment_gates from gates.yml with a pre-loop non-vacuity assert; pre-commit hook exit 0 on the staged set; status reconciliation honest (APPROVED not DONE, no fabricated SHA). Cleared for commit on operator approval.
- 2026-06-22 — **DONE.** Operator approved commit; steering staged-set verdict PASS (above). S-25d shipped: `gate_eval.render_table` per-series ungated core-macro block + `data_confidence_series` GateReport field (visibility-only, aggregate unchanged) + `parity_check` `us_payrolls` gate-id alias + class-guard. All 8 DoD satisfied; full suite 175 passed/1 skipped; `/code-reviewer` APPROVE WITH NOTES; `/process-sheriff` CLEAR; cross-check R1→R2→R3 sound + parity-delta pass sound. Frontmatter→DONE, PROGRESS/README→DONE, CHANGELOG held-tag dropped, all flipped atomically with this commit (DONE reads true as it lands). Paired CHANGELOG line under `### Added`. No push (separate operator-gated step; none this arc).
