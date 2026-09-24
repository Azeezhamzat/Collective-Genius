from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^(?P<subject_pk>\d+)/$',
            views.ArgumentMapView.as_view(),
            name='argument-map'),
]
