# Commerce OS: Build Specification for Claude Code and Codex

Nov 4, 2026 · @Ramani ranjan

## 1. How to use this spec with Claude Code or Codex

Do not paste this whole document into an agent. Put the permanent rules in files inside the repository, then give the agent one small task at a time from section 14, and review each result before the next.

**Setup, once**

1. Create a Git repository named `commerce-os` and save this document in it as `docs/SPEC.md` (export the doc as Markdown).
2. Add an `AGENTS.md` file at the repository root with the template below. Community guides report that Codex reads `AGENTS.md`, that Claude Code reads `CLAUDE.md`, and that a `CLAUDE.md` containing the single line `@AGENTS.md` pulls the same rules into Claude Code. Check each tool's own documentation to confirm this for the version you use.
3. Add empty `docs/PROGRESS.md` and `docs/DECISIONS.md` files. The agent updates the first after every task and records any new dependency in the second.
4. Create test accounts for every marketplace (eBay sandbox, OTTO sandbox, a Kaufland test account, your own Amazon seller account). Never give an agent real customer credentials.

**For every task**

1. Ask the agent for a plan first and read it. For anything touching more than 3 files, do not let it write code until you agree with the plan.
2. Let it implement with tests, then run the tests yourself.
3. Read the diff. Check marketplace code against the official documentation and the sandbox, because agents often write plausible but wrong API calls.
4. Commit on a branch per task, merge, and move to the next task.

**Which tool for what.** Claude Code runs interactively on your machine, which suits architecture-heavy tasks where you want to steer (database schema, workflows, connector interface). Codex can run tasks asynchronously in its own sandbox and return a pull request, which suits well-specified, independent tasks (one connector's tests, one screen, one validator). You can use either for any task; the rules file keeps them consistent.

**`AGENTS.md` template**

```markdown
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
```

**Task prompt template**

```markdown
Task: <id and title from section 14>
Read first: docs/SPEC.md sections <numbers>
Goal: <one sentence>
Build: <bullets>
Acceptance: <bullets copied from section 14>
Constraints: follow AGENTS.md; ask before adding a dependency.
Reply first with a plan only.
```

## 2. Build scope

The build target is one end-to-end path that works against marketplace sandboxes: a seller signs up, connects a channel, imports products, gets AI-written drafts, passes compliance checks, publishes, and then sees status, orders and stock stay in sync. This spec follows the product plan in the earlier document, "Commerce OS: Multichannel Seller Platform Plan", and where the two differ this one wins for building.

**MVP acceptance test (the whole MVP is done when this passes)**

1. A new seller registers, creates a workspace and invites a teammate.
2. They connect an eBay sandbox account and a Kaufland test account.
3. They import a CSV of 100 products, choose the "Ink and toner" or "Luggage" pack, and the system proposes channel categories and attributes.
4. AI drafts German and English content. The seller approves some drafts and edits others.
5. A listing with missing legal data (for example EU Responsible Person) cannot be published, and the work queue explains why.
6. Publishing 100 listings to both sandboxes completes in the background, and each listing shows live, in review or rejected with a plain-language reason.
7. A sandbox order on one channel reduces stock on the other within 2 minutes, and the reconciliation job reports zero drift.
8. Amazon and OTTO connectors pass the same contract tests against recorded responses, then run against real sandboxes or test accounts once approved.

**Defaults the agent should assume (do not ask about these)**

| Topic | Default |
| --- | --- |
| Order of connectors | eBay, then Kaufland, then Amazon, then OTTO; Shopify as a CSV import first |
| Languages | Content in German and English; interface in English first, German next |
| Currency and region | EUR; deployment in one EU region |
| Tenants | One workspace per seller or agency; users belong to one or more workspaces |
| Billing | None in MVP. Plans are recorded as a field and invoiced by hand |
| Time zone | Store all times in UTC; show in the user's time zone |
| IDs | UUIDs for every table |
| Money | Integer minor units (cents) plus a currency code, never floats |

**Not in the MVP:** repricing, advertising, forecasting, automation gallery, public API, mobile app, other product types, other regions, in-app payments.

**Glossary (use these names in code)**

| Term | Meaning |
| --- | --- |
| Tenant | A seller or agency workspace; owns all data |
| Channel | A marketplace type: `ebay`, `kaufland`, `amazon`, `otto`, `shopify` |
| Channel account | One tenant's connection to one channel and country |
| Product | The master record, independent of any marketplace |
| Variant | A sellable SKU of a product (size, colour) with EAN and cost |
| Pack | A product-type definition: attributes, rules and checks (for example `ink_toner`) |
| Listing | One variant on one channel account, with a state machine |
| Content | Text for a product in one language |
| Compliance record | Legal data for a product or tenant (manufacturer, EU Responsible Person, packaging number) |
| Workflow | A durable background process, such as publishing a listing |

## 3. Repository layout and conventions

Use one repository with clear boundaries, so an agent working on one area cannot easily break another. Category packs live as data files, and marketplace code lives only in the connectors package.

```text
commerce-os/
  AGENTS.md  CLAUDE.md  README.md  Makefile  docker-compose.yml  .env.example
  docs/
    SPEC.md  PROGRESS.md  DECISIONS.md
  apps/
    web/                      Next.js app (TypeScript)
      src/app/                routes (see section 11)
      src/components/         shared UI, built on shadcn/ui
      src/lib/                API client, i18n, formatting
    api/                      FastAPI service (Python)
      app/
        main.py  config.py  deps.py
        tenancy/              workspaces, users, roles, row-level security helpers
        catalog/              products, variants, attributes, images, CSV import
        packs/                loads pack definitions, validates attribute values
        mapping/              category and attribute mapping engine
        content/              AI drafts, approval, versions
        validation/           schema, channel-rule and compliance validators
        compliance/           manufacturer, EU Responsible Person, packaging, VAT data
        listings/             listing state machine and publish requests
        inventory/            stock ledger, buffers, allocation
        orders/               normalised orders, shipments, returns
        channels/             channel accounts, token storage, health
        queue/                work-queue items shown on the home screen
      alembic/                database migrations
      tests/
    worker/                   Temporal workers
      workflows/              publish_listing, sync_stock, import_orders, reconcile
      activities/             small steps that call the connectors and the database
  packages/
    connectors/
      base.py                 Connector protocol and shared types (section 7)
      ebay/  kaufland/  amazon/  otto/  shopify/
      testing/                recorded responses and a fake connector
    packs/
      ink_toner.yaml  luggage.yaml        pack definitions as data (section 15)
    ai/
      prompts/  schemas/  evals/          versioned prompts, output schemas, test sets
  infra/
    terraform/  docker/
```

**Coding conventions**

| Area | Rule |
| --- | --- |
| Python | Version 3.12 or newer, type hints everywhere, Ruff for lint and format, mypy or pyright in strict mode for `app/` and `packages/` |
| TypeScript | Strict mode, ESLint and Prettier, no `any` without a comment explaining why |
| Python packages | One workspace managed with `uv`; record any change of tool in `docs/DECISIONS.md` |
| Configuration | Environment variables read through one settings class; every variable listed in `.env.example` |
| Errors | Typed domain errors, mapped once to HTTP responses in `main.py`; connectors raise `ChannelError` subclasses (rate limit, auth expired, validation, transient) |
| Logging | Structured JSON with `tenant_id`, `request_id`, `workflow_id`; never log tokens, buyer names or addresses |
| API | Under `/api/v1`, JSON only, cursor pagination, an `Idempotency-Key` header on every create or publish call |
| Database | Snake-case tables, UUID primary keys, `created_at` and `updated_at` in UTC on every table, soft delete with `deleted_at` for products and variants |
| Git | Conventional commit messages, one branch per task from section 14, small pull requests |

## 4. Tech stack

These are firm choices so the agent does not drift between tools. Pin exact versions in lockfiles at the start of the project, using the latest stable releases at that time, and record any change in `docs/DECISIONS.md`.

| Concern | Choice | Notes |
| --- | --- | --- |
| Web framework | Next.js with the App Router, TypeScript | Server components for read-heavy pages, client components for grids and editors |
| UI | Tailwind CSS, shadcn/ui (Radix), lucide icons | Tokens in section 11 |
| Data grid | TanStack Table with virtualised rows | Bulk editing, saved views, column chooser |
| Data fetching | TanStack Query, API client generated from the OpenAPI file with `openapi-typescript` | Never hand-write API types |
| Forms | react-hook-form with zod | Same field rules as the backend where possible |
| Interface language | next-intl | English first, German second; no hard-coded strings |
| API | Python 3.12 or newer, FastAPI, Pydantic v2 | OpenAPI file generated and committed |
| Database access | SQLAlchemy 2 (async) with asyncpg, Alembic migrations | Row-level security policies live in migrations |
| Database | PostgreSQL with JSONB and the pgvector extension | One database; no separate vector store |
| Cache, locks, rate limits | Redis | Token buckets per tenant and channel account |
| Background workflows | Temporal with the Python SDK | Dev server in Docker Compose; hosting choice recorded later |
| HTTP client | httpx | Used only inside connectors |
| Validation of marketplace schemas | `jsonschema` plus a small extension for Amazon's custom vocabulary | Cached per product type and marketplace |
| Object storage | S3-compatible; MinIO in local development | Images, import files, stored publish payloads |
| Authentication | OIDC behind an `AuthProvider` interface; Keycloak in Docker Compose for development, a managed provider in production | Choose the production provider later; the interface keeps that cheap |
| AI | An `LLMClient` interface with the provider SDK behind it | Model names come from configuration (`LLM_MODEL_FAST`, `LLM_MODEL_WRITER`), never from code |
| Observability | OpenTelemetry, structlog, Sentry | Trace one listing across API, workflow and connector |
| Testing | pytest with pytest-asyncio, respx or recorded fixtures for HTTP, Testcontainers for Postgres and Redis; Vitest and Playwright for the web app | Rules in section 13 |
| Infrastructure | Docker, Terraform, GitHub Actions | EU region only |

**Do not** (these are the common agent mistakes for this project)

- Do not split into microservices. Modules in `apps/api` talk through Python function calls.
- Do not add GraphQL, a second database, Kafka or n8n to the core path.
- Do not call a marketplace from anywhere except `packages/connectors`.
- Do not store money as floats, or times without a time zone.
- Do not hard-code marketplace category IDs or attribute names in code. They belong in mapping tables.
- Do not let the AI write legal or safety text freely. It selects from approved templates (section 9).

## 5. Architecture and module boundaries

The system is three deployable parts (web app, API, worker) built from one codebase with strict one-way dependencies between modules. The earlier plan document has the layer diagram; this section gives the rules the code must follow.

**How a request flows.** The web app calls the API. The API checks the user, writes to the database and, for anything slow, starts a Temporal workflow and returns a job id. The worker runs the workflow's activities, which call modules and connectors and write results to the database. The web app reads the results through the API.

| Module | May depend on | Must not depend on |
| --- | --- | --- |
| `tenancy` | nothing | everything else |
| `packs` | `tenancy` | catalog, channels |
| `catalog` | `tenancy`, `packs` | content, listings, channels |
| `channels` (accounts, credential vault) | `tenancy` | catalog, listings |
| `compliance` | `tenancy`, `catalog` | listings, channels |
| `mapping` | `catalog`, `packs`, the schema cache tables, `LLMClient` | listings |
| `content` | `catalog`, `packs`, `LLMClient` | listings, channels |
| `validation` | `catalog`, `content`, `compliance`, `mapping`, `packs` | channels, workflows |
| `inventory` | `catalog` | listings |
| `listings` | `validation`, `mapping`, `content`, `catalog`, `inventory` (read only) | connectors directly |
| `orders` | `inventory`, `catalog` | listings |
| `queue` (work items) | reads from any module through events | writing to other modules' tables |
| worker activities | any module, and the connectors | the web layer |

Only worker activities and the channel test endpoint may import `packages/connectors`. Enforce all of this in CI with an import-checking tool such as `import-linter`, and fail the build on a circular dependency.

**Listing status.** A listing moves through a fixed set of states. Only the `publish_listing` workflow and the status-polling step may change them, and every change writes a row to `listing_events`.

&#91;embedded content: listing status flow · 7 states\]

A live listing can also be ended by the seller (status `ended`, not drawn), and a suppressed listing returns to Live once the cause is fixed and the channel accepts it again.

## 6. Database schema

This is the starting schema for the first Alembic migration. Use text columns with CHECK constraints instead of Postgres enum types, because they are easier to change. Every table also has `created_at` and `updated_at timestamptz NOT NULL DEFAULT now()`, left out below to keep the listing short. Tables marked global have no `tenant_id`.

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE FUNCTION app_tenant() RETURNS uuid LANGUAGE sql STABLE AS
$$ SELECT NULLIF(current_setting('app.tenant_id', true), '')::uuid $$;

-- Identity and tenancy -------------------------------------------------
CREATE TABLE tenants (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  plan text NOT NULL DEFAULT 'pilot' CHECK (plan IN ('pilot','starter','growth','scale'))
);
CREATE TABLE users (                      -- global
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  auth_subject text NOT NULL UNIQUE,
  email text NOT NULL UNIQUE,
  display_name text
);
CREATE TABLE memberships (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  user_id uuid NOT NULL REFERENCES users(id),
  role text NOT NULL CHECK (role IN ('owner','editor','viewer','agency_manager')),
  UNIQUE (tenant_id, user_id)
);

-- Channels ---------------------------------------------------------------
CREATE TABLE channel_accounts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  channel text NOT NULL CHECK (channel IN ('ebay','kaufland','amazon','otto','shopify')),
  country char(2) NOT NULL,
  external_account_id text,
  display_name text NOT NULL,
  status text NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending','active','auth_expired','error','disabled')),
  credentials_encrypted bytea NOT NULL,   -- envelope-encrypted, never returned by the API
  credentials_key_id text NOT NULL,
  scopes text[] NOT NULL DEFAULT '{}',
  last_sync_at timestamptz,
  last_error text,
  UNIQUE (tenant_id, channel, country, external_account_id)
);

