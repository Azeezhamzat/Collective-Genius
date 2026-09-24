# Collective Intelligence Roadmap

This is the working roadmap for turning Collective Genius (rebuilt from
[adhocracy+](https://github.com/liqd/adhocracy-plus)) into a best-in-class,
general-purpose collective intelligence platform — one that works as well
for a company, a research lab, an open-source project or a DAO as it does
for civic participation.

## Design principles

1. **Any group, not just governments.** Terminology, defaults and example
  content should read naturally for a company, a research team, a school
  or a neighborhood association — not only a municipality. (`organisation`
  = any group running processes; `project` = any structured process.)
2. **Structured input beats a firehose.** The platform's advantage over a
  Slack channel or a mailing list is *structure*: phases, deadlines, clear
  decision points, and — critically — synthesis of what a large group of
  responses actually means.
3. **Extend, don't replace, what already works.** adhocracy4's
  module/phase/blueprint architecture is a genuinely good foundation for
  pluggable participation mechanisms. New capabilities should be new
  blueprint types and apps, following the same pattern as `apps/ideas`,
  `apps/polls`, `apps/budgeting`, etc., not a parallel system.
4. **Make disagreement legible, not hidden.** A good CI tool doesn't just
  count votes — it shows a group *where* it agrees, where it doesn't, and
  why. This is the thesis behind the Synthesis module below.

## Phase 0 — Shipped in this rebuild

* **Rebrand**: platform name, default topics, map bounding box, and key
  user-facing copy generalized from civic-government-specific to
  general-purpose (see `apps/cms/settings/models.py`,
  `adhocracy-plus/config/settings/base.py`).
* **[`apps/synthesis`](../apps/synthesis)** — opinion clustering and
  consensus/divisiveness scoring for any module's comments, in the spirit
  of Polis/pol.is "bridging statements." Clusters participants into
  opinion groups from their comment ratings, then surfaces which comments
  the *whole* group agrees on (bridging/consensus) versus which ones split
  the group apart (divisive). This is the single highest-leverage feature
  for a CI tool: raw comment counts and vote totals don't tell a group
  whether it actually agrees on something — synthesis does. The core
  algorithm (`apps/synthesis/engine.py`) is dependency-free, pure-Python,
  and unit tested (`apps/synthesis/tests/test_engine.py`); run it with
  `python3 -m unittest apps.synthesis.tests.test_engine`.
* **[`apps/quadraticvoting`](../apps/quadraticvoting)** — quadratic
  voting: each participant gets a fixed budget of "voice credits" to
  spread across a set of options, where casting N votes on one option
  costs N² credits. This surfaces *intensity* of preference (a small
  minority that cares a lot can outweigh a majority that barely cares),
  which plain majority voting cannot. Standalone models (its own
  `VotingRound`/`Option`/`Allocation`, not tangled into adhocracy4's poll
  internals), but properly registered as a phase type
  (`apps/quadraticvoting/phases.py`) with a blueprint entry in
  `apps/dashboard/blueprints.py` — a project admin can add a "Quadratic
  voting" module from the normal blueprint picker, same as Polls or
  Debate, and it renders inside the module timeline. Core budget/tally
  rules are pure-Python and unit tested
  (`apps/quadraticvoting/tests/test_engine.py`, run with
  `python3 -m unittest apps.quadraticvoting.tests.test_engine`).

  Design note: Synthesis is deliberately *not* a phase type. A phase is
  "what participants do during this time period" — Synthesis doesn't add
  something to do, it analyzes comments that already exist in whatever
  phase is running (or has run). It's correctly a standalone page linked
  from wherever a project wants to surface it, not a step in the
  timeline. Quadratic Voting, by contrast, *is* something participants
  do, so it belongs in the timeline like Polls or Debate — which is why
  only it got full phase/blueprint registration.

  Still open for Quadratic Voting: an in-dashboard configuration UI for
  adding/editing `Option`s (currently only via `/django-admin/`) —
  mirroring `apps/polls`' `PollComponent` — is real additional scaffolding
  (a `dashboard.py` with a formset component) and isn't done yet.
* **[`apps/argumentmapping`](../apps/argumentmapping)** — Kialo-style
  argument mapping for `apps/debate`. A comment's own author can mark it
  as supporting or opposing whatever it's replying to; the argument map
  page then shows the whole reply tree sorted so the most strongly
  supported branches come first, with each node's own supporting/opposing
  descendant counts visible. Deliberately doesn't touch the existing
  React-based comment widget (`react_comments_async`) at all — stance is
  set on a separate, plain server-rendered page linked from the subject
  detail page, which keeps the change additive and avoids needing a JS
  build to verify it. The tree-building and strength-scoring logic
  (`apps/argumentmapping/engine.py`) is pure Python and unit tested,
  including cycle-safety on malformed input (`apps/argumentmapping/tests/
  test_engine.py`, 12 tests, run with
  `python3 -m unittest apps.argumentmapping.tests.test_engine`).
* **[`apps/summarization`](../apps/summarization)** — extractive "key
  points" summary of a module's comments, using word-frequency
  centrality (a simplified version of Luhn's 1958 method): comments that
  share vocabulary with many other comments in the same discussion are
  more likely to be about its actual central themes, so they're picked
  as the summary, alongside a plain "common themes" keyword list. No ML
  library or API key required by default — deliberately a dependency-free
  baseline behind a swappable `summarize(comments)` signature, so an
  LLM-backed backend can be added later (tracked in Phase 1) without
  changing callers. Pure-Python core, unit tested, 10 tests:
  `python3 -m unittest apps.summarization.tests.test_engine`.

  Same design note as Synthesis: this is an analysis overlay, not a
  phase, so it's a standalone page. Both Synthesis and Summarization are
  now linked directly from every module's page (`a4modules/
  module_detail.html`, a "Key points" / "Where this group agrees" link
  row) — before this they were only reachable if you already knew the
  URL, which defeated the point of building them.
* **[`apps/deduplication`](../apps/deduplication)** — "check for similar
  ideas" before submitting a new one, using TF-IDF + cosine similarity
  (standard, no ML library or API key needed). Linked directly from the
  idea-submission form (`apps/ideas/templates/.../idea_create_form.html`)
  as "Check if a similar idea already exists" — a plain GET-param search
  page, no JS, so it's also a shareable/bookmarkable link. Stateless: no
  models, nothing to migrate, just computed live off `Idea.objects`.
  Pure-Python core, unit tested, 9 tests:
  `python3 -m unittest apps.deduplication.tests.test_engine`.

  Update: now also wired into `apps/budgeting` proposals and
  `apps/mapideas` — `Proposal` and `MapIdea` turned out to be the same
  shape (`.module`, `.name`, `.description`, since both are built on the
  same `AbstractIdea`/`Item` base as `Idea`), so `services.py` was
  generalized to `find_similar_items(model, module, query_text, ...)`
  behind thin `find_similar_ideas` / `find_similar_proposals` /
  `find_similar_mapideas` wrappers, and all three submission forms now
  link to a "check for similar" page. `apps/debate` turned out not to be
  a good fit: `Subject` has the right shape, but unlike ideas/proposals/
  map-ideas, debate subjects are only ever added by project admins
  through the dashboard, not submitted by participants — there's no
  "about to submit, check for duplicates first" moment to hook into, so
  it was deliberately skipped rather than forced.
* **In-dashboard configuration for Quadratic Voting.** Project admins
  can now set a round's credit budget and add/edit/remove `Option`s from
  the normal project dashboard (`apps/quadraticvoting/dashboard.py` +
  `VotingRoundDashboardView`) instead of `/django-admin/`. Deliberately
  *not* built on `adhocracy4.dashboard.ModuleFormSetComponent`: that base
  class's formset assumes the parent instance is the Module itself, but
  `Option` hangs off `VotingRound`, one level below the Module -- forcing
  that mismatched abstraction seemed more likely to produce a subtle bug
  than a plain hand-written get-or-create-then-render-two-forms view, so
  that's what this is (a real Django `ModelForm` for the round's
  settings, plus `inlineformset_factory(VotingRound, Option, ...)` for
  its options).
* **[`apps/facilitator`](../apps/facilitator)** — a project-wide
  facilitator toolkit: recent comment activity (a 7-day bucketed
  count), a reported-comments queue (there was no server-rendered view
  of `adhocracy4.reports.Report` anywhere in this codebase before this —
  reports were only reachable through the REST API, presumably meant
  for a React widget), and quick links into each module's Synthesis/
  Summarization pages. Registered as a *project*-level
  `DashboardComponent` (`components.register_project`, not
  `register_module` — the other new dashboard component so far), so
  it's reached from the project dashboard and gated by the same
  `a4projects.change_project` permission as every other dashboard page.
  The date-bucketing logic (`apps/facilitator/engine.py`) is pure Python
  and unit tested, including day-boundary edge cases: `python3 -m
  unittest apps.facilitator.tests.test_engine` (8 tests).

* **LLM-backed summarization as an alternate backend**
  (`apps/summarization/backends.py`). `settings.A4_SUMMARIZATION_BACKEND`
  selects `'extractive'` (default, dependency-free, always available) or
  `'llm'` (calls Claude via the `anthropic` package — not added to
  requirements.txt since it's optional, `pip install anthropic` plus
  `ANTHROPIC_API_KEY` to use it). Any failure of the LLM backend — no
  key, no package installed, a network error, a malformed response —
  falls back to extractive automatically via a new
  `engine.summarize_with_fallback(primary, fallback, ...)` helper, which
  *is* unit tested (5 tests: primary succeeds, primary raises, every
  exception type falls back, the fallback callback fires, arguments
  forward correctly) even though `backends.py` itself can't be — it
  needs Django's settings machinery just to import, which this sandbox
  doesn't have, and the LLM path additionally needs a real network call
  this sandbox can't make. Review `backends.py` carefully before relying
  on the `'llm'` mode in production; the extractive default needs no
  such caveat.

* **[`apps/translation`](../apps/translation)** — on-demand machine
  translation of *discussion content*, not UI chrome. Reframed from the
  original "translate untranslated UI strings" idea: this project
  already has a real workflow for that (transifex-client, in
  requirements/dev.txt, translating maintained `.po` files) — a shadow
  auto-translate system for interface strings would just conflict with
  it. What has no solution at all today is a participant's own comment
  text when a group isn't all working in the same language, so that's
  what this adds: a language picker on the Synthesis and Summarization
  pages (both already extract and render comment text server-side,
  outside the React comment widget, which made this a clean place to
  hook in without touching JS this sandbox can't build or verify) that
  translates the displayed key/bridging/divisive comments on request,
  with a "machine translated" badge. `settings.A4_TRANSLATION_BACKEND`
  is `'none'` by default (feature fully off, no control shown anywhere);
  set to `'llm'` to enable it via Claude. Same fallback-on-failure shape
  as the summarization LLM backend, including the same honest limit on
  what's unit tested here: `engine.translate_with_fallback` is pure
  Python and covered by 5 tests (`python3 -m unittest
  apps.translation.tests.test_engine`), `backends.py` needs Django
  settings to even import and isn't tested standalone in this sandbox.

**Phase 1 is now complete** — every item originally listed here has
shipped, sometimes reframed along the way when digging in showed a
better or more honest scope (Synthesis/Quadratic Voting's phase-vs-
overlay split, deduplication skipping `apps/debate`, translation
targeting content instead of UI strings). See git log for the full
sequence of commits.

## Phase 2 — differentiating features

Bigger features that make this platform stand out, not just catch up.

### Shipped

* **[`apps/forecasting`](../apps/forecasting)** — prediction-market-style
  forecasting: for a question with a clear, checkable resolution
  criterion ("will X happen by Y date"), participants forecast a
  probability (0-100%); once a project admin resolves the question with
  the real outcome, the page shows the crowd's aggregate forecast (the
  mean of everyone's estimate -- wisdom of crowds applied to prediction,
  not voting) and a per-forecaster leaderboard by mean Brier score
  (Brier, 1950 -- the standard proper scoring rule for probabilistic
  forecasts, `(probability - outcome)²`, lower is better), so forecasting
  skill is tracked over many questions rather than "who guessed right
  once." A genuinely different collective-intelligence mechanism from
  anything else on this platform (see Metaculus, the Good Judgment
  Project) and, as far as this rebuild is aware, not offered as a
  first-class module by any comparable participation platform.

  Registered as a real phase/blueprint type, same as Quadratic Voting —
  forecasting is something participants *do*. Question management
  (add/edit/resolve) uses `adhocracy4.dashboard.ModuleFormSetComponent`
  properly this time (unlike Quadratic Voting's hand-written dashboard
  view): `Question` has a direct FK to `Module`, the exact shape that
  base class assumes, so there was no mismatch to work around.

  The scoring core (`apps/forecasting/engine.py` — `brier_score`,
  `aggregate_forecast`, `leaderboard`) is pure Python and unit tested,
  11 tests including the classic "two confident-but-wrong forecasters on
  opposite sides average out better calibrated than either" wisdom-of-
  crowds case: `python3 -m unittest apps.forecasting.tests.test_engine`.

* **[`apps/consent`](../apps/consent)** — sociocracy/Loomio-style
  consent decisions: a genuinely different decision rule from majority
  voting. Participants propose actions and respond **agree** / **stand
  aside** (doesn't support it, won't block it) / **object** (blocks the
  proposal, must give a reason). A proposal has consent once there are
  no *unresolved* objections — one unresolved objection blocks it
  regardless of how many people agree, by design: consent protects a
  real, unaddressed concern from being outvoted. An objection can be
  marked resolved by the objector or the proposer once it's been
  addressed, without the objector having to change their stance.
  Simplified from the original "propose → clarify → react → amend →
  consent-round" staged-flow idea to just proposals + responses:
  clarification and reaction already happen fine as ordinary discussion
  (comments exist generically), and formalizing five rigid stages as
  separate app states would have added real complexity for what the
  actual distinguishing mechanic — the consent rule itself — doesn't
  need. Registered as a real phase/blueprint type (participants
  propose *and* respond, so, like Quadratic Voting and Forecasting,
  this is something people *do*). The consent-resolution core
  (`apps/consent/engine.py` — `resolve`) is pure Python and unit
  tested, 7 tests including the core "one unresolved objection blocks
  it even with four agreements" case and the resolved-objection/
  mixed-objections cases: `python3 -m unittest
  apps.consent.tests.test_engine`.

* **[`apps/delphi`](../apps/delphi)** — Delphi-method structured
  elicitation: participants give an anonymous numeric estimate for a
  question, the group's aggregate (median, spread, anonymous
  rationales) is shown back, and a new round opens for people to revise
  their estimate. Repeated over a few rounds this typically converges
  without anyone anchoring on who said what first or defending a
  position socially — the anonymity is the actual mechanism, not an
  incidental privacy feature. `apps/delphi/services.has_converged`
  gives a plain "has the spread tightened meaningfully since round one"
  signal a project can show participants. Useful for research
  consortia and technical-standards work, a segment adhocracy+ never
  targeted.

  `Question.current_round` (admin-editable via the dashboard, same
  `ModuleFormSetComponent` pattern as Forecasting) is what opens a new
  round; past rounds' `Response`s become immutable automatically once
  it advances, since new submissions target the new round number and
  old ones are simply never queried against by ``round_number`` for the
  live round again. The round-aggregation and convergence core
  (`apps/delphi/engine.py` — `aggregate_round`, `has_converged`) is pure
  Python and unit tested, 11 tests covering the statistics themselves
  and every convergence edge case (too few rounds, spread barely
  changing, spread widening, zero spread in round one, empty rounds
  skipped, a custom threshold): `python3 -m unittest
  apps.delphi.tests.test_engine`.

* **[`apps/search`](../apps/search)** — cross-project semantic search:
  "has anyone already proposed something like this" across every idea,
  budgeting proposal, map-idea and debate subject in every project an
  organisation runs, not just the one module you happen to be in.
  Deliberately reuses `apps/deduplication/engine.py` (TF-IDF + cosine
  similarity) rather than writing a second copy of the same algorithm —
  that module was already a generic "find text similar to a query"
  engine, not specific to checking one module for duplicates, so this
  is the same math applied organisation-wide instead of module-wide. No
  new engine, no new unit tests needed: the similarity math is already
  covered by `apps/deduplication/tests/test_engine.py`. Stateless, same
  as deduplication — nothing to migrate, results computed live. Linked
  from the organisation landing page as "Search across all projects."

* **[`apps/documentrevisions`](../apps/documentrevisions) — partial,
  honestly scoped.** This is *not* the real-time collaborative-editing
  feature originally listed here. That needs a CRDT library (Yjs or
  similar), a WebSocket transport (Django Channels, an ASGI server —
  this project's `wsgi.py`-only stack doesn't have one), and a live
  multi-browser session to prove simultaneous-edit merging actually
  works — none of which this sandbox can build or verify (no network,
  no way to run two browser sessions against a live server, no
  Channels in the dependency stack). Building it anyway and calling it
  done would mean shipping something never actually exercised end to
  end, which is exactly the failure mode the honesty notes throughout
  this document exist to avoid. So: real-time co-editing stays
  genuinely undone, tracked below as future work with what it would
  actually require.

  What *is* real and safe to ship without that infrastructure: every
  `Paragraph` edit in `apps/documents` now keeps its previous text
  automatically (a `pre_save` signal on the existing `Paragraph` model,
  not a change to `apps/documents` itself — additive, lower risk than
  modifying a shared model in place), with a read-only history page per
  paragraph (linked from the chapter page) and a trivial-edit flag using
  a small diff-similarity wrapper around Python's stdlib `difflib`. A
  real, useful step toward "a group can see how a draft evolved," not a
  substitute for "a group can draft text together live" — those are
  different features and only the first one is what got built. The
  diff-similarity wrapper (`apps/documentrevisions/engine.py` —
  `similarity_ratio`, `is_trivial_edit`) is pure Python and unit tested,
  10 tests: `python3 -m unittest
  apps.documentrevisions.tests.test_engine`.

### Not yet

* **Real-time collaborative documents (the actual original ask).**
  What it would take, concretely, beyond what's in this sandbox: an
  ASGI server + Django Channels (or a separate sync service) for the
  WebSocket transport, a CRDT library on both ends (Yjs client-side,
  a Python CRDT implementation or a thin proxy to a `y-py`/`pycrdt`
  server process), a rewrite of the paragraph editor's JS to talk to it
  instead of posting a form, and conflict-free merge semantics that
  need real multi-client testing to trust — this genuinely can't be
  responsibly built blind. `apps/documentrevisions` (above) is the
  closest safe step taken toward it so far.
* **Plugin/module marketplace.** The blueprint system
  (`A4_DASHBOARD['BLUEPRINTS']`) already supports pluggable phase types
  — this rebuild has now shipped eight new module types through exactly
  that mechanism (Quadratic Voting, Forecasting, Consent, Delphi, and
  four standalone overlay apps), so what "formalize a plugin interface"
  actually means at this point is written up as a real, tested-by-use
  developer guide rather than new code: see
  [`docs/building_a_module.md`](./building_a_module.md). A registry/
  marketplace *listing* third-party modules is still open — worth
  revisiting once there's more than one codebase's worth of modules to
  list.

## Phase 3 — platform & ecosystem

### Shipped

* **[`apps/webhooks`](../apps/webhooks)** — outbound webhooks: an
  organisation registers an endpoint URL, and this platform POSTs a
  signed JSON payload to it when a subscribed event happens. The public
  REST API for reading/writing data (comments, ratings, polls) was
  already in place via DRF before this rebuild; what was missing was
  the *push* side for integrations (a Slack notifier, a Zapier hook, a
  custom dashboard) that want to react to events instead of polling.

  Four event types wired up so far, each a plain "a new X was created"
  hook — the simplest, least error-prone trigger shape —
  `report.created`, `consent_proposal.created`,
  `forecasting_question.created`, `synthesis_snapshot.created`; adding
  another is a ~10-line signal handler (see
  `apps/webhooks/signals.py` and `docs/building_a_module.md`).

  Two pieces of this are genuinely security/reliability-sensitive and
  are exactly what's unit tested: **payload signing** (HMAC-SHA256 over
  a canonical JSON encoding, `hmac.compare_digest` for the verification
  side so a receiver's check can't be timed byte-by-byte — a receiver's
  entire ability to trust a delivery came from this platform rests on
  this being right) and **retry scheduling** (exponential backoff, 1 min
  → 12 hours, so a receiver that's briefly down doesn't silently lose an
  event, but a dead endpoint isn't retried forever). 11 tests:
  `python3 -m unittest apps.webhooks.tests.test_engine`.

  Delivery itself uses stdlib `urllib.request`, not a new `requests`
  dependency, and (like everything network-touching in this rebuild)
  is not executed end-to-end here. There's no task queue configured in
  this project, so retries need `python manage.py send_webhook_retries`
  run on a real cron schedule in production — noted in the command's
  own `--help` text, not just here. Endpoint management is
  Django-admin-only for now (no participant-facing dashboard UI) — a
  reasonable v1 scope, same as how Synthesis/Summarization results were
  admin-visible before they got a proper page.

* **[`apps/trustsafety`](../apps/trustsafety)** — rate limiting and
  spam-likelihood flagging, the two pieces of "trust & safety at scale"
  that don't need a third-party provider to build responsibly.
  Proof-of-personhood is explicitly **not** attempted here (see below)
  — it needs a real identity-verification provider (World ID, Persona,
  a government eID scheme) and credentials/integration testing this
  sandbox has neither the access nor the standing to fake; claiming
  progress on it without that would be worse than leaving it undone.

  What did ship: **rate limiting** — a token-bucket limiter
  (`RateLimitMiddleware`) capping POST requests per user (or per IP,
  anonymous) in a rolling window, state kept in Django's cache
  framework so it works with whatever cache backend a deployment
  already has. Off by default (`A4_RATE_LIMIT_ENABLED = False`) since
  it can reject real traffic (a 429) if misconfigured — a deployment
  opts in deliberately, unlike the spam flag below.

  **Spam-likelihood flagging** — a small, legible heuristic (link
  density, repeated characters, shouting, a link with almost no other
  text — deliberately not an opaque learned score nobody could explain
  to someone who got flagged) that sets the *existing*
  `is_moderator_marked` field on `adhocracy4.comments.Comment` for new
  comments, rather than adding a new flag or, worse, blocking or hiding
  anything outright — moderators already have a workflow built around
  that field, and a heuristic false positive should cost a moderator
  one glance, never silently censor a real participant. On by default,
  since it's strictly additive (more visibility, zero blocking).

  Both cores (`apps/trustsafety/engine.py` — `TokenBucket`,
  `score_text`) are pure Python and unit tested, 16 tests — two of
  which caught real bugs during development: the "short message
  dominated by a link" rule was counting the URL itself as a "word"
  (so a genuinely link-dominated short message never tripped it), and
  a hand-picked "mild" spam example in the test itself didn't actually
  contain 5 repeated characters as intended. Both fixed, not glossed
  over: `python3 -m unittest apps.trustsafety.tests.test_engine`.

### Not yet

* **White-label multi-tenant SaaS.** `apps/organisations` already
  supports multiple orgs on one deployment; add per-organisation theming,
  custom domains, and usage-based billing hooks for a hosted offering.
  Custom domains and billing genuinely need real infrastructure (DNS/TLS
  provisioning, a payment processor account and API keys) this sandbox
  doesn't have — same reasoning as proof-of-personhood above. Per-
  organisation theming (colors/logo, no new infrastructure, `Organisation`
  already has an image field) is the safely buildable slice of this if
  picked up next.
* **Mobile apps / installable PWA.** Push notifications for phase
  deadlines and synthesis updates matter far more for engagement than a
  native app shell — start with a PWA before native.
* **Open data & auditability.** One-click export of full project data
  (already partially covered by `apps/exports`) in structured, versioned
  form, plus a public changelog of moderation actions, so outcomes are
  auditable by participants — important for trust in any collective
  decision, civic or otherwise.

## Explicitly out of scope (for now)

* Fully autonomous AI decision-making. This platform is for *augmenting*
  group intelligence, not replacing group judgment with a model's output.
  Any AI feature here should summarize, surface, or suggest — a human
  group should always make the actual call.
* Blockchain/token-based voting. Interesting adjacent space, but adds
  significant complexity and a hard dependency for no clear benefit over
  a well-audited traditional vote log; revisit if a concrete use case
  needs it.
