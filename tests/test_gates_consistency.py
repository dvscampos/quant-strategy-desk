"""Test A — single-source-of-truth enforcement.

Asserts that specific numeric values from config/gates.yml do NOT appear
verbatim in the prose files that reference it. Each tuple is:
  (file_path, section_heading, [forbidden_strings])

The check is scoped to the named section only (from the heading line until
the next same-level heading), so it does not false-positive on unrelated
sections that happen to use the same number.
"""

import re
from pathlib import Path

ROOT = Path(__file__).parent.parent

# (relative file path, exact section heading text, forbidden strings)
CONSISTENCY_RULES = [
    (
        "docs/RISK_FRAMEWORK.md",
        "### Cash Floor (Tiered by NAV)",
        ["15%", "10%", "€2,000", "€10,000", "15% of NAV", "10% of NAV"],
    ),
    (
        "docs/RISK_FRAMEWORK.md",
        "## VIX Emergency Protocol",
        ["< 20", "20–30", "30–35", "> 35", "20-30", "30-35"],
    ),
    (
        "docs/STRATEGY_LOGIC.md",
        "### Position Limits",
        ["≥ 10% of NAV", ">= 10% of NAV"],
    ),
]


def _extract_section(text: str, heading: str) -> str:
    """Return the text from `heading` until the next heading of equal or higher level."""
    level = len(re.match(r"^(#+)", heading).group(1))
    pattern = re.compile(r"^#{1," + str(level) + r"}\s", re.MULTILINE)
    start = text.find(heading)
    assert start != -1, f"Heading not found: {heading!r}"
    # find next same-or-higher heading after the start
    search_start = start + len(heading)
    match = pattern.search(text, search_start)
    end = match.start() if match else len(text)
    return text[start:end]


def test_no_duplicated_thresholds():
    errors = []
    for rel_path, heading, forbidden in CONSISTENCY_RULES:
        content = (ROOT / rel_path).read_text(encoding="utf-8")
        section = _extract_section(content, heading)
        for value in forbidden:
            if value in section:
                errors.append(
                    f"{rel_path} §{heading!r}: found duplicated threshold {value!r} "
                    f"— update config/gates.yml instead."
                )
    assert not errors, "\n".join(errors)
