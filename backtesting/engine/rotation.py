"""Strike Team rotation enforcement."""

from __future__ import annotations

from pathlib import Path

import yaml


def _load_agent_config() -> dict:
    config_path = Path(__file__).parent / "config" / "agents.yml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def get_consecutive_count(
    agent: str, role: str, history: list[dict]
) -> int:
    """Count how many consecutive recent sessions this agent filled this role (or any role)."""
    count = 0
    for entry in reversed(history):
        if entry.get(role) == agent or agent in entry.values():
            count += 1
        else:
            break
    return count


def get_agent_consecutive(agent: str, history: list[dict]) -> int:
    """Count consecutive sessions where agent appeared in ANY rotating role."""
    count = 0
    for entry in reversed(history):
        roles = {k: v for k, v in entry.items() if k not in ("session", "date", "notes", "risk")}
        if agent in roles.values():
            count += 1
        else:
            break
    return count


def valid_candidates(
    role: str,
    history: list[dict],
    already_assigned: dict[str, str] | None = None,
    config: dict | None = None,
) -> list[str]:
    """Return agents eligible for a role given rotation rules and current assignments."""
    if config is None:
        config = _load_agent_config()

    if already_assigned is None:
        already_assigned = {}

    role_config = config["roles"].get(role, {})

    if role == "risk":
        return [role_config["fixed"]]

    # Get pool
    if role == "challenger":
        # Any agent not already assigned this session
        all_agents = set()
        for r in ["macro", "signal", "architect"]:
            all_agents.update(config["roles"][r]["pool"])
        # Add Phase 7 agents not in any pool
        for a in config.get("phase7_agents", []):
            all_agents.add(a["name"])
        pool = list(all_agents)
    else:
        pool = role_config.get("pool", [])

    max_consec = role_config.get("max_consecutive", 2)
    exclusivity = config.get("exclusivity", [])
    assigned_agents = set(already_assigned.values())

    eligible = []
    for agent in pool:
        # Skip if already assigned this session
        if agent in assigned_agents:
            continue

        # Skip if exclusive agent already used in another role
        if agent in exclusivity and agent in assigned_agents:
            continue

        # Check consecutive limit
        consec = get_agent_consecutive(agent, history)
        if consec >= max_consec:
            continue

        eligible.append(agent)

    return eligible


def validate_team(
    team: dict[str, str],
    history: list[dict],
    config: dict | None = None,
) -> list[str]:
    """Validate a proposed team. Returns list of violations (empty = valid)."""
    if config is None:
        config = _load_agent_config()

    violations = []
    exclusivity = config.get("exclusivity", [])

    # Check risk is fixed
    if team.get("risk") != config["roles"]["risk"]["fixed"]:
        violations.append(f"Risk must be {config['roles']['risk']['fixed']}")

    # Check exclusivity — no agent in multiple roles
    agents_used = {}
    for role, agent in team.items():
        if role == "risk":
            continue
        if agent in agents_used:
            violations.append(f"{agent} assigned to both {agents_used[agent]} and {role}")
        agents_used[agent] = role

    # Check exclusive agents only fill one slot
    for agent in exclusivity:
        roles_filled = [r for r, a in team.items() if a == agent and r != "risk"]
        if len(roles_filled) > 1:
            violations.append(f"{agent} (exclusive) fills multiple roles: {roles_filled}")

    # Check pool membership
    for role in ["macro", "signal", "architect"]:
        if role in team:
            pool = config["roles"][role]["pool"]
            if team[role] not in pool:
                violations.append(f"{team[role]} not in {role} pool: {pool}")

    # Check consecutive limits
    for role in ["macro", "signal", "architect", "challenger"]:
        if role in team:
            agent = team[role]
            consec = get_agent_consecutive(agent, history)
            max_c = config["roles"].get(role, {}).get("max_consecutive", 2)
            if consec >= max_c:
                violations.append(f"{agent} at {consec} consecutive (max {max_c}) — must rotate")

    return violations


def record_assignment(
    team: dict[str, str],
    session_number: int,
    session_date: str,
    history: list[dict],
    notes: str = "",
) -> list[dict]:
    """Add a new entry to rotation history. Returns updated history."""
    entry = {
        "session": session_number,
        "date": session_date,
        **team,
        "notes": notes,
    }
    return history + [entry]


def consecutive_summary(history: list[dict], config: dict | None = None) -> list[dict]:
    """Current consecutive count per recently-active agent."""
    if config is None:
        config = _load_agent_config()

    # Collect all agents that have appeared
    seen = set()
    for entry in history:
        for k, v in entry.items():
            if k not in ("session", "date", "notes"):
                seen.add(v)

    result = []
    for agent in sorted(seen):
        if agent == config["roles"]["risk"]["fixed"]:
            result.append({"agent": agent, "consecutive": "N/A (fixed)", "status": "Fixed role"})
            continue
        consec = get_agent_consecutive(agent, history)
        if consec > 0:
            status = "**MUST rotate**" if consec >= 2 else "Available"
            result.append({"agent": agent, "consecutive": consec, "status": status})

    return result
