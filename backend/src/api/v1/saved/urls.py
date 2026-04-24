from django.urls import path

from . import views

urlpatterns = [
    path("venues", views.saved_venues, name="v1-saved-venues"),
    path(
        "venues/<str:venue_id>",
        views.remove_saved_venue,
        name="v1-saved-venues-destroy",
    ),
]
