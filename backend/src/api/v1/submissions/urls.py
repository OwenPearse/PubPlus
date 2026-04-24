from django.urls import path

from . import views

urlpatterns = [
    path("corrections", views.submit_correction, name="v1-submissions-corrections"),
    path("new-venues", views.submit_new_venue, name="v1-submissions-new-venues"),
]
