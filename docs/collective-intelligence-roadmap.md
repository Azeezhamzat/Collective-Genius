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

  Update: now also wired into `apps/budgeting` proposals — `Proposal`
  turned out to be the same shape (`.module`, `.name`, `.description`,
  since it's built on the same `AbstractIdea`/`Item` base as `Idea`), so
  `services.py` was generalized to `find_similar_items(model, module,
  query_text, ...)` behind two thin `find_similar_ideas` /
  `find_similar_proposals` wrappers, and both the idea and proposal
  submission forms now link to a "check for similar" page.
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

## Phase 1 (next) — high-leverage, low-risk

Features that extend existing primitives and don't require new
infrastructure.

* **Extend idea deduplication to `apps/mapideas` and `apps/debate`.**
  `find_similar_items` already takes any model shaped like an
  adhocracy4 `Item` (`.module`, `.name`, `.description`) — `MapIdea` and
  `Subject` both qualify. Just needs a third/fourth thin wrapper in
  `services.py` and a link from their respective create forms, same as
  Idea and Proposal.
* **LLM-backed summarization as an alternate backend.** Now that
  `apps/summarization` exists (below) with a plain `summarize(comments)`
  entry point, add an optional second backend behind the same signature
  that calls out to an LLM when an API key is configured, instead of (or
  blended with) the extractive default — genuinely better summaries for
  large discussions, still falling back to the dependency-free default
  when no key is set.
* **Expanded i18n.** Currently 5 languages; add machine-translation
  fallback (with a "translated" badge) for languages without a maintained
  translation, so non-English/German groups aren't second-class.

## Phase 2 — differentiating features

Bigger features that make this platform stand out, not just catch up.

* **Reputation & expertise weighting (opt-in, per-project).** Let a
  project optionally weight synthesis/voting by demonstrated
  participation quality (verified expertise tags, track record of
  well-received contributions) — never as a requirement, always visible
  and auditable, to avoid recreating opaque social-credit systems.
* **Prediction markets / forecasting module.** For decisions with a
  future, checkable outcome ("will this proposal reduce X by Y%"), let
  participants forecast outcomes with calibrated confidence, score
  forecasters over time (Brier score), and surface the community's
  aggregate forecast — a genuinely different and powerful collective
  intelligence mechanism (see Metaculus, Good Judgment Project) that no
  participation platform currently offers as a first-class module.
  New blueprint type + app, following the same pattern as `apps/polls`.
* **Structured consent-based decisions.** A Loomio/sociocracy-style
  decision flow: propose → clarify → react → amend → consent-round (only
  "I object because…" blocks; everything else is a stand-aside or
  agreement) — a genuinely different decision mechanism from majority
  voting, well suited to working groups and org governance.
* **Delphi-method rounds.** Multi-round structured expert elicitation:
  anonymous responses, aggregate feedback shown to all, revise, repeat.
  Useful for research consortia and technical standards work — a segment
  adhocracy+ never targeted.
* **Real-time collaborative documents.** CRDT-based co-editing (e.g. via
  Yjs) for `apps/documents`, so a group can draft text together, not just
  comment on a static version — turns the platform into a genuine
  co-creation tool, not just a feedback-collection one.
* **Cross-project semantic search.** Once an organisation has run many
  projects, let members search across all of them by meaning, not just
  keyword — "has anyone already proposed something like this."
* **Plugin/module marketplace.** The blueprint system
  (`A4_DASHBOARD['BLUEPRINTS']`) already supports pluggable phase types;
  formalize a plugin interface + registry so third parties can ship new
  module types (a new voting method, a new visualization) without forking
  the platform.

## Phase 3 — platform & ecosystem

* **API-first integrations.** Webhooks + a documented public API (DRF is
  already in place) for Slack/Teams notifications, Zapier/Make
  connectors, and embedding synthesis results in external dashboards.
* **White-label multi-tenant SaaS.** `apps/organisations` already
  supports multiple orgs on one deployment; add per-organisation theming,
  custom domains, and usage-based billing hooks for a hosted offering.
* **Mobile apps / installable PWA.** Push notifications for phase
  deadlines and synthesis updates matter far more for engagement than a
  native app shell — start with a PWA before native.
* **Trust & safety at scale.** Rate limiting, spam/bot detection, and
  (opt-in, privacy-respecting) proof-of-personhood for high-stakes votes,
  building on the existing captcha app.
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
