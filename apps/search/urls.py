from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^$', views.OrganisationSearchView.as_view(), name='search'),
]
