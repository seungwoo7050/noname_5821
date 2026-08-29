# Third-party notices

Direct dependencies are installed from their official registries at the exact
versions below. npm and uv lock files record package integrity and the complete
transitive graphs. No dependency source or third-party dataset is copied into this
repository.

| Package/artifact | Version | Source | License | Intended use and behavior |
| --- | --- | --- | --- | --- |
| Django | 5.2.17 | PyPI / `django/django` | BSD-3-Clause | authentication, administration, ORM, transactions, forms, HTTP API |
| psycopg (`binary` extra) | 3.3.4 | PyPI / `psycopg/psycopg` | LGPL-3.0-or-later | PostgreSQL protocol; server-side database traffic only |
| jsonschema | 4.26.0 | PyPI / `python-jsonschema/jsonschema` | MIT | checked-in public API fixture validation; no network behavior |
| Ruff | 0.16.5 | PyPI / `astral-sh/ruff` | MIT | local/CI Python linting only |
| Astro | 7.2.9 | npm / `withastro/astro` | MIT | server-rendered public web application and routing |
| `@astrojs/node` | 11.1.4 | npm / `withastro/adapters` | MIT | standalone Node server adapter |
| `@astrojs/check` | 0.9.10 | npm / `withastro/language-tools` | MIT | local/CI Astro and TypeScript checks |
| `@types/node` | 22.20.1 | npm / `DefinitelyTyped/DefinitelyTyped` | MIT | Node 22 type declarations for local contract tests |
| TypeScript | 5.9.3 | npm / `microsoft/TypeScript` | Apache-2.0 | static checking and compilation |
| Vitest | 4.1.11 | npm / `vitest-dev/vitest` | MIT | isolated frontend tests |
| Playwright Test | 1.62.1 | npm / `microsoft/playwright` | Apache-2.0 | local closed-loop browser acceptance |
| PostgreSQL container | `17.6-alpine@sha256:ef257d85f76e48da1c64832459b59fcaba1a4dac97bf5d7450c77753542eee94` | Docker Official Image / `docker-library/postgres` | PostgreSQL | loopback-only local canonical persistence |

The local PostgreSQL container publishes only to `127.0.0.1` and uses PostgreSQL's
trust mode solely for disposable local development with synthetic data. This is a
documented loopback exception, not a production configuration. Production images,
credentials, deployment, and redistribution are outside the MVP.

Registry metadata was reviewed on 2026-08-29. Frozen-install advisory commands are
part of the repository gate. A passing advisory scan is not a complete license or
supply-chain guarantee; transitive license output is retained in gate evidence.
