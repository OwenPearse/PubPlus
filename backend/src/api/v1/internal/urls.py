from django.urls import path

from api.v1.internal.views import internal_auth_probe

urlpatterns = [
    path("auth-probe", internal_auth_probe, name="internal-auth-probe"),
]
