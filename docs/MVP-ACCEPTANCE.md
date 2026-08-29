# MVP acceptance and evidence

The MVP is complete only when one real user outcome is closed and every blocking
invariant has evidence. Distinguish unit simulation, local integration, sandbox,
manual acceptance, and production evidence.

## Primary closed-loop scenario

- Preconditions and exact inputs: A clean local PostgreSQL 17.x database at the current migration revision; running Django 5.2.x and Astro 7.x processes; one active operator account; contracts `public-api/v1` and aggregation rule `median-v1`; and a synthetic fixture containing game slug `sample-game`, Korean alias `샘플 게임`, original alias `Sample Game`, platform code `PC`, completion scope `main_story`, three observations of 600, 720, and 900 whole minutes, observation date `2026-08-29`, and provenance identities `urn:local-fixture:playtime-001` through `003`. Manual acceptance repeats the loop with one owner-selected real game and at least three owner-controlled permitted observations.
- User actions: The operator logs in, creates the game, aliases, platform, and three draft observations, reviews each, and explicitly approves each observation. A visitor searches for the Korean alias and opens the result.
- System actions: Django authenticates and validates each operation, excludes drafts and rejections, and on the third approval atomically calculates `median-v1` as 720 minutes with sample count 3, stores the ordered included-observation identities, creates aggregate revision 1 and audit evidence, and exposes it through `/api/v1`. Astro fetches the real API response and renders 12 hours, sample count 3, scope, platform, and revision.
- Durable outcome: PostgreSQL contains the canonical game, three approved immutable observations, current aggregate revision, included-observation set, moderation decisions, and audit events. A clean restart preserves them, deterministic replay reproduces 720 minutes, and the public page renders the same revision. Draft and rejected data remain absent.
- Evidence and exact identity/revision: The completion evidence records repository commit SHA, migration revision, game UUID, alias UUIDs, platform UUID, three observation UUIDs and operation UUIDs, moderation-decision UUIDs, aggregate key, aggregate-revision UUID and number, ordered included-observation UUIDs, rule `median-v1`, audit-event UUIDs, API contract `public-api/v1`, JSON response hash, Playwright result, deterministic replay output, and manual screenshot or captured HTML for both the synthetic and owner-approved real record. Local integration and manual evidence are required; sandbox and production evidence are explicitly not claimed.

## Blocking negative scenarios

Define expected failure and proof for each applicable case.

- Unauthorized or unapproved action: An unauthenticated or non-operator request cannot create, approve, retire, or inspect internal observations and receives login or 403. A draft or rejected observation requested through the public API is absent and cannot affect sample count. Evidence is an authorization test plus API and browser checks.
- Invalid or conflicting data: Missing provenance or observation date, zero or negative minutes, fractional minutes, unsupported completion scope, invalid parent identity, conflicting normalized alias, or attempt to edit an approved observation is rejected with a stable code. Entity counts and the current aggregate revision prove that no invalid value was included.
- Duplicate/replay/concurrent request: Replaying the same operation UUID and payload returns the prior receipt; reusing it with different input is rejected. A duplicate fingerprint is not counted. Concurrent final approvals cannot create two current aggregate revisions or include an observation twice. Database constraints, deterministic replay, and concurrency tests provide evidence.
- External timeout or failure: Because there is no third-party provider, the applicable external failure is Astro-to-Django HTTP unavailability. A forced timeout or 503 produces a controlled unavailable page with a correlation identity, no guessed or stale playtime claim, and no database mutation. This is local integration evidence, not provider sandbox evidence.
- Partial write or interrupted transaction: A forced exception between observation approval, eligible-set selection, aggregate calculation, revision creation, current-pointer update, and audit creation leaves none of those changes committed. A subsequent retry with the same operation UUID succeeds once or resolves the prior receipt.
- Secret or sensitive-data exposure: Built Astro assets, rendered HTML, API errors, screenshots, logs, and fixtures contain no database password, Django secret, session cookie, operator password, private header, or unapproved raw provenance body. Automated secret scanning and manual inspection provide evidence.
- Migration/rollback incompatibility: The schema migrates from the documentation baseline to the MVP schema on an empty database. Any destructive migration is blocked without owner approval, backup, dry run, deterministic aggregate comparison, and restore evidence. A recorded backup can restore the accepted real game, observations, aggregate, and audit identities in a disposable environment.

## Required gates

- Focused checks per implementation atom: Unit simulation for title normalization, positive whole-minute validation, fixed completion scopes, draft exclusion, approval immutability, duplicate and operation identities, exact aggregate-key matching, minimum sample, odd and even median behavior, included-observation reproducibility, current-revision uniqueness, authorization, audit redaction, and transaction rollback; contract checks for every API field introduced.
- Full local repository gate: Frozen installs from both lock files, static and framework checks, no migration drift, all backend and frontend tests, deterministic aggregate replay, schema producer/consumer validation, production builds, secret and license checks, and Playwright closed-loop and negative browser scenarios from a clean checkout.
- Smallest real external-interface spike: Before expanding domain models, Astro must fetch and render one live Django JSON response backed by PostgreSQL over real local HTTP. No mock is accepted at the Astro-Django boundary. There is no third-party sandbox requirement.
- Manual human checkpoint: The owner creates the operator account, approves the first real observation source and game identity, approves the three real observations, verifies the displayed category, platform, median, sample count, and revision, records exact identities, and decides whether implementation may proceed toward public contributions, preview, or production. Production deployment, provider terms, 2FA, payment, analytics, public consent, or data import require later checkpoints.
- Dependency, security, privacy, and license checks: Every direct dependency has a pinned identity, known license, advisory review, and stated network/data behavior; no reference-site dataset or private interface is imported; no visitor personal data or play history is collected; operator secrets remain server-side; and the absence of payment, public accounts, analytics, advertising, and production claims is verified.

## Completion report

Require exact local and remote commit SHA, clean state, checks actually run, success
and failure evidence, external state changed, rollback path, blockers, deferred
work, and any claim that could not be proved.

For this MVP, the report must also list every accepted observation and aggregate identity named above, identify the real observation source only to the extent permitted by its reuse decision, state that no third-party account or production state was changed, and distinguish unit simulation, local integration, manual acceptance, sandbox evidence, and production evidence. A remote SHA is `Not applicable` until a remote repository exists; it must never be invented.
