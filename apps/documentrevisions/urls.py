from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^(?P<pk>\d+)/$',
            views.ParagraphHistoryView.as_view(),
            name='paragraph-history'),
]
