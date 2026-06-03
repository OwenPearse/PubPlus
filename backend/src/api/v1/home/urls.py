from django.urls import path

from api.v1.home.views import home_feed

urlpatterns = [
    path("", home_feed, name="home-feed"),
]
