from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^(?P<module_slug>[-\w_]+)/$',
            views.VotingRoundDetail.as_view(),
            name='votinground-detail'),
]
