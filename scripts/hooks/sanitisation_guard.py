#!/usr/bin/env python3
"""Pre-commit sanitisation guard.

Blocks a commit when an investor-private literal from the gitignored local/
ledger appears in the STAGED TRACKED diff. Reads private literals from local/
at runtime; they NEVER enter any agent/LLM context. Block reports name the
KIND + FILE only, never the literal value (PIN 1).

No-ops gracefully (exit 0) when no local/ private files exist — a fresh cloner
pre-onboarding is never blocked.

Detection scope (declared boundary, NOT a ghost contract): three provenance-
anchored kinds — ISIN-shape, exchange-qualified-ticker-shape, and a numeric
value present in the local/ ledger (matched across plain / comma-grouped US /
EU-locale representation variants). NOT covered (named, bounded residuals):
free-text PII, .env secrets, values living only in a generated .html, space-
separated or scientific-notation numbers, sub-floor (<=3-digit) integers, and
low-information <=2-significant-figure decimals (e.g. a 1.3 share price).
The guard is a mechanical SAFETY NET that fails CLOSED, not a perfect redactor. A git
error or an unreadable local/ file fails CLOSED (block); a legitimately empty/delete-only
diff still PASSES. Process/meta noise (steering logs, scratch, INDEX, *_draft) is excluded
from the harvest corpus by convention-glob. Ticker matching uses an alpha-aware boundary;
ISIN and numeric matching keep the digit-only lookaround (high-value, over-block-safe).

Declared fail-closed bounded residuals: space-separated numbers, scientific
notation, values in .html files only, sub-floor (<=3-digit) integers,
<=2-significant-figure decimals (Amendment 3), free-text PII, .env secrets.
"""

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

# Constants
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ALLOWLIST_PATH = REPO_ROOT / "config" / "sanitisation_allowlist.yml"
_MIN_INT_DIGITS = 4
_MIN_SIG_FIGS = 3  # a DECIMAL value needs >=3 significant figures to be "specific"
                   # (Amendment 3): drops low-information <=2-sig-fig decimals (1.3,
                   # 2.6, 0.5) whose short EU-variants ("1,3") collide ubiquitously,
                   # while keeping the verified leak class (qty 12.5, price 87.32, etc.).
ISIN_RE = re.compile(r"\b[A-Z]{2}[A-Z0-9]{9}[0-9]\b")
TICKER_RE = re.compile(r"\b[A-Z]{2,6}\.[A-Z]{1,3}\b")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}|\d{4}-\d{2}")
NUM_RE = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?")

# Process/meta artefacts excluded from the harvest corpus (non-ledger by construction;
# their meta-numbers self-poison the guard). Convention-glob (NOT an enumerated list) so a
# FUTURE process log (e.g. a 2026-07 steering file) is auto-excluded — closing the
# self-poisoning root cause. Anchored to unambiguous infixes; a no-swallow test guards
# against eating a real ledger source.
_PROCESS_LOG_INFIXES = (".steering-", ".issues-scratch")


class GitInvocationError(Exception):
    """A git subprocess failed. Callers MUST fail CLOSED (block) — distinguished from a
    legitimately empty diff (which returns "" and PASSES)."""


class LedgerReadError(Exception):
    """A local/ private file could not be read (OSError). Callers MUST fail CLOSED so a
    file's leak protection cannot silently drop."""


def _is_process_noise(path: Path) -> bool:
    """True for process/meta artefacts that must be excluded from the harvest corpus.

    Convention-glob over `path.name`/`path.stem` (path-agnostic — rooted wherever the
    caller passes `local_dir`). Matches: `INDEX.md`, any stem containing `_draft`, or any
    name carrying a `_PROCESS_LOG_INFIXES` infix. Deliberately does NOT match a bare
    leading underscore (too broad — would swallow a future `local/_scratch_portfolio.md`).
    """
    name = path.name
    if name == "INDEX.md":
        return True
    if "_draft" in path.stem:
        return True
    return any(infix in name for infix in _PROCESS_LOG_INFIXES)


def _local_dir() -> Path:
    """Return the local directory path, resolved at call time for test overrides."""
    return Path(os.environ.get("SANITISATION_LOCAL_DIR") or (REPO_ROOT / "local"))


