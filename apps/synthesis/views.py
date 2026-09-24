from django.views import generic

from adhocracy4.projects.mixins import DisplayProjectOrModuleMixin
from adhocracy4.projects.mixins import ProjectMixin

from .models import SynthesisSnapshot


class SynthesisModuleDetail(ProjectMixin, DisplayProjectOrModuleMixin,
                            generic.TemplateView):
    template_name = 'a4_candy_synthesis/module_synthesis.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        snapshot = SynthesisSnapshot.objects.filter(
            module=self.module).first()
        context['snapshot'] = snapshot
        if snapshot:
            results = list(snapshot.statement_results.select_related(
                'comment'))
            context['bridging_statements'] = [
                r for r in results if r.is_bridging][:10]
            context['divisive_statements'] = [
                r for r in results if r.is_divisive][:10]
        return context
