from django.urls import path

from .views import equipment_create, equipment_detail, equipment_edit, equipment_list

app_name = "equipment"

urlpatterns = [
    path("", equipment_list, name="list"),
    path("new/", equipment_create, name="create"),
    path("<str:code>/", equipment_detail, name="detail"),
    path("<str:code>/edit/", equipment_edit, name="edit"),
]
