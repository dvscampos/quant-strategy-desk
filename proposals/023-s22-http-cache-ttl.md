---
id: 023
title: HTTP-cache per-series TTL + --no-cache on macro fetch (S-22)
status: DONE
owner: Daniel Campos
opened: 2026-06-03
updated: 2026-06-03
tags: [data-layer, http-cache, staleness, S-22]
---

# 023 — HTTP-cache per-series TTL + `--no-cache` on macro fetch (S-22)

**Tier: MEDIUM**

> Evidence: 5 source files + 2 test files modified + 1 test file created (8 code/test files), > 30 net source lines, within established patterns (extends the existing cache-hit gate at `http_client.py:65` and reuses the existing `skip_cache` flag at `http_client.py:36` + the existing `data_staleness` thresholds in `config/gates.yml`). Three of the five source edits (`provider.py`, `providers/fred.py`, `providers/ecb.py`) are mechanical signature pass-through; two are substantive — `http_client.py` (cache-hit + failure-path + 429-cap reroute semantics) and `cli.py` (`_fetch_all` gains `gates`, `_cmd_fetch` re-plumbed, `--no-cache` arg). The two test-file edits update the 7 non-production `fetch()` call sites to pass `max_age_days` explicitly (L2 Option A, operator-authorised 2026-06-03). No new architecture, no auth/billing/security surface → MEDIUM, not HEAVY. No irreversible step (no push, no schema migration, no external state mutation). MEDIUM + no irreversible action → full L1–Ln + Delta Annexe + Isolated Challenger cross-check (per CLAUDE.md §3 and the `/propose`-specific tightening).

## Summary

`scripts/data/http_client.py`'s on-disk cache (`data/.http_cache/`) has no expiry: once a response file exists for a `(method, url, params)` hash, `get()` returns it unconditionally (`http_client.py:65`). A "live" `fetch` therefore silently serves arbitrarily old cached responses until the cache directory is manually cleared. This proposal adds (a) an **automatic per-series TTL** keyed to each series' `amber_age_days` threshold in `config/gates.yml`, so an over-age cache entry is treated as a miss and re-fetched, and (b) a manual **`--no-cache`** flag on the `fetch` CLI that reuses the existing `skip_cache` plumbing to force a fully-live fetch. The TTL is **bypass-on-expiry, never evict** — an expired entry stays on disk so the Data Degradation Protocol (DDP) step-2 stale-cache fallback (`docs/RISK_FRAMEWORK.md:286`) survives a failed re-fetch.

## Motivation / Problem

**Observed in War Room #3 (2026-06-02), recorded at `local/brainstorms/2026-05.issues-scratch.md` I-1:** a "live" `fetch` returned data byte-identical to the 2026-05-15 smoke (VIX vintage 2026-05-15, EUR/USD 1.1628, HICP unchanged) — 18 days stale. VIX and EUR/USD carry `red_age_days: 10`; HICP `red_age_days: 60`. On 18-day-stale data this would have tripped **≥ 2 Tier 1 series STALE/RED → session RED** (`gates.yml:187-191`) — a **false `Data_Confidence` RED caused purely by cache age, not by genuinely unavailable upstream data.** Only a manual `find data/.http_cache -type f ! -name .gitkeep -delete` forced genuinely live data (VIX 17.26 → 16.05, EUR/USD 1.1628 → 1.1649).

The root cause is structural, verified by direct Read this session:
- `http_client.py:65` — `if use_cache and not self.skip_cache and cache_path.exists(): return cache_path.read_text(...)`. Cache hit is unconditional; no mtime/TTL check.
- `cli.py:148-151` — `fetch` exposes only `--session` and `--force`; `--force` overwrites the **snapshot** (`cli.py:109`), not the HTTP cache.

## Proposal

### Design decisions (the two `/propose` forks, resolved by operator 2026-06-03)

**Q1 — TTL basis: `amber_age_days` (NOT `red_age_days`).**

This **diverges from the `red_age_days` lean** in the original framing. Reasoning, verified against `docs/RISK_FRAMEWORK.md:289-292`:

