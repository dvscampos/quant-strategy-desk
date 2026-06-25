---
id: 034
title: S-24-remainder — equity-vs-50wMA gate (yfinance provider) + structured manual-input slot
status: DONE
owner: Daniel Campos
opened: 2026-06-23
updated: 2026-06-25
tags: [S-24, data-layer, deployment-gates, provider, schema-change]
---

# 034 — S-24-remainder: equity-vs-50wMA gate + structured manual-input slot

**Tier: HEAVY** — new provider archetype (yfinance), new CLI subcommand, snapshot-schema extension (`manual_gates`), risk-relevant gate (drives "Abort European equity deployment"), 15 files. Evidence: 4 CREATE + 11 MODIFY (see §6; incl. Amendment-1 SHA cascade); blast radius WIDE on `gate_eval.py` (6+ dependents).

## Summary

Closes the two remaining legs of S-24. **Leg A** wires the `stoxx600_vs_50wk_ma` deployment gate — which already exists in `config/gates.yml:135-143` but is unwired to any fetch — to a new `EquityMaProvider` that pulls STOXX Europe 600 (`^STOXX`) daily history via yfinance, computes the 50-week (250-trading-day proxy) moving average, and returns the latest close's percentage deviation as a single observation. **Leg B** adds a structured manual-input slot for the three categorical judgement gates (`hormuz`, `ecb`, `tariff`) via a new `set-manual` CLI subcommand that injects a `manual_gates` block into an already-fetched snapshot and recomputes the canonical hash. Both legs convert gates that today read `unavailable → RED-by-omission` into gates carrying real values. A schema-doc edit in `docs/DATA_STANDARDS.md` documents the new `manual_gates` key and reconciles the already-stale source list. Design ratified by steering 2026-06-23.

## Motivation / Problem

Live `gate_eval` on the real `2026-06` snapshot (runtime-obs baseline, captured 2026-06-23):

```
| hormuz              | — | **RED** | … | unavailable | — |
| ecb                 | — | **RED** | … | unavailable | — |
| tariff              | — | **RED** | … | unavailable | — |
| stoxx600_vs_50wk_ma | — | **RED** | … | unavailable | — |
**Market_Risk_Tier**: RED
**Data_Confidence_Tier**: RED
```

Four of eight deployment gates are `unavailable`, each scored RED by the Data Failure Protocol (`gate_eval.py:423` — "not green by omission", `RISK_FRAMEWORK.md:321`). These four force both aggregate tiers to RED on every session regardless of the actual macro picture — the streetlight-effect blind spot the open P-07 roadmap item names. `stoxx600_vs_50wk_ma` is unwired despite a complete gate definition; `hormuz/ecb/tariff` are categorical human judgements with no write path into the snapshot (`snapshot.build_payload` emits only `{as_of, session, snapshot_hash, series}` — `snapshot.py:58-63`; the read path at `gate_eval.py:411-418` already supports `manual_gates`, but nothing writes it).

## 1. DECOMPOSE

| # | Sub-problem | Target scope | Type | DoD |
|---|---|---|---|---|
| A1 | Equity provider — yfinance `^STOXX`, 250-day MA, deviation, band-guard, DDP raise | `scripts/data/providers/equity_ma.py` (new) | New archetype | #3 |
| A2 | Fetch-loop wiring (series entry + provider branch) — **land together** (L4) | `config/gates.yml`, `scripts/data/cli.py` | Config + routing | #2,#4 |
| A3 | Gate mapping | `scripts/data/gate_eval.py` (`SERIES_TO_GATE`, `_GATE_STALENESS`) | Constant add | #2 |
| B1 | Manual-injection write path (`inject_manual_gates` + `set-manual` subcommand) | `scripts/data/snapshot.py`, `scripts/data/cli.py` | New write path + CLI | #5 |
| B2 | Manual-gate validation (keys ∈ categorical gates, values ∈ tier labels, verify-then-recompute hash, no schema bump) | `scripts/data/cli.py` | Guard | #6,#7 |
| D1 | Schema doc (`manual_gates` + source-list reconciliation incl. EUROSTAT) | `docs/DATA_STANDARDS.md` | Doc | — |
| T1 | Tests (provider, set-manual, wiring, end-to-end runtime-obs); declare yfinance dep | `tests/*`, `requirements.txt` | Test + dep | #1,#3,#4,#5,#6,#8 |

**7 sub-problems → 15 files: 4 CREATE + 11 MODIFY = 15 ✓** (breakdown in §6; `provider.py` added in Core-Team absorption; REPLAY_DELTA.md + proposal-003 added in Amendment 1 — the gates.yml SHA cascade).

## Proposal

### Leg A — equity-vs-50wMA gate (yfinance `EquityMaProvider`)

- **Source** (ratified): yfinance `^STOXX`. `docs/RISK_FRAMEWORK.md:253` already designates **yfinance** as the STOXX Europe 600 source. FRED does not carry the proprietary STOXX index; IBKR (DATA_STANDARDS priority 1) needs a live gateway, unsuited to unattended fetch. Verified live 2026-06-23: `^STOXX` → shortName "STXE 600" (the STOXX 600), currency EUR; the wrong sibling `^STOXX50E` (EURO STOXX 50) trades roughly an order of magnitude higher (~10×).
- **MA convention** (Flag A — label, comment, code agree): the gate label stays "STOXX 600 vs 50-week MA"; the implementation computes a **250-trading-day MA on daily closes** (50 weeks × 5 trading days = 250) using the **latest daily close** as the level. Daily bars (not weekly) give a fresh same-day vintage (~1-day staleness, aligned with the other daily gates VIX/brent) rather than a week-start vintage that could spuriously read AMBER. Verified 2026-06-23: the full 2-year daily history (>250 bars), a fresh latest close, deviation clearly above +2 → GREEN.
- **Output shape**: `fetch()` returns a single `SeriesObservation(source="YFINANCE", series_id="^STOXX", as_of=<latest close date>, value=<deviation pct>, vintage=<latest close date>, units="pct_deviation_from_ma")`. Storing the derived deviation (not the raw level) matches the PAYEMS precedent (`fred.py:33` stores MoM change, not level) and keeps `gate_eval` unchanged — the value classifies straight through `_classify_numeric` against the existing ±2 bands.
- **Symbol-collision + DDP band-guard** (Flag C, asymmetric): after computing the latest level,
  - level is `None` / `NaN` / `≤ 0` → **raise** (garbage / no-data → DDP loud fail);
  - level `> 2000` → **raise** (symbol collision — `^STOXX50E`, an order of magnitude higher / any 10× sibling drift);
  - otherwise **proceed** (a severe-bear low print computes its deviation and reads RED — never raised). The upper bound is the load-bearing collision guard; the lower check is a pure garbage-catcher, **not** a market-level floor.
