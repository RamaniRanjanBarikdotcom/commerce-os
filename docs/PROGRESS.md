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
- T01b (web and CI) is done on the same branch, `task/T01-scaffold`:
  - Minimal Next.js 16 app in `apps/web`: one placeholder page, strict TypeScript, ESLint, Prettier and a Vitest smoke test; Node 22 pinned in `.nvmrc`; exact npm versions.
  - Makefile `setup`, `dev`, `test` and `lint` now include the web commands.
  - `.github/workflows/ci.yml`: Python, web, `docker compose config` and gitleaks jobs; actions pinned by SHA; `contents: read`; no secrets.
  - Scaffold tests also check the npm scripts the Makefile calls, the Node pin and the CI rules.
- T01 acceptance: `make setup` and `make test` pass on a clean checkout. "CI is green" is checked once the branch is pushed and a pull request is opened.
- Next: T02 API skeleton (also adds import-linter and pytest-asyncio, and splits the uv project into workspace members).

## Open items

- Check whether any channel goes straight from submitted to live (eBay publish first). Resolve in T21 after reading the eBay documentation.
- `npm audit` has 16 moderate findings from one minimatch advisory in the ESLint toolchain (dev-only); revisit when eslint-config-next updates (see docs/DECISIONS.md).
- ESLint stays on 9.39.5 (marked "no longer supported" by npm) until the React, import and jsx-a11y plugins accept ESLint 10.
- Re-check ESLint 10 and TypeScript 7 support when the plugins allow it (by T09).
- The no-symlinks test cannot be exercised on this exFAT drive (it cannot hold symlinks); it will run for real in CI on Linux.

## Notes for later tasks

- T08: when T08 is built, test signed upload URLs against SeaweedFS first. If they don't work, tell the project owner before working around it.
- T08: SeaweedFS's S3 gateway runs without credentials in T01; configure credentials (`-s3.config`) in T08.
- T02 and T20: split the root uv project into workspace members for `apps/api` and `apps/worker`.
