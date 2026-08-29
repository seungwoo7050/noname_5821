#!/bin/sh
set -eu

secret_pattern='(-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----|AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,})'
if git grep -qE "$secret_pattern" -- . ':(exclude)scripts/check-secrets.sh'; then
  echo "secret scan failed: a credential-like value exists in tracked content" >&2
  exit 1
fi

if git grep -qE '(DJANGO_SECRET_KEY|POSTGRES_PASSWORD)=[A-Za-z0-9]' -- .; then
  echo "secret scan failed: a tracked secret variable has a literal value" >&2
  exit 1
fi

if [ -d apps/web/dist ] && rg -q 'DJANGO_SECRET_KEY|POSTGRES_PASSWORD|synthetic-runtime-only' apps/web/dist; then
  echo "secret scan failed: a server-only marker exists in built web assets" >&2
  exit 1
fi

echo "secret scan passed: tracked source and built web assets"
