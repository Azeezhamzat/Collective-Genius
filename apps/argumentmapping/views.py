from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import generic

from adhocracy4.comments.models import Comment
from apps.debate.models import Subject

from . import services
from .models import Stance


class ArgumentMapView(generic.View):
    template_name = 'a4_candy_argumentmapping/argument_map.html'

    def get_subject(self):
        return get_object_or_404(Subject, pk=self.kwargs['subject_pk'])

    def get(self, request, *args, **kwargs):
        return self.render()

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            login_url = reverse('account_login')
            return redirect('{}?next={}'.format(login_url, request.path))

        comment = get_object_or_404(
            Comment, pk=request.POST.get('comment_id'))
        if comment.creator_id != request.user.pk:
            messages.error(request, _(
                'You can only set the stance of your own comments.'))
            return self.render()

        value = request.POST.get('value')
        if value not in (Stance.SUPPORTS, Stance.OPPOSES):
            messages.error(request, _(
                'Please choose whether this comment supports or '
                'opposes.'))
            return self.render()

        Stance.objects.update_or_create(
            comment=comment, defaults={'value': value})
        messages.success(request, _('Stance saved.'))
        return self.render()

    def render(self):
        subject = self.get_subject()
        trees, comments_by_id = services.build_argument_map(subject)
        context = {
            'subject': subject,
            'module': subject.module,
            'project': subject.project,
            'trees': trees,
            'comments_by_id': comments_by_id,
        }
        return TemplateResponse(self.request, self.template_name, context)