- `gate_eval` measures staleness on the **data's `vintage`**, not the cache file's mtime (`RISK_FRAMEWORK.md:290`: "days since the datapoint's `vintage`"). The bug being fixed is a **false RED**, so the TTL must guarantee a cache-served vintage stays inside the GREEN band.
- `red_age_days` has **zero margin**: a cache entry can age right up to the RED boundary before bypass. Because `vintage_age = cache_age + publication_lag_at_fetch`, a red-keyed TTL can serve **RED-aged data**. Worked example: VIX fetched with a 2-day weekend publication lag, served at cache-age 9 (< red=10 → still served) → vintage-age 11 → **RED served**.
- `amber_age_days` bypasses **one tier earlier**, leaving lag margin so the re-fetch fires before the served vintage can trip RED; cache-served data stays GREEN.
- **Cost ≈ zero** (addresses the Wallet-Bleed adversarial vector): intra-session every cache entry is age-0 (cache always serves within a single `fetch` run; rate-limit protection intact). Cross-session, VIX/EUR-USD (`amber=5`) re-fetch every monthly War Room regardless; slow macro series (`amber=45`) only re-fetch past a ~1.5-month gap — exactly when fresh macro is wanted.

**Q2 — manual override: `--no-cache` only (NOT `--max-age-days N`).**

Reuses the existing `skip_cache` flag (`http_client.py:36`) — minimal surface, retires the manual `find … -delete` from #3. `--max-age-days N` is speculative (Simplicity First): the automatic per-series TTL already performs age-based bypass, and `--no-cache` fully covers the War Room pre-flight belt-and-braces. Deferred — add later only if a concrete need surfaces.

### Mechanism

**Threading the per-series max-age** (the URL-hash-keying crux — the cache is keyed by `sha256({method,url,params})` at `http_client.py:40-47`, NOT by series-id, so the TTL must be threaded from the caller that *has* the series context):

```
cli._fetch_all(providers, gates)
  └─ for each series_id: max_age = gates["data_staleness"]["series"][series_id]["amber_age_days"]
       └─ provider.fetch(series_id, max_age_days=max_age)     # fred.py:47 / ecb.py:61
            └─ self._client.get(url, params=params, max_age_days=max_age_days)   # fred.py:60 / ecb.py:70
                 └─ HttpClient.get(...) compares cache-file mtime against max_age_days
```

**`HttpClient.get()` — new logic (substantive edit):**

```python
# module level
import logging
log = logging.getLogger(__name__)
_SECONDS_PER_DAY = 86400   # enforced at the freshness compare below — not a ghost contract

def get(self, url, *, params=None, headers=None, use_cache=True, max_age_days=None):
    cache_path = self._cache_path("GET", url, params)
    cache_available = use_cache and not self.skip_cache and cache_path.exists()
    if cache_available and self._cache_fresh(cache_path, max_age_days):
        return cache_path.read_text(encoding="utf-8")
    # over-age (or no) cache → fall through to live re-fetch; the file is NOT deleted
    last_exc = None
    for attempt in range(1, self.max_retries + 1):
        ... existing retry loop; on success writes cache (109-112) + returns ...
        # L5 fix: 429-over-cap no longer raises in-loop. Set last_exc + break so it
        # converges on the single post-loop DDP decision (uniform with 500 / RequestException).
        if resp.status_code == 429 and retry_after > self.max_retry_after:
            last_exc = HttpError(f"HTTP 429 from {url}: Retry-After={retry_after:.0f}s "
                                 f"exceeds cap={self.max_retry_after:.0f}s")  # message preserved
            break
        ...
    # all attempts exhausted OR 429-cap abort — single decision point (replaces old :113 raise):
    if cache_available:
        # DDP step-2 (RISK_FRAMEWORK.md:286): over-age cache survives as the STALE fallback.
        log.warning("GET %s failed (%s); serving over-age cache as DDP STALE fallback", url, last_exc)
        return cache_path.read_text(encoding="utf-8")
    raise HttpError(f"GET {url} failed after {self.max_retries} attempts: {last_exc}")  # no cache → raise

def _cache_fresh(self, cache_path, max_age_days):
    if max_age_days is None:
        return True   # generic-client semantics: no TTL declared → never expires.
    age_seconds = time.time() - cache_path.stat().st_mtime
    return age_seconds < max_age_days * _SECONDS_PER_DAY
```

**L5 fix detail.** The current in-loop `raise HttpError(... aborting, trigger DDP fallback)` at `http_client.py:87-90` is replaced by `last_exc = HttpError(...); break`, and the `:86` comment becomes `# L19 (rev L5): cap exceeded — stop retrying; fall through to DDP fallback decision.` (the `L19` provenance tag is preserved, not dropped — it also anchors the `:34` `max_retry_after` field comment; delta-R3 L8). The 429-cap thus routes through the same post-loop `if cache_available` decision as the 500/RequestException exhaustion paths — a back-off outage is a degraded-mode condition, so the tagged-STALE cache fallback is the correct uniform response; `gate_eval` still flags vintage staleness. **`test_fred_429_exceeds_cap` is preserved**: it runs with `skip_cache=True` → `cache_available=False` → the post-loop `raise HttpError(f"GET {url} failed after {self.max_retries} attempts: {last_exc}")` fires, interpolating `{last_exc}` (the inner `Retry-After=3600…` message) so the test's `match="Retry-After=3600"` (an `re.search` substring) still matches. The outer raise carries an inline comment `# {last_exc} MUST be interpolated — test_fred_429_exceeds_cap matches the inner Retry-After substring` (delta-R3 L7) to guard the two-level interpolation chain against future wording drift.

