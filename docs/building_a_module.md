# Building a new participation module

This is a practical guide to adding a new module type to Collective
Genius, written from having actually built eight of them in one pass
(`apps/quadraticvoting`, `apps/forecasting`, `apps/consent`,
`apps/delphi` as full phase types, plus `apps/synthesis`,
`apps/summarization`, `apps/deduplication`, `apps/argumentmapping`,
`apps/facilitator`, `apps/translation`, `apps/search` as standalone
overlay apps). It documents the real mechanism this platform already
has for pluggable modules — the blueprint/phase system — rather than
proposing a new plugin API. If you're building module #9, start here
instead of re-deriving these decisions from scratch.

## Step 0: is this a phase, or an overlay?

This is the first and most consequential decision, and it's easy to
get wrong by defaulting to "make it a phase" because that's what most
existing modules are.

**A phase is something participants *do* during a time period** —
submit ideas, cast votes, forecast a probability, respond to a consent
round. It shows up in a project's timeline, gets a blueprint entry so
project admins can add it from the module picker, and becomes the
active content of whatever phase is currently running.

**A standalone overlay is an *analysis or utility* view** — it reads
data that already exists (usually comments) and presents it
differently, or offers a tool (search, translation, revision history)
that isn't tied to one specific point in a project's timeline. It gets
its own URL, is reached directly, and is linked in from wherever makes
sense (a module page, a create form, an organisation landing page).

Ask: "if a project admin added this to a module's timeline as *the*
thing participants do during a phase, would that be right?" If yes,
it's a phase. If the honest answer is "it doesn't really have a
phase, it's more like a feature that applies across a module or
project regardless of what phase is active," it's an overlay. Getting
this wrong doesn't just mean using the wrong template block (see
below) — it means fighting the framework the whole way.

Examples from this rebuild:
- Quadratic Voting, Forecasting, Consent, Delphi: phases. Participants
  vote/forecast/respond during a specific window.
- Synthesis, Summarization: overlays. They analyze whatever comments
  already exist, in whatever phase produced them, at any time.
- Deduplication, Search: overlays. They're a utility (a similarity
  search), not tied to a phase at all.
- Facilitator: an overlay, but *project*-level rather than
  module-level (see "Project-level vs module-level" below).

## Step 1: the pure-Python core, tested first

Before touching Django, write the actual algorithm as a plain Python
module with no Django import: `apps/yourmodule/engine.py`. This is
worth doing even when it feels like overhead for a simple feature,
because:

1. It's the only part of a new module this environment can actually
   run and verify. Everything that imports Django (`models.py`,
   `views.py`, `services.py`, `backends.py`) can be reviewed carefully
   but not executed here — there's no Django installed in this
   sandbox, and even a fully-configured deployment needs GDAL/GEOS and
   the rest of adhocracy4's dependency stack, none of which is
   available. `engine.py` sidesteps that entirely.
2. It forces the actual mechanism (Brier scoring, TF-IDF similarity,
   consent resolution, round convergence, diff-based triviality) to be
   separated from Django plumbing, which makes it easier to review,
   easier to get right, and reusable (see `apps/search` reusing
   `apps/deduplication/engine.py` wholesale rather than copying it).
3. Writing the tests first genuinely catches bugs. Concrete examples
   from this rebuild: a cyclic-input test for argument mapping's tree
   builder caught a real behavior mismatch between what was assumed
   and what the code actually did; a "small edit scores high"
   assertion in the document-revision diff wrapper caught an off-by-a-
   float-rounding-error test bound. Neither would have been caught by
   code review alone.

Pattern to follow: `apps/*/engine.py` + `apps/*/tests/test_engine.py`,
runnable standalone with `python3 -m unittest
apps.yourmodule.tests.test_engine`. Look at `apps/consent/engine.py`
(small, single-function) or `apps/forecasting/engine.py` (a few
related functions) for the right level of scope — one module's worth
of genuinely one mechanism, not a grab-bag.

