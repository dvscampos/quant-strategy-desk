#!/usr/bin/env python3
"""
Deterministic workspace plumbing. Idempotent: safe to run twice.
Creates local/ subdirectories, copies templates if targets absent, checks FRED key.
Never prompts for or echoes secrets.
"""

import os
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
LOCAL = REPO_ROOT / "local"
TEMPLATES = LOCAL / "templates"
ENV_FILE = REPO_ROOT / ".env"
ENV_EXAMPLE = REPO_ROOT / ".env.example"

SUBDIRS = [
    LOCAL / "brainstorms",
    LOCAL / "snapshots",
    LOCAL / "retros",
    LOCAL / "templates",
]

TEMPLATE_MAP = {
    "PORTFOLIO.template.md": "PORTFOLIO.md",
    "HYPOTHESIS_LOG.template.md": "HYPOTHESIS_LOG.md",
    "SESSIONS.template.md": "SESSIONS.md",
    "AGENT_PERFORMANCE.template.md": "AGENT_PERFORMANCE.md",
    "ROTATION_LOG.template.md": "ROTATION_LOG.md",
}


def create_dirs() -> None:
    for d in SUBDIRS:
        d.mkdir(parents=True, exist_ok=True)
    (LOCAL / ".gitkeep").touch(exist_ok=True)
    (LOCAL / "brainstorms" / ".gitkeep").touch(exist_ok=True)
    (LOCAL / "snapshots" / ".gitkeep").touch(exist_ok=True)


def copy_templates() -> None:
    for template_name, target_name in TEMPLATE_MAP.items():
        src = TEMPLATES / template_name
        dst = LOCAL / target_name
        if dst.exists():
            continue
        if not src.exists():
            print(f"  WARNING: template {template_name} not found — skipping.")
            continue
        shutil.copy2(src, dst)
        print(f"  Created {dst.relative_to(REPO_ROOT)}")


def ensure_env() -> None:
    if not ENV_FILE.exists():
        if ENV_EXAMPLE.exists():
            shutil.copy2(ENV_EXAMPLE, ENV_FILE)
            print(f"  Created .env from .env.example — fill in your values.")
        else:
            print("  WARNING: .env.example not found; skipping .env creation.")


def check_fred_key() -> None:
    fred_key = os.environ.get("FRED_API_KEY", "")
    if not fred_key:
        try:
            env_content = ENV_FILE.read_text() if ENV_FILE.exists() else ""
            for line in env_content.splitlines():
                line = line.strip()
                if line.startswith("FRED_API_KEY="):
                    raw = line.split("=", 1)[1]
                    fred_key = raw.split("#")[0].strip()
                    break
        except OSError:
            pass

    if not fred_key:
        print()
        print("  FRED_API_KEY not set in .env — live fetches will fail until you add it.")
        print("  Sign up: https://fred.stlouisfed.org/docs/api/api_key.html")
        print("  Then add FRED_API_KEY=<your_key> to .env. Continuing setup.")
        print()


def main() -> None:
    print("Initialising workspace...")
    create_dirs()
    copy_templates()
    ensure_env()
    check_fred_key()
    print("Workspace ready.")


if __name__ == "__main__":
    main()
    sys.exit(0)
