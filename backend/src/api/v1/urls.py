from django.urls import include, path

from api.v1.auth_probe_views import private_consumer_probe, public_probe
from api.v1.views import HealthView

urlpatterns = [
    path("health", HealthView.as_view(), name="health"),
    path("auth-probe/public", public_probe, name="auth-probe-public"),
    path("auth-probe/private", private_consumer_probe, name="auth-probe-private"),
    path("home/", include("api.v1.home.urls")),
    path("search/", include("api.v1.search.urls")),
    path("map/", include("api.v1.map.urls")),
    path("venues/", include("api.v1.venues.urls")),
    path("saved/", include("api.v1.saved.urls")),
    path("profile/", include("api.v1.profile.urls")),
    path("submissions/", include("api.v1.submissions.urls")),
    path("internal/", include("api.v1.internal.urls")),
]
