"""Tests for sanitisation guard.

Fixtures use SYNTHETIC/fake private literals only — never real ledger values (PIN 2).
Fixtures MAY contain real-but-PUBLIC allowlist identifiers (IE000YYE6WK5), NEVER real-private values.
"""

import hashlib
import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from scripts.hooks.sanitisation_guard import (
    GitInvocationError,
    LedgerReadError,
    _canonical,
    _group,
    _is_process_noise,
    _is_specific,
    _sig_figs,
    canonical_config_hash,
    extract_private_literals,
    find_leaks,
    load_allowlist,
    main,
    main_prepush,
    range_added_text,
    render_variants,
    staged_added_text,
)


@pytest.fixture
def synthetic_local(tmp_path, monkeypatch):
    """Create a synthetic local directory with fake private literals.

    Synthetic ledger content includes:
    - Fake ISIN: XX0000FAKE01 (12 chars, matches ISIN_RE)
    - Numeric values: 7.3, 5142.31, 5142.30
    - Date: 2026-06-04 (to prove dates are not harvested)
    - Real-but-public allowlist ISIN: IE000YYE6WK5
    """
    local_dir = tmp_path / "local"
    local_dir.mkdir()

    # Create synthetic PORTFOLIO.md with fake data
    portfolio = local_dir / "PORTFOLIO.md"
    portfolio.write_text(
        """# Synthetic Portfolio (FAKE DATA)

| Ticker | ISIN | Name | Shares | Price | Value |
|--------|------|------|--------|-------|-------|
| FAKE.XX | XX0000FAKE01 | Fake ETF | 100 | 7.3 | 5142.31 |
| TEST.XX | IE000YYE6WK5 | Public Test | 50 | 8.7 | 5142.30 |

Last updated: 2026-06-04
"""
    )

    monkeypatch.setenv("SANITISATION_LOCAL_DIR", str(local_dir))
    return local_dir


def test_is_specific():
    """Test _is_specific() with various inputs."""
    # Specific: >=4-digit integers, or decimals with >=3 significant figures
    assert _is_specific("5142") is True  # >= 4 digits
    assert _is_specific("5100") is True  # >= 4 digits
    assert _is_specific("63.41") is True  # 4 sig figs
    assert _is_specific("63.4") is True  # 3 sig figs — verified-leak (qty) class KEPT
    assert _is_specific("71.23") is True  # 4 sig figs
    assert _is_specific("5142.30") is True  # 6 sig figs (trailing zero significant)

    # Not specific (below threshold)
    assert _is_specific("200") is False  # < 4 digits
    assert _is_specific("5") is False  # < 4 digits
    assert _is_specific("5.00") is False  # fractional part is all zeros
    # Amendment 3 — low-information <=2-sig-fig decimals dropped (short EU-variants collide)
    assert _is_specific("1.3") is False  # 2 sig figs
    assert _is_specific("2.6") is False  # 2 sig figs
    assert _is_specific("0.5") is False  # 1 sig fig


def test_sig_figs():
    """Significant-figure counting: leading zeros not significant, trailing decimal zeros are."""
    assert _sig_figs("1.3") == 2
    assert _sig_figs("63.41") == 4
    assert _sig_figs("5142.30") == 6
    assert _sig_figs("0.50") == 2
    assert _sig_figs("0.05") == 1


def test_render_variants_preserve_trailing_zero():
    """Test render_variants() preserves trailing zeros."""
    # With trailing zero
    variants = render_variants("5142.30")
    assert variants == {"5142.30", "5,142.30", "5.142,30"}

    # Integer (no fractional part)
    variants = render_variants("5100")
    assert variants == {"5100", "5,100", "5.100"}


def test_find_leak_isin(synthetic_local):
    """Test ISIN leak detection."""
    records = extract_private_literals(synthetic_local)

    # Find the ISIN record (should exclude IE000YYE6WK5 which is allowlisted)
    isin_records = [r for r in records if r["kind"] == "ISIN" and r["key"] == "XX0000FAKE01"]
    assert len(isin_records) == 1

    # Added text contains the synthetic ISIN
    added_text = "Adding position XX0000FAKE01 to portfolio"
    allow = {"isins": set(), "tickers": set(), "values": set()}

    leaks = find_leaks(isin_records, added_text, allow)
    assert len(leaks) == 1
    assert leaks[0][0] == "ISIN"
    assert "local/PORTFOLIO.md" in leaks[0][1]


