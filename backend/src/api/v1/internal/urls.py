from django.urls import path

from api.v1.internal.views import (
    internal_auth_probe,
    internal_venue_detail,
    moderation_item_detail,
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
    path("venues/<str:venue_id>", internal_venue_detail, name="internal-venue-detail"),
]
