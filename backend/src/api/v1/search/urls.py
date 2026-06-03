from django.urls import path

from api.v1.search.views import search_filters, search_venues

urlpatterns = [
    path("filters", search_filters, name="search-filters"),
    path("venues", search_venues, name="search-venues"),
]
