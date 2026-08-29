# Completion report

## Delivered outcome

- User-visible closed loop: An authenticated Django operator workflow owns games,
  aliases, platforms, immutable observations, moderation, audited operation
  receipts, and atomic `median-v1` revisions. The read-only `public-api/v1` feeds
  an Astro 7 Korean/original-title search and Korean detail page. The synthetic
  accepted case displays 720 minutes as 12 hours, sample count 3, `main_story`,
  PC, rule `median-v1`, and revision 1.
- Explicit non-goals preserved: No public account or mutation, real-data import,
  scraping, external game API, analytics, advertising, payment, backlog, email,
  production infrastructure, deployment, or reference-service code/data was
  added or inspected.
- Gated implementation local/remote commit and branch: local `HEAD` and
  `origin/main` were both `f29c420e0144823bb5fb8f68f8eb338697a24158` on `main` when the final
  implementation gate passed. The report-only closure commit is identified in
  the final handoff because a commit cannot contain its own SHA.
- Origin and visibility: `https://github.com/seungwoo7050/audience-foundry-clear-time.git`,
  public, ordinary non-force pushes only.
- Clean/dirty state: clean before and after the gate on `f29c420`; ignored local
  build, cache, Playwright, and synthetic PostgreSQL artifacts remain outside Git.

## Local execution procedure

1. Use Node 22.x, Python 3.12.x, uv, fnm, Docker Compose v2, and inject a local
   `DJANGO_SECRET_KEY` through an owner-controlled runtime environment.
2. Run `make local-up`, `make migrate`, and from `apps/backend` run
   `uv run python manage.py load_synthetic_mvp` for labeled synthetic data.
3. Run `make gate`. This performs frozen installs, checks, tests, builds,
   advisories, license and secret checks, fixture replay, and browser acceptance.
4. For manual local serving, run Django on loopback port 8000 and the built Astro
   Node server with server-only `API_BASE_URL=http://127.0.0.1:8000` on port 4321.

## Evidence

- Focused checks: 28 Django/PostgreSQL tests passed: 2 viability, 5 model/constraint,
  7 draft/operation, 7 moderation/rollback, 1 real two-thread concurrency, 5 API
  producer/schema/privacy, and 1 fixture-idempotency test. Six Vitest tests passed:
  four API consumer/retry/compatibility and two Korean formatting tests.
- Full repository gate: `make gate` passed on exact clean commit `f29c420` on
  2026-08-29. It included `uv sync --frozen`, `npm ci` (415 audited packages),
  Ruff, Django system check, migration drift, all 34 backend/frontend tests, Astro
  type checks, the production server build, pip-audit, npm audit, secret scan,
  Python and Node license metadata, and five Playwright Chromium scenarios.
- Positive scenario: Real local PostgreSQL 17.6, Django 5.2.17, Astro 7.2.9,
  Node 22.22.0, HTTP, and Chromium rendered Korean and original alias search and
  the same UUID detail page with 12 hours, sample 3, PC, main story, and revision 1.
- Negative, retry, partial-failure, and rollback scenarios: Tests prove non-operator
  rejection, CSRF 403/public-method rejection, admin login redirect, invalid and
  fractional minutes, missing date/provenance checks, unsupported scope, oversized
  search 400, missing game 404, duplicate fingerprint, operation replay and
  conflict, terminal immutability, draft/rejected/exact-key exclusion, one-current
  concurrency, one retry for 503 and no retry for 400, controlled backend-unavailable
  503, and a simulated exception immediately before audit that rolls back the
  decision, observation transition, revision, pointer, and audit event.
- Restart and deterministic replay: After restarting the PostgreSQL container, the
  fixture loader returned the same operation, observation, decision, aggregate,
  included-observation, and audit identities with revision number still 1.
- API evidence: The persisted public detail response was 499 bytes with SHA-256
  `a9f51325676521294ee21866ae336a1a09e0f19dfbd99970f656a1ca840cabd7`.
- Real interface evidence versus mocks/simulations: PostgreSQL persistence,
  Django-to-database, Astro-to-Django HTTP, Chromium rendering, HTTP refusal on an
  unused backend port, and container restart are real local integration evidence.
  Domain records are synthetic. The transaction interruption uses an explicitly
  labeled test hook. No third-party sandbox or production evidence is claimed.
- Visual evidence: Playwright generated ignored local screenshots for the positive
  detail and backend-unavailable pages; CLI snapshot QA confirmed the search and
  detail accessibility trees. These contain synthetic public data only.

## Synthetic evidence identities

- Game: `11111111-1111-4111-8111-111111111111`; aliases:
  `44444444-4444-4444-8444-444444444441`,
  `44444444-4444-4444-8444-444444444442`; platform:
  `22222222-2222-4222-8222-222222222222`.