def test_find_leak_numeric_all_three_variants(synthetic_local):
    """Test numeric leak detection across all three representation variants."""
    records = extract_private_literals(synthetic_local)

    # Find the 5142.31 record
    num_records = [r for r in records if r["kind"] == "numeric value" and r["key"] == "5142.31"]
    assert len(num_records) == 1
    record = num_records[0]

    allow = {"isins": set(), "tickers": set(), "values": set()}

    # Test plain variant
    added_text_plain = "Value is 5142.31 EUR"
    leaks = find_leaks([record], added_text_plain, allow)
    assert len(leaks) == 1

    # Test US variant (comma thousands)
    added_text_us = "Value is 5,142.31 EUR"
    leaks = find_leaks([record], added_text_us, allow)
    assert len(leaks) == 1

    # Test EU variant (dot thousands, comma decimal)
    added_text_eu = "Value is 5.142,31 EUR"
    leaks = find_leaks([record], added_text_eu, allow)
    assert len(leaks) == 1


def test_clean_diff_no_leak(synthetic_local):
    """Test that benign added text produces no leaks."""
    records = extract_private_literals(synthetic_local)
    added_text = "This is a completely benign change with no private data"
    allow = {"isins": set(), "tickers": set(), "values": set()}

    leaks = find_leaks(records, added_text, allow)
    assert leaks == []


def test_allowlist_clears_isin(synthetic_local):
    """Test that allowlisted ISINs are not reported as leaks."""
    records = extract_private_literals(synthetic_local)

    # IE000YYE6WK5 is in the synthetic ledger and will be in records
    # But it's also in the allowlist
    added_text = "Adding IE000YYE6WK5 to the documentation"
    allow = {"isins": {"IE000YYE6WK5"}, "tickers": set(), "values": set()}

    leaks = find_leaks(records, added_text, allow)
    # Should not leak because it's allowlisted
    ie_leaks = [l for l in leaks if "IE000YYE6WK5" in str(l)]
    assert len(ie_leaks) == 0


def test_digit_adjacency_no_false_positive(synthetic_local):
    """Test that digit adjacency prevents false positives."""
    records = extract_private_literals(synthetic_local)

    # Find 5142.31 record
    num_records = [r for r in records if r["kind"] == "numeric value" and r["key"] == "5142.31"]
    assert len(num_records) == 1
    record = num_records[0]

    allow = {"isins": set(), "tickers": set(), "values": set()}

    # "5142.31" inside "95142.31" should NOT leak (different number)
    added_text1 = "Value is 95142.31"
    leaks = find_leaks([record], added_text1, allow)
    assert len(leaks) == 0

    # "5,142.31" inside "5,142.310" should NOT leak (different number)
    added_text2 = "Value is 5,142.310"
    leaks = find_leaks([record], added_text2, allow)
    assert len(leaks) == 0


def test_diff_side_date_exclusion():
    """A numeric value appearing as the YYYY of an ISO date in the diff is NOT a leak;
    the same value bare IS a leak. (Amendment 2 — diff-side date-exclusion.)"""
    record = {
        "kind": "numeric value",
        "key": "5142",
        "patterns": {"5142"},
        "source": "local/PORTFOLIO.md",
    }
    allow = {"isins": set(), "tickers": set(), "values": set()}
    # Inside an ISO date in the diff → skipped (not a leak)
    assert find_leaks([record], "updated 5142-06-04 today", allow) == []
    # Bare in the diff → flagged
    assert len(find_leaks([record], "nav was 5142 today", allow)) == 1
    # A decimal value can never sit inside an ISO date → still flagged even near a date
    rec2 = {"kind": "numeric value", "key": "5142.31", "patterns": {"5142.31"}, "source": "local/PORTFOLIO.md"}
    assert len(find_leaks([rec2], "on 2026-06-09 the value 5142.31 appeared", allow)) == 1


def test_re_escape_dot_literal(synthetic_local):
    """Test that dots in patterns are treated as literals, not wildcards."""
    records = extract_private_literals(synthetic_local)

    # Find 5142.31 record
    num_records = [r for r in records if r["kind"] == "numeric value" and r["key"] == "5142.31"]
    assert len(num_records) == 1
    record = num_records[0]

    allow = {"isins": set(), "tickers": set(), "values": set()}

    # "5142X31" should NOT match "5142.31" pattern (dot is literal, not wildcard)
    added_text = "Value is 5142X31"
    leaks = find_leaks([record], added_text, allow)
    assert len(leaks) == 0


def test_block_message_redacts_value(synthetic_local, capsys):
    """Test that block messages never include the actual value."""
    records = extract_private_literals(synthetic_local)

    # Find a numeric record
    num_records = [r for r in records if r["kind"] == "numeric value" and r["key"] == "5142.31"]
    assert len(num_records) == 1

    added_text = "Value is 5142.31 EUR"
    allow = {"isins": set(), "tickers": set(), "values": set()}

    leaks = find_leaks(records, added_text, allow)

    # Verify leaks tuple structure: (kind, source) only, NEVER the value
    for leak in leaks:
        assert len(leak) == 2
        kind, source = leak
        assert isinstance(kind, str)
        assert isinstance(source, str)
        # Verify the actual value is NOT in the tuple
        assert "5142.31" not in str(leak)


