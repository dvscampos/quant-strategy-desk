# Sharing This Framework

> **Disclaimer**: Nothing in this repository constitutes financial, tax, or investment advice. It is a personal framework tool. Always seek qualified advice for your own jurisdiction.

## What's shared vs what's yours

This repository contains two layers:

| Layer | Location | Tracked by git? |
|---|---|---|
| **Framework** — CLAUDE.md, agents, scripts, docs, templates, tests | everywhere except `local/` | Yes |
| **Your personal data** — portfolio, investor profile, session files, snapshots | `local/` | No — gitignored |

The `local/` directory is excluded from git by a single rule (`local/*` with a template allow-list). Your financial data stays on your machine by default.

## How to use this for your own investing

1. Clone the repo: `git clone <url> my-investments && cd my-investments`
2. Start Claude Code and open this directory.
3. Claude will detect the missing `local/INVESTOR_PROFILE.md` and run the 11-question onboarding.
4. After onboarding, run `python scripts/init_workspace.py` to set up `local/` directories and copy starter templates.
5. Add your `FRED_API_KEY` to `.env` (see `.env.example` for all keys).
6. Run your first War Room session with `/war-room`.

Your `local/` directory is your personal workspace. The framework files are the shared engine.

## How to contribute framework improvements back

Make your framework changes (agents, scripts, docs, templates — anything outside `local/`), then:

```bash
git diff              # your diff will be clean — local/ is gitignored
git add <files>
git push origin your-branch
# open a PR
```

Your portfolio and session history never appear in the diff by construction.

## Backup posture

`local/` is **not under git**. Before your first live session, enable continuous backup:

- **macOS**: Time Machine (automatic if configured)
- **Windows**: File History
- **Linux**: restic, rsync, or similar
- **Cross-platform alternative**: Dropbox / iCloud — move `local/` into a synced folder and symlink it here

Optional: `cd local && git init` treats `local/` as its own repo. Useful if you want commit history for your trades. Not required by the framework.

## Pre-push checklist

Before `git push`, verify:

- [ ] `git status` is clean (no unexpected tracked changes)
- [ ] `git ls-files | grep "^local/"` returns empty (no personal files tracked)
- [ ] `.env` does not appear in `git status` (should be gitignored)
- [ ] No ticker symbols, NAV amounts, or personal data in your framework diffs

## Security reminder

`.env` and `local/*` never leave your machine unless you explicitly override `.gitignore`. Never disable the `local/*` rule before a push. The pre-push checklist above is your last line of defence.

## Migration note (Obsidian users)

If you use Obsidian to view your portfolio files, moving files to `local/` will break internal wiki-links. After migration, open Obsidian and use **Edit → Find and Replace** (or the Obsidian URI handler) to update links from `PORTFOLIO.md` to `local/PORTFOLIO.md`, etc.
