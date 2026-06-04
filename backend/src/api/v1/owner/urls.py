from django.urls import path

from api.v1.owner.views import owner_auth_probe, owner_provision

urlpatterns = [
    path("provision", owner_provision, name="owner-provision"),
    path("auth-probe", owner_auth_probe, name="owner-auth-probe"),
]