def _canonical(token: str) -> str:
    """Strip thousands-commas to produce canonical value key.

    Examples (synthetic): "5,142.30" -> "5142.30", "5,100" -> "5100".
    Trailing zeros preserved.
    """
    return token.replace(",", "")


def _sig_figs(canonical: str) -> int:
    """Count significant figures of a comma-stripped number.

    Leading zeros are NOT significant; trailing zeros after a decimal point ARE.
    Examples (synthetic): "1.3"->2, "12.5"->3, "12.50"->4, "0.50"->2, "0.05"->1,
    "87.32"->4, "5142.30"->6.
    """
    return len(canonical.replace(".", "").lstrip("0"))


def _is_specific(canonical: str) -> bool:
    """Check if a canonical number is specific enough to warrant detection.

    Canonical is comma-stripped UK/US form (dot=decimal). Specific iff:
      (a) it has a non-zero fractional part AND >= _MIN_SIG_FIGS significant figures
          (Amendment 3 — a low-information <=2-sig-fig decimal like "1.3" is dropped), OR
      (b) its integer part has >= _MIN_INT_DIGITS digits.
    """
    if "." in canonical:
        intp, frac = canonical.split(".", 1)
        if frac and set(frac) != {"0"}:
            return _sig_figs(canonical) >= _MIN_SIG_FIGS
    else:
        intp = canonical
    return intp.isdigit() and len(intp) >= _MIN_INT_DIGITS


def _group(intp: str, sep: str) -> str:
    """Group integer digits in 3s with separator.

    Examples (synthetic): "5142" -> "5,142" (sep=",") / "5.142" (sep=".").
    """
    if not intp:
        return intp
    # Reverse, chunk by 3, join with sep, reverse back
    rev = intp[::-1]
    chunks = [rev[i:i+3] for i in range(0, len(rev), 3)]
    return sep.join(chunks)[::-1]


def render_variants(canonical: str) -> set[str]:
    """Render the THREE enumerated representation variants from the token string.

    canonical is UK/US comma-stripped. Returns:
      - plain: canonical itself (e.g. synthetic "5142.30" or "5100")
      - us: comma-grouped integer, dot decimal ("5,142.30" / "5,100")
      - eu: dot-grouped integer, comma decimal ("5.142,30" / "5.100")

    Never parse-then-format, so a significant trailing zero like "5142.30" is preserved.
    """
    if "." in canonical:
        intp, frac = canonical.split(".", 1)
    else:
        intp = canonical
        frac = ""

    plain = canonical
    us = _group(intp, ",") + ("." + frac if frac else "")
    eu = _group(intp, ".") + ("," + frac if frac else "")

    return {plain, us, eu}