def test_no_op_missing_local(tmp_path, monkeypatch, capsys):
    """Test that guard no-ops gracefully when local/ doesn't exist."""
    missing_dir = tmp_path / "nonexistent"
    monkeypatch.setenv("SANITISATION_LOCAL_DIR", str(missing_dir))

    result = main()
    assert result == 0

    captured = capsys.readouterr()
    assert "no local/ dir — guard inactive" in captured.err


def test_canonical_config_hash_golden(tmp_path):
    """Test canonical_config_hash is stable and changes with content."""
    # Create a synthetic allowlist
    config = tmp_path / "allowlist.yml"
    config.write_text(
        """allow:
  isins:
    - TEST1234ISIN01
  tickers:
    - TEST.XX
  values:
    - "9988.77"
"""
    )

    # Compute hash twice — should be identical
    hash1 = canonical_config_hash(config)
    hash2 = canonical_config_hash(config)
    assert hash1 == hash2

    # Golden hash for this exact content (parsed-canonical)
    # Compute expected hash
    data = yaml.safe_load(config.read_text())
    canonical_json = json.dumps(
        data, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str
    )
    expected_hash = hashlib.sha256(canonical_json.encode()).hexdigest()
    assert hash1 == expected_hash

    # Modify the config
    config.write_text(
        """allow:
  isins:
    - TEST1234ISIN01
    - ANOTHER12ISIN02
  tickers:
    - TEST.XX
  values:
    - "9988.77"
"""
    )

    # Hash should change
    hash3 = canonical_config_hash(config)
    assert hash3 != hash1


