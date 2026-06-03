from django.urls import path

from api.v1.map.views import map_venues

urlpatterns = [
    path("venues", map_venues, name="map-venues"),
]
