SHELL := /bin/sh
UV := UV_CACHE_DIR=../../.cache/uv uv

.PHONY: check test build gate local-up local-down migrate

check:
	cd apps/backend && $(UV) run ruff check .
	cd apps/backend && $(UV) run python manage.py check
	cd apps/backend && $(UV) run python manage.py makemigrations --check --dry-run
	cd apps/web && npm run check

test:
	cd apps/backend && $(UV) run python manage.py test
	cd apps/web && npm test

build:
	cd apps/web && npm run build

gate: check test build
	./scripts/check-secrets.sh

local-up:
	docker compose -f infra/local/compose.yaml up -d --wait

local-down:
	docker compose -f infra/local/compose.yaml down

migrate:
	cd apps/backend && $(UV) run python manage.py migrate
