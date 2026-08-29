#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$repo_root"
gate_secret=$(openssl rand -hex 32)
export DJANGO_SECRET_KEY="$gate_secret"
export UV_CACHE_DIR="$repo_root/.cache/uv"
mkdir -p output/playwright

docker compose -f infra/local/compose.yaml up -d --wait
cd apps/backend
uv sync --frozen
uv run python manage.py migrate
uv run python manage.py load_synthetic_mvp >/dev/null
cd ../web
fnm exec --using 22.22.0 npm ci
cd ../..

make check
make test
make build
cd apps/backend
uv run pip-audit --local
cd ../web
fnm exec --using 22.22.0 npm audit --audit-level=critical
cd ../..
./scripts/check-secrets.sh
uv run --project apps/backend python scripts/check_python_licenses.py
fnm exec --using 22.22.0 node scripts/check_node_licenses.mjs
make browser
git diff --exit-code
git diff --cached --exit-code
