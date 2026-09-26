from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.utils import timezone

from adhocracy4.categories.models import Category
from adhocracy4.comments.models import Comment
from adhocracy4.modules.models import Module
from adhocracy4.phases.models import Phase
from adhocracy4.polls.models import Choice
from adhocracy4.polls.models import Poll
from adhocracy4.polls.models import Question as PollQuestion
from adhocracy4.projects.enums import Access
from adhocracy4.projects.models import Project
from adhocracy4.ratings.models import Rating
from apps.argumentmapping.models import Stance
from apps.budgeting.models import Proposal
from apps.consent.models import Proposal as ConsentProposal
from apps.consent.models import Response as ConsentResponse
from apps.debate.models import Subject
from apps.delegation.models import Delegation
from apps.delegation.models import DelegationRound
from apps.delegation.models import Option as DelegationOption
from apps.delegation.models import Vote as DelegationVote
from apps.delphi.models import Question as DelphiQuestion
from apps.delphi.models import Response as DelphiResponse
from apps.documents.models import Chapter
from apps.documents.models import Paragraph
from apps.forecasting.models import Forecast
from apps.forecasting.models import Question as ForecastingQuestion
from apps.ideas.models import Idea
from apps.interactiveevents.models import LiveQuestion
from apps.mapideas.models import MapIdea
from apps.offlineevents.models import OfflineEvent
from apps.organisations.models import Organisation
from apps.quadraticvoting.models import Allocation
from apps.quadraticvoting.models import Option as QuadraticOption
from apps.quadraticvoting.models import VotingRound
from apps.synthesis.models import SynthesisSnapshot
from apps.synthesis.services import run_synthesis
from apps.topicprio.models import Topic

User = get_user_model()

NOW = timezone.now()


def past_window(days_ago=45, length_days=30):
    start = NOW - timedelta(days=days_ago)
    end = start + timedelta(days=length_days)
    return start, end


def active_window(started_days_ago=5, remaining_days=55):
    start = NOW - timedelta(days=started_days_ago)
    end = NOW + timedelta(days=remaining_days)
    return start, end


def future_window(starts_in_days=10, length_days=30):
    start = NOW + timedelta(days=starts_in_days)
    end = start + timedelta(days=length_days)
    return start, end


