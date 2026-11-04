# Commerce OS developer commands (spec section 13).
# Each recipe line is one plain command so it runs under both sh (CI) and cmd (Windows).

WEB := npm --prefix apps/web

.PHONY: setup dev test lint eval e2e openapi migrate seed

setup:
	uv sync --locked
	$(WEB) ci
	docker compose up -d --wait
	$(MAKE) seed

dev:
	docker compose up -d --wait
	$(WEB) run dev

test:
	uv run pytest
	$(WEB) test

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy
	$(WEB) run lint
	$(WEB) run format:check
	$(WEB) run typecheck

# Placeholders: these fail on purpose until the task named below builds them.
eval:
	@echo make eval is not implemented yet: it is built in T19.
	@exit 1

e2e:
	@echo make e2e is not implemented yet: it is built in T09.
	@exit 1

openapi:
	@echo make openapi is not implemented yet: it is built in T02.
	@exit 1

migrate:
	@echo make migrate is not implemented yet: it is built in T03.
	@exit 1

# Succeeds so that make setup passes; there is no schema to seed until T03.
seed:
	@echo make seed: nothing to seed yet, the schema arrives in T03.
