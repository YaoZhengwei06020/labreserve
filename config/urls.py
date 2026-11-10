from django.http import JsonResponse
from django.urls import path


def health(request):
    return JsonResponse({"service": "LabReserve", "stage": "technical-spike"})


urlpatterns = [path("health/", health)]
