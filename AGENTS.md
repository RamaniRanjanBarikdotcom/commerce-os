# Commerce OS

Multichannel seller platform: one product catalog, AI-written listings,
sync to Amazon, eBay, Kaufland, OTTO and Shopify.
Spec: docs/SPEC.md. Progress log: docs/PROGRESS.md. Decisions: docs/DECISIONS.md.

## Stack
- apps/web: Next.js (TypeScript), Tailwind, shadcn/ui, TanStack Table
- apps/api: Python 3.12 or newer, FastAPI, SQLAlchemy 2, Alembic, Pydantic v2
- apps/worker: Temporal workers in Python
- packages/connectors: one subpackage per marketplace
- PostgreSQL with row-level security, Redis

## Commands (defined in the Makefile)
make setup | make dev | make test | make lint | make migrate

## Rules
1. Read the relevant sections of docs/SPEC.md before coding. If the spec and the request conflict, stop and ask.
2. For tasks touching more than 3 files, write a plan first and wait for approval.
3. Add tests with every change. Run `make test` and `make lint` and fix failures before finishing.
4. Give every table a tenant_id and a row-level security policy, and add a test that a second tenant cannot read it.
5. Call marketplaces only from packages/connectors, through the shared Connector interface.
6. Keep secrets, tokens and real seller data out of code, logs, tests and fixtures. Read them from environment variables and list them in .env.example.
7. Change the database only through Alembic migrations.
8. A listing can become "validated" only after the validators in apps/api/app/validation pass.
9. Add a dependency only after writing one line in docs/DECISIONS.md.
10. Finish every task by updating docs/PROGRESS.md with what changed and what is next.
