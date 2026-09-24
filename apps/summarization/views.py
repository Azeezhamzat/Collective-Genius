from django.views import generic

from adhocracy4.projects.mixins import ProjectMixin

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
        if snapshot:
            context['key_comments'] = list(
                snapshot.key_comments.select_related('comment'))
        return context
