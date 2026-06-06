from django.urls import path

from api.v1.internal.owner_claims.views import (
    owner_claim_approve_existing,
    owner_claim_approve_new,
    owner_claim_detail,
    owner_claim_needs_more_info,
    owner_claim_reject,
    owner_claims_list,
    owner_claims_summary,
)

urlpatterns = [
    path("summary", owner_claims_summary, name="internal-owner-claims-summary"),
    path("", owner_claims_list, name="internal-owner-claims-list"),
    path(
        "<str:claim_request_id>",
        owner_claim_detail,
        name="internal-owner-claim-detail",
    ),
    path(
        "<str:claim_request_id>/approve-existing",
        owner_claim_approve_existing,
        name="internal-owner-claim-approve-existing",
    ),
    path(
        "<str:claim_request_id>/approve-new",
        owner_claim_approve_new,
        name="internal-owner-claim-approve-new",
    ),
    path(
        "<str:claim_request_id>/reject",
        owner_claim_reject,
        name="internal-owner-claim-reject",
    ),
    path(
        "<str:claim_request_id>/needs-more-info",
        owner_claim_needs_more_info,
        name="internal-owner-claim-needs-more-info",
    ),
]
