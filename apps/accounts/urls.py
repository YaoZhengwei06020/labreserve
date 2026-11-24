from django.urls import path

from .views import LabLoginView, logout_view

app_name = "accounts"

urlpatterns = [
    path("login/", LabLoginView.as_view(), name="login"),
    path("logout/", logout_view, name="logout"),
]