- Accepted observation 1: `f931d388-9266-4d79-b1ea-06d89ebab4ae`; draft operation
  `00000000-0000-4000-8000-000000000001`; draft audit
  `35732018-39a5-4359-b23b-3bf53aeea571`; decision
  `a905ea75-b9a2-4b00-a64d-317b0bf76b8b`; moderation operation
  `10000000-0000-4000-8000-000000000001`; moderation audit
  `9c91954a-8624-4727-8936-2cb502719725`.
- Accepted observation 2: `89b76681-a09e-46d6-a7bd-2c2f0de24cf2`; draft operation
  `00000000-0000-4000-8000-000000000002`; draft audit
  `5a5fb30e-1365-48d5-a499-e0bed54a5c56`; decision
  `7adcd2fd-0c28-401f-b849-89ce310a70bb`; moderation operation
  `10000000-0000-4000-8000-000000000002`; moderation audit
  `adb7e384-9b0e-4f10-803e-8fe38c1fff8d`.
- Accepted observation 3: `738eee9c-284b-486c-abb9-559b4e548922`; draft operation
  `00000000-0000-4000-8000-000000000003`; draft audit
  `71d4451c-7379-400e-a361-b6cf049ac246`; decision
  `051ed175-db6b-433d-a1b8-0ea92470ee7f`; moderation operation
  `10000000-0000-4000-8000-000000000003`; moderation/publish audit
  `cf7ae08b-67fd-4eda-b74d-917b1cd2a7ae`.
- Aggregate key: `fc14b335-d236-4ed0-a297-c5a05a9a6dca`; aggregate revision:
  `d967a3fe-467c-4e87-83be-8e84838e1353`, revision 1, `median-v1`, 720 minutes,
  sample 3. Ordered included observations: `738eee9c-284b-486c-abb9-559b4e548922`,
  `89b76681-a09e-46d6-a7bd-2c2f0de24cf2`,
  `f931d388-9266-4d79-b1ea-06d89ebab4ae`.
- Negative controls: rejected observation `9d46b635-d2e4-426d-84f5-0ca3f5406d0e`,
  draft audit `877947c1-339c-406a-8333-d3b2527d2552`, rejection audit
  `f1eecc0a-d324-4301-a7a1-37b275d02b4a`; retained draft observation
  `15dd6132-f37f-45e8-a409-32e8ed44ed60`, audit
  `dd6ee10c-8827-444f-b700-b1d2f4ccffdd`.

## Safety and compatibility

- Security/privacy/authorization implications: Astro has no write connection or
  canonical authority. Django session, CSRF, staff checks, row locks, database
  constraints, atomic transactions, and append-only service boundaries protect
  writes. Public JSON omits provenance, raw observations, operations, audit data,
  credentials, and operator identity. No visitor account or behavior is stored.
- Secret-handling evidence: The full gate scans tracked source and built web assets;
  no credential-like value or literal server secret was found. Runtime signing keys
  are generated or injected and never committed. Screenshots contain synthetic
  public display data only.
- Dependency/license/advisory result: Exact direct versions and integrity locks are
  committed. pip-audit and npm audit reported no known vulnerabilities. License
  metadata passed for 40 installed Python distributions and 323 installed Node
  packages; direct provenance and licenses are recorded in `THIRD_PARTY_NOTICES.md`.
  These checks do not claim zero supply-chain or legal risk.
- Data migration and backward compatibility: `catalog.0001_initial` is the only
  product migration and is non-destructive from the documentation baseline. It
  applies to an empty PostgreSQL 17 database and reports no model drift. No real
  data migration, destructive rollback, backup restore, or older API consumer
  exists. `public-api/v1` producer and consumer share checked JSON Schemas.
- External state changed and recovery: Authorized non-force commits were pushed to
  the public GitHub `main` branch. Local Docker created one loopback PostgreSQL
  container/network/volume containing synthetic data; `make local-down` stops it,
  and the disposable volume may be removed only through an explicit destructive
  cleanup decision. Git atoms are independently revertible with ordinary revert
  commits; pushed history was not rewritten.

## Remaining work

- Human or account checkpoints: The owner must create the first real operator
  account through a local secret-entry procedure, select and approve one real game
  identity and permitted observation source, approve at least three real
  observations, verify category/platform/median/sample/revision, capture permitted
  manual evidence, and approve any next step. No credential or real source value
  was requested or recorded here.
- Blockers and claims not proved: The synthetic local MVP has no implementation
  blocker. The required owner-approved real-data repeat and its backup/restore are
  not proved. No third-party sandbox, preview, production, public traffic,
  production backup, production security, provider account, domain/trademark,
  legal-source, or deployment claim is made.
- Known risks and deferred scope: PostgreSQL trust mode is a documented
  loopback-only synthetic-development exception. Production TLS, rate limiting,
  monitoring, retention, 2FA, recovery, abuse controls, public accounts,
  contributions, analytics, payment, and external data remain explicitly deferred.
