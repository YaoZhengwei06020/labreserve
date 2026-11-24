from django.urls import path

from .views.cancellation import cancel_reservation
from .views.reservation import create_reservation, create_reservation_submit, reservation_detail

app_name = "booking"

urlpatterns = [
    path("reservations/new/", create_reservation, name="create-reservation"),
    path("reservations/", create_reservation_submit, name="create-reservation-submit"),
    path("reservations/<int:slot_id>/cancel/", cancel_reservation, name="cancel-reservation"),
    path("reservations/<int:slot_id>/", reservation_detail, name="reservation-detail"),
]
