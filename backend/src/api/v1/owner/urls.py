from django.urls import path

from api.v1.owner.views import (
    owner_auth_probe,
    owner_provision,
    owner_venue_claim_candidates,
    owner_venue_claim_requests,
    owner_venue_detail,
    owner_venue_features,
    owner_venue_hours_patch,
    owner_venue_meal_special_detail,
    owner_venue_meal_specials,
    owner_venue_operational_profile_patch,
    owner_venue_proposals,
    owner_venue_restricted_change_request,
    owner_venues_list,
)

urlpatterns = [
    path("provision", owner_provision, name="owner-provision"),
    path("auth-probe", owner_auth_probe, name="owner-auth-probe"),
    path(
        "venue-claim-candidates",
        owner_venue_claim_candidates,
        name="owner-venue-claim-candidates",
    ),
    path(
        "venue-claim-requests",
        owner_venue_claim_requests,
        name="owner-venue-claim-requests",
    ),
    path("venues", owner_venues_list, name="owner-venues-list"),
    path("venues/<uuid:venue_id>", owner_venue_detail, name="owner-venue-detail"),
    path(
        "venues/<uuid:venue_id>/proposals",
        owner_venue_proposals,
        name="owner-venue-proposals",
    ),
    path(
        "venues/<uuid:venue_id>/operational-profile",
        owner_venue_operational_profile_patch,
        name="owner-venue-operational-profile-patch",
    ),
    path(
        "venues/<uuid:venue_id>/hours",
        owner_venue_hours_patch,
        name="owner-venue-hours-patch",
    ),
    path(
        "venues/<uuid:venue_id>/features",
        owner_venue_features,
        name="owner-venue-features",
    ),
    path(
        "venues/<uuid:venue_id>/meal-specials",
        owner_venue_meal_specials,
        name="owner-venue-meal-specials",
    ),
    path(
        "venues/<uuid:venue_id>/meal-specials/<uuid:special_id>",
        owner_venue_meal_special_detail,
        name="owner-venue-meal-special-detail",
    ),
    path(
        "venues/<uuid:venue_id>/restricted-change-requests",
        owner_venue_restricted_change_request,
        name="owner-venue-restricted-change-request",
    ),
]
