# Progress

## Current status

- Setup on `main`: AGENTS.md, CLAUDE.md, .gitignore, docs/SPEC.md (with approved spec edits 1 and 2), docs/PROGRESS.md and docs/DECISIONS.md.
- T01 is split into T01a and T01b because it would change more than about 600 hand-written lines.
- T01a (repository, Python, Makefile, Compose) is done on `task/T01-scaffold`:
  - `.gitattributes` keeps LF line endings; binaries are never converted.
  - Root uv project on Python 3.12 with ruff, mypy (strict), pytest and pip-audit locked in `uv.lock`.
  - Section 3 folder tree, with `__init__.py` for Python packages and `.gitkeep` elsewhere.
  - Docker Compose: Postgres 17 + pgvector, Redis, Temporal dev server, SeaweedFS, Keycloak, Mailpit; pinned tags, healthchecks, named volumes only, ports on 127.0.0.1.
  - Makefile with the nine section 13 targets (placeholders exit 1, seed exits 0).
  - Scaffold tests in `tests/test_scaffold.py`.
- Next: T01b (minimal Next.js app in `apps/web`, web commands in the Makefile, GitHub Actions CI).

## Open items

- Check whether any channel goes straight from submitted to live (eBay publish first). Resolve in T21 after reading the eBay documentation.
- The no-symlinks test cannot be exercised on this exFAT drive (it cannot hold symlinks); it will run for real in CI on Linux.

## Notes for later tasks

- T08: when T08 is built, test signed upload URLs against SeaweedFS first. If they don't work, tell the project owner before working around it.
- T08: SeaweedFS's S3 gateway runs without credentials in T01; configure credentials (`-s3.config`) in T08.
- T02 and T20: split the root uv project into workspace members for `apps/api` and `apps/worker`.