-- Packs and mapping --------------------------------------------------------
CREATE TABLE packs (                      -- global, loaded from packages/packs/*.yaml
  key text PRIMARY KEY,
  version int NOT NULL,
  definition jsonb NOT NULL
);
CREATE TABLE channel_category_maps (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid REFERENCES tenants(id),  -- NULL = shared default, set = tenant override
  channel text NOT NULL, country char(2) NOT NULL,
  pack_key text NOT NULL REFERENCES packs(key),
  channel_category_id text NOT NULL,
  channel_product_type text,              -- Amazon product type, where relevant
  confidence numeric(4,3),
  approved_by uuid REFERENCES users(id),
  approved_at timestamptz
);
CREATE TABLE channel_attribute_maps (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid REFERENCES tenants(id),
  channel text NOT NULL, country char(2) NOT NULL,
  pack_key text NOT NULL REFERENCES packs(key),
  internal_key text NOT NULL,
  channel_attribute text NOT NULL,
  transform jsonb NOT NULL DEFAULT '{}'   -- unit conversion, value mapping, formatting
);
CREATE TABLE channel_schemas_cache (      -- global
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  channel text NOT NULL, country char(2) NOT NULL,
  category_ref text NOT NULL, version text NOT NULL,
  schema jsonb NOT NULL, fetched_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (channel, country, category_ref, version)
);
CREATE TABLE category_embeddings (        -- global; vector size follows the chosen embedding model
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  channel text NOT NULL, country char(2) NOT NULL,
  category_id text NOT NULL, path text NOT NULL,
  embedding vector(1536) NOT NULL
);

-- Catalog ------------------------------------------------------------------
CREATE TABLE products (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  pack_key text NOT NULL REFERENCES packs(key),
  brand text, name text NOT NULL,
  source_text text,                       -- supplier description, datasheet text
  status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','ready','archived')),
  deleted_at timestamptz
);
CREATE TABLE variants (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  product_id uuid NOT NULL REFERENCES products(id),
  sku text NOT NULL, ean text,
  cost_minor bigint, currency char(3) NOT NULL DEFAULT 'EUR',
  weight_g int, options jsonb NOT NULL DEFAULT '{}',   -- colour, size
  deleted_at timestamptz,
  UNIQUE (tenant_id, sku)
);
CREATE TABLE attribute_values (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  product_id uuid NOT NULL REFERENCES products(id),
  variant_id uuid REFERENCES variants(id),
  key text NOT NULL, value jsonb NOT NULL, unit text,
  source text NOT NULL CHECK (source IN ('import','manual','ai','channel')),
  source_ref text                         -- file name, URL or model run id
);
CREATE UNIQUE INDEX attribute_values_uq ON attribute_values
  (tenant_id, product_id, COALESCE(variant_id, '00000000-0000-0000-0000-000000000000'), key);
CREATE TABLE images (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  product_id uuid NOT NULL REFERENCES products(id),
  storage_key text NOT NULL, position int NOT NULL DEFAULT 0,
  width int, height int
);

-- Content and compliance ---------------------------------------------------
CREATE TABLE contents (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  product_id uuid NOT NULL REFERENCES products(id),
  language char(2) NOT NULL, channel text,
  title text, bullets jsonb NOT NULL DEFAULT '[]', description text,
  keywords jsonb NOT NULL DEFAULT '[]',
  status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','approved','rejected','superseded')),
  author_type text NOT NULL CHECK (author_type IN ('human','ai')),
  model text, prompt_version text,
  source_facts jsonb NOT NULL DEFAULT '[]', -- which attribute keys each claim used
  version int NOT NULL DEFAULT 1,
  approved_by uuid REFERENCES users(id), approved_at timestamptz
);
CREATE TABLE compliance_records (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  scope text NOT NULL CHECK (scope IN ('tenant','product')),
  product_id uuid REFERENCES products(id),
  country char(2),
  kind text NOT NULL CHECK (kind IN ('manufacturer','eu_responsible_person','safety_text',
    'packaging_registration','dual_system','vat_id','ce_marking','food_info','other')),
  data jsonb NOT NULL,
  valid_from date, valid_to date
);

-- Listings -----------------------------------------------------------------
CREATE TABLE listings (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  channel_account_id uuid NOT NULL REFERENCES channel_accounts(id),
  variant_id uuid NOT NULL REFERENCES variants(id),
  status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','validated','submitted',
    'in_review','live','suppressed','rejected','ended')),
  channel_listing_id text,
  last_payload_hash text,
  rejection jsonb,                        -- raw channel error plus plain-language message
  published_at timestamptz,
  UNIQUE (channel_account_id, variant_id)
);
CREATE TABLE listing_payloads (           -- immutable history of what was sent
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  listing_id uuid NOT NULL REFERENCES listings(id),
  payload jsonb NOT NULL, response jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE listing_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  listing_id uuid NOT NULL REFERENCES listings(id),
  from_status text, to_status text NOT NULL,
  detail jsonb NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Stock ----------------------------------------------------------------------
CREATE TABLE stock_events (               -- append-only; never update or delete
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  variant_id uuid NOT NULL REFERENCES variants(id),
  kind text NOT NULL CHECK (kind IN ('received','sold','returned','adjusted','reserved','released')),
  quantity_delta int NOT NULL,
  channel_account_id uuid REFERENCES channel_accounts(id),
  reference text,
  idempotency_key text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, idempotency_key)
);
CREATE VIEW stock_current AS
  SELECT tenant_id, variant_id,
    COALESCE(SUM(quantity_delta) FILTER (WHERE kind IN ('received','sold','returned','adjusted')), 0) AS on_hand,
    COALESCE(SUM(quantity_delta) FILTER (WHERE kind IN ('reserved','released')), 0) AS reserved
  FROM stock_events GROUP BY tenant_id, variant_id;
CREATE TABLE channel_stock_settings (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  variant_id uuid NOT NULL REFERENCES variants(id),
  channel_account_id uuid NOT NULL REFERENCES channel_accounts(id),
  buffer int NOT NULL DEFAULT 0,
  mode text NOT NULL DEFAULT 'shared' CHECK (mode IN ('shared','fixed','priority')),
  fixed_quantity int,
  published_quantity int, published_at timestamptz,
  UNIQUE (variant_id, channel_account_id)
);

-- Orders ---------------------------------------------------------------------
CREATE TABLE orders (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  channel_account_id uuid NOT NULL REFERENCES channel_accounts(id),
  channel_order_id text NOT NULL,
  status text NOT NULL CHECK (status IN ('new','accepted','shipped','delivered','cancelled','returned')),
  placed_at timestamptz NOT NULL,
  currency char(3) NOT NULL, total_minor bigint NOT NULL,
  buyer_pii_encrypted bytea,              -- name and address; purged after the retention period
  pii_purge_after timestamptz,
  UNIQUE (channel_account_id, channel_order_id)
);
CREATE TABLE order_lines (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  order_id uuid NOT NULL REFERENCES orders(id),
  variant_id uuid REFERENCES variants(id),
  sku text NOT NULL, quantity int NOT NULL, unit_price_minor bigint NOT NULL
);
CREATE TABLE shipments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  order_id uuid NOT NULL REFERENCES orders(id),
  carrier text, tracking_number text,
  shipped_at timestamptz, confirmed_on_channel_at timestamptz
);

-- Work queue, audit, AI usage ----------------------------------------------------
CREATE TABLE work_items (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  kind text NOT NULL CHECK (kind IN ('listing_rejected','legal_gap','low_stock','ai_draft','sync_error','mapping_review')),
  severity text NOT NULL DEFAULT 'normal' CHECK (severity IN ('low','normal','high')),
  subject_type text NOT NULL, subject_id uuid NOT NULL,
  message text NOT NULL, action jsonb,
  status text NOT NULL DEFAULT 'open' CHECK (status IN ('open','resolved','dismissed')),
  resolved_at timestamptz
);
CREATE UNIQUE INDEX work_items_open_uq ON work_items (tenant_id, kind, subject_id) WHERE status = 'open';
CREATE TABLE audit_log (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  actor_user_id uuid REFERENCES users(id),
  actor_type text NOT NULL CHECK (actor_type IN ('user','system','ai')),
  action text NOT NULL, subject_type text, subject_id uuid,
  diff jsonb, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE ai_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  purpose text NOT NULL, model text NOT NULL, prompt_version text NOT NULL,
  input_hash text NOT NULL, tokens_in int, tokens_out int,
  cost_micro_usd bigint, latency_ms int,
  status text NOT NULL CHECK (status IN ('ok','invalid_output','error')),
  created_at timestamptz NOT NULL DEFAULT now()
);
```

**Row-level security, applied in the same migration to every table that has `tenant_id`**

```sql
ALTER TABLE <table> ENABLE ROW LEVEL SECURITY;
ALTER TABLE <table> FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON <table>
  USING (tenant_id = app_tenant()) WITH CHECK (tenant_id = app_tenant());
```

For the two mapping tables that allow shared defaults, use `USING (tenant_id IS NULL OR tenant_id = app_tenant())` and `WITH CHECK (tenant_id = app_tenant())`.

**How RLS must be used by the code**

1. The API connects as a database role that does not own the tables and cannot bypass row-level security. Migrations run as a separate owner role.
2. For every request, the first statement in the transaction is `SELECT set_config('app.tenant_id', :tenant_id, true)`, using the workspace chosen in the request and checked against the user's memberships.
3. Workflows set the same value at the start of every activity.
4. A test must prove that a second tenant gets zero rows from every tenant table (section 13).

## 7. Connector interface and channel notes

Every marketplace is implemented behind the same Python interface. The rest of the platform never knows which marketplace it is talking to. Build the interface and a `FakeConnector` first, then each real connector against the same contract tests.

```python
# packages/connectors/base.py
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Generic, Literal, Protocol, TypeVar

T = TypeVar('T')

class ChannelErrorKind(str, Enum):
    RATE_LIMITED = 'rate_limited'     # retry after retry_after_s
    AUTH_EXPIRED = 'auth_expired'     # stop, ask the seller to reconnect
    VALIDATION = 'validation'         # the data is wrong; do not retry
    NOT_FOUND = 'not_found'
    TRANSIENT = 'transient'           # network or 5xx; retry with back-off
    PERMANENT = 'permanent'

@dataclass(frozen=True)
class FieldError:
    path: str                         # for example 'attributes.wheels'
    code: str                         # channel code, kept for support
    message: str                      # plain English, shown to the seller

class ChannelError(Exception):
    def __init__(self, kind: ChannelErrorKind, message: str, *, retry_after_s: float | None = None,
                 field_errors: list[FieldError] | None = None, raw: dict | None = None): ...

@dataclass
class CategoryRef:    id: str; path: str; name: str; is_leaf: bool
@dataclass
class AttributeSpec:  key: str; label: str; required: bool; type: str; allowed_values: list[str] | None; unit: str | None
@dataclass
class CategorySchema: category_id: str; attributes: list[AttributeSpec]; json_schema: dict | None  # Amazon provides one

@dataclass
class ListingDraft:
    sku: str; ean: str | None
    category_id: str; product_type: str | None
    attributes: dict[str, Any]                       # already mapped to channel attribute names
    language: str; title: str; bullets: list[str]; description: str
    price_minor: int; currency: str; quantity: int
    image_urls: list[str]
    compliance: dict[str, Any]                       # manufacturer, EU Responsible Person, packaging number

@dataclass
class PublishResult:   accepted: bool; task_ref: str | None; channel_listing_id: str | None
@dataclass
class ListingStatus:   state: Literal['pending', 'live', 'rejected', 'suppressed']; channel_listing_id: str | None; errors: list[FieldError]; raw: dict
@dataclass
class StockUpdate:     sku: str; quantity: int
@dataclass
class OrderLine:       sku: str; quantity: int; unit_price_minor: int
@dataclass
class ChannelOrder:    channel_order_id: str; status: str; placed_at: datetime; currency: str; total_minor: int; lines: list[OrderLine]; buyer: dict | None
@dataclass
class Page(Generic[T]): items: list[T]; next_cursor: str | None

class Connector(Protocol):
    channel: str
    async def check_connection(self) -> dict: ...
    async def list_categories(self, parent_id: str | None = None) -> list[CategoryRef]: ...
    async def get_category_schema(self, category_id: str) -> CategorySchema: ...
    async def validate_listing(self, draft: ListingDraft) -> list[FieldError]: ...   # dry run where the channel allows it
    async def publish_listing(self, draft: ListingDraft, idempotency_key: str) -> PublishResult: ...
    async def get_listing_status(self, task_ref: str | None, sku: str) -> ListingStatus: ...
    async def update_stock(self, updates: list[StockUpdate]) -> None: ...
    async def update_price(self, sku: str, price_minor: int, currency: str) -> None: ...
    async def end_listing(self, sku: str) -> None: ...
    async def fetch_orders(self, since: datetime, cursor: str | None = None) -> Page[ChannelOrder]: ...
    async def confirm_shipment(self, channel_order_id: str, carrier: str, tracking_number: str) -> None: ...
    async def fetch_stock(self, skus: list[str]) -> dict[str, int]: ...             # used by reconciliation
```

**Rules every connector follows**

1. Connectors are stateless. They receive credentials, an HTTP client and a rate limiter in the constructor and never touch the database.
2. All outbound calls go through the rate limiter with the channel's limits, and honour `Retry-After` headers.
3. Every channel failure is converted to a `ChannelError` with the right kind and a plain-English message. Raw responses are kept in `raw` for support only.
4. Publishing is idempotent: the same `idempotency_key` never creates a second listing.
5. A shared contract test suite runs against the `FakeConnector` and every real connector using recorded responses in `packages/connectors/testing/`. Recordings must have tokens and personal data removed.
6. Check every endpoint name and field against the official documentation and the sandbox. Do not rely on memory.

**Per-channel build notes** (from the research in the plan; confirm against current documentation before coding each one)

| Channel | Authentication | Publish path | Status and orders | Watch out for |
| --- | --- | --- | --- | --- |
| eBay | OAuth consent per seller; Developers Program keys; sandbox available | Inventory API: inventory item, then offer, then publish. Bulk endpoints and the Sell Feed API for large loads | Fulfillment API for orders and shipment tracking | Seller needs business policies and an inventory location; listings made via the Inventory API cannot be edited in Seller Hub; standardised condition details are now required |
| Kaufland | Client key and secret key per seller, requests signed with HMAC-SHA256; one connection per country | REST product-data upload by EAN | Orders, returns and tickets through the Seller API; poll import status for product data | Documentation is released after a software-provider test account and security check |
| Amazon | Seller authorises your app; check current authentication details in the SP-API docs | Fetch the JSON Schema for the product type, validate locally, then Listings Items API (single) or JSON listings feed (bulk) | Listing status and issues through the Listings Items API; orders through the Orders API | Product Type Definitions default to 5 requests per second, burst 10; schemas use custom vocabulary; app approval needed for other sellers |
| OTTO | OAuth client credentials with scopes per interface | Match brand and category first, post products, then post quantities separately | Product requests are asynchronous: you get a task link and poll it after the time the response suggests | About 1,000 requests per minute and 20 per second per partner; HTTP 429 beyond that |
| Shopify | OAuth app install per store | GraphQL Admin API mutations | Webhooks for products, stock and orders | Cost-based throttling; use bulk operations for large reads |

## 8. Workflows and background jobs

Anything slow, asynchronous or retry-prone runs as a Temporal workflow in `apps/worker`. Workflows only orchestrate. Each step is a small activity that calls the database or a connector, so it can be retried and tested alone.

| Workflow | Trigger | Steps | Notes |
| --- | --- | --- | --- |
| `publish_listing(listing_id)` | Seller presses publish, or a bulk publish | 1. Load listing, approved content, attributes, compliance data. 2. Build the channel draft with the attribute map. 3. Validate locally, then `connector.validate_listing`. 4. If errors: set status back to `draft`, store errors, create a `listing_rejected` or `legal_gap` work item, stop. 5. `connector.publish_listing` with key = listing id + payload hash. 6. Save the payload to `listing_payloads`, set `submitted`. 7. Poll `get_listing_status` using Temporal timers until `live`, `rejected` or `suppressed`, or 72 hours pass. 8. Save the result, write a `listing_events` row, open or close work items | Signals: `cancel`, `retry_now`. Never retry `VALIDATION` or `AUTH_EXPIRED` errors |
| `bulk_publish(batch_id)` | Publish wizard | Starts `publish_listing` children in chunks sized to the channel's rate limit | Progress is stored so the interface can show a live bar |
| `sync_stock(variant_id)` | Every new `stock_events` row | Wait 5 seconds to merge bursts, compute the quantity per channel (below), call `update_stock` in batches, store `published_quantity` | Started with signal-with-start so one workflow per variant absorbs repeated signals |
| `import_orders(channel_account_id)` | Temporal schedule, every 2 minutes per active account | `fetch_orders` since the saved cursor, upsert orders, write `sold` stock events with key `channel:order:line`, start `sync_stock` for the affected variants | Safe to run twice: unique keys stop duplicates |
| `confirm_shipment(order_id)` | Seller enters tracking | `connector.confirm_shipment`, then mark the shipment confirmed | Retries on transient errors |
| `reconcile_stock(channel_account_id)` | Hourly | `fetch_stock` for live SKUs, compare with the ledger and `published_quantity`, push a correction on any difference, open a `sync_error` work item if drift repeats | Zero drift is part of the MVP acceptance test |
| `refresh_channel_schema(...)` | Daily and on demand | Fetch category schemas and lists, store in `channel_schemas_cache` and refresh embeddings | Respect product-type API limits |
| `generate_content(product_id, language, channel)` | Seller requests drafts | The AI pipeline in section 9 | Writes drafts only, never publishes |
| `check_connections()` | Daily | `check_connection` for each active account, mark `auth_expired` and open a work item if it fails |  |

**Retry rules for every activity.** Exponential back-off starting at 2 seconds, capped at 5 minutes, up to 8 attempts for `TRANSIENT` and `RATE_LIMITED` (use `retry_after_s` when given). No retry for `VALIDATION`, `AUTH_EXPIRED`, `NOT_FOUND` or `PERMANENT`. Every activity sets the tenant first (section 6, step 3).

**Rate limiter.** A Redis token bucket keyed by `rl:{channel}:{channel_account_id}`, implemented as one atomic Lua script. Limits come from configuration per channel (for example OTTO: 20 requests per second per partner). Every connector call acquires a token first and waits if none is available.

**Stock quantity published to a channel**

```python
def quantity_for_channel(on_hand: int, reserved: int, setting) -> int:
    available = max(0, on_hand - reserved)
    if setting.mode == 'fixed':
        return min(available, setting.fixed_quantity or 0)
    return max(0, available - setting.buffer)        # 'shared' and 'priority'

def allocate(on_hand: int, reserved: int, settings: list) -> dict:
    # 'priority' channels are served first when stock is short; others share the rest equally.
    ...
```

The default buffer is 0. The interface suggests a buffer per product of units sold during the longest sync delay multiplied by 1.5, and the seller can accept or change it.

## 9. AI pipeline

The model writes and extracts; deterministic code decides what may go live. Build the pipeline as small steps with typed inputs and outputs, so each step can be tested and each model call can be logged to `ai_runs`.

**The client interface**

```python
# apps/api/app/content/llm.py
class LLMClient(Protocol):
    async def generate_structured(self, *, purpose: str, prompt_id: str, prompt_version: str,
                                  inputs: dict, output_schema: dict, model_role: Literal['fast', 'writer'],
                                  tenant_id: UUID) -> StructuredResult: ...
# StructuredResult: data (validated against output_schema), tokens_in, tokens_out, model, latency_ms
```

The client validates every response against the schema. On invalid output it retries once with the validation error attached, then records `invalid_output` in `ai_runs` and raises. It checks the tenant's monthly AI credit allowance before calling, and caches by `input_hash` so identical requests are free.

**Pipeline steps**

| Step | Model role | Input | Output | Hard rule |
| --- | --- | --- | --- | --- |
| `classify_product` | fast | Product name and source text, list of packs | `{pack_key, confidence}` | Must choose from the pack list |
| `extract_attributes` | fast | Source text, the pack's attribute definitions | List of `{key, value, unit, evidence}` | Every value needs an `evidence` quote from the source text; no evidence means the value is dropped |
| `map_category` | fast | Product facts, top 5 to 10 candidate categories from search | `{choice_id, confidence, reason}` | `choice_id` must be in the candidate list; low confidence creates a `mapping_review` work item |
| `write_content` | writer | Facts, pack rules, channel limits, glossary, keywords, language | Schema below | Uses only the facts given |
| `critique_content` | code first, optional fast model | Draft and facts | Pass or list of problems | Checks below; one automatic rewrite allowed, then human review |
| Legal text | none | Pack, country | Approved template text | Chosen by code, never written by the model |

**Output schema for `write_content`**

```json
{
  "type": "object",
  "required": ["title", "bullets", "description", "keywords", "used_facts"],
  "additionalProperties": false,
  "properties": {
    "title": { "type": "string", "maxLength": 200 },
    "bullets": { "type": "array", "items": { "type": "string", "maxLength": 500 }, "maxItems": 8 },
    "description": { "type": "string" },
    "keywords": { "type": "array", "items": { "type": "string" } },
    "used_facts": { "type": "array", "items": { "type": "string" },
                    "description": "attribute keys every claim in the text relies on" }
  }
}
```

The channel's real title and bullet limits come from configuration and are enforced by the validators, not trusted from the model.

**Prompt rules (put these in `packages/ai/prompts/write_content/v1.md`)**

1. Write natively in the target language from the facts, not by translating English.
2. Use only the provided facts. If a fact is missing, leave it out.
3. Never state a number, capacity, yield, size or compatibility that is not in the facts.
4. Mention printer or other OEM brands only in the form "compatible with \<model>", never as if the product were original.
5. Follow the glossary for the language and pack (for example fixed German terms for printer consumables).
6. Return only JSON matching the schema.

Every prompt file has a version. The version string is stored in `contents.prompt_version` and `ai_runs.prompt_version`, and a new version is a new file, never an edit of an old one.

**Deterministic validators** (in `apps/api/app/validation/`, all must pass before a listing can become `validated`)

- Channel rules: title length, bullet count and length, image count and size, forbidden words, required attributes from the channel schema.
- Numeric claims: every number in the text must appear in the product facts (after unit conversion).
- Compatibility pattern: OEM brand names appear only inside the approved "compatible with" phrasing; images flagged for human review if they might show OEM logos.
- Compliance gates: manufacturer, EU Responsible Person, packaging registration and category-specific records present for the target country.
- Language check: detected language matches the requested language.
- Duplicate check: content for sibling variants and countries is not near-identical (embedding similarity above 0.9 is flagged).

**Risk tiers.** `risk_tier(product, pack, channel)` returns `low`, `medium` or `high`. High (first listing of a pack, any food or fertilizer pack, compatible-cartridge listings that name OEM models) always needs a human approval. Medium is sampled, deterministically, about 1 in 10 by hash of the content id. Low can auto-approve.

**Evaluation harness**

- Test cases live in `packages/ai/evals/<pack>/cases.jsonl`: facts, language, channel, and the constraints the output must meet. Start with 30 cases per pack from real listings and grow to about 200.
- `make eval` runs every case against the current prompt versions and reports: schema validity rate, numeric-claim violations (must be 0), banned-term hits (must be 0), length compliance, and a rubric score from a second model call that is spot-checked by a person.
- A new prompt version or model must match or beat the previous one on every metric before it becomes the default.

**Cost controls.** Log tokens and cost for every call. Send bulk generation through the provider's asynchronous batch interface where one exists. Enforce each plan's monthly AI credit allowance in `LLMClient`.

## 10. REST API

The web app is the first client of this API, and agencies get it later as the public API, so design it properly from the start. Commit the generated OpenAPI file and generate the TypeScript client from it.

**Conventions**

- All paths start with `/api/v1`. The active workspace is sent in an `X-Workspace-Id` header and checked against the user's memberships on every request.
- Lists use cursor pagination (`?limit=50&cursor=...`) and return `{items, next_cursor}`.
- Creates and publishes require an `Idempotency-Key` header. Repeating the same key returns the first result.
- Errors use the problem-details format (`type`, `title`, `status`, `detail`, plus `field_errors` where relevant).
- Long operations return `202 Accepted` with a job id and a status URL. Never block a request on a marketplace call.
- Responses never include credentials, encrypted fields or raw buyer personal data.

| Area | Method and path | Purpose |
| --- | --- | --- |
| Session | `GET /me` | Current user and the workspaces they belong to |
| Workspaces | `POST /workspaces`, `GET /workspaces/current`, `POST /workspaces/current/invitations`, `PATCH /memberships/{id}` | Create a workspace, invite users, change roles |
| Channels | `GET /channel-accounts` | List connections and their health |
|  | `POST /channel-accounts/connect/{channel}/start` | Begin OAuth or credential entry; returns a redirect URL or a form description |
|  | `GET /channel-accounts/connect/{channel}/callback` | OAuth return; stores encrypted credentials |
|  | `POST /channel-accounts/{id}/credentials` | For channels that use pasted keys (for example Kaufland) |
|  | `POST /channel-accounts/{id}/test`, `DELETE /channel-accounts/{id}` | Check the connection, disconnect |
| Catalog | `GET/POST /products`, `GET/PATCH/DELETE /products/{id}` | Products with filters by pack, status, channel status |
|  | `GET/POST /products/{id}/variants`, `PATCH /variants/{id}` | Variants, SKU, EAN, cost |
|  | `PUT /products/{id}/attributes` | Set attribute values in bulk, validated against the pack |
|  | `POST /products/{id}/images` | Returns an upload URL; image metadata saved on completion |
|  | `POST /imports/products` and `GET /imports/{id}` | CSV upload, column mapping, progress and row errors |
| Packs | `GET /packs`, `GET /packs/{key}` | Pack definitions for building forms |
| Mapping | `GET /products/{id}/mapping?channel_account_id=` | Proposed category and attributes with confidence |
|  | `PUT /products/{id}/mapping/{channel_account_id}` | Approve or change the mapping; saved for reuse |
| Content | `POST /products/{id}/content/generate` | Body: languages and channels; returns a job |
|  | `GET /products/{id}/content`, `PATCH /content/{id}` | Read and edit drafts |
|  | `POST /content/{id}/approve`, `POST /content/{id}/reject` | Approval with user and time recorded |
| Compliance | `GET/PUT /compliance/tenant`, `GET/PUT /products/{id}/compliance` | Seller-level and product-level legal data |
|  | `GET /compliance/gaps` | Products blocked for missing data, by country |
| Listings | `GET /listings` | Filter by status, channel, product |
|  | `POST /listings/validate` | Dry-run validation for a set of variants and channel accounts |
|  | `POST /listings/publish` | Starts `bulk_publish`; returns a job id |
|  | `GET /listings/{id}`, `GET /listings/{id}/events`, `GET /listings/{id}/payloads` | Detail, history, what was sent |
|  | `POST /listings/{id}/end` | End a listing |
| Inventory | `GET /inventory`, `POST /inventory/adjustments` | Stock per variant; manual adjustments become ledger events |
|  | `GET/PUT /inventory/channel-settings` | Buffers and allocation mode per variant and channel |
| Orders | `GET /orders`, `GET /orders/{id}` | Unified orders |
|  | `POST /orders/{id}/shipments` | Enter tracking; starts `confirm_shipment` |
| Work queue | `GET /work-items`, `POST /work-items/{id}/resolve`, `POST /work-items/{id}/dismiss` | Home screen data |
| Jobs | `GET /jobs/{id}` | Progress for any `202` operation |
| Audit | `GET /audit-log` | Who changed what, including AI-written text |
| Webhooks in | `POST /webhooks/{channel}/{channel_account_id}` | Signed events from marketplaces; verify the signature, then start a workflow |

## 11. Frontend spec

The interface is a work queue first, with spreadsheet-style grids for bulk work and a side-by-side editor for AI drafts. The plan document's section 10 has two wireframes (home and product editor) that match the layouts described here.

**Design tokens** (put in `apps/web/src/styles/tokens.css`; extend Tailwind with these names)

```css
:root {
  --bg: #ffffff;           --surface: #f7f7f5;      --border: #d9d8d2;
  --text: #1a1a1a;         --text-muted: #5f5e58;
  --accent: #2563eb;       --accent-tint: #e8effd;
  --good: #16a34a;         --warning: #f59e0b;      --critical: #dc2626;     --neutral: #6b7280;
  --radius: 8px;           --row-compact: 40px;     --row-comfortable: 48px;
  --font-sans: 'Inter', 'Noto Sans Devanagari', system-ui, sans-serif;
  --text-xs: 12px; --text-sm: 14px; --text-md: 16px; --text-lg: 20px; --text-xl: 28px;
}
```

Spacing uses a 4-pixel base with steps of 4, 8, 12, 16, 24, 32. Surfaces are flat: 1-pixel borders, no heavy shadows, no gradients. One accent colour is used only for primary actions and selected items. Dark mode is not in the MVP, but use the tokens everywhere so it can be added later.

**Status chips** (a chip always shows an icon and a word, never colour alone)

| Listing status | Label | Colour token |
| --- | --- | --- |
| `draft` | Draft | `--neutral` |
| `validated` | Ready | `--accent` |
| `submitted`, `in_review` | In review | `--warning` |
| `live` | Live | `--good` |
| `suppressed` | Suppressed | `--warning` |
| `rejected` | Rejected | `--critical` |
| `ended` | Ended | `--neutral` |

**Routes** (Next.js App Router, in `apps/web/src/app/`)

| Route | Screen |
| --- | --- |
| `/login`, `/onboarding` | Sign-in; create workspace, connect the first channel, import products |
| `/` | Home: work queue |
| `/products`, `/products/new`, `/products/import` | Grid, create, CSV import |
| `/products/[id]` | Product editor with tabs set by `?tab=` (details, attributes, images, content, channels, compliance, history) |
| `/listings`, `/listings/publish` | Listing list; publish wizard |
| `/inventory` | Stock, buffers, drift alerts |
| `/orders`, `/orders/[id]` | Unified orders and detail |
| `/compliance` | Seller-level legal data and list of product gaps |
| `/service-desk` | MVP: request form that sends an email or webhook set by an environment variable |
| `/settings/channels`, `/settings/team`, `/settings/audit` | Connections, users and roles, audit log |

**Screen specifications**

1. **Home.** Header "Needs your attention" and a client switcher (shown only to agency users). Four counters (rejected listings, legal gaps, low stock, AI drafts) that filter the list below. A "Fix next" list of work items, each row showing product, channel chip, issue text and a Fix button that opens the exact screen and tab needed. A channel health strip with one card per connected account showing last sync time and any error. Data: `GET /work-items`, `GET /channel-accounts`.
2. **Products grid.** Virtualised table with columns for image, name, SKU, pack, stock, one status chip per connected channel, and last edited. Saved views, column chooser, filters, multi-select with bulk actions (choose pack, generate content, publish, archive). Clicking a row opens the editor in a side panel; a full-page link is available. Inline editing for name, price and stock.
3. **Product editor.** Header with name and one chip per channel account. Tabs: Details; Attributes (form built from the pack definition, with units and allowed values); Images (upload, reorder, size warnings); Content (language and channel selectors, current text beside the AI draft with accept, edit and reject, and the `used_facts` shown as chips); Channels (mapped category per channel with confidence, approve or change); Compliance (fields required for each target country); History (listing events and audit entries). A sticky publish-check bar at the bottom lists blocking problems with an "Add data" action.
4. **Import wizard.** Upload, map columns to attributes with automatic guesses, preview 20 rows with errors, confirm, then show progress from `GET /imports/{id}`.
5. **Publish wizard.** Step 1 choose products; step 2 choose channel accounts and countries; step 3 validation results with inline fixes and a count of blocked items; step 4 confirm and watch live progress per channel. Blocked items can be skipped.
6. **Inventory.** Table of stock per variant with channel quantities and drift flags; side panel to set buffer and mode; manual adjustment dialog that requires a reason.
7. **Orders.** Unified list with channel, status, date and total; detail page with lines and shipment form; buyer personal data hidden until the user opens the order, and not shown after the retention period.
8. **Compliance centre.** Seller-level cards (packaging registration, dual-system contract status, VAT IDs, EU Responsible Person) with status, and a table of products with gaps grouped by country.
9. **Channel settings.** One card per channel with Connect, Test and Disconnect. OAuth channels redirect; Kaufland shows a form for client key and secret key; show the status `auth_expired` with a Reconnect button.

**Shared components to build first:** `AppShell`, `DataGrid`, `StatusChip`, `ChannelChip`, `WorkItemRow`, `DiffViewer`, `FactChips`, `PackForm`, `ComplianceGateBanner`, `JobProgress`, `EmptyState`, `ConfirmDialog`.

**Rules for every screen**

- Provide loading, empty and error states. Empty states say what to do next.
- Poll `GET /jobs/{id}` every 2 seconds, backing off to 10 seconds, until the job ends.
- Autosave editor drafts and warn before leaving with unsaved changes.
- All text goes through next-intl. Layouts must tolerate strings about 30% longer (German).
- Meet WCAG 2.2 AA, with full keyboard control of the grid and dialogs.
- Home, Orders and approvals must work on a 360-pixel-wide phone; grids and the editor are desktop-first.

## 12. Security, tenancy and compliance rules

These rules are requirements, each with a test. The compliance rules come from the research in the plan document (section 9) and are planning input, so a lawyer or compliance specialist must confirm them before launch.

**Tenancy**

- Row-level security as described in section 6 is mandatory on every table with `tenant_id`.
- Looking up which workspaces a user belongs to happens before a tenant is chosen, so it cannot use a tenant-scoped query. Do it through one `SECURITY DEFINER` function, `memberships_for_user(auth_subject)`, that returns only that user's rows.
- Background workflows receive `tenant_id` as an explicit argument and set it at the start of every activity.

**Roles**

| Capability | viewer | editor | agency\_manager | owner |
| --- | --- | --- | --- | --- |
| Read everything in the workspace | yes | yes | yes | yes |
| Edit catalog, content, compliance data | no | yes | yes | yes |
| Approve content and publish | no | yes | yes | yes |
| Connect or disconnect channel accounts | no | no | yes | yes |
| View audit log | no | no | yes | yes |
| Invite users, change roles, change plan | no | no | no | yes |

An agency manager can switch between the workspaces of their clients but never sees data from a workspace they were not added to.

**Secrets and personal data**

1. Channel credentials are encrypted with envelope encryption: a data key encrypts the credentials, and a key-management service key wraps the data key. Local development reads a key from an environment variable behind the same interface.
2. Credentials are decrypted only when a connector is constructed inside a workflow activity or request. They are never logged, returned by the API or placed in an error message.
3. Buyer name and address are stored encrypted and purged after `pii_purge_after`. Use 90 days after the order is complete as the default, configurable, and confirm the right period with your legal adviser.
4. Log lines carry ids, never names, emails or addresses.
5. Connectors request the smallest permission set each channel allows.

**Compliance gates** (implemented as validators; a failing gate blocks `validated` and creates a `legal_gap` work item whose message names the missing field)

| Rule | Applies when | Block unless |
| --- | --- | --- |
| C1 Product safety (GPSR) | Any listing to an EU country | A manufacturer record and an EU Responsible Person record exist for the product or the workspace, with name, postal address and email, and safety information is present where the pack requires it |
| C2 German packaging | Listing to Germany | The workspace has a packaging registration number and a dual-system contract status recorded |
| C3 Food information | Pack is a food pack | Ingredients, allergens, nutrition values, net quantity and food business operator are present; the best-before date may be supplied at delivery |
| C4 Fertilizer | Pack is a fertilizer pack | The route (CE-marked or national) is recorded, CE data is present when the route is CE-marked, and a human has approved the listing |
| C5 Compatible cartridges | Pack is ink or toner and the product is not an original | OEM names appear only in the approved compatible-with wording, no OEM logos are in the images, and the model is not on the hold-for-review list |
| C6 VAT data | Always | Not blocking; the workspace VAT ID is stored and exported for the seller's accountant |

The hold-for-review list for C5 is a table that you maintain by hand. Start empty and add models when a brand-owner dispute is known.

**Application security checklist**

- HTTPS only, strict CORS, secure cookies, protection against cross-site request forgery for cookie sessions.
- Every input validated with Pydantic and zod; parameterised queries only.
- CSV and image uploads checked for size, type and content before processing.
- Image URLs supplied by sellers are fetched only through a function that blocks internal network addresses.
- Webhook endpoints verify the marketplace's signature before doing anything.
- Per-workspace API rate limits.
- Dependency and secret scanning in CI; no secrets in the repository.
- Audit log entries for logins, channel connections, content approvals, publishes and role changes.
- Automated database backups with a tested restore, and an outside penetration test before the first paying customer.

## 13. Testing, CI/CD and environments

Tests are what let you trust code you did not write by hand, so every task in section 14 ships with tests and a task is not done until they pass in CI.

**Test layers**

| Layer | Tools | What it covers |
| --- | --- | --- |
| Unit | pytest, Vitest | Pure logic: validators, stock quantity calculation, attribute transforms, price floor, CSV parsing |
| Integration | pytest with Testcontainers (Postgres with pgvector, Redis) | API endpoints, migrations, row-level security, repositories |
| Workflow | Temporal's test environment with time skipping and the `FakeConnector` | Publish, stock sync, order import and reconciliation, including retries and failures |
| Connector contract | One shared suite run against `FakeConnector` and each real connector using recorded responses | Same behaviour from every marketplace |
| End to end | Playwright against Docker Compose | Sign up, connect a fake channel, import, generate, approve, publish, see status |
| AI evaluation | `make eval` (section 9) | Prompt and model quality |

**Tests that must exist (the agent adds each one in the task named in section 14)**

1. **Tenant isolation:** a test that discovers every table with a `tenant_id` column and proves a second tenant reads zero rows and cannot write.
2. **Idempotent publishing:** publishing twice with the same key creates one listing.
3. **Idempotent stock events and orders:** replaying `import_orders` produces no duplicate `sold` events.
4. **Reconciliation:** a deliberately wrong channel quantity is detected and corrected.
5. **Compliance gates:** each rule C1 to C5 blocks a non-compliant listing and passes a compliant one.
6. **No secrets leaked:** the API never returns credential fields, and a log-capture test confirms a fixture token never appears in logs.
7. **Retry behaviour:** `VALIDATION` and `AUTH_EXPIRED` errors are never retried; `RATE_LIMITED` honours `retry_after_s`.
8. **Contract test for the OpenAPI file:** CI fails if the committed file differs from the generated one.

Aim for at least 80% line coverage in `validation`, `inventory`, `listings` and `compliance`, where mistakes cost sellers money. Do not chase a global percentage.

**CI pipeline (GitHub Actions), on every pull request**

1. Lint and format: Ruff, ESLint, Prettier.
2. Type check: mypy or pyright, `tsc`.
3. Python tests, including Testcontainers.
4. Web unit tests.
5. Migration check: `alembic upgrade head` on an empty database, and a check that models and migrations agree.
6. OpenAPI generation and diff.
7. Security: dependency audit (`pip-audit`, `npm audit`) and secret scanning.
8. Build Docker images.
9. Playwright end-to-end tests on pushes to `main` and when a pull request carries a label.

**Environments**

| Environment | Purpose | Notes |
| --- | --- | --- |
| Local | Development | Docker Compose with Postgres, Redis, Temporal dev server, MinIO, Keycloak and a mail catcher; `make setup` starts everything and loads seed data |
| Staging | Pilot rehearsal | EU region; marketplace sandboxes and test accounts only; same infrastructure code as production |
| Production | Real sellers | EU region; real credentials only here |

**Deployment.** Build Docker images in CI, deploy with Terraform and a rolling update. Run migrations as a separate step before the new version starts, and write them in two phases (add first, remove later) so a rollback is just redeploying the previous image.

**Dashboards and alerts to create with the first deployment:** error rate per channel, publish duration, queue depth, stock drift count, AI cost per day, and auth-expired accounts.

**Makefile targets the first task must create:** `setup`, `dev`, `test`, `lint`, `eval`, `e2e`, `openapi`, `migrate`, `seed`.

## 14. Build order: epics and tasks

There are 36 tasks in 9 epics. Give the agent one task at a time using the template in section 1. "Read" lists the sections of this spec the agent must read first; "After" lists tasks that must be finished before this one. Tasks with no shared dependency can be run in parallel, for example by a second agent or a second engineer. As a rough, unverified guess, epics E0 to E2 take 6 to 8 weeks for two engineers working with agents, and the whole MVP takes 5 to 6 months, which matches the roadmap in the plan document.

### E0 Foundations

| ID | Task | Read | After | Done when |
| --- | --- | --- | --- | --- |
| T01 | Repository scaffold: folders from section 3, `AGENTS.md`, `CLAUDE.md`, Makefile, Docker Compose (Postgres with pgvector, Redis, Temporal dev server, MinIO, Keycloak, mail catcher), CI skeleton | 1, 3, 4, 13 | none | `make setup` and `make test` pass on a clean checkout and CI is green |
| T02 | API skeleton: FastAPI app, settings class, structured logging, problem-details errors, health endpoint, OpenAPI export, generated TypeScript client | 3, 4, 10 | T01 | `GET /health` returns ok; `make openapi` writes the file and the web client types |
| T03 | Database foundation: first Alembic migration with the whole schema from section 6, RLS on every tenant table, separate owner and app roles, test helper that sets the tenant | 6, 12, 13 | T01 | The tenant-isolation test passes for every table with `tenant_id` |
| T04 | Authentication and tenancy: `AuthProvider` with a Keycloak implementation, `/me`, workspaces, invitations, memberships, role checks, `memberships_for_user` | 6, 10, 12 | T02, T03 | A test exists for each row of the roles table, and a user cannot reach another workspace |

### E1 Catalog

| ID | Task | Read | After | Done when |
| --- | --- | --- | --- | --- |
| T05 | Packs: pack file format, loader into the `packs` table, the `ink_toner` and `luggage` packs from section 15, attribute validation | 6, 15 | T03 | Invalid values are rejected with field errors; pack endpoints return definitions |
| T06 | Catalog API: products, variants, attribute values, soft delete, filters, pagination, audit entries | 6, 10 | T04, T05 | CRUD tests pass; attribute writes are validated against the pack |
| T07 | CSV import: upload, automatic column mapping guess, preview, background import with row errors | 10, 11 | T06 | A 100-row sample imports with a row-level error report; importing again is idempotent by SKU |
| T08 | Images: signed upload URLs, metadata, size warnings, safe URL-fetch helper | 6, 12 | T06 | Upload works against local MinIO; the helper blocks internal addresses (tested) |
| T09 | Web shell and catalog screens: `AppShell`, `DataGrid`, `StatusChip`, products grid, import wizard, editor tabs for details, attributes and images | 11 | T02, T06, T07, T08 | Playwright creates a product, imports a CSV and edits attributes; the grid is keyboard-navigable; strings come from next-intl |

### E2 Connector core and eBay

| ID | Task | Read | After | Done when |
| --- | --- | --- | --- | --- |
| T10 | Connector core: interface, error types, `FakeConnector`, shared contract test suite, recording helper that strips tokens | 7, 13 | T01 | `FakeConnector` passes the contract suite; recordings contain no tokens |
| T11 | Rate limiter and credential vault: Redis token bucket in Lua, envelope encryption, channel-account endpoints with test and disconnect | 7, 8, 12 | T03, T10 | A test shows the 20-requests-per-second cap holds; credentials are never returned or logged |
| T12 | eBay connector: OAuth connect against the sandbox, categories, schema, validate, publish, status, stock, price, orders, shipment | 7 | T11 | Contract tests pass on recordings; one product is published to the eBay sandbox by hand |
| T13 | Schema cache and mapping data: `refresh_channel_schema`, category lists, embeddings, mapping table CRUD | 6, 8, 9 | T05, T12 | eBay categories are searchable; an approved mapping is reused for the next product |

### E3 Mapping and AI

| ID | Task | Read | After | Done when |
| --- | --- | --- | --- | --- |
| T14 | `LLMClient`: interface, provider implementation, schema validation with one retry, `ai_runs` logging, caching, credit limit | 9 | T03 | Tests with a stub provider cover invalid output, cache hit at zero cost, and the credit limit |
| T15 | `classify_product`, `extract_attributes`, `map_category` with the evidence rule | 9 | T13, T14 | A value without an evidence quote is dropped; a category outside the candidates is rejected |
| T16 | Content generation: `write_content` prompt version 1, German and English glossaries, API-triggered job | 9, 15 | T05, T14 | Output validates against the schema; `used_facts` and an `ai_runs` row are stored |
| T17 | Validators and `risk_tier` | 9, 12 | T16 | At least 5 failing and 5 passing cases per validator |
| T18 | Approval flow and editor UI: content API, approve and reject, `DiffViewer`, `FactChips`, Channels tab with mapping approval | 10, 11 | T09, T16, T17 | Playwright generates, edits and approves content; approval writes an audit entry |
| T19 | Evaluation harness: case format, `make eval`, metrics, prompt-version comparison | 9 | T16, T17 | The report shows all metrics and fails when any numeric-claim violation exists |

### E4 Publishing

| ID | Task | Read | After | Done when |
| --- | --- | --- | --- | --- |
| T20 | Temporal foundation: worker app, tenant-aware activity base class, test-environment helper | 8 | T03, T10 | A sample workflow runs locally and under time-skipping tests |
| T21 | `publish_listing` workflow and listing state machine: transitions, events, payload history, failure handling, work items | 5, 6, 8 | T12, T17, T20 | Tests cover success, validation failure, rejection, suppression, timeout and idempotent retry |
| T22 | `bulk_publish`, jobs API, publish wizard | 8, 10, 11 | T09, T21 | 100 listings reach the eBay sandbox with live progress in the interface |
| T23 | Work queue: work-item generation from listing and compliance events, API, Home screen | 6, 10, 11 | T09, T21 | A rejected listing creates an item; fixing the cause closes it; counters match the list |
| T24 | Kaufland connector | 7 | T11, T13 | Contract tests pass; a publish works on the test account once approved |

### E5 Stock and orders

| ID | Task | Read | After | Done when |
| --- | --- | --- | --- | --- |
| T25 | Stock ledger and inventory API: events, view, adjustments with a required reason, channel settings | 6, 8, 10 | T06 | Replaying events gives the same totals; a duplicate idempotency key is ignored |
| T26 | `sync_stock` workflow: debounce, quantity calculation, batching, `published_quantity` | 8 | T12, T20, T25 | Ten rapid changes lead to one update call; shared, fixed and priority modes are tested |
| T27 | Orders: `import_orders` schedule, orders, lines, shipments, `confirm_shipment`, encrypted buyer data and purge job | 6, 8, 12 | T12, T20, T25 | Replay creates no duplicates; a sale reduces stock; purge removes buyer data when due |
| T28 | `reconcile_stock`, drift alerts, Inventory and Orders screens | 8, 11 | T26, T27 | An injected drift is detected and corrected in one run; screens match section 11 |

### E6 Compliance

| ID | Task | Read | After | Done when |
| --- | --- | --- | --- | --- |
| T29 | Compliance records API and gates C1 to C6 | 12, 15 | T06, T17 | Each rule blocks a bad listing and passes a good one |
| T30 | Compliance centre and the publish-check bar in the editor | 11, 12 | T18, T29 | The interface blocks publishing and names the missing field |

### E7 Amazon and OTTO

| ID | Task | Read | After | Done when |
| --- | --- | --- | --- | --- |
| T31 | Amazon connector: product-type schema fetch and local validation, Listings Items API, status, orders | 7 | T11, T13 | Contract tests pass; one product publishes from your own seller account |
| T32 | OTTO connector: brand and category matching, asynchronous product tasks, quantity calls | 7 | T11, T13 | Contract tests pass; the sandbox flow works |

### E8 Hardening and pilot

| ID | Task | Read | After | Done when |
| --- | --- | --- | --- | --- |
| T33 | Audit log screen, dashboards and alerts from section 13 | 11, 13 | T21, T26 | Dashboards show per-channel errors, queue depth, drift and AI cost |
| T34 | Security pass: walk through the section 12 checklist, fix gaps, prepare the outside penetration test | 12 | T30 | Checklist is fully ticked with a link to the test or code for each item |
| T35 | End-to-end acceptance suite for the MVP acceptance test in section 2, plus a seed script for a demo workspace | 2, 13 | all above | The suite passes in CI against Docker Compose |
| T36 | Pilot polish: onboarding in under 15 minutes, empty states, help text, German interface strings | 11 | T35 | A new tester reaches a live sandbox listing in under 15 minutes without help |

**Example: the filled-in prompt for T03**

```markdown
Task: T03 Database foundation
Read first: docs/SPEC.md sections 6, 12, 13
Goal: Create the first Alembic migration containing the full schema from section 6, with row-level security on every table that has tenant_id.
Build:
- Migration with all tables, constraints, the stock_current view and the app_tenant() function
- Two database roles: an owner role used by migrations and an app role that cannot bypass RLS
- A test helper that sets app.tenant_id for a transaction
- A test that finds every table with a tenant_id column and proves a second tenant reads zero rows and cannot insert
Acceptance: the tenant-isolation test passes; make migrate works on an empty database; make test and make lint pass.
Constraints: follow AGENTS.md; ask before adding a dependency.
Reply first with a plan only.
```

## 15. Seed data: category packs

A pack is a data file in `packages/packs/`, loaded into the `packs` table. It defines the attributes a product type needs, the rules the validators apply, and which compliance gates (section 12) apply. These are starting definitions based on the listing work you already do; review them against your real listings before relying on them.

**File format**

```yaml
key: ink_toner                # unique, stable
version: 1                    # increase on any change
label: Ink and toner cartridges
default_risk: high            # used by risk_tier until enough approved listings exist
compliance_gates: [C1, C2, C5]
attributes:                   # key, label, type, required, level (product or variant),
  - ...                       # unit, allowed_values, min, max, description
rules: {}                     # pack-specific validator settings
glossary: de                  # file in packages/ai/glossary/
```

Attribute types: `string`, `integer`, `decimal`, `boolean`, `enum`, `list_string`, `dimensions_cm`.

**`ink_toner.yaml`**

```yaml
key: ink_toner
version: 1
label: Ink and toner cartridges
default_risk: high
compliance_gates: [C1, C2, C5]
attributes:
  - {key: product_kind, label: Product kind, type: enum, required: true, level: product,
     allowed_values: [ink_cartridge, toner_cartridge, drum_unit, ribbon, other]}
  - {key: condition, label: Condition, type: enum, required: true, level: product,
     allowed_values: [new_compatible, remanufactured, original]}
  - {key: colour, label: Colour, type: enum, required: true, level: variant,
     allowed_values: [black, cyan, magenta, yellow, photo_black, tri_colour, multipack]}
  - {key: compatible_models, label: Compatible printer models, type: list_string, required: true, level: product, min: 1}
  - {key: oem_part_numbers, label: Original part numbers replaced, type: list_string, required: true, level: product, min: 1}
  - {key: page_yield, label: Page yield, type: integer, unit: pages, required: false, level: variant,
     description: Only from the supplier datasheet; never estimated}
  - {key: page_yield_standard, label: Yield standard, type: enum, required: false, level: variant,
     allowed_values: [iso_19752, iso_19798, iso_24711, other, unknown]}
  - {key: volume_ml, label: Ink volume, type: decimal, unit: ml, required: false, level: variant}
  - {key: pack_size, label: Units in pack, type: integer, required: true, level: variant, min: 1}
  - {key: has_chip, label: Has chip, type: boolean, required: false, level: variant}
  - {key: country_of_origin, label: Country of origin, type: string, required: false, level: product}
rules:
  oem_brands_file: packages/packs/oem_brands.yaml
  banned_terms: [original, genuine, oem]
  compatible_phrase_required_when: {condition: [new_compatible, remanufactured]}
glossary: de
```

**`luggage.yaml`**

```yaml
key: luggage
version: 1
label: Luggage and bags
default_risk: medium
compliance_gates: [C1, C2]
attributes:
  - {key: luggage_type, label: Type, type: enum, required: true, level: product,
     allowed_values: [cabin_trolley, medium_trolley, large_trolley, suitcase_set, backpack, duffel, other]}
  - {key: shell_material, label: Shell material, type: enum, required: true, level: product,
     allowed_values: [abs, polycarbonate, polypropylene, polyester, nylon, leather, aluminium, other]}
  - {key: dimensions_cm, label: Outer dimensions incl. wheels and handle, type: dimensions_cm, required: true, level: variant}
  - {key: volume_l, label: Volume, type: decimal, unit: l, required: true, level: variant}
  - {key: wheels, label: Number of wheels, type: enum, required: true, level: product, allowed_values: ['0', '2', '4']}
  - {key: lock_type, label: Lock, type: enum, required: false, level: product, allowed_values: [none, tsa_combination, key]}
  - {key: expandable, label: Expandable, type: boolean, required: false, level: variant}
  - {key: colour, label: Colour, type: string, required: true, level: variant}
  - {key: set_size, label: Pieces in set, type: integer, required: false, level: variant, min: 1}
  - {key: warranty_months, label: Warranty, type: integer, unit: months, required: false, level: product}
  - {key: cabin_size_claim, label: Marketed as cabin size, type: boolean, required: false, level: variant}
  - {key: country_of_origin, label: Country of origin, type: string, required: false, level: product}
rules:
  cabin_limit_cm: [55, 40, 20]       # configurable; airlines differ
  cabin_claim_rule: >
    cabin_size_claim may be true only if the outer dimensions are within cabin_limit_cm.
    Text may say the size is within common cabin limits, and must never promise acceptance by a named airline.
glossary: de
```

**`oem_brands.yaml`** (start list used only to detect brand names in text; extend it as needed)

```yaml
brands: [brother, canon, epson, hp, hewlett-packard, lexmark, samsung, xerox, kyocera, ricoh, konica minolta, oki]
```

**German glossary starter, `packages/ai/glossary/de.yaml`** (have a native German speaker review it before use)

```yaml
terms:
  ink_cartridge: Druckerpatrone
  toner_cartridge: Tonerkartusche
  drum_unit: Trommeleinheit
  compatible_with: kompatibel zu
  remanufactured: wiederaufbereitet
  page_yield: Seitenreichweite
  ink_volume: Füllmenge
```

**Sample import file for tests and demos** (all names, models and barcodes are fake)

```csv
sku,name,pack,brand,product_kind,condition,colour,compatible_models,oem_part_numbers,page_yield,pack_size,ean,cost_eur,stock
TST-T-BK,Black toner cartridge,ink_toner,ExampleBrand,toner_cartridge,new_compatible,black,"Printer X100; Printer X200",PN-100X,3000,1,0000000000001,6.50,40
TST-T-CY,Cyan toner cartridge,ink_toner,ExampleBrand,toner_cartridge,new_compatible,cyan,"Printer X100; Printer X200",PN-100C,2500,1,0000000000002,8.10,25
TST-I-5P,Ink set 5 colours,ink_toner,ExampleBrand,ink_cartridge,remanufactured,multipack,"Printer Y50",PN-50SET,,5,0000000000003,9.40,12
```

For luggage, add a second sample file with fake cabin and large trolleys, including one row whose dimensions are above the cabin limit and `cabin_size_claim` set to true, so the claim rule has a failing case.

## 16. Definition of done and pitfalls with AI coding agents

An agent can write most of this code, but it will not tell you when it is wrong. Your job shifts from typing to reviewing, and the checklist below is how you keep that review honest.

**A task is done when**

- [ ] Every acceptance item in section 14 is met, and each one is checked by a test or by a manual step you performed.
- [ ] `make test` and `make lint` pass locally and in CI.
- [ ] New tests would fail if the feature were broken (read them; see pitfall 2).
- [ ] No new dependency without a line in `docs/DECISIONS.md`.
- [ ] Any new environment variable is in `.env.example`, and no secret or real seller data is in the diff.
- [ ] Database changes are in an Alembic migration that works on an empty database.
- [ ] The OpenAPI file and generated web client are up to date.
- [ ] `docs/PROGRESS.md` says what changed and what comes next.

**The MVP is done when** the acceptance test in section 2 passes in CI, the security checklist in section 12 is ticked, a lawyer or compliance specialist has reviewed the compliance gates, and at least 3 pilot sellers have used it on real or sandbox accounts.

**Pitfalls and how to avoid them**

| # | Pitfall | What to do |
| --- | --- | --- |
| 1 | **Plausible but wrong marketplace code.** Agents invent endpoint names and fields from memory | Give the agent the official documentation page for each call; verify in the sandbox; record test fixtures only from real sandbox responses, never let the agent write them from imagination |
| 2 | **Tests that only confirm what the code does.** They pass but prove nothing | Read each test against the acceptance line; temporarily break the code and confirm the test fails |
| 3 | **Missing tenant isolation.** One forgotten filter leaks data across sellers | Row-level security plus the automatic isolation test; reject any pull request that bypasses the app role |
| 4 | **Over-building and extra libraries** | Rule 9 in `AGENTS.md`; stop an agent that starts a task not in section 14 |
| 5 | **Invented legal text or compliance claims** | Legal wording only from approved templates; lawyer review; never accept legal copy written by a model |
| 6 | **Secrets in fixtures, logs or commits** | Secret scanning in CI and as a pre-commit hook; never give an agent production keys |
| 7 | **Drift in long sessions.** Quality drops and earlier rules are forgotten | One task per session; start fresh for the next task; the rules file and progress log carry the memory |
| 8 | **Huge changes that cannot be reviewed.** As a rule of thumb, more than about 600 changed lines is too much to review properly | Split the task, or ask the agent to deliver in steps with a commit for each |
| 9 | **Real AI calls in tests.** Cost and flaky results | Tests use a stub provider; only `make eval` calls a real model, and with a budget cap |
| 10 | **Direct pushes and failing builds merged.** | Branch protection on `main`, required CI checks, agents work on branches only |
| 11 | **Real customer data in prompts or fixtures** | Use fake data (section 15); keep real data out of any agent session |

**What only you can do (an agent cannot)**

- Apply for and manage marketplace API approvals and contracts; this starts in week 1 and gates connector testing.
- Get the legal and compliance review done.
- Review German text with a native speaker.
- Decide product questions the spec leaves open; record each decision in `docs/DECISIONS.md`.
- Run the outside penetration test.
- Find and talk to the pilot sellers.

**Honest effort note.** Agents make the writing of code much faster, but integration work (marketplace quirks, approvals, sandbox behaviour, real data) is where most of the time will go, and it cannot be skipped by better prompts. Plan for the time estimate in section 14 to stretch if approvals are slow.

**First three actions:** create the repository, add `AGENTS.md` and this spec as `docs/SPEC.md`, then run task T01 with the template from section 1.
