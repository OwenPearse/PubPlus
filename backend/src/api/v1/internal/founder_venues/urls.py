from django.urls import path

from api.v1.internal.founder_venues import views

urlpatterns = [
    path("leads", views.list_leads, name="internal-founder-venues-leads"),
    path(
        "leads/<str:lead_id>",
        views.lead_detail_or_patch,
        name="internal-founder-venues-lead-detail",
    ),
    path(
        "leads/<str:lead_id>/mark-do-not-contact",
        views.mark_do_not_contact,
        name="internal-founder-venues-mark-dnc",
    ),
    path(
        "leads/<str:lead_id>/enrich",
        views.enrich_lead_website,
        name="internal-founder-venues-enrich",
    ),
    path("import", views.import_leads, name="internal-founder-venues-import"),
    path(
        "recompute-scores",
        views.recompute_scores,
        name="internal-founder-venues-recompute-scores",
    ),
    path("top", views.top_leads, name="internal-founder-venues-top"),
    path(
        "export.csv",
        views.export_leads_csv,
        name="internal-founder-venues-export-csv",
    ),
]