def test_range_added_text_synthetic_repo(tmp_path):
    """Test range_added_text() extracts added lines from a multi-commit range."""
    # Create a synthetic git repo
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()
    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.test"], cwd=repo_dir, check=True, capture_output=True)

    # Create initial file
    test_file = repo_dir / "test.txt"
    test_file.write_text("line1\nline2\n")
    subprocess.run(["git", "add", "test.txt"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo_dir, check=True, capture_output=True)

    # Add more lines in second commit
    test_file.write_text("line1\nline2\nline3\nline4\n")
    subprocess.run(["git", "add", "test.txt"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "add lines"], cwd=repo_dir, check=True, capture_output=True)

    # Get the commit range (all commits)
    result = subprocess.run(
        ["git", "rev-list", "HEAD"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        check=True,
    )
    commits = result.stdout.strip().splitlines()
    assert len(commits) == 2

    # Test range_added_text with monkeypatch for REPO_ROOT
    import scripts.hooks.sanitisation_guard as sg
    original_repo_root = sg.REPO_ROOT
    try:
        sg.REPO_ROOT = repo_dir
        added = range_added_text("HEAD~1..HEAD")
        # Should contain the added lines from the second commit
        assert "line3" in added
        assert "line4" in added
        # Should NOT contain "+++" header lines
        assert "+++" not in added
    finally:
        sg.REPO_ROOT = original_repo_root


def test_main_prepush_blocks_on_leak(tmp_path, monkeypatch, capsys):
    """Test main_prepush() BLOCKS (returns 1) when a private literal appears in an outgoing commit."""
    # Create synthetic local dir with a fake private value
    local_dir = tmp_path / "local"
    local_dir.mkdir()
    portfolio = local_dir / "PORTFOLIO.md"
    # Use a fake ISIN that's distinct and unlikely to collide
    portfolio.write_text("| ISIN | Value |\n|------|-------|\n| ZZ9999TEST99 | 7777 |\n")

    monkeypatch.setenv("SANITISATION_LOCAL_DIR", str(local_dir))

    # Create a synthetic git repo
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()
    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.test"], cwd=repo_dir, check=True, capture_output=True)

    # Create initial commit
    test_file = repo_dir / "test.txt"
    test_file.write_text("initial\n")
    subprocess.run(["git", "add", "test.txt"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo_dir, check=True, capture_output=True)

    # Create a second commit with the private literal
    test_file.write_text("initial\nLeak: ZZ9999TEST99\n")
    subprocess.run(["git", "add", "test.txt"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "leak"], cwd=repo_dir, check=True, capture_output=True)

    # Monkeypatch stdin to simulate pre-push protocol
    # Format: <local-ref> <local-sha> <remote-ref> <remote-sha>
    # For a new branch (never pushed), remote_sha is all zeros
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        check=True,
    )
    local_sha = result.stdout.strip()
    stdin_data = f"refs/heads/main {local_sha} refs/heads/main {'0' * 40}\n"

    # Monkeypatch REPO_ROOT and stdin
    import scripts.hooks.sanitisation_guard as sg
    original_repo_root = sg.REPO_ROOT
    try:
        sg.REPO_ROOT = repo_dir
        monkeypatch.setattr("sys.stdin", subprocess.io.TextIOWrapper(subprocess.io.BytesIO(stdin_data.encode())))

        result = main_prepush()
        assert result == 1  # BLOCKED

        captured = capsys.readouterr()
        assert "PUSH BLOCKED" in captured.err
        assert "ISIN" in captured.err
        assert "ZZ9999TEST99" not in captured.err  # Value should be redacted
    finally:
        sg.REPO_ROOT = original_repo_root


def test_main_prepush_passes_clean(tmp_path, monkeypatch, capsys):
    """Test main_prepush() PASSES (returns 0) on a clean range, with records>0 diagnostic."""
    # Create synthetic local dir with a fake private value
    local_dir = tmp_path / "local"
    local_dir.mkdir()
    portfolio = local_dir / "PORTFOLIO.md"
    portfolio.write_text("| ISIN | Value |\n|------|-------|\n| ZZ9999TEST99 | 7777 |\n")

    monkeypatch.setenv("SANITISATION_LOCAL_DIR", str(local_dir))

    # Create a synthetic git repo
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()
    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.test"], cwd=repo_dir, check=True, capture_output=True)

    # Create initial commit
    test_file = repo_dir / "test.txt"
    test_file.write_text("initial\n")
    subprocess.run(["git", "add", "test.txt"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo_dir, check=True, capture_output=True)

    # Create a second commit with NO private data
    test_file.write_text("initial\nclean change\n")
    subprocess.run(["git", "add", "test.txt"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "clean"], cwd=repo_dir, check=True, capture_output=True)

    # Monkeypatch stdin to simulate pre-push protocol
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        check=True,
    )
    local_sha = result.stdout.strip()
    stdin_data = f"refs/heads/main {local_sha} refs/heads/main {'0' * 40}\n"

    # Monkeypatch REPO_ROOT and stdin
    import scripts.hooks.sanitisation_guard as sg
    original_repo_root = sg.REPO_ROOT
    try:
        sg.REPO_ROOT = repo_dir
        monkeypatch.setattr("sys.stdin", subprocess.io.TextIOWrapper(subprocess.io.BytesIO(stdin_data.encode())))

        result = main_prepush()
        assert result == 0  # PASSED

        captured = capsys.readouterr()
        # Must have the records=N diagnostic with N>0 (guard ACTIVE)
        assert "records=" in captured.err
        # Extract the N value
        import re
        match = re.search(r"records=(\d+)", captured.err)
        assert match is not None
        records_count = int(match.group(1))
        assert records_count > 0  # Guard was ACTIVE (not inactive)
    finally:
        sg.REPO_ROOT = original_repo_root


def test_install_hook_pre_push(tmp_path):
    """Test install_hook(hook_type='pre-push') installs the pre-push symlink correctly."""
    from scripts.init_workspace import install_hook, REPO_ROOT

    # Create a synthetic .git structure
    test_repo = tmp_path / "test_repo"
    test_repo.mkdir()
    git_dir = test_repo / ".git"
    git_dir.mkdir()
    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir()

    # Create a synthetic source hook
    scripts_dir = test_repo / "scripts" / "hooks"
    scripts_dir.mkdir(parents=True)
    source_hook = scripts_dir / "pre-push"
    source_hook.write_text("#!/usr/bin/env python3\n# test hook\n")

    # Monkeypatch REPO_ROOT
    original_repo_root = REPO_ROOT
    import scripts.init_workspace as siw
    try:
        siw.REPO_ROOT = test_repo

        # Install the hook
        install_hook("pre-push")

        # Verify symlink was created
        target = hooks_dir / "pre-push"
        assert target.exists()
        assert target.is_symlink()
        assert target.resolve() == source_hook.resolve()
    finally:
        siw.REPO_ROOT = original_repo_root


def test_install_hook_foreign_pre_push_not_overwritten(tmp_path, capsys):
    """Test install_hook(hook_type='pre-push') does NOT overwrite a pre-existing foreign hook."""
    from scripts.init_workspace import install_hook, REPO_ROOT

    # Create a synthetic .git structure
    test_repo = tmp_path / "test_repo"
    test_repo.mkdir()
    git_dir = test_repo / ".git"
    git_dir.mkdir()
    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir()

    # Create a synthetic source hook
    scripts_dir = test_repo / "scripts" / "hooks"
    scripts_dir.mkdir(parents=True)
    source_hook = scripts_dir / "pre-push"
    source_hook.write_text("#!/usr/bin/env python3\n# test hook\n")

    # Create a foreign pre-existing hook
    target = hooks_dir / "pre-push"
    target.write_text("#!/bin/bash\n# foreign hook\n")

    # Monkeypatch REPO_ROOT
    original_repo_root = REPO_ROOT
    import scripts.init_workspace as siw
    try:
        siw.REPO_ROOT = test_repo

        # Attempt to install the hook
        install_hook("pre-push")

        # Verify the foreign hook was NOT overwritten
        assert target.read_text() == "#!/bin/bash\n# foreign hook\n"

        # Verify warning message was printed
        captured = capsys.readouterr()
        assert "A pre-push hook already exists; NOT overwriting it" in captured.out
    finally:
        siw.REPO_ROOT = original_repo_root


# =====================================================================================
# S-31 — precision (ITEM 1) + fail-closed (ITEM 2) + corpus (ITEM 4). Synthetic only.
# CARDINAL: every narrowing is PAIRED with a real-leak-STILL-blocks assertion.
# =====================================================================================

_NO_ALLOW = {"isins": set(), "tickers": set(), "values": set()}


def _git_init(repo):
    """Initialise a synthetic git repo (no origin)."""
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@t.t"], cwd=repo, check=True, capture_output=True)


# --- ITEM 1: ticker-only alpha boundary (a1) + paired detection-intact -------------

def test_ticker_alpha_boundary_fp_fixed_and_delimited_still_blocks():
    """(a1) A ticker glued to trailing letters with NO separator no longer blocks
    (named residual); EVERY delimited shape (the realistic leak shape) STILL blocks."""
    rec = {"kind": "ticker", "key": "FAKE.XX", "patterns": {"FAKE.XX"}, "source": "local/PORTFOLIO.md"}
    # FP fixed — glued-no-separator passes
    assert find_leaks([rec], "ticker FAKE.XXY here", _NO_ALLOW) == []
    assert find_leaks([rec], "FAKE.XXDEUTSCHE", _NO_ALLOW) == []
    # Detection intact — all delimited shapes block
    for txt in ["FAKE.XX listed", "|FAKE.XX|", "/FAKE.XX/", "see FAKE.XX.", "FAKE.XX"]:
        assert len(find_leaks([rec], txt, _NO_ALLOW)) == 1, txt


def test_isin_path_digit_only_unchanged_overblocks_never_underblocks():
    """(a1-isin) ISIN stays on the digit-only matcher: a glued-alpha ISIN STILL blocks
    (over-block, the cardinal-safe direction); standalone STILL blocks."""
    rec = {"kind": "ISIN", "key": "XX0000FAKE01", "patterns": {"XX0000FAKE01"}, "source": "local/PORTFOLIO.md"}
    assert len(find_leaks([rec], "XX0000FAKE01Notes", _NO_ALLOW)) == 1  # glued alpha → still blocks
    assert len(find_leaks([rec], "ref XX0000FAKE01 here", _NO_ALLOW)) == 1  # standalone


def test_numeric_glued_to_letters_still_blocks():
    """(a2) The numeric path is UNCHANGED — a value glued to a currency code (the
    highest-stakes leak class) STILL blocks."""
    rec = {"kind": "numeric value", "key": "5142", "patterns": render_variants("5142"), "source": "local/PORTFOLIO.md"}
    assert len(find_leaks([rec], "nav 5142EUR today", _NO_ALLOW)) == 1


def test_isin_match_unaffected_by_date_skip():
    """(f) An ISIN match adjacent to an ISO date still blocks (an ISIN is longer than any
    ISO-date span so the date-skip cannot contain it). Numeric path untouched."""
    rec = {"kind": "ISIN", "key": "XX0000FAKE01", "patterns": {"XX0000FAKE01"}, "source": "local/PORTFOLIO.md"}
    assert len(find_leaks([rec], "on 2026-06-09 the ISIN XX0000FAKE01 appeared", _NO_ALLOW)) == 1


# --- ITEM 4: corpus exclusion + no-swallow + tracked-path invariant ----------------

def test_corpus_excludes_process_noise_keeps_retained(tmp_path, monkeypatch):
    """(a3/routing, harvest side) A value in a RETAINED source is harvested; a value
    living ONLY in an EXCLUDED process-noise file is NOT harvested."""
    local_dir = tmp_path / "local"
    (local_dir / "brainstorms").mkdir(parents=True)
    (local_dir / "SESSIONS.md").write_text("nav 8473.55 recorded\n")  # retained
    (local_dir / "brainstorms" / "2026-07.steering-foo.md").write_text("meta 9261.44\n")  # future steering → excluded
    (local_dir / "brainstorms" / "INDEX.md").write_text("idx 7531.22\n")  # excluded
    (local_dir / "brainstorms" / "x_draft.md").write_text("draft 6420.11\n")  # excluded
    monkeypatch.setenv("SANITISATION_LOCAL_DIR", str(local_dir))
    keys = {r["key"] for r in extract_private_literals(local_dir)}
    assert "8473.55" in keys
    assert "9261.44" not in keys
    assert "7531.22" not in keys
    assert "6420.11" not in keys


def test_process_noise_does_not_swallow_retained_sources():
    """No-swallow guard: _is_process_noise excludes every NOISE file and NO retained source."""
    base = Path("local")
    retained = [
        "AGENT_PERFORMANCE.md", "HYPOTHESIS_LOG.md", "INVESTOR_PROFILE.md", "PORTFOLIO.md",
        "ROTATION_LOG.md", "SESSIONS.md", "brainstorms/2026-03.md", "brainstorms/2026-04.md",
        "brainstorms/2026-05.md", "brainstorms/2026-04.pre-session.md",
        "brainstorms/2026-05.pre-session.md", "retros/2026-04-24.md",
    ]
    for n in retained:
        assert _is_process_noise(base / n) is False, n
    noise = [
        "brainstorms/INDEX.md", "brainstorms/2026-05.issues-scratch.md",
        "brainstorms/2026-06.steering-data-layer.md",
        "brainstorms/2026-06.steering-tooling-remainder.md",
        "brainstorms/_phase4_working_prompt_draft.md",
    ]
    for n in noise:
        assert _is_process_noise(base / n) is True, n


def test_templates_not_harvested(tmp_path, monkeypatch):
    """(e) Tracked-path invariant: a templates/* file (tracked) is NOT harvested."""
    local_dir = tmp_path / "local"
    (local_dir / "templates").mkdir(parents=True)
    tfile = local_dir / "templates" / "PORTFOLIO.template.md"
    tfile.write_text("template value 8473.55\n")
    monkeypatch.setenv("SANITISATION_LOCAL_DIR", str(local_dir))
    monkeypatch.setattr(
        "scripts.hooks.sanitisation_guard._tracked_paths", lambda d: {tfile.resolve()}
    )
    keys = {r["key"] for r in extract_private_literals(local_dir)}
    assert "8473.55" not in keys


def test_corpus_routing_production_blocks_retained_passes_excluded(tmp_path, monkeypatch, capsys):
    """(b-routing, production) Through main_prepush: a value committed that lives in a
    RETAINED source BLOCKS; a value that lives ONLY in an EXCLUDED file PASSES."""
    local_dir = tmp_path / "local"
    (local_dir / "brainstorms").mkdir(parents=True)
    (local_dir / "SESSIONS.md").write_text("nav 8473.55\n")  # retained → V1 harvested
    (local_dir / "brainstorms" / "2026-07.steering-foo.md").write_text("meta 9261.44\n")  # excluded → V2 not harvested
    monkeypatch.setenv("SANITISATION_LOCAL_DIR", str(local_dir))

    repo = tmp_path / "repo"
    repo.mkdir()
    _git_init(repo)
    f = repo / "doc.md"
    f.write_text("init\n")
    subprocess.run(["git", "add", "doc.md"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True, capture_output=True)

    import scripts.hooks.sanitisation_guard as sg
    monkeypatch.setattr(sg, "REPO_ROOT", repo)

    def run_prepush():
        sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True).stdout.strip()
        stdin = f"refs/heads/main {sha} refs/heads/main {'0'*40}\n"
        monkeypatch.setattr("sys.stdin", subprocess.io.TextIOWrapper(subprocess.io.BytesIO(stdin.encode())))
        return main_prepush()

    # Commit the EXCLUDED-only value → PASSES (not harvested)
    f.write_text("init\nseen 9261.44\n")
    subprocess.run(["git", "add", "doc.md"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "excluded value"], cwd=repo, check=True, capture_output=True)
    assert run_prepush() == 0

    # Commit the RETAINED value → BLOCKS
    f.write_text("init\nseen 9261.44\nleak 8473.55\n")
    subprocess.run(["git", "add", "doc.md"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "retained value"], cwd=repo, check=True, capture_output=True)
    assert run_prepush() == 1
    assert "PUSH BLOCKED" in capsys.readouterr().err


# --- ITEM 2: fail-closed (git error) + empty-but-valid passes ----------------------

def test_main_fails_closed_on_git_error(tmp_path, monkeypatch, capsys):
    """(c) main() with a non-git REPO_ROOT → staged_added_text raises → clean BLOCK."""
    local_dir = tmp_path / "local"
    local_dir.mkdir()
    (local_dir / "PORTFOLIO.md").write_text("| ISIN |\n| ZZ9999TEST99 |\n")
    monkeypatch.setenv("SANITISATION_LOCAL_DIR", str(local_dir))
    non_git = tmp_path / "nongit"
    non_git.mkdir()
    import scripts.hooks.sanitisation_guard as sg
    monkeypatch.setattr(sg, "REPO_ROOT", non_git)
    assert main() == 1
    err = capsys.readouterr().err
    assert "COMMIT BLOCKED" in err and "failing CLOSED" in err


def test_main_passes_clean_empty_diff(tmp_path, monkeypatch):
    """(c) main() with a valid git repo + EMPTY staged diff + records present → PASSES
    (empty-but-valid is NOT an error — the guard must not block its own clean commit)."""
    local_dir = tmp_path / "local"
    local_dir.mkdir()
    (local_dir / "PORTFOLIO.md").write_text("| ISIN |\n| ZZ9999TEST99 |\n")
    monkeypatch.setenv("SANITISATION_LOCAL_DIR", str(local_dir))
    repo = tmp_path / "repo"
    repo.mkdir()
    _git_init(repo)
    import scripts.hooks.sanitisation_guard as sg
    monkeypatch.setattr(sg, "REPO_ROOT", repo)
    assert main() == 0


def test_staged_added_text_raises_on_git_error(tmp_path, monkeypatch):
    """staged_added_text raises GitInvocationError (not returns "") on a git error."""
    non_git = tmp_path / "nongit"
    non_git.mkdir()
    import scripts.hooks.sanitisation_guard as sg
    monkeypatch.setattr(sg, "REPO_ROOT", non_git)
    with pytest.raises(GitInvocationError):
        staged_added_text()


def test_range_added_text_raises_on_git_error(tmp_path, monkeypatch):
    """range_added_text raises GitInvocationError on a git error."""
    non_git = tmp_path / "nongit"
    non_git.mkdir()
    import scripts.hooks.sanitisation_guard as sg
    monkeypatch.setattr(sg, "REPO_ROOT", non_git)
    with pytest.raises(GitInvocationError):
        range_added_text("HEAD~1..HEAD")


def _prepush_with_stdin(repo, monkeypatch, stdin_data):
    monkeypatch.setattr("sys.stdin", subprocess.io.TextIOWrapper(subprocess.io.BytesIO(stdin_data.encode())))
    return main_prepush()


def test_main_prepush_fails_closed_on_malformed_stdin(tmp_path, monkeypatch, capsys):
    """(c) A malformed pre-push line (not 4 fields) → fail CLOSED."""
    local_dir = tmp_path / "local"
    local_dir.mkdir()
    (local_dir / "PORTFOLIO.md").write_text("| ISIN |\n| ZZ9999TEST99 |\n")
    monkeypatch.setenv("SANITISATION_LOCAL_DIR", str(local_dir))
    repo = tmp_path / "repo"
    repo.mkdir()
    _git_init(repo)
    import scripts.hooks.sanitisation_guard as sg
    monkeypatch.setattr(sg, "REPO_ROOT", repo)
    assert _prepush_with_stdin(repo, monkeypatch, "refs/heads/main abc123\n") == 1
    assert "PUSH BLOCKED" in capsys.readouterr().err


def test_main_prepush_passes_delete_only(tmp_path, monkeypatch):
    """(c) A branch-delete line (local_sha all zeros) → legitimate PASS (not malformed)."""
    local_dir = tmp_path / "local"
    local_dir.mkdir()
    (local_dir / "PORTFOLIO.md").write_text("| ISIN |\n| ZZ9999TEST99 |\n")
    monkeypatch.setenv("SANITISATION_LOCAL_DIR", str(local_dir))
    repo = tmp_path / "repo"
    repo.mkdir()
    _git_init(repo)
    import scripts.hooks.sanitisation_guard as sg
    monkeypatch.setattr(sg, "REPO_ROOT", repo)
    stdin = f"refs/heads/main {'0'*40} refs/heads/main {'a'*40}\n"
    assert _prepush_with_stdin(repo, monkeypatch, stdin) == 0


def test_main_prepush_fails_closed_no_origin_no_stdin(tmp_path, monkeypatch, capsys):
    """(c) Empty stdin + no origin/main → cannot establish a range → fail CLOSED."""
    local_dir = tmp_path / "local"
    local_dir.mkdir()
    (local_dir / "PORTFOLIO.md").write_text("| ISIN |\n| ZZ9999TEST99 |\n")
    monkeypatch.setenv("SANITISATION_LOCAL_DIR", str(local_dir))
    repo = tmp_path / "repo"
    repo.mkdir()
    _git_init(repo)
    f = repo / "doc.md"
    f.write_text("x\n")
    subprocess.run(["git", "add", "doc.md"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True, capture_output=True)
    import scripts.hooks.sanitisation_guard as sg
    monkeypatch.setattr(sg, "REPO_ROOT", repo)
    assert _prepush_with_stdin(repo, monkeypatch, "") == 1
    assert "PUSH BLOCKED" in capsys.readouterr().err


def test_main_prepush_fails_closed_on_git_show_error(tmp_path, monkeypatch, capsys):
    """(c) A git-show error on a commit → fail CLOSED (skipping is fail-open per commit)."""
    local_dir = tmp_path / "local"
    local_dir.mkdir()
    (local_dir / "PORTFOLIO.md").write_text("| ISIN |\n| ZZ9999TEST99 |\n")
    monkeypatch.setenv("SANITISATION_LOCAL_DIR", str(local_dir))
    repo = tmp_path / "repo"
    repo.mkdir()
    _git_init(repo)
    f = repo / "doc.md"
    f.write_text("x\n")
    subprocess.run(["git", "add", "doc.md"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True, capture_output=True)
    f.write_text("x\ny\n")
    subprocess.run(["git", "add", "doc.md"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "second"], cwd=repo, check=True, capture_output=True)
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True).stdout.strip()

    import scripts.hooks.sanitisation_guard as sg
    monkeypatch.setattr(sg, "REPO_ROOT", repo)
    orig_run = subprocess.run

    def fake_run(cmd, *a, **k):
        if isinstance(cmd, list) and "show" in cmd:
            raise subprocess.CalledProcessError(1, cmd)
        return orig_run(cmd, *a, **k)

    monkeypatch.setattr(subprocess, "run", fake_run)
    stdin = f"refs/heads/main {sha} refs/heads/main {'0'*40}\n"
    assert _prepush_with_stdin(repo, monkeypatch, stdin) == 1
    assert "PUSH BLOCKED" in capsys.readouterr().err


# --- ITEM 2 (L3 fold-in): ledger-read fail-closed + latin-1 fallback ---------------

def test_extract_fails_closed_on_ledger_oserror(tmp_path, monkeypatch):
    """(c-read) An OSError reading a local/ file → LedgerReadError (fail CLOSED)."""
    local_dir = tmp_path / "local"
    local_dir.mkdir()
    (local_dir / "PORTFOLIO.md").write_text("ZZ9999TEST99\n")
    monkeypatch.setenv("SANITISATION_LOCAL_DIR", str(local_dir))
    import pathlib
    orig = pathlib.Path.read_text

    def boom(self, *a, **k):
        if self.name == "PORTFOLIO.md":
            raise OSError("simulated unreadable")
        return orig(self, *a, **k)

    monkeypatch.setattr(pathlib.Path, "read_text", boom)
    with pytest.raises(LedgerReadError):
        extract_private_literals(local_dir)


def test_main_fails_closed_on_ledger_oserror(tmp_path, monkeypatch, capsys):
    """(c-read) main() blocks cleanly on a LedgerReadError (not an uncaught traceback)."""
    local_dir = tmp_path / "local"
    local_dir.mkdir()
    (local_dir / "PORTFOLIO.md").write_text("ZZ9999TEST99\n")
    monkeypatch.setenv("SANITISATION_LOCAL_DIR", str(local_dir))
    import pathlib
    orig = pathlib.Path.read_text

    def boom(self, *a, **k):
        if self.name == "PORTFOLIO.md":
            raise OSError("simulated")
        return orig(self, *a, **k)

    monkeypatch.setattr(pathlib.Path, "read_text", boom)
    assert main() == 1
    err = capsys.readouterr().err
    assert "COMMIT BLOCKED" in err and "failing CLOSED" in err


def test_latin1_fallback_still_harvests_non_utf8_ledger(tmp_path, monkeypatch, capsys):
    """(c-read) A non-UTF-8 ledger is best-effort latin-1 decoded — its ASCII-shaped
    value is STILL harvested (no under-block) + a loud warning (no DoS)."""
    local_dir = tmp_path / "local"
    local_dir.mkdir()
    # Latin-1 bytes (ç, é) make this invalid UTF-8; the ASCII value survives latin-1.
    (local_dir / "PORTFOLIO.md").write_bytes("preço 8473.55 \xe9\n".encode("latin-1"))
    monkeypatch.setenv("SANITISATION_LOCAL_DIR", str(local_dir))
    keys = {r["key"] for r in extract_private_literals(local_dir)}
    assert "8473.55" in keys  # detection preserved despite non-UTF-8
    assert "not UTF-8" in capsys.readouterr().err  # loud, non-silent