If your feature calls out to something inherently untestable here
(an LLM, a network service), separate that into a `backends.py` with a
safe, dependency-free default and a swappable alternate backend, and
put the *fallback-on-failure wiring* — not the network call itself —
in `engine.py` where it can be tested. See
`apps/summarization/engine.py`'s `summarize_with_fallback` and
`apps/translation/engine.py`'s `translate_with_fallback`: the actual
backend that calls an LLM isn't tested here, but the "if it fails,
degrade to the safe default instead of breaking the page" logic is,
because that's the part a bug would actually hurt someone.

## Step 2: models

- `module = models.ForeignKey(module_models.Module, on_delete=models.CASCADE, related_name='yourmodule_things')`
  for anything scoped to one module. Import as
  `from adhocracy4.modules import models as module_models`.
- If you need `.project` on your model (dashboard permission checks
  usually do), add a plain property:
  `@property def project(self): return self.module.project` — no
  migration needed, it's Python, not a field.
- User references: `from django.conf import settings` then
  `models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)`.
  Never import the user model directly.
- Write the migration by hand (`0001_initial.py`) rather than
  generating it — there's no working `manage.py makemigrations` here.
  Get the dependency right: your FK to `Module` needs
  `('a4modules', '0005_module_is_draft')` in `dependencies` (that's the
  latest `a4modules` migration at the commit this project's
  `requirements/base.txt` pins adhocracy4 to — check
  `requirements/base.txt` for the exact commit and look at that
  commit's `adhocracy4/modules/migrations/` if adhocracy4 has since
  moved on). A FK to `settings.AUTH_USER_MODEL` needs
  `migrations.swappable_dependency(settings.AUTH_USER_MODEL)`, not a
  literal app/migration name.
- **Check whether you even need a separate model**, or whether an
  existing one already has the right shape. `apps/deduplication` and
  `apps/search` have no models at all — they compute results live from
  `Idea`/`Proposal`/`MapIdea` data that already exists.

### Comment access, if you need it

`adhocracy4.comments.models.Comment` at the pinned commit has `.module`
and `.project` as **computed properties**, not indexed database
columns — there's no way to do `Comment.objects.filter(module=...)` at
the database level. If you need "every comment in this module/project,"
the pattern (used identically in `apps/synthesis`, `apps/summarization`,
`apps/facilitator`) is:

```python
def comments_for_module(module):
    for comment in Comment.objects.filter(is_removed=False, is_censored=False):
        try:
            comment_module = comment.module
        except AttributeError:
            continue
        if comment_module and comment_module.pk == module.pk:
            yield comment
```

This is a full table scan and is documented as such everywhere it's
used. It's fine at the scale a single module's or project's discussion
reaches. If it ever becomes a real bottleneck, the actual fix belongs
upstream in adhocracy4 (an indexed `module` field on `Comment`), not a
workaround here.

## Step 3: is this a phase? Register it.

```python
# apps/yourmodule/phases.py
from django.utils.translation import gettext_lazy as _
from adhocracy4 import phases
from . import apps, models, views

class YourPhase(phases.PhaseContent):
    app = apps.Config.label          # matches apps.py's Config.label
    phase = 'yourphase'              # short, unique within this app
    view = views.YourModuleDetail

    name = _('Your phase')
    description = _('One sentence shown in the phase timeline.')
    module_name = _('your module')

    features = {'crud': (models.YourMainModel,)}

phases.content.register(YourPhase())
```

Then add a blueprint entry in `apps/dashboard/blueprints.py` (import
your `phases` module at the top, add a
`('your-slug', ProjectBlueprint(title=..., description=...,
content=[YourPhase()], image='images/yourmodule.svg',
settings_model=None))` tuple to the list) and an icon at
`adhocracy-plus/assets/images/blueprints/yourmodule.svg` — copy the
structure of an existing one (270×150 viewBox, `#2A3CD4` background
rect, white icon shape), webpack copies everything under
`assets/images/**/*` flat into `static/images/<filename>` so the
blueprint's `image=` value is just `images/yourmodule.svg`, no
subdirectory.

