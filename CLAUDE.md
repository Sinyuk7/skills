# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Scope

This repo is a collection of agent skills under `./skills/`. Each skill is self-contained (`SKILL.md` + optional `workflows/`, `knowledge/`, `templates/`, `schemas/`, `evals/`, `scripts/`). Do not enumerate skills here — read `./skills/` directly when you need the current set.

## Authoritative Design Policy

**Always read [AGENTS.md](AGENTS.md) alongside this file before creating, editing, or refactoring any skill.** It is the single source of truth for:

- SKILL type system and routing rules
- Positive boundary definition / no-knowledge-coupling invariant
- Evidence-precedes-answer discipline
- Reasoning-vs-execution split
- Required file structure, anti-patterns, acceptance criteria

Do not restate AGENTS.md content in individual SKILL.md files — link to it.

## Development Loop

Edits to `./skills/<name>/` go live in host agents via symlink sync:

```bash
./init.sh --dry-run              # preview
./init.sh                        # sync to default agents (.agents .claude .codex .codemaker)
./init.sh --claude               # single target
./init.sh --all                  # every known agent
./init.sh --refresh              # drop same-named entries first (use after rename/delete)
./init.sh --refresh --kill-stale # also terminate stale CodeMaker/Qzhddr processes
```

`init.sh` only adds; plain re-runs will not remove renamed or deleted skills — use `--refresh`. Host agents cache `SKILL.md` per session, so on-disk edits may require a session restart (or `--kill-stale` for CodeMaker) to take effect. Requires Bash 4+.

## Conventions

- Edit skills in-place under `./skills/`; symlinks point here, so changes are live after reload.
- Keep `SKILL.md` compact — push procedures into `workflows/`, policy into `knowledge/`, shapes into `templates/`.
- Ship evals with behavior changes; "refactor without evals" is a non-acceptance per AGENTS.md §11.
