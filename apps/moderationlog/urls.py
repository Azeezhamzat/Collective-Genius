from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^(?P<project_slug>[-\w_]+)/$',
            views.ModerationLogView.as_view(),
            name='moderation-log'),
]