- **DDP failure path**: empty history, `< 250` usable closes, or a yfinance exception → `raise` → `_fetch_all` (`cli.py:101-103`) → `sys.exit(1)`. Never a silent gate. A missing `yfinance` import raises (not the silent `{}` of `reconcile_ibkr.py`, since this source is now load-bearing).
- **Fetch-loop wiring** (L9 coupling — land together): add `^STOXX` to `config/gates.yml data_staleness.series` (`source: YFINANCE`, `amber_age_days: 5`, `red_age_days: 10`) **and** a `YFINANCE` branch in `cli._build_providers` (`cli.py:67-86`) constructing `EquityMaProvider()` with a `known_series()` fail-fast guard — exactly parallel to the existing EUROSTAT branch. Without both, every subsequent `fetch` hits `unresolvable → sys.exit(1)`.
- **Gate mapping**: add `"^STOXX": "stoxx600_vs_50wk_ma"` to `SERIES_TO_GATE` (`gate_eval.py:96`) and `"stoxx600_vs_50wk_ma": {"amber": 5, "red": 10}` to `_GATE_STALENESS` (`gate_eval.py:105`). Being in `SERIES_TO_GATE` makes `^STOXX` a *gated* series → excluded from the S-25d ungated fold (`gate_eval.py:461`), so no double-count.

### Leg B — structured manual-input slot (`set-manual` subcommand)

