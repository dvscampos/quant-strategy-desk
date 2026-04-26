"""Skill invariant tests (DoD #12, L37).

Greps SKILL.md and gate-consuming agent YAMLs for forbidden strings that would
indicate the old recall-based gate evaluation has been re-introduced.

Agent discovery (opt-out must be explicit):
  Every agents/*.yml must declare `gate_consumption: true` or `gate_consumption: false`.
  Absent field = test failure (no silent omissions).
  Files with `gate_consumption: true` are added to WATCHED_FILES automatically.

Forbidden patterns (any match in a watched file → test fails):
  - "from memory"
  - "recall the latest"
  - "fallback to recall"
  - "re-derive the tier"

These patterns represent the availability-bias failure mode Phase 1B was built to retire.
"""

from __future__ import annotations

import re
from pathlib import Path
import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_ROOT = Path(__file__).parent.parent
_SKILL_MD = _ROOT / ".claude" / "commands" / "war-room" / "SKILL.md"
_AGENTS_DIR = _ROOT / "agents"

FORBIDDEN_STRINGS = [
    "from memory",
    "recall the latest",
    "fallback to recall",
    "re-derive the tier",
]


# ---------------------------------------------------------------------------
# Agent discovery
# ---------------------------------------------------------------------------

_GC_PATTERN = re.compile(r"^gate_consumption:\s*(true|false)\s*$", re.MULTILINE)


def _read_gate_consumption(yml_path: Path) -> bool | None:
    """Return True/False for gate_consumption field, None if absent.

    Uses regex rather than yaml.safe_load because some agent YAMLs contain
    complex block sequences that trip the YAML parser (colons inside sequence items).
    """
    text = yml_path.read_text(encoding="utf-8")
    match = _GC_PATTERN.search(text)
    if match is None:
        return None
    return match.group(1) == "true"


def _load_gate_consuming_agents() -> list[Path]:
    """Return paths of agents/*.yml with gate_consumption: true.

    Every agent YAML must declare gate_consumption explicitly — absent field
    raises AssertionError so the test suite fails loudly.
    """
    consuming = []
    for yml_path in sorted(_AGENTS_DIR.glob("*.yml")):
        value = _read_gate_consumption(yml_path)
        if value is None:
            pytest.fail(
                f"{yml_path.name} is missing required field 'gate_consumption: true|false'. "
                "Every agent YAML must declare this explicitly (Phase 1B invariant). "
                "If this agent does not consume the gate table, add 'gate_consumption: false'."
            )
        if value is True:
            consuming.append(yml_path)
    return consuming


def _build_watched_files() -> list[Path]:
    return [_SKILL_MD] + _load_gate_consuming_agents()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_all_agents_declare_gate_consumption() -> None:
    """Every agents/*.yml must have an explicit gate_consumption: true|false field."""
    for yml_path in sorted(_AGENTS_DIR.glob("*.yml")):
        value = _read_gate_consumption(yml_path)
        assert value is not None, (
            f"{yml_path.name} is missing 'gate_consumption: true|false' field. "
            "Add 'gate_consumption: true' if it consumes the gate table, "
            "or 'gate_consumption: false' if it does not."
        )


@pytest.mark.parametrize("watched_path", _build_watched_files(), ids=lambda p: p.name)
@pytest.mark.parametrize("forbidden", FORBIDDEN_STRINGS)
def test_no_recall_fallback_in_watched_files(watched_path: Path, forbidden: str) -> None:
    if not watched_path.exists():
        pytest.fail(f"Watched file does not exist: {watched_path}")
    contents = watched_path.read_text(encoding="utf-8").lower()
    assert forbidden not in contents, (
        f"Forbidden pattern '{forbidden}' found in {watched_path}.\n"
        "This indicates recall-based gate evaluation has been re-introduced, "
        "violating the Phase 1B invariant. Remove the pattern and wire to gate_eval output."
    )
