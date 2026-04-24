from django.urls import path

from . import views

urlpatterns = [
    path("", views.consumer_profile, name="v1-consumer-profile"),
]
