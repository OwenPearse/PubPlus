from django.urls import path

from api.v1.search.views import search_venues

urlpatterns = [
    path("venues", search_venues, name="search-venues"),
]
