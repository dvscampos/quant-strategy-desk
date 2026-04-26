"""Phase 7 verdict scoring and agent performance tracking."""

from __future__ import annotations

from .models import AgentScore, Verdict, VerdictCategory, VerdictResult

# Score map
SCORES = {
    VerdictCategory.LEGITIMATE: +2.0,
    VerdictCategory.APPROVE: 0.0,
    VerdictCategory.NOISE: -1.0,
    VerdictCategory.NA: -0.5,
}


def categorise_verdict(verdict: Verdict) -> VerdictCategory:
    """Determine category from result and any pre-set category."""
    if verdict.category:
        return verdict.category
    if verdict.result == VerdictResult.APPROVE:
        return VerdictCategory.APPROVE
    if verdict.result == VerdictResult.NA:
        return VerdictCategory.NA
    # FLAG — default to noise unless explicitly marked legitimate
    return VerdictCategory.NOISE


def score_session(verdicts: list[Verdict]) -> dict[str, float]:
    """Score a single session's verdicts. Returns {agent: score_delta}."""
    scores = {}
    for v in verdicts:
        cat = categorise_verdict(v)
        scores[v.agent] = SCORES[cat]
    return scores


def compute_cumulative(all_verdicts: list[Verdict]) -> list[AgentScore]:
    """Compute cumulative scores across all sessions."""
    agents: dict[str, AgentScore] = {}

    for v in all_verdicts:
        if v.agent not in agents:
            agents[v.agent] = AgentScore(agent=v.agent)

        a = agents[v.agent]
        cat = categorise_verdict(v)

        if cat == VerdictCategory.APPROVE:
            a.total_approve += 1
        elif cat == VerdictCategory.LEGITIMATE:
            a.total_flag += 1
            a.legitimate_count += 1
        elif cat == VerdictCategory.NOISE:
            a.total_flag += 1
            a.noise_count += 1
        elif cat == VerdictCategory.NA:
            a.total_na += 1

        a.cumulative_score += SCORES[cat]

    # Assign tiers
    for a in agents.values():
        a.tier = _assign_tier(a)

    return sorted(agents.values(), key=lambda x: -x.cumulative_score)


def _assign_tier(a: AgentScore) -> str:
    """Assign tier based on cumulative performance."""
    total_sessions = a.total_approve + a.total_flag + a.total_na
    if total_sessions == 0:
        return "New"

    if a.noise_count == 0 and a.total_na <= 1:
        return "Reliable"
    if a.noise_count <= 1 and a.total_na <= 2:
        return "Clean"
    if a.cumulative_score < -2.0:
        return "Low Signal"
    if a.noise_count > 0 and a.legitimate_count > 0:
        return "Mixed"
    if a.total_na >= total_sessions * 0.5:
        return "Low Signal"
    return "Improving"


def format_scores_table(scores: list[AgentScore], session_count: int) -> str:
    """Format cumulative scores as a markdown table."""
    lines = [
        f"## Signal-to-Noise Ratio (after {session_count} sessions)",
        "",
        "| Agent | APR | FLAG | N/A | Noise | Legit | Score | Tier |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for a in scores:
        lines.append(
            f"| {a.agent} | {a.total_approve} | {a.total_flag} | {a.total_na} "
            f"| {a.noise_count} | {a.legitimate_count} | {a.cumulative_score:+.1f} | {a.tier} |"
        )
    return "\n".join(lines)


def rotation_priority(scores: list[AgentScore]) -> list[str]:
    """Return agents ordered by score (highest first) for rotation preference."""
    return [a.agent for a in scores if a.tier not in ("Low Signal",)]
