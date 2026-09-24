from django.conf import settings
from django.views import generic

from adhocracy4.projects.mixins import ProjectMixin
from apps.translation import backends as translation_backends

from .models import SynthesisSnapshot


class SynthesisModuleDetail(ProjectMixin, generic.TemplateView):
    template_name = 'a4_candy_synthesis/module_synthesis.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        snapshot = SynthesisSnapshot.objects.filter(
            module=self.module).first()
        context['snapshot'] = snapshot
        context['translation_enabled'] = translation_backends.is_enabled()
        context['languages'] = getattr(settings, 'LANGUAGES', ())

        target_language = self.request.GET.get('lang', '').strip()
        context['target_language'] = target_language

        if snapshot:
            results = list(snapshot.statement_results.select_related(
                'comment'))
            bridging_statements = [r for r in results if r.is_bridging][:10]
            divisive_statements = [r for r in results if r.is_divisive][:10]

            if target_language and context['translation_enabled']:
                for result in bridging_statements + divisive_statements:
                    result.translated_text = translation_backends.translate(
                        result.comment.comment, target_language)

            context['bridging_statements'] = bridging_statements
            context['divisive_statements'] = divisive_statements
        return context
