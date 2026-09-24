from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^ideas/(?P<module_slug>[-\w_]+)/$',
            views.SimilarIdeasView.as_view(),
            name='similar-ideas'),
    re_path(r'^proposals/(?P<module_slug>[-\w_]+)/$',
            views.SimilarProposalsView.as_view(),
            name='similar-proposals'),
    re_path(r'^mapideas/(?P<module_slug>[-\w_]+)/$',
            views.SimilarMapIdeasView.as_view(),
            name='similar-mapideas'),
]