Your phase view (`views.py`) needs:

```python
from adhocracy4.projects.mixins import ProjectMixin, DisplayProjectOrModuleMixin

class YourModuleDetail(ProjectMixin, DisplayProjectOrModuleMixin, generic.View):
    template_name = 'a4_candy_yourmodule/your_template.html'
    ...
```

`DisplayProjectOrModuleMixin` is what makes `{% extends extends %}`
resolve to `a4modules/module_detail.html` when your view is reached
through the module's own canonical URL (which it is, when dispatched as
the active phase) — your template then fills `{% block phase_content %}`
and the surrounding module chrome (title, timeline, breadcrumbs) is
already handled for you. **A phase view needs no `urls.py` of its
own** — `apps/polls`, `apps/quadraticvoting`, `apps/forecasting`,
`apps/consent` and `apps/delphi` all have none; the module's own
`module-detail` URL dispatches to whichever phase is active via
`Phase.view`.

## Step 3, alternative: is this an overlay? Give it a URL.

```python
# apps/yourmodule/views.py
class YourOverlayView(ProjectMixin, generic.TemplateView):
    template_name = 'a4_candy_yourmodule/your_template.html'
```

No `DisplayProjectOrModuleMixin` here. Your template extends
`"base.html"` directly with a plain `{% block content %}` — **do not**
use `{% extends extends %}` / `{% block phase_content %}` for an
overlay reached by its own URL; that block only exists inside
`a4modules/module_detail.html`, so it silently renders nothing when
`extends` resolves to `a4projects/project_detail.html` instead (this
was a real bug in an earlier version of `apps/synthesis` in this
rebuild — caught and fixed, see the git history — precisely because it
looked plausible and compiled fine).

Give it its own `urls.py` and add it to
`adhocracy-plus/config/urls.py`'s organisation-scoped `include([...])`
block:

```python
path('yourmodule/', include(('apps.yourmodule.urls', 'a4_candy_yourmodule'),
                            namespace='a4_candy_yourmodule')),
```

Link to it from wherever it's actually discoverable — a module page's
insight row, a create-form page, an organisation landing page. **An
overlay with no incoming link is a real gap, not a minor one**: this
happened with Synthesis and Summarization in this rebuild (both were
only reachable if you already knew the URL) and was fixed as its own
follow-up commit. Don't skip this step.

## Step 4: does an admin need to configure it?

Depends on the shape of your data relative to `Module`:

- **Your child model has a *direct* FK to `Module`** (like
  `forecasting.Question`, `delphi.Question`): use
  `adhocracy4.dashboard.ModuleFormSetComponent` — it's built for
  exactly this shape.

  ```python
  # forms.py
  QuestionFormSet = inlineformset_factory(
      module_models.Module, YourChildModel,
      fields=(...), formset=ModuleDashboardFormSet,
      extra=3, can_delete=True)

  # dashboard.py
  class YourComponent(ModuleFormSetComponent):
      identifier = 'yourmodule_things'
      weight = 20
      label = _('Things')
      form_title = _('Edit things')
      form_class = forms.YourFormSet
      form_template_name = 'a4_candy_yourmodule/includes/formset.html'

      def is_effective(self, module):
          return module.phases[0].content().app == apps.Config.label

      def get_base_url(self, module):
          return reverse('a4dashboard:dashboard-yourmodule_things-edit', kwargs={
              'organisation_slug': module.project.organisation.slug,
              'module_slug': module.slug,
          })

  components.register_module(YourComponent())
  ```

  Note the `get_base_url` override is required even though the base
  class provides one — the inherited version reverses with only
  `[module.slug]` as an arg, but every dashboard URL in this
  *particular* project is nested under `<organisation_slug>/dashboard/`
  (see `apps/dashboard/urls.py`), so it needs `organisation_slug` too.
  Every hand-written dashboard component in this codebase
  (`apps/topicprio`, `apps/polls`, `apps/quadraticvoting`, this
  pattern) overrides it for the same reason — don't skip it and expect
  the inherited version to work.

  Your `form_template_name` partial renders *inside* an already-open
  `<form>` tag with CSRF and a submit button already provided by
  `a4dashboard/base_form_module.html` — it should render only
  `{{ form.management_form }}` + a loop over `{% for sub_form in form %}`
  with `{{ sub_form.as_p }}`, nothing else. See
  `apps/forecasting/templates/a4_candy_forecasting/includes/question_formset.html`.

