# Commerce OS

Multichannel seller platform: one product catalog, AI-written listings, and sync to
eBay, Kaufland, Amazon, OTTO and Shopify. The specification is [docs/SPEC.md](docs/SPEC.md);
progress and decisions are in [docs/PROGRESS.md](docs/PROGRESS.md) and
[docs/DECISIONS.md](docs/DECISIONS.md). Rules for coding agents are in [AGENTS.md](AGENTS.md).

## Prerequisites

- Git
- [uv](https://docs.astral.sh/uv/) (downloads Python 3.12 from `.python-version`)
- GNU make
- Docker with Docker Compose v2

## Quick start

```sh
make setup   # install Python tools, start local services, seed data
make test    # run the tests
make lint    # ruff, ruff format check, mypy (strict)
```

`make dev` starts the local services. `make eval`, `make e2e`, `make openapi` and
`make migrate` fail on purpose until the tasks that build them (T19, T09, T02, T03).

## Local services

All ports bind to 127.0.0.1. Defaults are development-only; copy `.env.example` to `.env`
to change them. Data is kept in named Docker volumes (`docker compose down -v` deletes it).

| Service | Port | Purpose |
| --- | --- | --- |
| PostgreSQL 17 with pgvector | 5432 | Main database |
| Redis | 6379 | Cache, locks, rate limits |
| Temporal dev server | 7233, UI 8233 | Background workflows |
| SeaweedFS | 8333 | Local S3-compatible object storage |
| Keycloak | 8080 | Development identity provider |
| Mailpit | SMTP 1025, UI 8025 | Mail catcher |

## Windows notes

- This repository may live on a drive without file ownership (for example exFAT). Git then
  needs `safe.directory` for this folder, and uv warns that it falls back to copying files.
- Use named Docker volumes only and do not add symlinks (see docs/DECISIONS.md).
