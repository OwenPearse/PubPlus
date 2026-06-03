from django.urls import path

from api.v1.reference.views import reference_localities

urlpatterns = [
    path("localities", reference_localities, name="reference-localities"),
]
