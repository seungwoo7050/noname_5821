# Fixed product decisions

This is the starting contract for the first implementation session. A fixed
decision changes only through an explicit human decision and a dedicated commit.

## Repository and history

- Expected repository and visibility: The approved project repository is the public GitHub repository `seungwoo7050/audience-foundry-clear-time` with its existing `origin`. Public visibility applies to source and synthetic evidence only; it does not authorize publishing credentials, internal provenance, private operator data, or an unapproved real-observation source.
- Expected baseline branch and commit: Implementation begins on `main` from documentation-only commit `001cf287e7b2ac7e731528302fc0bf1bfd86e36f`. Normal non-force pushes to `origin/main` are authorized; history rewriting remains forbidden.
- Legacy code/history reuse policy: No legacy implementation or history is assumed. Reuse is limited to owner-approved generic starter configuration after license and behavior review; game records, playtime observations, aggregation rules, moderation, and migrations are created for this repository.
- External repositories that are frozen, imported, or out of scope: HowLongToBeat and other game databases are reference products only. Their code, private interfaces, page structure, user submissions, and datasets are not imported or scraped. Existing game, Content Foundry, or other repositories remain untouched unless a later explicit decision defines a lawful one-way interface.

## Product invariants

List statements that must remain true across every successful and failed flow.
Make each statement testable.

1. Every canonical entity uses a product-owned stable identifier; titles, slugs, and store identifiers are not primary identities.
2. Every playtime observation records one game, one platform, one completion scope, a positive whole-minute duration, provenance identity, observation date, and moderation state.
3. Draft and rejected observations never contribute to a public aggregate.
4. An approved observation is immutable. Correction creates a new observation and moderation decision; it does not rewrite the old duration.
5. An aggregate includes only observations whose game, platform, and completion scope exactly match its key.
6. The provisional MVP publishes a median only when at least three eligible observations exist. A smaller set is explicitly `insufficient_data`. Rule `median-v1` uses the middle value for an odd sample and the arithmetic mean of the two middle values for an even sample; an exact half-minute result is rounded up to the next whole minute (`600.5` becomes `601`).
7. Every aggregate revision records its rule revision and exact included observation identities so the displayed value can be reproduced.
8. Approval, rejection, aggregate creation, and aggregate supersession are attributable to an authenticated operator and recorded in append-only audit evidence.
9. Final observation approval, aggregate revision creation, and audit event commit atomically or not at all.
10. Exact duplicate observations are rejected or resolve to the previously accepted operation receipt; they are never counted twice.
11. The public Astro application is read-only and has no authority to approve, alter, delete, or recalculate canonical data.
12. The MVP stores no public user account, payment, personal backlog, or sensitive personal data.
13. No reference service's playtime dataset is treated as product-owned data without a separate human decision covering source, license, attribution, and import method.

## Actors and authority

- Actor identities and trust boundaries: An unauthenticated public visitor may only read published game and aggregate data. An authenticated operator is a Django account controlled by the project owner and may create canonical records, enter observations, make moderation decisions, and publish or retire aggregates. Astro is a read-only system actor. PostgreSQL is the canonical persistence boundary.
- Actions allowed for each actor: Visitors may search and open public pages. Operators may create games, aliases, platforms, observations, approvals, rejections, and superseding corrections. Django may calculate aggregates only under the fixed rule revision. Astro may request versioned public JSON and render it. No other actor mutates data in the MVP.
- Human-only decisions or checkpoints: Creating the first operator account; approving a real observation source; deciding whether two editions are one game or distinct canonical records; approving or rejecting observations; changing category, minimum-sample, or aggregation rules; accepting a dependency or license; running a destructive migration; selecting production hosting; enabling public submissions, analytics, advertising, payment, or production deployment.

## State model

- Initial state: The database contains schema and one authenticated operator but no published game aggregate. Games, aliases, and observations begin as drafts; an aggregate key begins as `insufficient_data`.
- Allowed transitions and actors: An operator may move an observation from `draft` to `approved` or `rejected`. When approval raises the eligible count to at least three, Django calculates and publishes an aggregate revision. A later approved or corrected observation creates a new aggregate revision and supersedes the former one. An operator may retire a game or aggregate from current display without deleting history.
- Terminal, retryable, rejected, and partial-failure states: `rejected` and `retired` are terminal for a specific observation or revision; a new observation or explicit reactivation decision is required. Validation and authorization failures are rejected without mutation. Astro-to-Django read failures are retryable and do not change state. Database or audit failure rolls back the whole approval and aggregate operation; there is no accepted partial state.

## First implementation sequence

1. Prove the riskiest internal interface first: Astro 7 must render one real JSON response from a running Django 5.2 application backed by PostgreSQL, using no mock at the HTTP boundary.
2. Add canonical game, alias, platform, observation, moderation, aggregate-revision, and audit models with database constraints.
3. Add operator authentication and draft entry using Django's existing administration and form capabilities.
4. Add approval, rejection, deduplication, and immutability operations with transaction and audit tests.
5. Implement rule revision `median-v1`: exact key matching, provisional minimum three, median in whole minutes, sample count, and included observation identities.
6. Add the versioned read-only public API that exposes only current approved aggregates or an explicit insufficient-data state.
7. Add Astro Korean/original-title search and the game detail page.
8. Close the synthetic local scenario, then repeat it manually with one owner-approved real game and observation set and record exact identities and evidence.

## Explicit non-goals

The first implementation does not add public accounts or submissions, contributor reputation, personal backlog, recommendations, ratings, reviews, achievements, release calendars, prices, subscription catalogs, store or affiliate links, charts, notifications, external game APIs, automated crawling or scraping, advertising, payment, mobile applications, production infrastructure, or migration from another service.

## Decision-change policy

Only the project owner may change a fixed product decision. A change requires a dedicated commit that updates every affected contract document, states the previous and new decision, identifies evidence or tests, describes recalculation and migration impact, and names any new human checkpoint. No implementation commit may silently change a completion category, eligibility rule, minimum sample, statistic, authority boundary, provenance rule, or MVP acceptance outcome. A rule change that can alter a displayed value requires a new named rule revision and deterministic recomputation evidence.

## Approved decision changes

- 2026-08-29 repository decision: The owner replaced the provisional `clear-time` identity and undecided remote visibility with public repository `seungwoo7050/audience-foundry-clear-time`, retained `main`, authorized ordinary non-force pushes to the existing `origin`, and recorded baseline `001cf287e7b2ac7e731528302fc0bf1bfd86e36f`. Read-only Git and GitHub checks verified that local `HEAD` and `origin/main` matched that commit before this change. This decision changes no product data, aggregation result, schema, migration, or external provider. The existing checkpoints for secrets, real-observation source approval, production, legal terms, and destructive migration remain unchanged.
- 2026-08-29 `median-v1` whole-minute decision: The owner resolved the previously unspecified even-sample half-minute case by approving arithmetic median rounded half-up to a whole minute. For integer-minute inputs this affects only exact `.5` results, for example `600.5` becomes `601`. No aggregate data existed when the decision was recorded, so no migration or recalculation is required. Focused odd, even-integer, and even-half tests plus deterministic replay are required; later changes require a new rule revision and recalculation evidence.
