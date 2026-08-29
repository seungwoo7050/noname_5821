# Domain brief

## Product identity

- Working name: 클리어타임 (Clear Time). This is a working name only; trademark and domain availability have not been checked.
- One-sentence product: A Korean-language game database that publishes provenance-preserving playtime aggregates so a player can judge whether a game fits the time available.
- Business owner or decision maker: The project owner. No delegated product decision maker is established for the MVP.

## Customer and problem

- First customer segment: Korean-speaking PC and console players choosing what to start or finish based on limited free time.
- Primary user and actor roles: Public visitor who searches and reads; authenticated operator who creates canonical game records, enters playtime observations, moderates them, and publishes aggregates. Public contributors and personal backlog users are outside the MVP.
- Painful job or unmet need: A player needs a consistent estimate for a defined completion scope and platform, with sample size and provenance, rather than an unexplained number attached to an ambiguous game title.
- Current workaround and its cost: The player checks foreign-language playtime databases, store reviews, forums, videos, and personal notes. The cost is title translation, inconsistent completion categories, uncertain sample quality, and repeated comparison.
- Why this is worth solving now: The project will test whether a Korean-language, structured playtime dataset can attract useful search visits while keeping the raw observations, aggregation rules, and moderation history under the owner's control.

## First closed loop

1. An authenticated operator creates one canonical game with Korean and original-title aliases and one platform record.
2. The operator records three synthetic or owner-controlled playtime observations for the same completion scope and platform, each with minutes, provenance identity, observation date, and a unique operation identity.
3. Django validates and stores the observations as drafts. The operator explicitly approves each observation; rejected and draft observations remain excluded.
4. When the provisional minimum of three approved observations is reached, Django calculates a median, sample count, and immutable aggregate revision in the same transaction as the final approval and audit event.
5. Astro requests the current approved aggregate through the versioned Django read API and renders a Korean-language game detail page.
6. A public visitor searches by Korean or original title and sees the completion scope, platform, median playtime, sample count, and aggregate revision.
7. The durable outcome is the retained raw observations, moderation decisions, aggregate revision, and audit evidence that reproduce the displayed value.

## Success measures

State measurable MVP outcomes and unacceptable failures.

- Success: With one owner-approved real game record and at least three owner-controlled observations, a visitor can find the game using a recorded alias and see the correct median, sample count, scope, platform, and revision. The page, API, aggregate row, included observation identities, and audit events agree.
- Unacceptable failure: A draft or rejected observation changes a public aggregate; the displayed value cannot be reproduced from its included observations; different completion scopes or platforms are mixed; a duplicate observation is counted twice; or data is copied from HowLongToBeat or another source without an explicit source and reuse decision.

## Scope

- MVP capabilities: Operator authentication; canonical game, alias, platform, and playtime-observation entry; draft validation; approval or rejection; provisional minimum-sample rule; median and sample-count calculation; immutable aggregate revisions; append-only audit evidence; Korean/original-title search; one public game detail page; Astro-to-Django contract tests.
- Explicit non-goals: Public registration or submissions, personal backlogs, recommendations, ratings, reviews, achievements, price or subscription availability, store links, release calendars, multiplayer duration, difficulty modeling, charts, email, analytics providers, advertising, payment, scraping, third-party game-data APIs, and production deployment.
- Later possibilities that must not shape the first implementation: Public contributions and contributor trust, additional statistics and outlier policies, platform comparisons, completion planning, backlog import, subscription-catalog and price data, alerts, charts, recommendations, affiliate links, advertising, and mobile applications.

## Domain language

- **Game:** The canonical product-owned identity for one game. A title, edition label, or store identifier is not its identity.
- **Game alias:** A Korean, original-language, English, alternate, or edition search label linked to one game.
- **Platform:** A controlled product-owned value such as a PC or console platform; it is part of an observation and aggregate scope.
- **Completion scope:** One of `main_story`, `main_plus_optional`, or `completionist` in the MVP. The categories are distinct and never merged implicitly.
- **Playtime observation:** An immutable duration in whole minutes for one game, platform, and completion scope, with provenance and moderation state.
- **Provenance identity:** An owner-controlled identifier that explains where an observation came from without importing an unapproved third-party dataset.
- **Moderation decision:** An authenticated operator's approval or rejection of an observation.
- **Eligible observation:** An approved, non-duplicate observation that satisfies the aggregate's exact game, platform, and completion-scope key.
- **Aggregate:** A reproducible statistic calculated from a named set of eligible observations.
- **Aggregate revision:** An immutable version containing the median, sample count, included observation identities, rule revision, and calculation time.
- **Insufficient data:** Fewer than the provisional minimum of three eligible observations; no public median is published for that key.

## Facts, assumptions, and open questions

- Verified facts: The project is being considered as a Korean-language counterpart to the playtime information model discussed under HowLongToBeat. The owner prioritizes using open-source software for generic capabilities while owning the operating rules and canonical data. Astro 7, Python 3.12, and Django 5.2 LTS are fixed technology versions for this contract.
- Assumptions to test: Korean-language game-title search demand is sufficient; median playtime with explicit scope and sample count is useful; three observations are an acceptable provisional MVP publication threshold; operator-controlled initial observations can prove the loop before public contributions; and users will value transparent revision and sample information over a single unexplained duration.
- Open questions that do not block implementation: Final product and repository name; remote repository visibility; the first real games and platforms; the permitted real-observation sources; whether editions are separate games or releases; future outlier and minimum-sample rules; public contribution and account policy; backlog scope; monetization; production hosting; and trademark or domain availability. No missing or contradictory decision blocks the local MVP loop because third-party imports, public mutation, payment, and production deployment are explicitly excluded.
