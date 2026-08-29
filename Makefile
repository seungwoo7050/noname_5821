SHELL := /bin/sh
UV := UV_CACHE_DIR=../../.cache/uv uv
NODE := fnm exec --using 22.22.0

.PHONY: check test build gate local-up local-down migrate

check:
	cd apps/backend && $(UV) run ruff check .
	cd apps/backend && $(UV) run python manage.py check
	cd apps/backend && $(UV) run python manage.py makemigrations --check --dry-run
	cd apps/web && $(NODE) npm run check

test:
	cd apps/backend && $(UV) run python manage.py test
	cd apps/web && $(NODE) npm test

build:
	cd apps/web && $(NODE) npm run build

gate:
	./scripts/full-gate.sh

browser:
	cd apps/web && $(NODE) npm run test:browser

local-up:
	docker compose -f infra/local/compose.yaml up -d --wait

local-down:
	docker compose -f infra/local/compose.yaml down

migrate:
	cd apps/backend && $(UV) run python manage.py migrate