class Command(BaseCommand):
    help = (
        'Seed a demo organisation, projects and modules covering every '
        'participation module available on Collective Genius, grounded '
        'in a real agri-food systems research scenario. Safe to re-run: '
        'existing rows are looked up by name/slug and reused.'
    )

    def handle(self, *args, **options):
        self.users = self._create_users()
        self.org = self._create_organisation()

        self._seed_ideas()
        self._seed_mapideas()
        self._seed_debate()
        self._seed_budgeting()
        self._seed_topicprio()
        self._seed_documents()
        self._seed_polls()
        self._seed_interactiveevents()
        self._seed_offlineevents()
        self._seed_delphi()
        self._seed_consent()
        self._seed_delegation()
        self._seed_forecasting()
        self._seed_quadraticvoting()

        self.stdout.write(self.style.SUCCESS(
            'Demo data seeded under organisation '
            f'"{self.org.name}" ({self.org.slug}).'
        ))

    # -- helpers -----------------------------------------------------

    def _create_users(self):
        specs = [
            ('gkaruri', 'grace.karuri@example.com'),
            ('mklein', 'mark.klein@example.com'),
            ('afarmer', 'farmer.rep@example.com'),
            ('kofi', 'policy.officer@example.com'),
            ('leila', 'civic.participant@example.com'),
        ]
        users = []
        for username, email in specs:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'email': email, 'is_active': True},
            )
            if created:
                user.set_password('demo-participant-1')
                user.save()
            users.append(user)
        return users

    def _initiator(self):
        return User.objects.filter(username='initiator').first() \
            or self.users[0]

    def _get_or_create_project(self, name, description, access=Access.PUBLIC,
                               information=''):
        project, _created = Project.objects.get_or_create(
            name=name,
            organisation=self.org,
            defaults={
                'description': description,
                'information': information,
                'access': access,
                'is_draft': False,
            },
        )
        return project

    def _get_or_create_module(self, project, name, description, weight=1):
        module, _created = Module.objects.get_or_create(
            name=name,
            project=project,
            defaults={
                'description': description,
                'weight': weight,
                'is_draft': False,
            },
        )
        return module

    def _get_or_create_phase(self, module, phase_type, name, description,
                             start, end, weight=0):
        phase, created = Phase.objects.get_or_create(
            module=module,
            type=phase_type,
            defaults={
                'name': name,
                'description': description,
                'start_date': start,
                'end_date': end,
                'weight': weight,
            },
        )
        if not created:
            phase.start_date = start
            phase.end_date = end
            phase.save()
        return phase

    def _get_or_create_category(self, module, name):
        category, _created = Category.objects.get_or_create(
            module=module, name=name,
        )
        return category

    def _comment(self, target, creator, text):
        comment, _created = Comment.objects.get_or_create(
            content_type=ContentType.objects.get_for_model(target),
            object_pk=target.pk,
            creator=creator,
            comment=text,
        )
        return comment

    def _rating(self, target, creator, value):
        Rating.objects.update_or_create(
            content_type=ContentType.objects.get_for_model(target),
            object_pk=target.pk,
            creator=creator,
            defaults={'value': value},
        )

    # -- organisation -------------------------------------------------

    def _create_organisation(self):
        initiator = User.objects.filter(username='initiator').first()
        admin = User.objects.filter(username='admin').first()

        org, _created = Organisation.objects.get_or_create(
            name='collective-genius-demo',
            defaults={'imprint': 'imprint collective-genius-demo'},
        )
        for initiator_candidate in filter(None, [initiator, admin]):
            org.initiators.add(initiator_candidate)

        org.set_current_language('en')
        org.title = 'Agri-Food Systems Research Lab'
        org.description = (
            'Mixed-methods research on how farmers and food-system actors '
            'perceive, value and take up sustainable practices — from '
            'smallholder fieldwork across Africa to deliberative civic '
            'assemblies on food systems and climate change.'
        )
        org.slogan = (
            'Collective intelligence for sustainable agri-food systems'
        )
        org.save()
        return org

    # -- ideas: collect_feedback (crud + comment + rate) --------------

    def _seed_ideas(self):
        project = self._get_or_create_project(
            'Farmer Perception & Uptake of Cluster Farming',
            'Crowdsourcing barriers and enablers behind the gap between '
            'farmers believing a sustainable practice works and actually '
            'adopting it.',
            information=(
                'Following a 300-farmer, 10-community study that found 79% '
                'of farmers believed a sustainable practice effective while '
                'only 9% adopted it, this project collects ideas on what '
                'would close that perception-to-uptake gap.'
            ),
        )
        module = self._get_or_create_module(
            project, 'Barriers & Enablers to Practice Uptake',
            'Share and discuss what stops farmers from adopting practices '
            'they already believe in, and what would help.',
        )
        start, end = active_window()
        self._get_or_create_phase(
            module, 'a4_candy_ideas:collect_feedback',
            'Collect ideas and get feedback',
            'Create new ideas and get feedback through rates and comments.',
            start, end,
        )
        cat = self._get_or_create_category(module, 'Extension & Training')

        ideas_data = [
            ('Peer farmer-to-farmer demonstration plots',
             'Trusted local farmers running visible demonstration plots '
             'did more to shift adoption than any leaflet or workshop.'),
            ('Bundle the practice with credit access',
             'Uptake tracked closely with whether the practice was linked '
             'to microcredit or input support, not just belief in it.'),
            ('Coordinate adoption within, not across, communities',
             'Several respondents said they would only adopt once '
             'neighbours in the same cooperative did — uptake is '
             'coordinated, not individual.'),
            ('Translate NLP-coded survey findings into local-language briefs',
             'The Python NLP analysis of open-ended answers surfaced trust '
             'and coordination themes that never made it back to '
             'participants in a usable form.'),
        ]
        for i, (name, description) in enumerate(ideas_data):
            idea, created = Idea.objects.get_or_create(
                name=name, module=module,
                defaults={
                    'description': description,
                    'creator': self.users[i % len(self.users)],
                    'category': cat,
                },
            )
            if created:
                self._comment(idea, self._initiator(),
                              'Thanks for flagging this — folding it '
                              'into the community workshop agenda.')
                self._comment(idea, self.users[(i + 1) % len(self.users)],
                              'Saw the same pattern in our fieldwork.')
                self._rating(idea, self.users[(i + 2) % len(self.users)], 1)
                self._rating(idea, self.users[(i + 3) % len(self.users)], 1)

    # -- mapideas: collect_feedback ------------------------------------

    def _seed_mapideas(self):
        project = self._get_or_create_project(
            'Mapping Sustainable Farming Pilots Across Communities',
            'A community-sourced map of where cluster-farming and other '
            'sustainable practices are being piloted.',
        )
        module = self._get_or_create_module(
            project, 'Community Practice Map',
            'Drop a pin where your community is piloting a sustainable '
            'practice, and describe how it is going.',
        )
        start, end = active_window()
        self._get_or_create_phase(
            module, 'a4_candy_mapideas:collect_feedback',
            'Collect ideas and get feedback',
            'Create new map ideas and get feedback through rates and '
            'comments.',
            start, end,
        )

        pins = [
            ('Benguerir cooperative pilot plot', 'Benguerir, Morocco',
             32.2381, -7.9558,
             'Cluster-farming pilot supported through the UM6P outreach '
             'programme, now in its second season.'),
            ('Rehamna smallholder cluster', 'Rehamna, Morocco',
             32.3306, -8.1050,
             'Ten smallholders coordinating input purchase and harvest '
             'timing after the 2022 fieldwork.'),
            ('Ouled Hassoune demonstration site', 'Ouled Hassoune, Morocco',
             32.1122, -8.0206,
             'Community host from the Global Citizens’ Assembly '
             'sessions is trialling the practice here.'),
        ]
        for i, (name, label, lat, lon, description) in enumerate(pins):
            MapIdea.objects.get_or_create(
                name=name, module=module,
                defaults={
                    'description': description,
                    'creator': self.users[i % len(self.users)],
                    'point': {'type': 'Point', 'coordinates': [lon, lat]},
                    'point_label': label,
                },
            )

    # -- debate (+ argument mapping stances on its comments) -------------

    def _seed_debate(self):
        project = self._get_or_create_project(
            'Should Support Target Smallholders or Cooperatives?',
            'A structured debate on where agri-food support programmes '
            'should focus, drawn from the OCP Africa / UM6P fieldwork.',
        )
        module = self._get_or_create_module(
            project, 'Policy Debate',
            'Debate subjects raised by the outreach programme.',
        )
        start, end = active_window()
        self._get_or_create_phase(
            module, 'a4_candy_debate:debate',
            'Debate phase', 'Debate subjects.',
            start, end,
        )

        subjects_data = [
            ('Target individual smallholders directly',
             'Direct support reaches the farmer fastest, but the fieldwork '
             'showed adoption is coordinated within communities, not '
             'individual.'),
            ('Route support through cooperatives',
             'Cooperatives can coordinate adoption and credit access, but '
             'risk excluding farmers outside existing cooperative networks.'),
        ]
        stance_comments = [
            (Stance.SUPPORTS, 'This matches what the outreach officers '
             'reported from the Africa Initiative programme.'),
            (Stance.OPPOSES, 'Depends heavily on how mature the '
             'cooperative is in that region — I would not lead with '
             'this.'),
        ]
        for i, (name, description) in enumerate(subjects_data):
            subject, created = Subject.objects.get_or_create(
                name=name, module=module,
                defaults={
                    'description': description,
                    'creator': self._initiator(),
                },
            )
            if created:
                for j, (stance_value, text) in enumerate(stance_comments):
                    creator = self.users[(i + j) % len(self.users)]
                    comment = self._comment(subject, creator, text)
                    Stance.objects.get_or_create(
                        comment=comment, defaults={'value': stance_value},
                    )

    # -- budgeting: collect_feedback -------------------------------------

    def _seed_budgeting(self):
        project = self._get_or_create_project(
            'Community Research & Extension Fund',
            'Participatory budget for community-level research and '
            'extension activities tied to the outreach programme.',
        )
        module = self._get_or_create_module(
            project, 'Extension Activity Proposals',
            'Propose and cost an extension or research activity for the '
            'community fund.',
        )
        start, end = active_window()
        self._get_or_create_phase(
            module, 'a4_candy_budgeting:collect_feedback',
            'Collect ideas and get feedback',
            'Create new proposals and get feedback through rates and '
            'comments.',
            start, end,
        )

        proposals = [
            ('Farmer-to-farmer demonstration plot network',
             'Fund five peer-run demonstration plots across the 10 '
             'communities from the original study.', 4200,
             'Benguerir region', 32.24, -7.95),
            ('Local-language survey findings briefing',
             'Translate the NLP-coded survey findings into local-language '
             'briefings and community meetings.', 1500,
             'Rehamna region', 32.33, -8.10),
            ('Delphi-style consensus workshop series',
             'Run a structured Delphi process with cooperative leaders to '
             'agree adoption support priorities.', 2800,
             'Ouled Hassoune region', 32.11, -8.02),
        ]
        for i, (name, description, budget, label, lat, lon) in \
                enumerate(proposals):
            Proposal.objects.get_or_create(
                name=name, module=module,
                defaults={
                    'description': description,
                    'creator': self.users[i % len(self.users)],
                    'budget': budget,
                    'point': {'type': 'Point', 'coordinates': [lon, lat]},
                    'point_label': label,
                },
            )

    # -- topicprio (deliberately a PAST phase; feeds synthesis) -----------

    def _seed_topicprio(self):
        project = self._get_or_create_project(
            'Prioritizing Research Themes for Anticipatory Innovation '
            'Systems',
            'Ranking candidate research themes for the forthcoming work '
            'on anticipatory innovation systems in African agri-food '
            'contexts.',
        )
        module = self._get_or_create_module(
            project, 'Research Theme Prioritization',
            'Rate and comment on candidate research themes. This round '
            'has already closed — shown here to demonstrate the '
            '"finished" state of a module.',
        )
        start, end = past_window()
        self._get_or_create_phase(
            module, 'a4_candy_topicprio:prioritize',
            'Prioritize phase', 'Prioritize and comment topics.',
            start, end,
        )

        topics = [
            ('Triangular trap dynamics in innovation systems',
             'How anticipatory capacity, absorptive capacity and '
             'coordination interact across African innovation systems.'),
            ('Emissions trajectories and smallholder practice change',
             'Linking the 54-country EDGAR emissions analysis to '
             'household-level practice adoption data.'),
            ('Trust and coordination as adoption determinants',
             'Following up the 79% belief / 9% adoption gap with a '
             'dedicated trust-and-coordination study.'),
        ]
        comments_for_synthesis = []
        for i, (name, description) in enumerate(topics):
            topic, created = Topic.objects.get_or_create(
                name=name, module=module,
                defaults={
                    'description': description,
                    'creator': self.users[i % len(self.users)],
                },
            )
            if created:
                self._rating(topic, self.users[(i + 1) % len(self.users)], 1)
                self._rating(topic, self.users[(i + 2) % len(self.users)], 1)
            comment = self._comment(
                topic, self.users[i % len(self.users)],
                'My read: {}'.format(name.lower()),
            )
            comments_for_synthesis.append(comment)

        # Rate the comments themselves (not just the topics) so the
        # synthesis engine -- which clusters opinions from comment
        # ratings -- has something real to analyse.
        for comment in comments_for_synthesis:
            for j, user in enumerate(self.users):
                if user.pk == comment.creator_id:
                    continue
                value = 1 if (j + comment.pk) % 2 == 0 else -1
                self._rating(comment, user, value)

        if not SynthesisSnapshot.objects.filter(module=module).exists():
            run_synthesis(module, min_votes_per_statement=2)

    # -- documents --------------------------------------------------------

    def _seed_documents(self):
        project = self._get_or_create_project(
            'Draft Deliberation Protocol — Global Citizens’ '
            'Assembly on Food Systems',
            'Comment on the draft protocol used to facilitate the online '
            'deliberative sessions on food systems and climate change.',
        )
        module = self._get_or_create_module(
            project, 'Deliberation Protocol (Draft)',
            'Chapter-by-chapter draft of the facilitation protocol, open '
            'for paragraph-level comments.',
        )
        start, end = active_window()
        self._get_or_create_phase(
            module, 'a4_candy_documents:comment',
            'Comment phase',
            'Post comments on the paragraphs of the text',
            start, end,
        )

        chapters = [
            ('1. Framing the session',
             ['Each of the 14 sessions opens with a short, neutral framing '
              'of the topic — food systems, climate change or '
              'agroecology — read aloud by the community host.',
              'Participants are reminded that the goal is deliberation, '
              'not debate: understanding trade-offs, not winning a point.']),
            ('2. Co-design exercise',
             ['Small breakout groups co-design a concrete proposal '
              'addressing the session topic, guided by prepared briefing '
              'materials.',
              'The host consolidates group outputs into a shared '
              'summary before the closing plenary.']),
        ]
        for chapter_i, (chapter_name, paragraphs) in enumerate(chapters):
            chapter, _created = Chapter.objects.get_or_create(
                name=chapter_name, module=module,
                defaults={
                    'creator': self._initiator(),
                    'weight': chapter_i,
                },
            )
            for para_i, text in enumerate(paragraphs):
                paragraph, p_created = Paragraph.objects.get_or_create(
                    chapter=chapter, weight=para_i,
                    defaults={'text': f'<p>{text}</p>'},
                )
                if p_created:
                    self._comment(
                        paragraph,
                        self.users[(chapter_i + para_i) % len(self.users)],
                        'Worked well in the January cohort — '
                        'suggest keeping this as-is.',
                    )

    # -- polls (deliberately a FUTURE phase) -------------------------------

    def _seed_polls(self):
        project = self._get_or_create_project(
            'Quick Poll: Preferred Channel for Farmer Engagement',
            'A short poll to decide how the outreach programme should '
            'communicate with participating communities. Opens soon — '
            'shown here to demonstrate the "not yet started" state.',
        )
        module = self._get_or_create_module(
            project, 'Engagement Channel Poll',
            'Vote on your preferred channel for updates and check-ins.',
        )
        start, end = future_window()
        self._get_or_create_phase(
            module, 'a4polls:voting',
            'Voting phase',
            'Answer the questions and comment on the poll.',
            start, end,
        )

        poll, _created = Poll.objects.get_or_create(
            module=module, defaults={'creator': self._initiator()},
        )
        if not poll.questions.exists():
            q1 = PollQuestion.objects.create(
                poll=poll, label='How should we reach you between visits?',
                weight=0,
            )
            for w, label in enumerate(
                    ['SMS', 'WhatsApp group', 'Community radio announcement',
                     'In-person only']):
                Choice.objects.create(question=q1, label=label, weight=w)

            PollQuestion.objects.create(
                poll=poll,
                label='Anything else you would want from the programme?',
                weight=1, is_open=True,
            )

    # -- interactiveevents --------------------------------------------------

    def _seed_interactiveevents(self):
        project = self._get_or_create_project(
            'Live Town Hall Q&A — Africa’s Emissions Trajectory',
            'Live "Speak Up" session for questions on the greenhouse-gas '
            'emissions analysis across 54 African countries.',
        )
        module = self._get_or_create_module(
            project, 'Speak Up: Emissions Trajectory Q&A',
            'Submit and like questions live during the town hall.',
        )
        start, end = active_window()
        self._get_or_create_phase(
            module, 'a4_candy_interactive_events:issue',
            'Issue phase', 'Add question.',
            start, end,
        )

        questions = [
            'Which countries are driving the trend most in the last five '
            'years?',
            'How does the emissions analysis connect back to the '
            'farmer-level adoption data?',
            'Will the anticipatory innovation systems framework be applied '
            'to this dataset too?',
        ]
        for text in questions:
            LiveQuestion.objects.get_or_create(
                module=module, text=text,
                defaults={'is_live': False},
            )

    # -- offlineevents (project-level, no module) ---------------------------

    def _seed_offlineevents(self):
        project = self._get_or_create_project(
            'Field Research & Community Workshops',
            'Real-world workshops and field visits across the 10 study '
            'communities — shown on the project timeline.',
        )

        events = [
            ('Community kickoff workshop', 'Workshop', -60,
             'Introduced the study to community leaders and agreed the '
             'fieldwork schedule across the 10 communities.'),
            ('Delphi consensus session with cooperative leads',
             'Delphi session', -20,
             'Structured stakeholder deliberation, documented toward '
             'consensus on adoption support priorities.'),
            ('Findings feedback session', 'Feedback event', 25,
             'Present the perception-vs-uptake findings back to '
             'participating farmers and gather their reactions.'),
        ]
        for name, event_type, day_offset, description in events:
            OfflineEvent.objects.get_or_create(
                name=name, project=project,
                defaults={
                    'creator': self._initiator(),
                    'event_type': event_type,
                    'date': NOW + timedelta(days=day_offset),
                    'description': f'<p>{description}</p>',
                },
            )

    # -- delphi: structured, anonymous, multi-round estimation --------------

    def _seed_delphi(self):
        project = self._get_or_create_project(
            'Delphi Round: Cluster-Farming Adoption Priorities',
            'Anonymous, structured estimation with cooperative leads, in '
            'the same style used in the i4Policy Delphi processes.',
        )
        module = self._get_or_create_module(
            project, 'Adoption Priorities Delphi',
            'Give an anonymous numeric estimate and revise it once you '
            'see the group’s aggregate.',
        )
        start, end = active_window()
        self._get_or_create_phase(
            module, 'a4_candy_delphi:delphi',
            'Delphi round phase',
            'Give an anonymous numeric estimate, see the group’s '
            'aggregate, and revise it over structured rounds.',
            start, end,
        )

        question, _created = DelphiQuestion.objects.get_or_create(
            module=module,
            title='What share of smallholders in your community will '
                  'adopt cluster farming within 2 years?',
            defaults={
                'description': 'Base this on the current pilot uptake, '
                               'not on stated intent alone.',
                'scale_hint': '0-100%',
            },
        )
        # Two closed rounds plus an open third round, so the module page
        # shows both the round-over-round convergence chart (needs >= 2
        # finished rounds) and a live form to submit round 3.
        if question.current_round < 3:
            question.current_round = 3
            question.save()

        round_1_estimates = [
            (35, 'Uptake tends to track the demonstration plots, not the '
             'training sessions.'),
            (20, 'Credit access is the binding constraint in my '
             'community.'),
            (45, 'Cooperative coordination is already strong here.'),
        ]
        for i, (value, rationale) in enumerate(round_1_estimates):
            DelphiResponse.objects.get_or_create(
                question=question, round_number=1,
                creator=self.users[i % len(self.users)],
                defaults={'value': value, 'rationale': rationale},
            )

        round_2_estimates = [
            (28, 'Seeing the group leaning lower changed my estimate.'),
            (24, 'Still think credit access caps this below 30%.'),
            (30, 'Coming down some, but coordination is genuinely strong '
             'here.'),
        ]
        for i, (value, rationale) in enumerate(round_2_estimates):
            DelphiResponse.objects.get_or_create(
                question=question, round_number=2,
                creator=self.users[i % len(self.users)],
                defaults={'value': value, 'rationale': rationale},
            )

    # -- consent: propose and decide without a majority vote -----------------

    def _seed_consent(self):
        project = self._get_or_create_project(
            'Consent Decision: Extension Fund Allocation Rule',
            'Decide the allocation rule for the extension fund by consent '
            'rather than a majority vote.',
        )
        module = self._get_or_create_module(
            project, 'Allocation Rule Decision',
            'Propose an allocation rule and respond by consent: agree, '
            'stand aside, or object.',
        )
        start, end = active_window()
        self._get_or_create_phase(
            module, 'a4_candy_consent:consent',
            'Consent decision phase',
            'Propose actions for the group, and decide by consent.',
            start, end,
        )

        proposal, _created = ConsentProposal.objects.get_or_create(
            module=module,
            title='Adopt a cooperative-first allocation rule',
            defaults={
                'description': 'Route at least 60% of the extension fund '
                               'through cooperatives, with the remainder '
                               'open to individual smallholder proposals.',
                'creator': self._initiator(),
            },
        )
        responses = [
            (ConsentResponse.AGREE, ''),
            (ConsentResponse.STAND_ASIDE,
             'Not my preference, but I will not block it.'),
            (ConsentResponse.OBJECT,
             'This excludes the smallholders outside any cooperative in '
             'the Ouled Hassoune area — need a carve-out for them '
             'first.'),
        ]
        for i, (stance, reason) in enumerate(responses):
            ConsentResponse.objects.get_or_create(
                proposal=proposal, creator=self.users[i % len(self.users)],
                defaults={'stance': stance, 'reason': reason},
            )

    # -- delegation: liquid democracy ----------------------------------------

    def _seed_delegation(self):
        project = self._get_or_create_project(
            'Liquid Democracy: Programme Priority for Next Year',
            'Vote directly, or delegate your vote to someone you trust, '
            'on next year’s outreach programme priority.',
        )
        module = self._get_or_create_module(
            project, 'Programme Priority Vote',
            'Vote directly, or delegate to someone you trust.',
        )
        start, end = active_window()
        self._get_or_create_phase(
            module, 'a4_candy_delegation:delegation',
            'Liquid democracy phase',
            'Vote directly, or delegate your vote to someone you trust.',
            start, end,
        )

        round_, _created = DelegationRound.objects.get_or_create(
            module=module,
            title='Where should the outreach programme focus next year?',
        )
        option_titles = [
            'Expand the demonstration plot network',
            'Invest in credit-linked adoption support',
            'Run more Delphi-style consensus workshops',
        ]
        options = []
        for w, title in enumerate(option_titles):
            option, _created = DelegationOption.objects.get_or_create(
                delegation_round=round_, title=title, defaults={'weight': w},
            )
            options.append(option)

        DelegationVote.objects.get_or_create(
            delegation_round=round_, creator=self.users[0],
            defaults={'option': options[0]},
        )
        DelegationVote.objects.get_or_create(
            delegation_round=round_, creator=self.users[1],
            defaults={'option': options[1]},
        )
        Delegation.objects.get_or_create(
            delegation_round=round_,
            delegator=self.users[2],
            defaults={'delegatee': self.users[0]},
        )

    # -- forecasting: probability estimates on a resolvable question ---------

    def _seed_forecasting(self):
        project = self._get_or_create_project(
            'Forecasting: Will Adoption Reach 50%?',
            'Forecast the probability that cluster-farming adoption '
            'reaches 50% across the 10 study communities.',
        )
        module = self._get_or_create_module(
            project, 'Adoption Forecast',
            'Forecast the probability of the question’s outcome.',
        )
        start, end = active_window()
        self._get_or_create_phase(
            module, 'a4_candy_forecasting:forecast',
            'Forecasting phase',
            'Forecast the probability of each question’s outcome.',
            start, end,
        )

        question, _created = ForecastingQuestion.objects.get_or_create(
            module=module,
            title='Will cluster-farming adoption reach 50% across the 10 '
                  'study communities within 2 years?',
            defaults={
                'resolution_criteria': 'Resolves YES if a community-level '
                                       'follow-up survey finds 50% or more '
                                       'of surveyed farmers have adopted '
                                       'the practice.',
                'closes_at': NOW + timedelta(days=50),
            },
        )
        for i, probability in enumerate([30, 45, 25, 55, 40]):
            if i >= len(self.users):
                break
            Forecast.objects.get_or_create(
                question=question, creator=self.users[i],
                defaults={'probability': probability},
            )

        # A second, already-resolved question -- shown alongside the open
        # one above so the module page demonstrates both the live
        # forecast form and the resolved-outcome probability meter plus
        # forecaster leaderboard.
        resolved_question, _created = \
            ForecastingQuestion.objects.get_or_create(
                module=module,
                title='Did the Benguerir pilot reach 30% adoption in its '
                      'first season?',
                defaults={
                    'resolution_criteria': 'Resolves YES if the '
                                           'season-end community survey '
                                           'found 30% or more of '
                                           'surveyed farmers had adopted '
                                           'the practice.',
                    'is_resolved': True,
                    'outcome': True,
                },
            )
        if not resolved_question.is_resolved:
            resolved_question.is_resolved = True
            resolved_question.outcome = True
            resolved_question.save()
        for i, probability in enumerate([70, 55, 80, 65, 60]):
            if i >= len(self.users):
                break
            Forecast.objects.get_or_create(
                question=resolved_question, creator=self.users[i],
                defaults={'probability': probability},
            )

    # -- quadratic voting: spend a voice-credit budget across options --------

    def _seed_quadraticvoting(self):
        project = self._get_or_create_project(
            'Quadratic Voting: Prioritize Outreach Investments',
            'Spend a shared voice-credit budget across candidate outreach '
            'investments to show strength of preference, not just rank.',
        )
        module = self._get_or_create_module(
            project, 'Outreach Investment Priorities',
            'Spend voice credits across options to express how strongly '
            'you feel, not just which one you prefer.',
        )
        start, end = active_window()
        self._get_or_create_phase(
            module, 'a4_candy_quadraticvoting:voting',
            'Quadratic voting phase',
            'Spend voice credits across options to express how strongly '
            'you feel, not just which one you prefer.',
            start, end,
        )

        round_, _created = VotingRound.objects.get_or_create(
            module=module,
            title='Which outreach investments should we prioritize?',
            defaults={'credit_budget': 100},
        )
        option_titles = [
            'Peer demonstration plots',
            'Local-language communication materials',
            'Cooperative coordination workshops',
        ]
        options = []
        for w, title in enumerate(option_titles):
            option, _created = QuadraticOption.objects.get_or_create(
                voting_round=round_, title=title, defaults={'weight': w},
            )
            options.append(option)

        allocations = [
            (self.users[0], [6, 2, 1]),
            (self.users[1], [1, 5, 3]),
            (self.users[2], [3, 3, 4]),
        ]
        for user, votes in allocations:
            for option, vote_count in zip(options, votes):
                Allocation.objects.get_or_create(
                    option=option, creator=user,
                    defaults={'votes': vote_count},
                )

        # Close the round so the module page shows the results chart
        # rather than the ballot form (results are hidden while open, to
        # avoid influencing later votes).
        if round_.is_open:
            round_.is_open = False
            round_.save()
