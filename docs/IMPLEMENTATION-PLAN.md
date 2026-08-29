# Implementation plan

Each row is one reviewable commit atom and answers one primary review question.

| Atom | Review question and purpose | Expected files/dependencies | Focused proof | Rollback boundary | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | Does the repository contract name the approved public origin, branch policy, and exact baseline? | `docs/PRODUCT-DECISIONS.md`, `docs/DOMAIN-BRIEF.md` | clean Git state; local and remote baseline comparison | documentation-only decision commit | complete (`3b17c60`) |
| 2 | Is the MVP decomposed into independently reviewable and provable changes before code? | this plan | required fields and ordering review; `git diff --check` | plan-only commit | in progress |
| 3 | Can contributors reproduce the fixed Python, Node, Astro, Django, and PostgreSQL dependency graph without product behavior? | root scripts, `apps/backend` and `apps/web` manifests/locks, `infra/local`, notices | frozen installs; framework version checks; license/advisory review | dependency/scaffold commit; no domain migration | planned |
| 4 | Can Astro 7 render a live Django 5.2 JSON response backed by PostgreSQL 17 over HTTP? | minimal backend viability endpoint, Astro viability route, live smoke script/tests | real PostgreSQL query, running Django and Astro, HTTP response and rendered HTML; no HTTP mock | viability-only behavior commit | planned |
| 5 | Does PostgreSQL enforce the canonical identity, scope, lifecycle, and one-current-revision contracts? | domain models, migrations, deterministic synthetic fixture, model tests | migration drift, constraint and exact-key tests | forward schema migration; empty local DB can be recreated | planned; size exception below |
| 6 | Are draft entry, operation identity, duplicate rejection, authorization, immutability, and audit redaction enforced? | domain service/admin/forms and focused tests | authorization, validation, replay/conflict, duplicate, immutable-state, redaction tests | service/admin commit; schema from atom 5 retained | planned; size exception below |
| 7 | Does moderation atomically approve/reject, calculate `median-v1`, supersede revisions, and roll back on failure? | transactional moderation service and focused tests | minimum-three, odd/even median, draft/rejected exclusion, concurrency guard, replay, audit failure rollback | moderation commit; revert restores draft-only behavior | planned; size exception below |
| 8 | Does `public-api/v1` expose only public current state with a checked producer/consumer contract? | versioned URLs/views, JSON Schema/examples, backend contract tests, web client tests | schema validation, alias search, detail, insufficient data, 400/404, no internal fields | read-only API contract commit | planned |
| 9 | Can a Korean-speaking visitor search aliases and read the matching aggregate without gaining write authority? | Astro search/detail/unavailable routes, styles, frontend and browser tests | Korean/original alias, 12-hour display, sample/scope/revision, bounded input, controlled 503, secret inspection | presentation-only commit | planned; size exception below |
| 10 | Does the closed loop survive restart and cover negative, retry, partial-failure, and rollback scenarios? | integration/Playwright scripts and evidence generated from synthetic fixtures | live end-to-end run, deterministic replay, restart persistence, failure injection, secret scan | test/evidence tooling commit; no product mutation | planned |
| 11 | Does the full repository gate pass on the exact final implementation commit? | gate scripts and any blocking fixes | frozen installs, checks, tests, builds, schema/migration drift, licenses/advisories, secret scan, Playwright | gate/fix commit where needed; no history rewrite | planned |
| 12 | Does the report distinguish proved synthetic/local evidence from the pending human-approved real-data checkpoint? | `docs/COMPLETION-REPORT.md` | final SHA/branch/origin/clean checks; remote SHA comparison | documentation-only closure commit | planned |

## Ordering rationale

The approved repository decision and this plan precede code. Reproducible dependency
and local-service scaffolding is isolated next. The smallest real Astro–Django–
PostgreSQL interface is then exercised before domain models depend on it. Schema
and deterministic fixtures establish contracts before write behavior. Draft and
identity rules precede transactional moderation; failure and rollback proof lands
with the behavior it protects. The versioned read contract precedes the public UI.
Live browser and restart evidence follow the closed loop, then the exact final
implementation commit receives the full gate. The completion report is last so it
can describe verified state without mixing report cleanup into behavior.

## Size exceptions

Atoms 5–7 and 9 may exceed 200 meaningful lines because a Django migration and its
model constraints, an atomic audited state transition and its failure tests, and a
complete Astro route with its accessibility/error proof are respectively
inseparable validation and rollback units. Within each atom, production behavior
is kept in one primary module where practical and tests are colocated. Lockfiles,
framework-generated migration metadata, and formatting churn are excluded from
the meaningful-line count and remain isolated from later behavior.

## Blocking findings

No readiness blocker remains after owner approval of the public repository,
existing origin, `main` push policy, and baseline SHA. The real-data acceptance
repeat remains a human checkpoint because the owner has not yet selected and
approved a real game or observation source. It cannot be replaced by synthetic
evidence and does not authorize inspecting a reference service or external data.
Security, authorization, data-integrity, destructive-migration, secret-exposure,
idempotency, audit-atomicity, or interface-compatibility failures discovered by an
atom stop dependent implementation until resolved.
