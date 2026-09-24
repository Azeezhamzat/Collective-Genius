from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^(?P<project_slug>[-\w_]+)/subscribe/$',
            views.SubscribeView.as_view(),
            name='push-subscribe'),
    re_path(r'^(?P<project_slug>[-\w_]+)/unsubscribe/$',
            views.UnsubscribeView.as_view(),
            name='push-unsubscribe'),
]