**L2 fix detail (Option A).** `HttpClient.get` keeps `max_age_days=None` (legitimate generic low-level-client semantics). The footgun is closed one layer up, at the macro-fetch boundary: `DataProvider.fetch` makes `max_age_days` **keyword-only with no default** —

```python
@abstractmethod
def fetch(self, series_id: str, *, max_age_days: float | None) -> SeriesObservation: ...
```

so any provider caller that forgets it fails loudly at call time rather than silently restoring the unbounded cache. The 7 non-production call sites (`tests/test_live_smoke.py:49`, `tests/test_data_providers.py:53,68,77,84,98,105`) are updated to pass it explicitly (`max_age_days=None` for the cassette/error tests; `max_age_days=cfg["amber_age_days"]` for the live smoke, mirroring production). `cli._fetch_all` (the sole production caller) passes the per-series `amber_age_days`.

**DDP coexistence (item d — load-bearing).** TTL is **bypass-on-expiry, not eviction**: an over-age entry is treated as a cache miss for the *normal* path (→ re-fetch), but the file is never deleted. If the re-fetch then fails after all retries, the over-age file is returned as the DDP step-2 STALE fallback (`RISK_FRAMEWORK.md:286`: "The shared HTTP client's on-disk cache … may satisfy this step without contacting the source"). The returned observation still carries its own old `vintage`, so `gate_eval` tags it STALE correctly. **`skip_cache=True` (i.e. `--no-cache`, and unit tests) suppresses BOTH the fresh-serve and the failure-fallback** (`cache_available` is `False`), preserving the existing raise-on-failure semantics the 429/malformed tests assert.

**No ghost contract (item c).** No new TTL *magic-number* constant is introduced — the per-series age budget is read from the existing `amber_age_days` in `config/gates.yml`. The only new constant, `_SECONDS_PER_DAY = 86400`, is a unit-conversion factor enforced at the `_cache_fresh` compare site (it gates the `<` comparison directly), so it is not a name-promising-but-unenforced symbol.

## Scope & Out-of-Scope

**In scope:** per-series `amber`-keyed TTL on `HttpClient.get()`; `--no-cache` flag on `fetch`; signature pass-through through the provider ABC + both providers + the fetch loop; a new `tests/test_http_client.py` exercising the real `get()` path.

**Out of scope (deferred):** `--max-age-days N` (Q2, speculative). S-21/S-23 (ISIN pricing), S-24 (gate wiring), S-25 (macro series investigation) — separate working sessions. No `config/gates.yml` content change (TTL *reads* existing thresholds; no SHA-lock concern since the file is not mutated).

## Definition of Done

1. `python -m pytest tests/test_http_client.py -v` — all pass, including: (a) fresh-within-TTL → cache served, network NOT called (assert the monkeypatched `requests.Session.get` recorded **zero** calls); (b) older-than-TTL → live re-fetch fired (network called once); (c) re-fetch-fails-after-expiry via injected `requests.RequestException` → over-age cache returned as STALE fallback (DDP path, NOT raised); (c′) over-age + 429-over-cap → same STALE fallback fires (L5 — proves the reroute reaches the post-loop decision); (d) `skip_cache=True` → fresh-serve and failure-fallback both suppressed (raises). All assertions traverse the real `HttpClient.get()` entry-point with a monkeypatched `requests.Session.get` + monkeypatched cache-file mtime (or `time.time`) — no live network, no FRED key.
2. `python -m pytest tests/test_data_providers.py -v` — existing provider tests still pass **after** the rows 6–7 call-site edits add `max_age_days` explicitly. Because `DataProvider.fetch` is keyword-only with **no default** (L2), those call-site edits are **required, not optional** — omitting any of them raises `TypeError` at call time, not a silent pass. This DoD proves only signature compatibility (collection + pass-through), NOT TTL coverage: both clients set `skip_cache=True`, so the freshness path is never exercised here — TTL coverage is DoD #1's job (delta-R1 L8).
3. Runtime observation (not "tests pass"): a CLI/test run demonstrating an over-age cache entry being bypassed and a fresh one served, and the `--no-cache` flag forcing a live path — shown as actual output, with `data/.http_cache/` cleared beforehand if needed.
4. `grep -n "max_age_days" scripts/data/http_client.py scripts/data/provider.py scripts/data/providers/fred.py scripts/data/providers/ecb.py scripts/data/cli.py` — symbol threaded through all five files.
5. `grep -n "no-cache\|no_cache" scripts/data/cli.py` — flag wired into argparse + `_build_providers`.

