from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^(?P<project_slug>[-\w_]+)/$',
            views.OpenDataIndexView.as_view(),
            name='opendata-index'),
    re_path(r'^(?P<project_slug>[-\w_]+)/export\.json$',
            views.OpenDataExportView.as_view(),
            name='opendata-export'),
]
