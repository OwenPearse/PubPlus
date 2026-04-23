from django.urls import path

from api.v1.venues.views import venue_detail

urlpatterns = [
    path("<str:venue_id>", venue_detail, name="venue-detail"),
]
