from django.http import JsonResponse
from django.urls import include, path
from django.views.generic import RedirectView


def health(request):
    return JsonResponse({"service": "LabReserve", "stage": "technical-spike"})


urlpatterns = [
    path("", RedirectView.as_view(pattern_name="equipment:list", permanent=False), name="home"),
    path("accounts/", include("apps.accounts.urls")),
    path("equipment/", include("apps.equipment.urls")),
    path("", include("apps.booking.urls")),
    path("health/", health),
]
