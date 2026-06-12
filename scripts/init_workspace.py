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

from dotenv import load_dotenv

load_dotenv()

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


def install_hook(hook_type: str = "pre-commit") -> None:
    """Install sanitisation guard hook.

    Args:
        hook_type: Type of hook to install ("pre-commit" or "pre-push")
    """
    git_dir = REPO_ROOT / ".git"
    if not git_dir.is_dir():
        print(f"  Skipping {hook_type} hook install — no .git directory.")
        return

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    source = REPO_ROOT / "scripts" / "hooks" / hook_type
    target = hooks_dir / hook_type

    if not source.exists():
        print(f"  Skipping {hook_type} hook install — tracked hook missing.")
        return

    source.chmod(source.stat().st_mode | 0o111)
    rel = os.path.relpath(source, hooks_dir)

    if target.is_symlink() or target.exists():
        try:
            if target.resolve() == source.resolve():
                return  # already ours — idempotent no-op
        except OSError:
            pass
        print(f"  A {hook_type} hook already exists; NOT overwriting it.")
        print(f"  To enable the sanitisation guard, run:  ln -sf {rel} {target}")
        return

    try:
        target.symlink_to(rel)
        print(f"  Installed {hook_type} sanitisation guard ({target.relative_to(REPO_ROOT)} -> {rel}).")
    except OSError:
        print(f"  Could not create symlink; to enable the guard run:  ln -sf {rel} {target}")


def main() -> None:
    print("Initialising workspace...")
    create_dirs()
    copy_templates()
    ensure_env()
    check_fred_key()
    install_hook("pre-commit")
    install_hook("pre-push")
    print("Workspace ready.")


if __name__ == "__main__":
    main()
    sys.exit(0)
