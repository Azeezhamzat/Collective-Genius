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

## Phase 1 (next) — high-leverage, low-risk

Features that extend existing primitives and don't require new
infrastructure.

* **In-dashboard configuration for Quadratic Voting.** A
  `apps/quadraticvoting/dashboard.py` component (formset for `Option`s,
  a field for `credit_budget`), so a project admin doesn't have to touch
  `/django-admin/` to set up a round. Mirror `apps/polls/dashboard.py`'s
  `PollComponent`.
* **AI-assisted idea deduplication.** When someone starts a new idea/
  proposal, semantically search existing ones in the same module and
  surface likely duplicates before they submit — reduces fragmentation of
  a discussion across near-identical entries. Natural fit on top of
  `apps/ideas` and `apps/budgeting`.
* **Comment thread summarization.** An on-demand "summarize this
  discussion" action per module, built the same way as Synthesis: a
  swappable summarization backend (extractive by default, LLM-backed when
  an API key is configured) rather than a hard dependency on one vendor.
* **Argument mapping for debates.** `apps/debate` currently threads
  comments; add explicit "supports / opposes / because" relations between
  comments (Kialo-style) so a debate's structure is visible at a glance,
  not just a flat or nested list.
* **Facilitator toolkit.** A dashboard view for moderators showing: new
  activity since last visit, comments needing moderation, and — powered by
  Synthesis — where the group currently stands. Builds on the existing
  `apps/dashboard` and `apps/moderatorfeedback`.
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