def _tracked_paths(local_dir: Path) -> set[Path]:
    """Return set of tracked file paths under local_dir.

    Uses git ls-files; on any failure falls back to local_dir/templates/*.
    """
    try:
        result = subprocess.run(
            ["git", "ls-files", str(local_dir)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        paths = set()
        for line in result.stdout.splitlines():
            line = line.strip()
            if line:
                paths.add((REPO_ROOT / line).resolve())
        return paths
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        # Fallback: templates/ is the only tracked subtree
        templates_dir = local_dir / "templates"
        if templates_dir.is_dir():
            return {p.resolve() for p in templates_dir.rglob("*") if p.is_file()}
        return set()


def extract_private_literals(local_dir: Path) -> list[dict]:
    """Extract private literals from untracked .md files in local_dir.

    Returns list of records:
      {"kind": "ISIN"|"ticker"|"numeric value", "key": <canonical/exact>,
       "patterns": set[str], "source": <relpath str>}

    Skips tracked files, non-.md files, and process/meta noise (_is_process_noise).
    A non-UTF-8 file is best-effort latin-1 decoded (detection preserved) with a loud
    warning; a genuine OSError raises LedgerReadError (fail CLOSED — protection must not
    silently drop).
    """
    if not local_dir.is_dir():
        return []

    tracked = _tracked_paths(local_dir)
    records_map = {}  # (kind, key) -> record (for dedup)

    for path in local_dir.rglob("*.md"):
        if not path.is_file():
            continue
        if path.resolve() in tracked:
            continue
        # Exclude process/meta noise BEFORE the read so an unreadable excluded file
        # can never trigger a (fail-closed) read error.
        if _is_process_noise(path):
            continue

        # Compute source path BEFORE the read so it is defined in the read-error branches.
        try:
            source = str(path.relative_to(REPO_ROOT))
        except ValueError:
            # In tests, tmp_path is not under REPO_ROOT
            source = str(path.relative_to(local_dir.parent))

        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # A non-UTF-8 file (e.g. a Latin-1 broker-statement paste). Best-effort
            # latin-1 re-read NEVER raises and preserves all ASCII content (ISINs,
            # tickers, digits), so a real ledger's values are STILL harvested and STILL
            # block — no silent under-block. A stray binary .md yields at-worst harmless
            # over-blocking noise — no DoS. Loud warning so the operator is not silent.
            print(
                f"sanitisation-guard: WARNING — {source} is not UTF-8; "
                "scanning with latin-1 fallback (detection preserved).",
                file=sys.stderr,
            )
            try:
                text = path.read_text(encoding="latin-1")
            except OSError as exc:
                raise LedgerReadError(f"cannot read local/ private file {source}") from exc
        except OSError as exc:
            # Genuinely unreadable (permission/IO). is_file() above already filtered
            # dirs/broken symlinks, so this is a real file whose protection we cannot
            # verify — fail CLOSED (the harvest aborts; re-run after fixing the file).
            raise LedgerReadError(f"cannot read local/ private file {source}") from exc

        # Extract ISINs
        for isin in ISIN_RE.findall(text):
            key = ("ISIN", isin)
            if key not in records_map:
                records_map[key] = {
                    "kind": "ISIN",
                    "key": isin,
                    "patterns": {isin},
                    "source": source,
                }

        # Extract tickers
        for ticker in TICKER_RE.findall(text):
            key = ("ticker", ticker)
            if key not in records_map:
                records_map[key] = {
                    "kind": "ticker",
                    "key": ticker,
                    "patterns": {ticker},
                    "source": source,
                }

        # Extract numeric values (excluding dates)
        # Build date spans to exclude
        date_spans = []
        for match in DATE_RE.finditer(text):
            date_spans.append((match.start(), match.end()))

        for match in NUM_RE.finditer(text):
            # Check if this number overlaps any date span
            num_start, num_end = match.start(), match.end()
            overlaps_date = any(
                not (num_end <= d_start or num_start >= d_end)
                for d_start, d_end in date_spans
            )
            if overlaps_date:
                continue

            token = match.group()
            canonical = _canonical(token)

            if not _is_specific(canonical):
                continue

            key = ("numeric value", canonical)
            if key not in records_map:
                records_map[key] = {
                    "kind": "numeric value",
                    "key": canonical,
                    "patterns": render_variants(canonical),
                    "source": source,
                }

    return list(records_map.values())


def load_allowlist(path: Path) -> dict:
    """Load allowlist from YAML file.

    Returns: {"isins": set, "tickers": set, "values": set[str]}
    Missing file returns empty sets.
    """
    if not path.exists():
        return {"isins": set(), "tickers": set(), "values": set()}

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not data or "allow" not in data:
            return {"isins": set(), "tickers": set(), "values": set()}

        allow = data["allow"]
        return {
            "isins": set(allow.get("isins", [])),
            "tickers": set(allow.get("tickers", [])),
            "values": set(allow.get("values", [])),
        }
    except (yaml.YAMLError, OSError, UnicodeDecodeError):
        return {"isins": set(), "tickers": set(), "values": set()}


def canonical_config_hash(path: Path) -> str:
    """Compute canonical hash of YAML config (parsed content, not raw bytes).

    PIN 3 — parsed-canonical, the ONLY hashing path.
    """
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    canonical_json = json.dumps(
        data, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str
    )
    return hashlib.sha256(canonical_json.encode()).hexdigest()


def staged_added_text() -> str:
    """Return all added lines from staged diff.

    Runs git diff --cached -U0 --no-color and extracts lines starting with "+"
    but not "+++".
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "-U0", "--no-color"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        lines = []
        for line in result.stdout.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                lines.append(line[1:])  # Remove leading "+"
        return "\n".join(lines)
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as exc:
        # A genuine git error — fail CLOSED. A clean run with no '+' lines returns ""
        # above (empty-but-valid → PASSES); only an ERROR reaches here.
        raise GitInvocationError("git diff --cached failed") from exc


def range_added_text(rng: str) -> str:
    """Return all added lines from a commit range.

    Runs git log -p -U0 --no-color <rng> and extracts lines starting with "+"
    but not "+++". Same extraction logic as staged_added_text().
    """
    try:
        result = subprocess.run(
            ["git", "log", "-p", "-U0", "--no-color", rng],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        lines = []
        for line in result.stdout.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                lines.append(line[1:])  # Remove leading "+"
        return "\n".join(lines)
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as exc:
        # A genuine git error — fail CLOSED (see staged_added_text).
        raise GitInvocationError(f"git log -p failed for range {rng}") from exc


def _print_push_block_git_error(detail: str) -> None:
    """Emit a clean PUSH-BLOCK message for a git/scan error (fail-closed, not a crash)."""
    print("PUSH BLOCKED — sanitisation guard", file=sys.stderr)
    print(f"  git invocation failed ({detail}); failing CLOSED.", file=sys.stderr)
    print(
        "  Resolve the git error and retry; bypass only with git push --no-verify.",
        file=sys.stderr,
    )


def find_leaks(records: list[dict], added_text: str, allow: dict) -> list[tuple[str, str]]:
    """Find leaks of private literals in added text.

    Returns list of (kind, source) tuples for leaked records.
    Never includes the actual value.
    """
    leaks = []
    seen = set()

    # Diff-side ISO-date spans (reuse the SAME DATE_RE used on ledger extraction —
    # symmetric, not new normalisation). A numeric match that falls ENTIRELY inside
    # a date span (e.g. the YYYY of a governance-doc date `2026-06-09`) is not a leak:
    # it lets a ledger bare-year stop false-positiving against committed dates.
    # Ledger extraction is unchanged, so a bare-year-valued NAV outside a date is
    # still harvested (R2-L3 stays closed). Fail-open bound: the ONLY way a real
    # >=4-digit private value is wrongly skipped is if it appears as the YYYY of an
    # ISO date in the diff (decimal/grouped variants contain '.'/',', absent from
    # ISO dates, so they can never sit inside a date span).
    date_spans = [(m.start(), m.end()) for m in DATE_RE.finditer(added_text)]

    for record in records:
        kind = record["kind"]
        key = record["key"]

        # Check allowlist
        if kind == "ISIN" and key in allow["isins"]:
            continue
        if kind == "ticker" and key in allow["tickers"]:
            continue
        if kind == "numeric value" and key in allow["values"]:
            continue

        # Check for pattern matches. Ticker records use an alpha-AND-digit boundary
        # (tickers are low-information and prone to coincidental-substring over-blocks);
        # ISIN and numeric records KEEP the digit-only lookaround — an ISIN is high-value
        # (over-block, never under-block) and a numeric glued to letters (e.g. "5142EUR")
        # is the highest-stakes leak class and MUST still match. (S-31 ITEM 1, tickers-only.)
        matched = False
        for pattern in record["patterns"]:
            if kind == "ticker":
                regex = re.compile(r"(?<![A-Za-z0-9])" + re.escape(pattern) + r"(?![A-Za-z0-9])")
            else:
                regex = re.compile(r"(?<!\d)" + re.escape(pattern) + r"(?!\d)")
            for m in regex.finditer(added_text):
                # Skip a match that sits ENTIRELY inside a diff-side ISO-date span.
                inside_date = any(
                    d_start <= m.start() and m.end() <= d_end
                    for d_start, d_end in date_spans
                )
                if not inside_date:
                    matched = True
                    break
            if matched:
                break

        if matched:
            leak_key = (kind, record["source"])
            if leak_key not in seen:
                leaks.append(leak_key)
                seen.add(leak_key)

    return leaks


def main() -> int:
    """Main entry point for pre-commit hook."""
    local_dir = _local_dir()

    if not local_dir.exists():
        print(
            "sanitisation-guard: no local/ dir — guard inactive (clean for fresh clone).",
            file=sys.stderr,
        )
        return 0

    if os.environ.get("SANITISATION_LOCAL_DIR"):
        print(
            f"sanitisation-guard: reading private literals from {local_dir} (override active).",
            file=sys.stderr,
        )

    try:
        records = extract_private_literals(local_dir)
    except LedgerReadError as exc:
        print("COMMIT BLOCKED — sanitisation guard", file=sys.stderr)
        print(f"  {exc}; failing CLOSED.", file=sys.stderr)
        print(
            "  Fix the file (permissions/readability) and retry; "
            "bypass only with git commit --no-verify.",
            file=sys.stderr,
        )
        return 1

    if not records:
        print(
            "sanitisation-guard: no private literals found — guard inactive.",
            file=sys.stderr,
        )
        return 0

    allow = load_allowlist(ALLOWLIST_PATH)
    try:
        added = staged_added_text()
    except GitInvocationError as exc:
        print("COMMIT BLOCKED — sanitisation guard", file=sys.stderr)
        print(f"  git invocation failed ({exc}); failing CLOSED.", file=sys.stderr)
        print(
            "  Resolve the git error and retry; bypass only with git commit --no-verify.",
            file=sys.stderr,
        )
        return 1
    leaks = find_leaks(records, added, allow)

    if leaks:
        print("COMMIT BLOCKED — sanitisation guard", file=sys.stderr)
        if ALLOWLIST_PATH.exists():
            print(
                f"  allowlist canonical-hash: {canonical_config_hash(ALLOWLIST_PATH)[:12]}",
                file=sys.stderr,
            )
        for kind, src in leaks:
            print(
                f"  a {kind} literal from {src} appears in the staged diff (value redacted).",
                file=sys.stderr,
            )
        print(
            "  Redact it, or add the accepted-public value to config/sanitisation_allowlist.yml.",
            file=sys.stderr,
        )
        print(
            "  Emergency bypass: git commit --no-verify (use sparingly).",
            file=sys.stderr,
        )
        return 1

    return 0


def main_prepush() -> int:
    """Main entry point for pre-push hook."""
    local_dir = _local_dir()

    if not local_dir.exists():
        print(
            "sanitisation-guard(pre-push): no local/ dir — guard inactive (clean for fresh clone).",
            file=sys.stderr,
        )
        return 0

    try:
        records = extract_private_literals(local_dir)
    except LedgerReadError as exc:
        print("PUSH BLOCKED — sanitisation guard", file=sys.stderr)
        print(f"  {exc}; failing CLOSED.", file=sys.stderr)
        print(
            "  Fix the file (permissions/readability) and retry; "
            "bypass only with git push --no-verify.",
            file=sys.stderr,
        )
        return 1

    if not records:
        print(
            "sanitisation-guard(pre-push): no private literals found — guard inactive.",
            file=sys.stderr,
        )
        return 0

    # Emit diagnostic — records present but guard may still pass clean
    print(f"sanitisation-guard(pre-push): records={len(records)}", file=sys.stderr)

    # Parse pre-push stdin protocol: <local-ref> <local-sha> <remote-ref> <remote-sha>
    # Each line represents one ref being pushed
    stdin_input = sys.stdin.read()
    lines = [line.strip() for line in stdin_input.strip().splitlines() if line.strip()]

    # Determine outgoing commit ranges
    ranges_to_scan = []
    if not lines:
        # Fallback: direct invocation or test — scan origin/main..HEAD if origin/main exists
        try:
            subprocess.run(
                ["git", "rev-parse", "--verify", "origin/main"],
                cwd=REPO_ROOT,
                capture_output=True,
                check=True,
            )
            ranges_to_scan.append("origin/main..HEAD")
        except (subprocess.CalledProcessError, FileNotFoundError, OSError) as exc:
            # No stdin AND no origin/main baseline — we cannot establish what to scan.
            # Scanning nothing here is fail-OPEN; fail CLOSED instead. (Production
            # pre-push always supplies stdin, so this only affects direct invocation.)
            _print_push_block_git_error(f"cannot resolve origin/main: {exc}")
            return 1
    else:
        for line in lines:
            parts = line.split()
            if len(parts) != 4:
                # A real git pre-push always emits 4 whitespace-separated fields; the
                # empty-line filter above already dropped blanks. A malformed line means
                # we cannot trust the ranges — fail CLOSED.
                print("PUSH BLOCKED — sanitisation guard", file=sys.stderr)
                print(
                    "  malformed pre-push stdin line (expected 4 fields); failing CLOSED.",
                    file=sys.stderr,
                )
                print(
                    "  Bypass only with git push --no-verify (use sparingly).",
                    file=sys.stderr,
                )
                return 1
            local_ref, local_sha, remote_ref, remote_sha = parts

            # Skip branch deletes (local_sha is all zeros)
            if local_sha == "0" * 40:
                continue

            # New ref / never-pushed (remote_sha is all zeros)
            if remote_sha == "0" * 40:
                # Scan full history of local_sha
                ranges_to_scan.append(local_sha)
            else:
                # Scan commits between remote_sha and local_sha
                ranges_to_scan.append(f"{remote_sha}..{local_sha}")

    # Scan each range
    allow = load_allowlist(ALLOWLIST_PATH)
    for rng in ranges_to_scan:
        # Get all commits in this range
        try:
            result = subprocess.run(
                ["git", "rev-list", rng],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=True,
            )
            commits = [c.strip() for c in result.stdout.splitlines() if c.strip()]
        except (subprocess.CalledProcessError, FileNotFoundError, OSError):
            # If rev-list fails, fall back to range_added_text for the whole range.
            # range_added_text now RAISES on a git error → fail CLOSED (never scan
            # nothing). rev-list's own except is preserved (not weakened to a crash).
            try:
                added = range_added_text(rng)
            except GitInvocationError as exc:
                _print_push_block_git_error(f"range scan failed for {rng}: {exc}")
                return 1
            leaks = find_leaks(records, added, allow)
            if leaks:
                print("PUSH BLOCKED — sanitisation guard", file=sys.stderr)
                if ALLOWLIST_PATH.exists():
                    print(
                        f"  allowlist canonical-hash: {canonical_config_hash(ALLOWLIST_PATH)[:12]}",
                        file=sys.stderr,
                    )
                for kind, src in leaks:
                    print(
                        f"  a {kind} literal from {src} appears in range {rng} (value redacted).",
                        file=sys.stderr,
                    )
                print(
                    "  Redact it, or add the accepted-public value to config/sanitisation_allowlist.yml.",
                    file=sys.stderr,
                )
                print(
                    "  Emergency bypass: git push --no-verify (use sparingly).",
                    file=sys.stderr,
                )
                return 1
            continue

        # Scan each commit individually
        for commit in commits:
            # Get added lines for this commit
            try:
                result = subprocess.run(
                    ["git", "show", "-U0", "--no-color", "--format=", commit],
                    cwd=REPO_ROOT,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                lines_list = []
                for line in result.stdout.splitlines():
                    if line.startswith("+") and not line.startswith("+++"):
                        lines_list.append(line[1:])
                commit_added = "\n".join(lines_list)
            except (subprocess.CalledProcessError, FileNotFoundError, OSError) as exc:
                # Cannot read this commit — skipping is fail-OPEN per commit; fail CLOSED.
                _print_push_block_git_error(f"cannot read commit {commit[:12]}: {exc}")
                return 1

            leaks = find_leaks(records, commit_added, allow)
            if leaks:
                print("PUSH BLOCKED — sanitisation guard", file=sys.stderr)
                if ALLOWLIST_PATH.exists():
                    print(
                        f"  allowlist canonical-hash: {canonical_config_hash(ALLOWLIST_PATH)[:12]}",
                        file=sys.stderr,
                    )
                for kind, src in leaks:
                    print(
                        f"  a {kind} literal from {src} appears in commit {commit[:12]} (value redacted).",
                        file=sys.stderr,
                    )
                print(
                    "  Redact it, or add the accepted-public value to config/sanitisation_allowlist.yml.",
                    file=sys.stderr,
                )
                print(
                    "  Emergency bypass: git push --no-verify (use sparingly).",
                    file=sys.stderr,
                )
                return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