## Risks & Mitigations

(The L1–Ln adversarial pass + Isolated Challenger cross-check are **complete** — Challenger R1 (flawed, 11 items) and the bounded delta-R3 pass (flawed, 10 items) are recorded in the §Delta Annexe R2/R3. The flags below are the **post-pass residual RISK FLAGS**, including the delta-R3 L5/L9 items absorbed as accepted limitations.)

- **Wallet-Bleed (adversarial vector #1).** TTL forces cross-session re-fetches. Mitigated: amber-keyed TTL re-fetches only past the amber gap (monthly for daily series — desired; ~1.5 months for slow macro); intra-session every entry is age-0 so no intra-run amplification; the existing `min_interval` rate-limit (`cli.py:54`) and `max_retries` cap are untouched.
- **DDP safety-net removal.** The single highest risk — mitigated by bypass-on-expiry-not-evict + the explicit failure-path fallback (see Mechanism). Called out as a dedicated DoD item (#1c).
- **`skip_cache` double-duty.** `--no-cache` (operator intent: force live) and the unit-test `skip_cache=True` (intent: ignore cache) share one flag. Verified compatible: both want "never serve cache, raise on failure" — the failure-fallback is correctly gated behind `cache_available` so neither path regresses. The 429/malformed tests (`test_data_providers.py:64-77`) that rely on raise-on-failure with `skip_cache=True` are preserved.
- **mtime as freshness proxy.** Cache mtime = last-fetch time, not data vintage. Accepted by design: the TTL is a *cache-age* gate; data *vintage* staleness remains `gate_eval`'s job. Amber-keying (vs red) is the margin that keeps cache-age contribution inside GREEN (see Q1).
- **`last_exc=None` on `max_retries=0` (delta-R3 L5).** If the retry loop runs zero times, the post-loop raise interpolates `last_exc=None` → `"failed after 0 attempts: None"`. Pre-existing exposure (the current `:113` raise has the same), not introduced by this change; unreachable from `gates.yml` (`retry.max_attempts: 3`). Accepted; no guard added.
- **No static guard for ABC override-signature drift (delta-R3 L9).** Python does not enforce that a future `DataProvider` subclass's `fetch` override matches the new keyword-only signature; a mismatched override would raise `TypeError` at call time, not definition time. The no-default choice is deliberate — it trades a silent default-shadowing bug (the L2 footgun) for a loud runtime failure. Noted; acceptable for a 2-subclass surface.

## FILES CHANGED (PROPOSED)

| # | Action | File | Reason | Blast radius |
|---|--------|------|--------|--------------|
| 1 | MODIFY | `scripts/data/http_client.py` | **Substantive:** `max_age_days` kwarg + `_cache_fresh` + `_SECONDS_PER_DAY` + module logger; gate cache-hit on freshness; replace `:113` terminal raise with single post-loop DDP-fallback decision; reroute the `:87-90` 429-over-cap from in-loop raise to `last_exc`+`break` (L5) | MODERATE — imported by `cli.py`, `providers/fred.py`, `providers/ecb.py`, `tests/test_data_providers.py`, `tests/test_live_smoke.py` |
| 2 | MODIFY | `scripts/data/provider.py` | `DataProvider.fetch` ABC → `(self, series_id, *, max_age_days: float \| None)` — keyword-only, **no default** (L2 Option A) | MODERATE — 2 subclasses |
| 3 | MODIFY | `scripts/data/providers/fred.py` | `fetch()` accepts keyword-only `max_age_days`, passes to `self._client.get(...)` at line 60 | ISOLATED |
| 4 | MODIFY | `scripts/data/providers/ecb.py` | `fetch()` accepts keyword-only `max_age_days`, passes to `self._client.get(...)` at line 70 | ISOLATED |
| 5 | MODIFY | `scripts/data/cli.py` | **Substantive:** `_build_providers(gates, no_cache=...)` sets `skip_cache`; `_fetch_all(providers, gates)` looks up per-series `amber_age_days`; `_cmd_fetch` re-plumbed to pass `gates`; add `--no-cache` argparse flag (+ help text noting it disables the DDP fallback → raises on outage) | ISOLATED (entry point; `_fetch_all`/`_build_providers` callers are cli-internal only) |
| 6 | MODIFY | `tests/test_data_providers.py` | Pass `max_age_days=None` at the 6 `fetch()` call sites (53,68,77,84,98,105) — back-compat for the new keyword-only signature (L2) | — |
| 7 | MODIFY | `tests/test_live_smoke.py` | Pass `max_age_days=cfg["amber_age_days"]` at the `:49` `fetch()` call (mirrors production) (L2) | — |
| 8 | CREATE | `tests/test_http_client.py` | TTL fresh/expired + DDP-fallback (RequestException exhaustion AND 429-cap) + skip_cache-raises tests, all traversing real `get()` | — |
| 9 | CREATE | `proposals/023-s22-http-cache-ttl.md` | This proposal artefact (self-admin) | — |
| 10 | MODIFY | `proposals/README.md` | Index row for 023 (self-admin) | — |
| 11 | MODIFY | `PROGRESS.md` | Close the S-22 row (self-admin, at `/commemorate`) | — |
| 12 | MODIFY | `CHANGELOG.md` | `[Unreleased] ### Fixed` entry (self-admin, at `/commemorate`) | — |
| 13 | MODIFY | `docs/retros/<date>.md` | Session retro (self-admin, untracked by design — never `git add`) | — |

> Aggregate: 13 files = 8 code/test (5 source MODIFY + 2 test MODIFY + 1 test CREATE) + 5 self-admin (1 CREATE proposal + 4 MODIFY: README, PROGRESS, CHANGELOG, retro). Code/test = 5 + 2 + 1 = 8 ✓. Self-admin = 1 + 4 = 5 ✓. Total = 8 + 5 = 13 ✓.

## REVERSIBILITY

**FULLY REVERSIBLE** — all changes are local code/config/test/doc. `git revert` restores all state. No external API mutation, no schema migration, no public push. (`docs/retros/` is untracked by design — Proposal 005 sanitisation — and is not part of the revertable commit.) No IRREVERSIBLE change ⇒ no RISK-FLAGS escalation required.

## Core Team Review (A–D)

> Inline mode (no `agents/persona-*.md` files present; Core Team A–D from `AGENTS.md`).

### A — Quant Architect
The threading is clean: series context lives in `fetch()`, the cache key does not, so passing `max_age_days` down from the fetch loop is the only correct route — no derivation inside the client. Amber-over-red is the right call: keying the cache-age budget to the *tighter* gate is what keeps `cache_age + publication_lag` inside GREEN. One craft note: `_cache_fresh` returning `True` on `max_age_days=None` must be a deliberate documented default (it is — back-compat for `test_live_smoke.py` which omits the kwarg). [post-L2 annotation: `test_live_smoke.py:49` now passes `max_age_days` explicitly (§6 row 7); the `get()`/`_cache_fresh` `None`-default the Architect refers to still stands at the client layer.] **VERDICT: APPROVE WITH CONDITIONS** — condition: the TTL test must assert the *network was not called* on the fresh-serve branch (not merely that a value was returned), else it's theatre.

### B — Portfolio Manager
This directly fixes a decision-integrity bug: War Room #3 nearly acted on an 18-day-stale macro picture flagged as a false RED. The amber-keyed TTL means the desk re-fetches exactly when it matters (monthly daily-series refresh; macro past ~6 weeks). `--no-cache` gives me a one-flag pre-flight override instead of a hand-typed `find … -delete`. **VERDICT: APPROVE.**

### C — CTO
Reuses existing plumbing (`skip_cache`, `data_staleness` thresholds) rather than inventing a parallel mechanism — minimal surface, good. The failure-path fallback is the only behavioural change to the shared client; it's correctly gated behind `cache_available` so `skip_cache` callers (tests + `--no-cache`) keep raise-on-failure. Confirm `time.time()` vs `st_mtime` are both wall-clock (they are) so the comparison is sound, and that the test monkeypatches one of them deterministically. **VERDICT: APPROVE WITH CONDITIONS** — condition: DoD #1 must exercise all four branches through the real `get()`, per the test-the-guard-at-the-entry-point rule.

### D — Risk Officer
The DDP step-2 fallback is a safety control (`RISK_FRAMEWORK.md:286`); any change near it gets mandatory scrutiny (review-patterns.md §Risk Check). Bypass-on-expiry-not-evict preserves it, and the failure-path explicitly returns the over-age file — good. My hard condition: there must be a test proving that re-fetch-failure-after-expiry returns the stale cache rather than raising, because that is the exact outage path the DDP protects. Also confirm a `--no-cache` live-fetch failure does NOT silently fall back (it must raise) — operator asked for live, and a silent stale-serve under `--no-cache` would be a worse surprise than an error. **VERDICT: APPROVE WITH CONDITIONS** — conditions: DoD #1c (DDP fallback test) and #1d (`skip_cache` raises) are both mandatory and non-negotiable.

**Core Team summary:** 1 APPROVE (B), 3 APPROVE WITH CONDITIONS (A, C, D). All conditions are already encoded as DoD #1a–#1d. No REJECT. Not unanimous-unconditional, so the orchestrator-adversarial unanimous-scrutiny prompt does not fire.

## Delta Annexe — Round 1 (Core Team)
- **Absorbed:** A's "assert network not called" → DoD #1a. C's "all four branches through real `get()`" → DoD #1 framing. D's "DDP fallback test" → DoD #1c; D's "`--no-cache` must raise, not silently fall back" → DoD #1d.
- **Resisted:** none.

## Delta Annexe — Round 2 (Isolated Challenger Cross-Check)

`Cross-Check path: isolated-challenger — reason: no external/alternate model API is configured in this environment.`

Challenger R1 verdict: **flawed** (11 L-items: 4 structural, 5 substantive, 2 craft). Each load-bearing claim independently re-verified by the producer against the source files before disposition (CLAUDE.md FATAL-claim / External-agent-claim verification).

**ABSORBED (scope-correcting — safe inline per G15):**

- **L1 — cli re-plumbing mischaracterised as mechanical.** *Verified:* `cli.py:83` `_fetch_all(providers: dict)`, `:116` `_build_providers(gates)`, `:117` `_fetch_all(providers)`. Absorb: §6 row 5 + tier-evidence corrected — `cli.py` is a **substantive** edit (not "mechanical pass-through"): `_fetch_all` gains a `gates` param, `_cmd_fetch` is updated to pass it, plus the `amber` lookup + `--no-cache` arg + `_build_providers(gates, no_cache=)`. The "four mechanical" set is now three (`provider.py`, `providers/fred.py`, `providers/ecb.py`); two substantive (`http_client.py`, `cli.py`).
- **L3 — DoD #1 test seam + which failure injected.** Absorb: the new `tests/test_http_client.py` monkeypatches `requests.Session.get` directly (it is a fresh standalone test, not vcrpy-bound). DoD #1c amended: the failure branch injects a `requests.RequestException` (exhausts the retry loop at `http_client.py:76-81`) so the post-loop fallback is genuinely reached — explicitly NOT a 429-over-cap (see L5).
- **L4 — get() rewrite must replace the terminal raise.** *Verified:* `http_client.py:113` is the loop-terminal `raise`; cache write is at `109-112` inside the loop. Absorb: Mechanism clarified — line 113's `raise` is **replaced** by `if cache_available: log + return stale; else: raise`. The in-loop success-path cache write (109-112) is unchanged.
- **L6 — amber TTL can still serve RED-aged HICP.** *Verified:* HICP `amber=45/red=60` (gates.yml:218-221), publication lag ~17d (ecb.py:11); gap(15) < lag(17). Absorb: §Q1 corrected — amber-keying eliminates false-RED **only where `(red − amber) ≥ publication_lag`** (holds for VIX/EUR-USD; violated for HICP). Residual: a ~2-day window (cache-age [red−lag, amber] = [43,45]) where a RED-aged HICP cache may still be served; `gate_eval` still flags it RED on vintage (no wrong data accepted — only a re-fetch not pre-empted). amber remains strictly better than red (wider red window serves more stale data); claim re-scoped, choice stands.
- **L7 — `--no-cache` failure aborts whole run.** *Verified:* `cli.py:91-93` `except (HttpError, Exception): sys.exit(1)`. Absorb: documented in §RISK FLAGS + the `--no-cache` argparse `help=` text — a `--no-cache` fetch failure aborts the whole run (by design: operator asked for live; re-run without `--no-cache` to use cache/DDP). This is the existing `_fetch_all` behaviour, not new.
- **L8 — DoD #2 is vacuous as TTL evidence.** *Verified:* `test_data_providers.py:38-45` both clients set `skip_cache=True`. Absorb: DoD #2 re-scoped — it proves only signature back-compat (collection + pass-through), NOT TTL coverage; TTL coverage is DoD #1's job.
- **L9 — wall-clock vs monotonic clock skew.** *Verified:* rate-limit uses `time.monotonic()` (`http_client.py:52,75`); freshness uses `time.time()` vs `st_mtime`. Absorb as accepted limitation: `time.time()` is the *correct* pairing for a persisted wall-clock mtime (monotonic cannot compare cross-process); clock-skew is inherent to any mtime-TTL, worst case serves stale → `gate_eval` flags on vintage. Persona C's "both wall-clock" note refers only to the freshness pair, which is correct.
- **L10 / L11 — craft.** L10: Challenger self-confirmed the line-cites are accurate; annotation placement clarified. L11: pre-existing redundant `except (HttpError, Exception)` tuple is out of scope; one-line note added that the fallback **returns** (not raises) so it flows up cleanly, staying out of the exit-1 trap.

**ABSORBED — scope-expanding, OPERATOR-AUTHORISED 2026-06-03 (G15 explicit decision recorded):**

- **L2 → Option A (operator-authorised).** *Verified:* the `fetch()` call-site count is **8 total**, not the 5 I estimated — 1 production (`cli.py:88`) + 7 non-production (`tests/test_live_smoke.py:49`, `tests/test_data_providers.py:53,68,77,84,98,105`), all in already-enumerated files (no un-enumerated caller surfaced, so the L2 escape-hatch did not fire). Absorbed: `DataProvider.fetch` `max_age_days` is keyword-only **no default**; `HttpClient.get` keeps `max_age_days=None` (generic-client semantics); the 7 non-production sites pass it explicitly. Closes the footgun at the macro-fetch boundary where it is load-bearing. Escape-hatch on standby: if an un-enumerated caller had surfaced, fall back to None-default + runtime warning — not needed.
- **L5 → Fix (operator-authorised).** *Verified:* `http_client.py:83-90` raises in-loop on `retry_after > max_retry_after`. Absorbed: the 429-cap sets `last_exc` (preserving the `Retry-After=…` text so `test_fred_429_exceeds_cap` still matches) + `break`s, converging on the single post-loop `if cache_available` decision — uniform with the 500/RequestException paths. *Rationale (operator):* a 429-cap is a back-off outage, so the tagged-STALE fallback is the correct degraded mode; `gate_eval` still flags vintage staleness. `:86` comment updated. Escape-hatch on standby: if the message/no-retry semantics couldn't survive `break`, fall back to narrowing §87 + manual-DDP-only — not needed; the `break` cleanly preserves both.

**RESISTED:** none.

## Delta Annexe — Round 3 (bounded delta cross-check on L2+L5 expansion)
> Per CLAUDE.md adversarial-sequence stop-rule (L52): the two operator-authorised expansions add new mechanism (429-cap reroute) + new contract (keyword-only `fetch`) + new files (2 test edits), so the delta gets **exactly one** further Challenger pass — on the DELTA ONLY (retry-loop edit + `fetch` ABC signature + 7 test call sites), bounded by steering's fixed termination tree (sound/scope-correcting → proceed; further-expansion-needed → take no-expansion alternative or carve to a follow-up amendment; hard cap one pass).

**Result — delta cross-check R3: flawed, 10 L-items; disposition below. No item required further scope expansion → 023 proceeds to the approval gate. Hard cap honoured (one delta pass; no R4).** The Challenger reviewed against the pre-implementation working tree (023 is unimplemented — no code on disk), so several items re-describe R1-absorbed design.

- **ABSORBED (scope-correcting, no new mechanism):**
  - **L7** — outer raise carries a pin-comment so the two-level `{last_exc}` interpolation that preserves `match="Retry-After=3600"` can't silently drift. *Verified test_data_providers.py:67.*
  - **L8** — `:86` comment keeps the `L19` provenance tag (`L19 (rev L5)`); it co-anchors the `:34` field comment. *Verified http_client.py:34,86.*
  - **L5 / L9** — added as accepted §RISK notes (pre-existing `max_retries=0` `None`-interpolation; no static ABC override-signature guard).
- **CONFIRMED ALREADY-HANDLED (no change):**
  - **L1** — `cache_available` is defined in the §Mechanism `get()` body as `use_cache and not self.skip_cache and cache_path.exists()` (the line-65 predicate). Under `skip_cache=True` → `False` → raises, preserving the 429 test.
  - **L3** — `_fetch_all(providers, gates)` + `_cmd_fetch` re-plumb was absorbed in R1 (L1) and is in §6 row 5; production `amber_age_days` reaches the call site via the threaded `gates`. Path is `scripts/data/cli.py` throughout §6.
  - **L4** — the line-105 `test_ecb_unknown_alias` edit is in the 7-site list; with the kwarg supplied, the registry `KeyError` still fires ahead of any `get()`. Edit is load-bearing (a miss → `TypeError`), which is the intended loud-failure trade.
- **RESISTED (out-of-delta-scope — re-litigates R1-absorbed design, excluded by steering's pass boundary):**
  - **L2** — "serve TTL-expired cache on failure" *is* the R1-reviewed DDP step-2 fallback (RISK_FRAMEWORK.md:286), not a new contract introduced by the L2/L5 delta. The 429-cap reroute only adds one more entry-path into that already-decided fallback. No-expansion stance: the R1 design stands as reviewed.
  - **L6** — "no consumer branches on a fallback signal" was R1's L11 absorption: the in-client fallback **returns** the stale body (it does not raise), so the observation flows through `_fetch_all` transparently and `gate_eval` tags it STALE by vintage. On the no-cache path the raise → `sys.exit(1)` is the correct can't-degrade-abort, unchanged from today.
  - **L10** — provenance note only: the delta is described against the R1-staged (not yet committed) tree because 023 is a DRAFT with nothing implemented. Expected for a proposal; no action.

## Amendments
None yet.

## Status Log

> Append-only. The closing DONE entry MUST be paired with a `CHANGELOG.md` line.

- 2026-06-03 — DRAFT opened. Tier MEDIUM. Q1 resolved to `amber_age_days` (diverges from red lean — see Design decisions); Q2 resolved to `--no-cache` only. Core Team R1: 1 APPROVE + 3 APPROVE-WITH-CONDITIONS (conditions encoded as DoD #1a–#1d). §4b Challenger pass held pending steering verification of §6 paths + DDP framing.
- 2026-06-03 — Steering CLEARED §6 paths + DDP framing. Isolated Challenger R1 run (`isolated-challenger` — no second model configured): verdict **flawed**, 11 L-items (4 structural / 5 substantive / 2 craft). 9 absorbed inline (scope-correcting); **L2 + L5 escalated to operator** (scope-expanding fixes — see Delta Annexe R2). Awaiting operator decision on L2/L5 before the user approval gate. No code written yet.
- 2026-06-03 — Operator AUTHORISED both expansions (G15 explicit decision). L2 → Option A (fetch keyword-only no-default; 7 non-prod call sites updated); L5 → Fix (429-cap reroute to post-loop DDP decision). §6 → 13 files (8+5), Mechanism + DoD amended. Bounded delta cross-check (R3) on the L2+L5 delta pending per L52. Still no code written.
- 2026-06-03 — Delta cross-check R3 complete (isolated-challenger, one bounded pass, hard cap honoured): flawed, 10 L-items. 4 absorbed scope-correcting (L7 interp-pin, L8 L19-tag, L5+L9 RISK notes); 4 confirmed already-handled (L1, L3, L4 + sub); 3 resisted out-of-delta-scope (L2, L6 re-litigate R1 DDP design; L10 provenance). No further-expansion item → no R4. 023 ready for the user approval gate pending steering's on-disk verification of the two edited surfaces.
- 2026-06-03 — **APPROVED for implementation** by operator (via steering). Pre-approval: two sibling-inconsistency fixes (DoD #2 no-default wording; §Risks preamble pass-complete) + a bracketed post-L2 annotation on the verbatim R1 Quant Architect verdict (verdict left verbatim per append-only history). Consistency audit PASS (§6 13 rows, 8+5=13, L-items contiguous R1→delta-R3, cross-refs resolve). Next: implement via Sonnet implementation-agent → Opus git-diff vs §6 → /code-reviewer (focus L5 reroute) → runtime DoD #1–3 → relay to steering before /commemorate.
- 2026-06-03 — **DONE.** Implemented via Sonnet implementation-agent; Opus verified `git diff HEAD` matches §6 (5 source + 2 test MODIFY + `tests/test_http_client.py` CREATE + README index row; no out-of-scope file). Runtime: `python3 -m scripts.data fetch --help` shows the `--no-cache` flag; `python3 -m pytest tests/test_http_client.py tests/test_data_providers.py` → **11 passed** (re-confirmed by /code-reviewer and steering). /code-reviewer **APPROVE WITH NOTES** (4 NOTE-level, none gating; finding #4 non-atomic cache write logged as future hardening **S-26**). One implementation-agent scope slip — it `git checkout`'d `proposals/README.md` (the known N=2 anti-pattern), wiping the live 023 index row; orchestrator restored it. PROGRESS S-22 → DONE, CHANGELOG `### Fixed` appended. Paired with the CHANGELOG entry (entry-or-it-didn't-happen). Commit pending explicit operator approval — no push.