- **Your data hangs off something one level below `Module`** (like
  `quadraticvoting.Option`, which belongs to a `VotingRound`, which
  belongs to a `Module`): `ModuleFormSetComponent` doesn't fit —
  `ModuleComponentFormView.get_object()` returns the `Module` itself
  and passes it as the formset's `instance`, but your formset's real
  parent is the intermediate model, not the Module. Don't force it;
  write a plain view by hand instead: get-or-create the intermediate
  object, build a `ModelForm` for it plus an
  `inlineformset_factory(IntermediateModel, ChildModel, ...)` for the
  children, handle GET/POST yourself. See
  `apps/quadraticvoting/views.py`'s `VotingRoundDashboardView` for the
  full pattern. More code, but correct — forcing a mismatched
  abstraction to save fifteen lines isn't a good trade.

- **Participants create the top-level objects themselves** (like
  `consent.Proposal`, where anyone proposes an action): no dashboard
  component needed at all. Handle creation in the participant-facing
  phase view itself (a `create_proposal` POST action alongside the
  response-submission action — see `apps/consent/views.py`).

## Step 5: project-level vs module-level (rare)

Most components are module-level (`components.register_module`,
`is_effective(self, module)`). If your feature genuinely spans every
module in a project — `apps/facilitator`'s toolkit aggregates activity
and reports across an entire project, not one module — use
`components.register_project` instead, `is_effective(self, project)`
(usually just `return True`), and base your view on `ProjectMixin` +
`DashboardBaseMixin` + `DashboardComponentMixin` without needing
`self.module` at all (`DashboardComponentMixin.get_context_data`
handles `self.module` being `None` gracefully — `ProjectComponentFormView`
in adhocracy4 itself is built the same way, so this is a proven
pattern, not a guess).

## Checklist

- [ ] Decided phase vs. overlay, and can articulate why in one sentence
- [ ] `engine.py` (or nothing, if there's genuinely no new algorithm)
      + `tests/test_engine.py`, actually run and passing
- [ ] `models.py` + hand-written `migrations/0001_initial.py` with
      correct dependencies
- [ ] `apps.py` with a `label` that matches everywhere else it's
      referenced (phases.py's `app = apps.Config.label`, the dashboard
      component's `is_effective` check)
- [ ] Added to `INSTALLED_APPS` in
      `adhocracy-plus/config/settings/base.py`
- [ ] Phase: registered in `phases.py`, blueprint entry + icon added.
      Overlay: `urls.py` + wired into `adhocracy-plus/config/urls.py`,
      **and linked from somewhere a participant would actually find it**
- [ ] Admin configuration, if needed, using the right pattern for your
      model's shape (Step 4)
- [ ] `python3 -m py_compile` on every new file (catches syntax errors;
      doesn't catch import-time errors, since Django itself isn't
      installed in this sandbox — that's a real limit, not a
      formality, and it's why every commit in this rebuild says so
      explicitly rather than claiming full verification)
- [ ] `docs/collective-intelligence-roadmap.md` and `README.md` updated
