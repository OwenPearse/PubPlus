from django.urls import include, path

from api.v1.internal.views import (
    internal_auth_probe,
    internal_venue_detail,
    moderation_item_decision,
    moderation_item_detail,
    moderation_item_notes,
    moderation_queue,
)

urlpatterns = [
    path("auth-probe", internal_auth_probe, name="internal-auth-probe"),
    path("moderation/queue", moderation_queue, name="internal-moderation-queue"),
    path(
        "moderation/items/<str:item_id>",
        moderation_item_detail,
        name="internal-moderation-item-detail",
    ),
    path(
        "moderation/items/<str:item_id>/decision",
        moderation_item_decision,
        name="internal-moderation-item-decision",
    ),
    path(
        "moderation/items/<str:item_id>/notes",
        moderation_item_notes,
        name="internal-moderation-item-notes",
    ),
    path("venues/<str:venue_id>", internal_venue_detail, name="internal-venue-detail"),
    path(
        "founder-venues/",
        include("api.v1.internal.founder_venues.urls"),
    ),
    path(
        "owner-claims/",
        include("api.v1.internal.owner_claims.urls"),
    ),
]