- **Mechanism** (ratified): a **separate** `set-manual` subcommand, not an extension of `fetch`. Cleanly separates the unattended network pull from human judgement.
- **Write path**: `set-manual --session YYYY-MM --gate hormuz=Open --gate ecb="Hold or cut" --gate tariff="No escalation"`:
  1. require the snapshot to **exist** (else error — this is an in-place update, distinct from `fetch`'s refuse-without-`--force` at `cli.py:119-123`);
  2. **verify the existing hash** before touching it (refuse on mismatch — never build on a tampered snapshot, per `RISK_FRAMEWORK.md:318`);
  3. **validate** each gate: key ∈ the categorical `deployment_gates` (`hormuz`/`ecb`/`tariff`), value ∈ that gate's tier labels (loud reject on a typo — avoids the silent `_classify_categorical → RED` at eval time);
  4. inject `snapshot["manual_gates"][gate] = {"value": <label>, "as_of": <ISO date entered>}`, recompute the hash via `SnapshotWriter.inject_manual_gates` (a new pure classmethod, **not** `build_payload`), **atomic-write** (`.tmp` + `os.replace`).
- **No schema-version bump**: `manual_gates` is additive and the read path already handles it at version 1 (`gate_eval.py:411-418`); bumping to 2 would make an un-upgraded `gate_eval` *raise* (`_validate_schema`, `gate_eval.py:253-258`). The DATA_STANDARDS §134 "schema change = new proposal" governance is satisfied by *this* proposal documenting the key; the version integer does not move because no reader-breaking change occurs.
- **Manual-gate staleness** (ratified): keep the existing D4 fresh-by-design invariant — `cached + no staleness_days → GREEN` data-confidence contribution (`gate_eval.py:201-216`). No `gate_eval` change. The operator re-enters these each War Room session; staleness decay is explicitly out of scope (banked as a separate follow-up if ever wanted).
- **`build_payload` + golden hash untouched**: the new `inject_manual_gates` classmethod is independent of `build_payload`, so `test_snapshot_hash.test_golden_hash` (`_GOLDEN_HASH` pinned, no `manual_gates`) stays green.

### Docs

- `docs/DATA_STANDARDS.md` — add `manual_gates` to the schema Shape + Field spec; add a one-line "written only via `set-manual`, never hand-edited" provenance note; reconcile the already-stale `:165` source list (`"FRED" | "ECB"` → add the shipped `"EUROSTAT"` **and** the new `"YFINANCE"` — decision 3, ratified in-scope).

## Scope & Out-of-Scope

**In scope**: leg A (equity provider + wiring + mapping), leg B (`set-manual` + injection + validation), the DATA_STANDARDS edit (incl. EUROSTAT reconciliation), `requirements.txt` yfinance declaration, tests, runtime-obs.

**Out of scope (deferred)**: second STOXX-600 cross-validation source (→ S-29 multi-source pricing); manual-gate staleness decay (separate follow-up); an equity-provider on-disk stale-cache fallback (banked — the DDP partial-failure path covers it, see L22); graceful per-source degradation in `_fetch_all` so one flaky source doesn't abort the whole fetch (banked follow-up, L22); operator-attestation steps in `brainstorms/_TEMPLATE.md` when the equity gate reads RED / on manual re-entry (Risk cond1/cond2 — a War-Room-template change, separate from this data-layer arc); a `set-manual --clear` path to revert a gate to `unavailable` (B-I3 — to reset, re-fetch a fresh snapshot or overwrite with a conservative tier); central-bank meeting-calendar pull (S-24 residual, separate); any War Room #4 run; any push (operator-gated, separate).

**Aggregate-tier note (B-I4)**: Market_Risk_Tier is **not** asserted non-RED off wiring — manual values classify to their entered tier, and 3 simultaneous AMBER (a realistic geopolitical-stress + ECB-hold + tariff-uncertainty combination, newly reachable for the first time) trip `amber_count_escalation` → Market RED. The operator should expect this.

## Definition of Done

Binary, runtime-obs-executed (`#42` — every count/tier DoD run on the real `gate_eval` surface, never fixture-asserted-only):

1. `python3 -m pytest -q` → all green (baseline 175 passed / 1 skipped; new tests added).
2. **Leg-A provider math (monkeypatched yfinance — the real provider path, L16)**: `test_equity_ma_provider` feeds a synthetic 250+-bar daily frame and asserts `EquityMaProvider.fetch()` returns `value == round((latest−MA250)/MA250×100, …)`, `units="pct_deviation_from_ma"`, `vintage == latest close date`. This exercises the provider code (MA + deviation), which a fixture-snapshot DoD does **not**.
3. **Leg-A live smoke (network-gated, optional)**: a `PYTEST_LIVE=1`-gated test (mirroring `tests/test_live_smoke.py`) fetches `^STOXX` and asserts a plausible deviation + level in the band. Marked optional — not part of the default suite.
4. **Leg-A render/aggregate (real `gate_eval` surface)**: `gate_eval --format markdown` on a fixture snapshot carrying a live-shaped `^STOXX` observation renders `stoxx600_vs_50wk_ma` as `data_source: live` with a real tier (exercises the read/render/aggregate path — explicitly *complementary to* #2, not a substitute for it).
5. **Leg-A band-guard**: `test_equity_ma_provider` asserts raise on level `≤0`/`NaN`/`>2000`, and proceed (→ computes deviation, reads RED if below MA) on a low-but-positive level.
6. **Leg-A wiring**: `test_build_providers_routes_yfinance` (parallel to `test_build_providers_routes_eurostat`) — `^STOXX` resolves to `EquityMaProvider`; an unknown yfinance alias fails fast.
7. **Leg-A stale-penalty (L17)**: a test confirms that a `^STOXX` observation with vintage `> red_age_days` old is downgraded one tier by the existing L23 penalty (GREEN→AMBER), documenting the new gate's participation in the cautious-fail machinery.
8. **Leg-B injection + refuse-on-tamper (L18)**: `set-manual` on a copy of a real snapshot produces a snapshot whose hash **re-verifies** (`SnapshotWriter.verify` True) and whose `gate_eval` shows `hormuz/ecb/tariff` as `data_source: cached` with their entered tier; **and** `set-manual` on a hash-mismatched snapshot exits non-zero **without writing** (traverses the refuse-on-tamper guard, not just the helper).
9. **Leg-B WRITE-side strictness + CLI surface (L25)**: via `cli.main()` (`set-manual` arg-parser + dispatch), `set-manual` accepts **only the 3 categorical judgement gates** (hormuz/ecb/tariff) and rejects (non-zero exit, no write) an unknown gate key, a **numeric gate key** (e.g. `brent` — fetched, not manually entered), and a categorical value not in the gate's tier labels. (The write side is deliberately *stricter* than the read side — see #13.)
10. **Leg-B no-bump (L23-craft)**: `set-manual` MUST NOT add a `schema_version` key (preserving the `build_payload` shape); `gate_eval` does not raise.
11. **Leg-B input-immutability (A-F3)**: `inject_manual_gates` leaves the input dict unmodified (`"manual_gates" not in input` after return).
12. **Aggregate (real surface)**: on a fixture snapshot with all 4 formerly-unavailable gates supplied (equity live + 3 manual), `gate_eval` shows **zero** gates with `data_source: unavailable`; `Data_Confidence_Tier` is no longer forced RED *by omission* (its value depends on the supplied tiers + other series' staleness — reported as executed, not asserted a priori; Market_Risk_Tier **not** asserted non-RED).
13. **Leg-B READ-side permissiveness + shared-codepath (Condition 2 / L52)** — the kind-gated `_validate_schema` is **deliberately *more permissive* than the write side** (legacy snapshots predate `set-manual`), exercised (not asserted) by **two** explicit tests:
    - (a) **categorical validated**: a snapshot with a categorical manual gate value NOT in its tier labels (e.g. `hormuz="open"` lowercase) → `evaluate_gates` raises (cautious-fail);
    - (b) **numeric passed through UNvalidated**: `evaluate_gates(local/snapshots/2026-04.json)` does NOT raise — that snapshot carries BOTH categorical manual gates (`hormuz="Threatened / exercises"`, `ecb="Hold or cut"`, `tariff="New threats / negotiations"`) AND **legacy numeric manual gates** (a brent price + a stoxx deviation) which the guard must let through to `_classify_numeric`, never label-check.
    Plus `test_parity_check` green (count stays 8) and `test_snapshot_hash.test_golden_hash` green (`build_payload` untouched).
14. `git diff` matches the §6 FILES CHANGED list exactly (15 files, incl. the Amendment-1 SHA cascade).

## Risks & Mitigations

See the L1–Ln adversarial pass below (the living risk register). Top-line:
- **yfinance flakiness / rate-limit** (Wallet-Bleed vector): single monthly fetch, fixed 2-y window, no retry loop; failure raises loudly → operator follows DDP. No unbounded pagination.
- **Availability regression (L22 — known trade-off, documented)**: because the equity series now rides the all-or-nothing `_fetch_all` loop (`cli.py:101-103`, `except (…Exception): sys.exit(1)`), a persistent yfinance outage blocks the *entire* snapshot — today the macro fetch cannot be blocked by yfinance. Accepted for this arc (monthly cadence; transient → re-run; the failure is loud, never silent). Graceful per-source degradation (skip the equity series → it reads `unavailable → RED`, the sanctioned DDP partial-failure path of `RISK_FRAMEWORK.md:321`) is banked as a follow-up rather than re-architecting `_fetch_all`'s contract for all providers in this arc.
- **No on-disk stale-cache for the equity gate (A-F1/CTO C2)**: yfinance bypasses `HttpClient`, so unlike the other 7 gates the equity gate has no `.http_cache/` DDP fallback. Documented in `DATA_STANDARDS.md`; a failed equity fetch surfaces as `unavailable → RED` (visible, not silent). Minimal last-good cache banked, not built.
- **Wrong-index silent gating**: band-guard (L1) + symbol verified. Coverage is narrow (catches the `^STOXX50E` collision (an order of magnitude higher) / any ≥2000 symbol; a same-scale wrong variant would pass — accepted residual, L21).
- **Single-source on a deployment-abort gate**: justified omission (L3), operator-ratified, compensating controls named.
- **Hash corruption via manual edit**: `set-manual` is the only sanctioned mutation; it re-verifies before and recomputes after (L6/L7); refuse-on-tamper is DoD-tested at the entry point (L18).
- **Transitive dependency fragility (CTO C1)**: yfinance pulls pandas/numpy (already used unpinned by `backtesting/`); now load-bearing → pinned explicitly in `requirements.txt`.

## Adversarial Loophole Pass (L1–Ln)

> Living artefact — extended across review rounds, never replaced. Producer pre-dispatch enumeration; Challenger (§4b) extends.

- **L1 — Wrong-symbol collision.** `^STOXX` silently swapped for `^STOXX50E` (an order of magnitude higher) gates on the wrong index. **Closed by** the asymmetric band-guard: raise if level `> 2000`. Symbol identity verified 2026-06-23 (shortName "STXE 600").
- **L2 — yfinance no-data / patchy / short history.** Empty frame or `< 250` usable closes → a wrong/garbage MA. **Closed by** raise → `_fetch_all` → `sys.exit(1)` (DDP loud fail); never a silent value.
- **L3 — Single-source on "Abort European equity deployment".** One un-cross-checked feed drives a high-stakes RED action. **Closed by** justified omission (operator-ratified): all existing providers are single-source; the dominant failure (wrong symbol) is caught by L1; no-data raises loudly (L2); the Risk Guardian sees `data_source`+`staleness` in the table. Second source banked → S-29.
- **L4 — Fetch-loop coupling.** A `data_staleness.series` entry without a `_build_providers` branch makes every `fetch` abort. **Closed by** landing both in the same change; DoD #4 routing test + DoD #2 end-to-end exercise the wired path.
- **L5 — schema_version trap.** Bumping to 2 makes un-upgraded `gate_eval` raise. **Closed by** not bumping; `manual_gates` read at v1; DoD #7.
- **L6 — set-manual on a missing/tampered snapshot.** Building on corrupt state. **Closed by** require-exists + verify-existing-hash-before-inject + recompute-after.
- **L7 — Overwrite semantics vs the L8 no-overwrite fetch guard.** `set-manual` intentionally updates in place. **Closed by** documenting it as a distinct, sanctioned in-place mutation (vs `fetch`'s refuse-without-`--force`); atomic `.tmp`+`os.replace`.
- **L8 — Silent categorical typo.** `hormuz=open` (lowercase) → `_classify_categorical` returns RED silently. **Closed by** set-manual validating the value ∈ the gate's tier labels at injection (loud reject).
- **L9 — D4 fresh-by-design staleness.** A forgotten-stale manual judgement reads GREEN forever. **Closed by** accepted bounded residual (operator re-enters each session); decay out of scope (ratified).
- **L10 — Golden-hash breakage.** Touching `build_payload` breaks the pinned hash. **Closed by** a separate `inject_manual_gates` classmethod; DoD #9.
- **L11 — Undeclared load-bearing dependency.** yfinance present but undeclared; a fresh cloner's gate silently fails. **Closed by** declaring it in `requirements.txt` (runtime tier) + provider raising on ImportError.
- **L12 — MA label/code mismatch (Flag A).** Label "50-week" vs 250-day code. **Closed by** the identity 250 trading days = 50 weeks, documented in the gates.yml comment + provider docstring; label is semantically correct.
- **L13 — Aggregate-tier over-claim.** Asserting Market/Data_Confidence non-RED off wiring alone. **Closed by** DoD #8 reporting executed tiers on the real surface with named inputs, never asserting non-RED a priori.
- **L14 — Consumer breakage (parity / dashboard / prompts).** **Closed by** verified no-change: stoxx + manual labels already self-map in `parity_check._PROSE_LABEL_TO_GATE_ID:57-78` (gate count stays 8); `generate_dashboard.py:71` scrapes prose session files, not `gate_eval` output; `prompts.py:89,111` injects `gate_table` as a `.format()` kwarg value (braces in values are not re-processed; new content has none anyway). DoD #9 re-runs `test_parity_check`.
- **L15 — Weekly-bar vintage staleness.** Week-start vintage spuriously AMBER. **Closed by** daily bars; vintage = latest daily close (~1-day staleness).
- **L16 [structural] — DoD "real surface" was fixture-only.** A fixture snapshot with a pre-computed `^STOXX` value exercises `gate_eval`'s read path but never `EquityMaProvider.fetch()` / the MA math / the routing branch. **Closed by** splitting the DoD: #2 (monkeypatched provider math), #3 (optional live smoke), #6 (routing test) traverse the provider path; #4 keeps the render/aggregate fixture check, explicitly labelled complementary. Verified: `gate_eval.py:396-408` reads only `series_map[id]["value"]`.
- **L17 [structural] — Stale-penalty interaction unmodelled.** Adding `^STOXX` to `_GATE_STALENESS` means a `>10`-day-old snapshot downgrades a GREEN equity tier (L23 penalty, `gate_eval.py:429-435`). The "classifies straight through" prose under-modelled this. **Closed by** acknowledging it is the *intended* cautious-fail behaviour shared by every numeric gate (consistent, not a bug); the daily-vintage choice keeps it GREEN-eligible under normal fresh-fetch cadence; DoD #7 tests it. Verified against bytes.
- **L18 [substantive] — Refuse-on-tamper untested (entry-point-guard anti-pattern).** The L6 "verify before inject" claim had no DoD exercising the refuse branch; `inject_manual_gates` could recompute unconditionally and still pass green. **Closed by** DoD #8 feeding a hash-mismatched snapshot → non-zero exit + no write (traverses the production guard, per CLAUDE.md "test the guard at the entry-point").
- **L19 [substantive] — Source-list reconciliation has no asserting test.** Doc enum can drift again. **Resisted (doc-only):** the `:165` edit lists all four sources (FRED/ECB/EUROSTAT/YFINANCE); an asserting doc-vs-`source_name` test is brittle and banked, not built. Verified `2026-06.json` already ships `EUROSTAT` (doc already stale today).
- **L20 [structural] — `manual_gates` value-shape unvalidated at read.** `_validate_schema` (`gate_eval.py:260-267`) checks keys only; a valid-key/invalid-value snapshot reads RED silently; the stored `as_of` has no reader. **Closed by** a value-in-tier-labels guard in `_validate_schema` (cautious-fail), documenting `as_of` as audit-only, and a D4 comment at the `staleness_days` read (`:415`). Verified.
- **L21 [substantive] — Band-guard over-claims "any 10× sibling".** Real protection is narrow (the EURO STOXX 50 collision, an order of magnitude higher / any ≥2000). **Closed by** rewording to the accurate coverage + naming the same-scale-variant residual (a same-magnitude gross-return variant) as accepted. Verified the two indices differ by ~10×.
- **L22 [substantive] — One flaky source aborts the whole fetch.** `_fetch_all` (`cli.py:101-103`) `sys.exit(1)`s on any series failure; the wired equity series can now block all 8. **Closed by** documenting it in §Risks as a known availability trade-off (accepted for monthly cadence; loud not silent) + banking graceful per-source degradation (the sanctioned `unavailable → RED` partial-failure path) rather than re-architecting `_fetch_all` here. Verified.
- **L23 [craft] — DoD no-bump wording.** "(or 1)" hedged. **Closed by** rewording DoD #10 to "MUST NOT add a `schema_version` key."
- **L24 [craft] — `prompts.py` brace-safety rider.** "has none anyway" invites a future braced label. **Closed by** L14 rewording: the `.format()`-kwarg-value invariant is load-bearing (braces in substituted values are never re-scanned); "none anyway" is incidental, not the guarantee. Verified `prompts.py:89,111`.
- **L25 [substantive] — `set-manual` CLI dispatch/arg-parser untested.** `cli.main()` gains a `set-manual` arm + `--gate key=value` parsing with no named coverage. **Closed by** DoD #9 routing validation through `cli.main()`. Verified `main()` has only `fetch`/`gate_eval` arms today.
- **L26 [substantive] — 0.86 confidence unlabelled.** **Closed by** labelling it single-author (pre-Challenger) in §2 and naming the bypass asymmetry it must be read against (CLAUDE.md confidence-state distinction).
- **L27 [craft] — Bare line-cites drift.** This proposal's own edits shift the cited lines. **Closed by** acknowledgement: cites are accurate at draft (point-in-time artefact); property anchors used where cheap. Accepted residual.

## 2. ARCHITECT

**Primary sub-problem A (equity provider integration):**

> **Approach A — yfinance `EquityMaProvider`** (own HTTP; monkeypatched tests) — Confidence **0.86**
> Pros: yfinance is the project-documented STOXX 600 source (`RISK_FRAMEWORK.md:253`); already a repo dependency (`reconcile_ibkr.py`); `^STOXX` verified working (EUR, daily, fresh); `history()` returns the MA window natively and cleanly; established monkeypatch test pattern (`test_reconcile_ibkr`).
> Cons: bypasses the `HttpClient` (so no S-22 cache TTL / no on-disk DDP cache fallback); test harness diverges from the vcrpy-cassette pattern of FRED/ECB/Eurostat.
>
> **Approach B — Stooq CSV via `HttpClient`** — Confidence 0.55
> Pros: architecturally consistent (cassette-testable, S-22 cache, DDP on-disk fallback).
> Cons: Stooq is **not** in the DATA_STANDARDS hierarchy; its STOXX-600 symbol is unverified; CSV-history parsing is more fragile; reliability concerns.
>
> **Chosen: A** — the DATA_STANDARDS hierarchy + `RISK_FRAMEWORK.md:253` name yfinance explicitly; symbol verified; the `HttpClient`-bypass cost is bounded (monthly fetch; loud-fail on error preserves the DDP "never silently substitute" principle; the snapshot itself is the audit cache). Cross-validation (the "never rely on a single source" rule) is a justified omission for this arc (L3) — banked → S-29. _Confidence **0.86 is single-author** (pre-Challenger); see Delta Annexe R2 for the post-cross-check disposition. The bypass asymmetry — the equity series uniquely lacks the on-disk DDP cache fallback the other 7 gates enjoy, while sharing the all-or-nothing `_fetch_all` loop (L22) — is the main residual the number must be read against._

**Primary sub-problem B (manual write path):**

> **Approach A — separate `set-manual` subcommand** — Confidence **0.88** — **Chosen.** Cleanly separates unattended network fetch from human judgement; leaves `build_payload` + the golden-hash test untouched; intentional in-place update with verify-then-recompute.
> **Approach B — extend `fetch` with `--manual` flags** — Confidence 0.5. One command, but mixes automated + manual inputs in one atomic write and touches `build_payload` (golden-hash test surface). Rejected (steering-ratified).

## 6. FILES CHANGED (PROPOSED)

**CREATE (4):**
- `CREATE` `scripts/data/providers/equity_ma.py` — `EquityMaProvider`: yfinance `Ticker("^STOXX").history(period="2y", interval="1d", auto_adjust=True)`, defensive scalar `Close` extraction (mirroring `backtesting/engine/data.py:152-160` — CTO F6), named module constants `_MA_WINDOW_DAYS = 250` / `_SYMBOL_COLLISION_UPPER = 2000` with band-guard comment documenting the deliberate asymmetry (Risk cond3), DDP-raise on yfinance exception / `<250` bars / empty (A1).
- `CREATE` `tests/test_equity_ma_provider.py` — monkeypatched `yfinance` (the `test_reconcile_ibkr` pattern): deviation arithmetic, band-guard (raise on ≤0/NaN/>2000; proceed→deviation on a low-but-positive level), `<250`-bars raise, ImportError raise, ±2 boundary (A1; L16/Risk cond4).
- `CREATE` `tests/test_set_manual.py` — injection; hash re-verify-then-recompute; **refuse-on-tamper** (feed a hash-mismatched snapshot → non-zero exit + no write — L18); deep-copy (input dict unmodified — A-F3); validation (unknown/numeric gate key, value-not-in-tier-labels reject); **`set-manual` via `cli.main()` arg-parser + dispatch** (L25) (T1).
- `CREATE` `proposals/034-s24-equity-gate-manual-slot.md` — this artefact (self-admin).

**MODIFY (9):**
- `MODIFY` `config/gates.yml` — `^STOXX` in `data_staleness.series` (YFINANCE, 5/10); document the 250-day daily-proxy convention on the `stoxx600_vs_50wk_ma` comment (A2, Flag A).
- `MODIFY` `scripts/data/cli.py` — `YFINANCE` branch in `_build_providers` **mirroring the EUROSTAT branch's `known_series()` fail-fast, NOT the FRED branch** (A-F2); `set-manual` subcommand (no FRED-key gate — C-F7) + arg parser + `main()` dispatch arm; `inject_manual_gates`-based atomic write with a pid-suffixed tmp (`f"{session}.{os.getpid()}.tmp"` — C-F3).
- `MODIFY` `scripts/data/gate_eval.py` — `SERIES_TO_GATE` + `_GATE_STALENESS` entries (A3); a value guard in `_validate_schema` that fires **only for `kind == "categorical"` manual gates** (assert the extracted value ∈ `tiers.values()`; **numeric manual gates — e.g. `brent`/`stoxx600_vs_50wk_ma` in `2026-04.json` — are left to `_classify_numeric`, NOT label-checked**), extracting the value via the same dict-or-scalar logic as the reader at `:411-418` (cautious-fail — A-F8/L20; the L52 shared-codepath touch — Condition 2); a one-line D4 comment at the `staleness_days` read (`:415` — A-F6); render the manual gate's `as_of`/`staleness_days` in the existing Staleness column (visibility — PM I2/Risk cond2).
- `MODIFY` `scripts/data/snapshot.py` — `inject_manual_gates(payload, manual_gates) -> payload` classmethod: **deep-copies** the input, merges `manual_gates`, recomputes the hash via `compute_hash`; does not touch `build_payload` (A-F3/L10).
- `MODIFY` `scripts/data/provider.py` — update the `source` field comment `# "FRED" | "ECB"` → add `"EUROSTAT" | "YFINANCE"` (A-F7).
- `MODIFY` `docs/DATA_STANDARDS.md` — `manual_gates` Shape example + concrete field spec (`{value, as_of}`; `as_of` documented audit-only) + "written only via `set-manual`, never hand-edited" provenance + "YFINANCE provider has no on-disk DDP stale-cache fallback" note (CTO C2/C3); `:165` source-list reconciliation incl. EUROSTAT + YFINANCE (D1).
- `MODIFY` `tests/test_gate_eval.py` — end-to-end `^STOXX`→gate wiring (SERIES_TO_GATE) + categorical manual fold-in + the L17 stale-penalty interaction on the new gate (T1; ±2 epsilon already covered at `:179-187`).
- `MODIFY` `requirements.txt` — declare `yfinance>=0.2.54`, and pin its now-load-bearing transitives `pandas>=2.0` + `numpy>=1.24` explicitly (CTO C1, L11).
- `MODIFY` `proposals/README.md` — index row (self-admin).
- `MODIFY` `backtesting/REPLAY_DELTA.md` — **SHA cascade** (Amendment 1): the gates.yml `^STOXX` entry shifts the canonical content SHA `c437a025…` → `58b9151b…447e`; current-canonical line replaced in-place (the "at replay" `89ff983d…` preserved). Matches the Proposal 032 precedent.
- `MODIFY` `proposals/003-phase-1b-data-integration.md` — **SHA cascade** (Amendment 1): append-only Status Log entry recording the new canonical SHA, so `TestArtefactSync` stays green.

**Aggregate: 4 CREATE + 11 MODIFY = 15 files ✓** (provider.py added in Core-Team absorption — A-F7; REPLAY_DELTA.md + proposal-003 added in Amendment 1 — the inherent SHA cascade of any gates.yml edit, precedent Proposal 032). Self-admin enumerated: the proposal artefact (CREATE) + README (MODIFY). PROGRESS.md / CHANGELOG.md / retro deferred to `/commemorate` + `/retro` per convention.

## 7. REVERSIBILITY

**FULLY REVERSIBLE** — all changes are local code / config / docs / tests + one new snapshot-key written by an opt-in subcommand. `git revert` restores all state; no external mutation, no data sent to third parties, no irreversible step. (yfinance fetches are read-only GETs.) No IRREVERSIBLE change → no RISK FLAGS escalation. The eventual public push is a **separate, operator-gated** step outside this proposal.

## Core Team Review (A–D)

_Dispatched as isolated Task sub-agents (>3 files → AGENTS.md Mandatory Sub-Agent Reviews; no self-review). Verdicts absorbed in the Delta Annexe below._

### Quant Architect
**VERDICT: APPROVE WITH CONDITIONS.** F1 HttpClient-bypass / no stale-cache (HIGH); F2 YFINANCE branch must mirror EUROSTAT's `known_series()` guard, not FRED (HIGH); F3 `inject_manual_gates` deep-copy contract (MED); F4 `250` magic→config (MED); F5 `2000` magic→config (MED); F6 `staleness_days` read/write mismatch (MED); F7 `provider.py` `source` comment not in FILES (LOW); F8 `_validate_schema` value-in-tier-labels (LOW); F9 `known_series()` not on ABC (LOW).

### Portfolio Manager
**VERDICT: APPROVE WITH CONDITIONS.** Bundling justified; net-positive (current always-RED desensitises operators). I1 provider-level vintage freshness check (HIGH); I2 surface manual `as_of` in render (MED); I3 document no `--clear` path (LOW-MED); I4 document `amber_count_escalation` when 3 manual AMBER (LOW).

### CTO
**VERDICT: APPROVE WITH CONDITIONS.** C1 pin pandas/numpy/yfinance — transitive load-bearing (HIGH); C2 yfinance exception contract + `--no-cache` help text + DDP-no-cache doc (HIGH); C3 DATA_STANDARDS concrete `manual_gates` shape + governance note (MED); C4 `as_of` UTC + `auto_adjust=True` + defensive scalar `Close` (MED); F3 tmp-file pid suffix for concurrency (MED); F7 `set-manual` must not gate on FRED key (LOW); F8 atomic-write duplication (LOW).

### Risk Officer
**VERDICT: APPROVE WITH CONDITIONS.** Accepts S-29 deferral at micro-NAV; conditions are process-level. cond1 operator attestation when equity reads RED (MED, `_TEMPLATE.md`); cond2 manual-gate freshness attestation / surface `as_of` (MED); cond3 band-guard asymmetry code comment (LOW); cond4 explicit ±2 boundary test (LOW). Confirmed: neither leg can convert a correct RED → false GREEN via code logic alone (wrong-symbol false-GREEN is closed by the >2000 guard).

> **Orchestrator note:** all four APPROVE WITH CONDITIONS (no unanimous-clean-approval scrutiny trigger). E (Trader) / F (Compliance) not convened — no order-execution or new tradeable/regulatory instrument surface (the gate consumes an index *level*, not a position).

## Delta Annexe — Round 1 (Core Team)

Every absorbed/resisted item verified against bytes (cites inline). Classification per CLAUDE.md G15: all absorptions are scope-**correcting** or **narrowing** (DoD strengthening, defensive guards, named constants, docs) — none expand §1 DECOMPOSE; one file added (`provider.py`, A-F7).

**Absorbed:**
- **A-F2** (mirror EUROSTAT `known_series`, not FRED) — verified `cli.py:69-82`: FRED branch has no guard, EUROSTAT does. §6 made explicit.
- **A-F3 / CTO** (deep-copy `inject_manual_gates`; pid tmp suffix) — DoD #11 + §6.
- **A-F6** (D4 `staleness_days` comment) — verified read at `gate_eval.py:415`.
- **A-F7** (`provider.py` `source` comment) — verified stale at `provider.py:17`; added to §6 (→13 files).
- **A-F8 / L20** (`_validate_schema` value-in-tier-labels) — verified keys-only at `gate_eval.py:260-267`; guard added (cautious-fail).
- **CTO C1** (pin pandas/numpy/yfinance) — `requirements.txt` lacks all three; backtesting uses pandas unpinned. §6.
- **CTO C2** (yfinance exception contract; `--no-cache` help note; DDP-no-cache doc) — §Risks + DATA_STANDARDS.
- **CTO C3** (concrete `manual_gates` shape + governance note) — DATA_STANDARDS edit expanded.
- **CTO C4** (`as_of` UTC; `auto_adjust=True`; defensive `Close`) — verified the pattern at `backtesting/engine/data.py:152-160`; §6.
- **PM I2 / Risk cond2** (surface manual `as_of` in render) — minimal: render `as_of` in the existing Staleness column (parity reads col 0/2 only — safe).
- **PM I3** (no `--clear`), **PM I4** (`amber_count_escalation`), **Risk cond3** (band asymmetry comment), **Risk cond4** (±2 boundary — already at `test_gate_eval.py:179-187`, plus provider-level in DoD #5) — §Scope/§Risks/§6.

**Resisted (with reason):**
- **A-F4 / A-F5** (move `250` / `2000` to `gates.yml`) — **resisted.** `gates.yml` is the SoT for *gate thresholds* (the ±2 bands + staleness — which ARE there); provider-internal computation params live in the provider module by established precedent (`fred.py:26 _LOOKBACK`, `fred.py:30 _SERIES_META`, `eurostat.py:42 _SERIES_REGISTRY`). Encoded as named module constants (`_MA_WINDOW_DAYS`, `_SYMBOL_COLLISION_UPPER`) with comments — satisfies "no magic numbers" consistently with the archetype. Threading per-series config into providers is a new mechanism not currently used (FRED reads its own `_SERIES_META`, not `gates.yml`).
- **A-F9** (`known_series()` abstract on the ABC) — **resisted.** Verified `FredProvider` has no `known_series` (it accepts any FRED id); an `@abstractmethod` would break it. The duck-typed guard in `_build_providers` is the existing contract; a broader ABC refactor is out of scope.
- **A-F1 / B-I1 / Risk cond1** (build a stale-cache / provider freshness raise / operator attestation) — **partially resisted.** The provider sets `vintage` = the real latest-close date, so `gate_eval`'s amber5/red10 staleness machinery already catches a stale close (no redundant provider-level raise). Operator-attestation steps belong in `brainstorms/_TEMPLATE.md` (a War-Room-process change, out of this data-layer arc) — banked. A dedicated equity stale-cache is banked (the `unavailable → RED` DDP partial-failure path is the interim fallback).

## Delta Annexe — Round 2 (Cross-Model Critique / Isolated Challenger)

**Cross-Check path: isolated-challenger — reason: no external/alternate model API is configured in this environment (CLAUDE.md §3 condition a).**

Challenger R1 verdict: **flawed** (L16–L27; 3 structural). Every specific claim independently re-verified against bytes before absorption (CLAUDE.md FATAL-claim verification). Disposition: structural items L16/L17/L20 are all closable inline by DoD-strengthening + a small `_validate_schema` guard + prose clarification — **no §1 DECOMPOSE restructure, no §6 expansion beyond the A-F7 file**. Absorptions are scope-correcting (G15-safe).

**Absorbed:** L16 (split DoD #2/#3/#4 — provider path now traversed; verified `gate_eval.py:396-408` reads only the stored value), L17 (stale-penalty acknowledged as intended cautious-fail + DoD #7; verified `:429-435`), L18 (refuse-on-tamper DoD #8 — entry-point guard), L20 (value-in-tier-labels guard + `as_of` audit-only; verified `:260-267`), L21 (band over-claim reworded + residual named; verified the two indices differ by ~10×), L22 (availability trade-off documented + banked; verified `cli.py:101-103`), L23 (DoD #10 reworded), L24 (L14 `.format`-invariant reworded; verified `prompts.py:89,111`), L25 (CLI dispatch DoD #9; verified `main()` arms), L26 (0.86 labelled single-author).

**Resisted:** L19 (asserting doc-vs-`source_name` test — doc-only edit lists all four sources; test brittle, banked), L27 (bare line-cites — accurate at draft, point-in-time artefact; accepted residual).

**Closure-mechanism scrutiny (CLAUDE.md N=3):** each closure is a DoD item, a named guard, or a prose clarification verifiable at implementation — none introduces a new unverified surface. Because Challenger R1 returned structural items, this amended draft is presented to the operator for ship-vs-(R2-Challenger) arbitration (the structural-present escalation rule) — see the approval gate below.

## Amendments

- **Amendment 1 (2026-06-25, Leg-A implementation) — SHA cascade enumeration.** The approved gates.yml `^STOXX` edit shifts the canonical `compute_gates_content_sha` from `c437a025…cec96` → `58b9151b…447e`, which `TestArtefactSync` pins in `backtesting/REPLAY_DELTA.md` (current-canonical line) and `proposals/003` (Status Log). These two artefacts were **under-enumerated** in the original §6 (an inherent self-admin consequence of any gates.yml change — precedent Proposal 032). Surfaced as 2 failing `TestArtefactSync` guards during Leg-A verification (Real-time Execution Stop). Scope-**correcting** (not expanding): REPLAY_DELTA current line replaced in-place (historical `89ff983d…` preserved); proposal-003 got an append-only entry. FILES CHANGED 13 → 15. Suite green (186 passed / 1 skipped). Since only Leg A touches gates.yml, the SHA is final.

## Status Log

> Append-only. Closing DONE entry pairs with a CHANGELOG.md line.

- 2026-06-23 — DRAFT opened. Design ratified by steering (4 decisions + 3 flags). Pre-flight: every cite verified on disk; yfinance `^STOXX` symbol + level + deviation verified live; regression gate PASS (real 2026-06 snapshot renders prior S-25c/d features); blast radius WIDE on gate_eval.py.
- 2026-06-23 — Review complete. Core Team A–D all APPROVE WITH CONDITIONS (Sonnet sub-agents, isolated). Isolated Challenger R1: flawed (L16–L27, 3 structural), all claims byte-verified; absorbed into amended draft (DoD 10→14 items; FILES 12→13; §Risks + §Scope + L-pass extended). Awaiting operator approval (structural-present escalation — operator arbitrates ship vs R2-Challenger).
- 2026-06-25 — (working session) Condition 1 (count reconcile) satisfied in-draft; Condition 2 (the L20 `_validate_schema` guard must not regress `2026-04.json`) surfaced a real spec defect — `2026-04.json` carries numeric manual gates (`brent`/`stoxx`), so the guard is now `kind=="categorical"`-gated (DoD #13 exercises it). **Leg-A IMPLEMENTED** (Sonnet implementation-agent; orchestrator git-diff-verified, no scope slip): `equity_ma.py` provider + gates.yml/cli/gate_eval wiring + provider.py + requirements pins + 11 new tests. Amendment 1 (SHA cascade) handled. Suite 186 passed / 1 skipped. Leg B + docs pending. _(Steering arbitration verdict authored separately below — not pre-written by the working session, per [[feedback-status-log-audit-authorship]].)_
- 2026-06-25 — (steering) Leg-A checkpoint **VERIFIED CLEAN on the bytes** — suite 186/1 re-run, SHA oracle independently recomputed, cascade complete, Condition 2 resolved kind-gated, Flag C asymmetric band confirmed in code. Proceed to Leg B.
- 2026-06-25 — (working session) **Leg-B IMPLEMENTED** (Sonnet implementation-agent; orchestrator-reviewed the full diff, in-scope, gates.yml untouched per carry-forward 3): `snapshot.inject_manual_gates` (deep-copy, build_payload untouched), `cli.set-manual` (write-side strict: 3 categorical only, refuse-on-tamper at the production entry point, atomic pid-suffixed write, UTC as_of), `gate_eval._validate_schema` kind-gated read-side guard (categorical validated, legacy numeric passed through) + as_of render + D4 comment. 11 new tests; suite **197 passed / 1 skipped**. **INCIDENT (resolved):** the agent ran its live demo against the REAL `local/snapshots/2026-06.json` (against an explicit "use a temp copy" instruction), injecting demo manual_gates. Caught by byte-verification; the snapshot was **restored byte-identical** (manual_gates removed, hash recomputed = original `7e9dfa…`, `verify()` True) — `local/` is gitignored so no tracked-diff impact, but it would have contaminated the due War Room #4. Docs (Leg 3) + the DoD runtime-obs sweep pending. _(Steering verdict slot left for steering to author.)_
- 2026-06-25 — (steering) Leg-B **VERIFIED CLEAN on the bytes** — incident restoration byte-confirmed (2026-06.json: no manual_gates, 8 series, hash 7e9dfa, verify True) and contained (no stray .tmp, no collateral snapshot mutation); suite 197/1 re-run; Condition-2 kind-gating confirmed in code (read-permissive `_validate_schema` + write-strict `set-manual`). Proceed to Leg 3 + runtime-obs sweep.
- 2026-06-25 — (working session) **Leg 3 (docs) DONE + runtime-obs sweep EXECUTED.** `DATA_STANDARDS.md`: `manual_gates` Shape + field spec (`{value, as_of}`, as_of audit-only, no schema-version bump note) + `set-manual`-only provenance + YFINANCE-no-DDP-cache note + `:165` source-list reconciled (FRED|ECB → +EUROSTAT +YFINANCE). Runtime-obs on the real CLI `gate_eval` surface (temp /tmp fixture, NOT real data): BEFORE = 4 gates unavailable→RED, Market RED, Data_Confidence RED; AFTER (equity live deviation → GREEN + 3 manual cached→GREEN with `as of` render) = **0 unavailable gates**, Data_Confidence **AMBER** (real brent-9d-staleness, not omission), Market **AMBER** (executed 2-AMBER<3, never asserted non-RED a priori). **Full suite 197/1; SHA final 58b9151b; 15-file set complete (4 CREATE + 11 MODIFY).** All 3 legs + Amendment 1 implemented & orchestrator-verified. **Ready for the steering staged-blob gate** (staged-set name-check + sanitisation hook + DONE markers) → then `/commemorate`. _(Steering staged-blob verdict slot left for steering.)_
- 2026-06-25 — (working session) **#32 sanitisation BLOCK remediated.** Steering's staged-blob gate held: 3 of 15 files carried session-derived economics literals colliding with private brainstorm values (`scripts/data/providers/equity_ma.py`, `tests/test_set_manual.py`, `proposals/034`). Per radioactive-BLOCK discipline (no `--no-verify`, no learning the value, no allowlist — session-derived defaults to SCRUB): swapped ALL concrete economics/market literals in the 3 files for placeholders, not just the colliding one — proposal market levels/deviations genericised ("an order of magnitude higher", "a brent price + a stoxx deviation"); `test_set_manual.py` synthetic values → clearly-fictional out-of-range + year 2099 (test-fixture rule); `equity_ma.py` docstring market levels genericised (constants 250/2000 kept — config, not economics). Each file single-file-staged + hook-checked clean (exit 0); full 15-file staged-set hook exit 0; suite **197/1**; staging left clean. **Banked at the arc seam:** fresh N-evidence for the no-concrete-economics-in-tracked-files rule (proposal/test/provider embedded session literals that should have been placeholders from the start). _(Steering re-gate verdict slot left for steering.)_
- 2026-06-25 — STAGED-BLOB GATE CLEARED (steering, on the bytes). Suite 197/1 re-run; #32 sanitisation hook exit 0 on the real populated 15-file staged set (after a #32 BLOCK on 3 files — equity_ma.py / test_set_manual.py / proposal-034 — was remediated by SCRUB, no --no-verify/allowlist, each re-confirmed individually clean); staged-set name-check = 15; staged gates.yml blob → pinned SHA 58b9151b…447e; runtime-obs BEFORE/AFTER executed by steering on the real gate_eval surface (4 unavailable→RED ⇒ 0 unavailable; Data_Confidence RED-by-omission ⇒ AMBER real-signal; Market AMBER reported-as-executed, not asserted); Flag-C band-guard logic intact post-scrub; live-data incident restoration byte-verified + contained. Endorsed for /commemorate.
- 2026-06-25 — **DONE** (status flipped this session; commit lands same-session). `/commemorate`: `/process-sheriff` WARN (code-review + docs sequenced inside the gate, both resolved); `/code-reviewer` **APPROVE WITH NOTES** — 2 WARN test-theatre fixed (vacuous no-bump assertion → real `assert "schema_version" not in`; ImportError-path test rewired via `sys.modules` to exercise the real `fetch` try/except), NOTE 3 fixed (`_validate_schema` value extraction → `mg.get` for reader-parity + clean error), NOTE 4 left (harmless dead `level is None`). Suite **197/1**; runtime-obs executed. PROGRESS S-24 row + CHANGELOG `### Added` updated. 17-file commit (the 15-file set + PROGRESS.md + CHANGELOG.md) staged by explicit name. PUSH deferred (operator-gated, separate — pre-push sanitisation gate over `origin/main..main`).
