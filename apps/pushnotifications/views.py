import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseBadRequest
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import generic

from adhocracy4.projects.models import Project

from .models import PushSubscription


class SubscribeView(LoginRequiredMixin, generic.View):
    """Registers (or updates) the calling browser's Web Push
    subscription for one project. Called from the "enable
    notifications" button's JS after ``PushManager.subscribe()``
    succeeds; login is required since a subscription belongs to a
    specific user, the same way Follow does.
    """

    def post(self, request, *args, **kwargs):
        project = get_object_or_404(
            Project, slug=self.kwargs['project_slug'])
        try:
            data = json.loads(request.body)
            endpoint = data['endpoint']
            p256dh_key = data['keys']['p256dh']
            auth_key = data['keys']['auth']
        except (KeyError, ValueError, TypeError):
            return HttpResponseBadRequest('Invalid subscription payload.')

        PushSubscription.objects.update_or_create(
            endpoint=endpoint,
            defaults={
                'user': request.user,
                'project': project,
                'p256dh_key': p256dh_key,
                'auth_key': auth_key,
            },
        )
        return JsonResponse({'status': 'subscribed'})


class UnsubscribeView(LoginRequiredMixin, generic.View):

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            endpoint = data['endpoint']
        except (KeyError, ValueError, TypeError):
            return HttpResponseBadRequest('Invalid unsubscribe payload.')

        PushSubscription.objects.filter(
            endpoint=endpoint, user=request.user).delete()
        return JsonResponse({'status': 'unsubscribed'})
