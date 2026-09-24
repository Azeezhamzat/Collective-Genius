from django.conf import settings
from django.views import generic

from adhocracy4.projects.mixins import ProjectMixin
from apps.translation import backends as translation_backends

from .models import SummarySnapshot


class SummaryModuleDetail(ProjectMixin, generic.TemplateView):
    """Standalone overlay page, same reasoning as apps/synthesis: this
    analyzes comments that already exist in whatever phase is running or
    has run, it isn't itself something to do, so it isn't a phase type.
    """

    template_name = 'a4_candy_summarization/module_summary.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        snapshot = SummarySnapshot.objects.filter(
            module=self.module).first()
        context['snapshot'] = snapshot
        context['translation_enabled'] = translation_backends.is_enabled()
        context['languages'] = getattr(settings, 'LANGUAGES', ())

        target_language = self.request.GET.get('lang', '').strip()
        context['target_language'] = target_language

        if snapshot:
            key_comments = list(
                snapshot.key_comments.select_related('comment'))
            if target_language and context['translation_enabled']:
                for key_comment in key_comments:
                    key_comment.translated_text = \
                        translation_backends.translate(
                            key_comment.comment.comment, target_language)
            context['key_comments'] = key_comments
        return context
