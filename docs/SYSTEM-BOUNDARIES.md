# System boundaries

## Ownership

- Data and behavior this product owns: Canonical game, alias, platform, completion-scope, and observation identities; provenance records; moderation state; duplicate rules; aggregate eligibility and median calculation; aggregate revisions; search ranking for recorded aliases; audit evidence; the read-only public API; and Korean-language public presentation.
- Data and behavior owned by users: Public visitors own their browser requests and local browser state. The MVP does not collect visitor accounts, play histories, backlogs, reviews, or submissions. Operators remain responsible for the truthfulness and permitted use of the observations they enter.
- External or frozen systems: Human-reviewed game pages, personal records, documents, or other allowed sources remain owned by their publishers or creators. HowLongToBeat and similar services are frozen references, not providers. The browser, operating system, container runtime, and open-source dependencies are external infrastructure.
- Systems explicitly outside the MVP: Third-party game metadata, store, price, subscription, achievement, authentication, email, analytics, advertising, payment, object-storage, and notification providers; public contribution systems; personal backlog import; Content Foundry integration; production deployment; and automated scraping.

## Context and data flow

Describe the first loop as ordered trust-boundary crossings. Identify the source of
truth at every step.

1. Outside the product, the operator prepares an owner-controlled or permitted observation and decides it may be entered. The original source remains authoritative for itself; the product owns only the normalized observation and its provenance record.
2. Through the authenticated Django operator interface, the operator submits game identity, alias, platform, completion scope, minutes, provenance identity, observation date, and a unique operation UUID. Django is the validation and authorization authority.
3. PostgreSQL stores the draft observation and audit evidence in one transaction. PostgreSQL is the source of truth for product-owned state.
4. Through a separate authenticated action, the operator approves or rejects the observation. Approval locks the aggregate key, identifies all eligible observations, and either preserves `insufficient_data` or creates a new `median-v1` aggregate revision atomically with the audit event.
5. Astro sends a server-side read request to the Django public API. Django returns only current canonical games and approved aggregate revisions under contract `public-api/v1`.
6. Astro renders Korean-title search results and a game detail page. Astro is the presentation authority, not a data or calculation authority.
7. The visitor's browser receives public HTML. No visitor input crosses into the canonical write boundary in the MVP.

## External interfaces

For each interface, complete one entry.

### Operator browser to Django operator interface

- Owner and exact version/revision: Product-owned Django application on Python 3.12.x and Django 5.2.x LTS; operator-form contract revision `ops/v1`, verified by integration tests against the running application.
- Input contract: HTTPS or local HTTP form submissions containing an operation UUID, canonical game or alias values, platform, completion scope, positive whole-minute duration, provenance identity, observation date, and an explicit operator action.
- Output contract: Success or validation HTML response, stable operation receipt, resulting entity or aggregate revision identity when created, and corresponding audit-event identity. Rejections return field or invariant codes and never alter a public aggregate.
- Authentication and secret boundary: Django session authentication and CSRF protection. Credentials and secret keys terminate at Django and are never passed to Astro or stored in page source, fixtures, or logs.
- Error and timeout behavior: Authorization failure returns login or 403; validation conflict returns 400-equivalent form errors; server failure returns 5xx. A timed-out browser request may be retried only with the same operation UUID.
- Retry/idempotency behavior: The operation UUID is unique. Replaying a completed operation returns or identifies the prior receipt; a conflicting payload under the same UUID is rejected. Observation fingerprint and aggregate-key constraints prevent duplicate counting or two current aggregate revisions.
- Smallest real viability proof: Log in locally as the real operator account, create three observations, approve them, and verify the observation, aggregate revision, included-observation set, and audit identities directly in PostgreSQL.
- Mutation and rollback boundary: Django owns the mutation and calculation. Observation state, aggregate revision, current pointer, and audit event commit in one PostgreSQL transaction. Failure rolls the transaction back; correction uses a new observation and aggregate revision rather than destructive editing.

### Astro public application to Django read API

- Owner and exact version/revision: Both sides are product-owned. Astro 7.x consumes Django contract `public-api/v1`; compatibility is verified with checked-in schema and live contract tests.
- Input contract: Server-side `GET` requests by canonical game identifier, exact normalized alias, or bounded search query. Optional filters are limited to recorded platform and completion scope. No mutation body or credential is accepted.
- Output contract: UTF-8 JSON containing current canonical game data and either an approved aggregate revision with median minutes, sample count, rule revision, and revision identity, or an explicit `insufficient_data` state. Errors use stable codes and correlation identity without stack traces.
- Authentication and secret boundary: Public read endpoints require no user credential. Internal network locations may be configuration values, but no backend secret is embedded in browser JavaScript or Astro-generated HTML.
- Error and timeout behavior: Astro uses a 2-second connection and 5-second total request budget by default. Invalid input is 400, missing game is 404, and backend unavailability becomes a controlled 503 page rather than a guessed playtime.
- Retry/idempotency behavior: `GET` is side-effect free. Astro may make one retry for a connection reset or 502/503 and must not retry a 4xx response. Aggregate revision identity permits response comparison.
- Smallest real viability proof: A running Astro process fetches one real `median-v1` aggregate from a running Django process over HTTP with PostgreSQL persistence and renders median, sample count, scope, platform, and revision; no mock is used at this interface.
- Mutation and rollback boundary: Not applicable because the interface is read-only. Failure changes no canonical state.

### Public browser to Astro application

- Owner and exact version/revision: Product-owned Astro 7.x public UI; page contract revision `web/v1`, verified by browser tests and manual acceptance.
- Input contract: A bounded game-title search query or canonical public URL, optionally with a recorded platform and completion scope. The MVP accepts no account, play history, review, upload, backlog, or payment data.
- Output contract: Accessible HTML containing search results or one game detail page. A published aggregate shows scope, platform, median, sample count, and revision; insufficient data is explicit; drafts and rejected observations are absent.
- Authentication and secret boundary: No visitor authentication. Astro must not expose Django operator routes, cookies, environment secrets, raw provenance details marked internal, or internal audit content.
- Error and timeout behavior: Invalid or oversized search input receives a validation response. A Django API failure produces a controlled unavailable state and correlation identity, not a cached or invented duration.
- Retry/idempotency behavior: Browser reads are side-effect free and may be repeated. The application does not persist visitor search history in the MVP.
- Smallest real viability proof: A browser search by the recorded Korean title opens the approved detail page; a negative scenario cannot expose or count a draft or rejected observation.
- Mutation and rollback boundary: Not applicable because the public UI is read-only.

## Provider and account readiness

No third-party provider account is required for the local MVP. The owner must create the initial Django operator account and enter local secret values manually. Implementation must stop for human approval before using a real observation source whose reuse terms are unclear, adding public login or contributions, enabling 2FA, accepting provider legal terms, creating production identifiers, entering deployment credentials, collecting user consent, adding analytics or advertising, importing a backlog, or deploying to production. Payment is not applicable to the MVP.

## Legacy and migration boundary

There is no approved legacy implementation, playtime dataset, user account set, runtime state, or external contract. Reference services may be observed manually for product understanding but must not be read through private interfaces, copied, crawled, or treated as seed data. A future import requires an explicit decision naming the source owner, license or permission, exact schema revision, provenance retention, duplicate and edition strategy, dry-run evidence, rollback, and migration checkpoint. Until then, all external repositories and datasets remain untouched.
