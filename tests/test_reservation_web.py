from copy import deepcopy
from datetime import timedelta
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import include, path, reverse
from django.utils import timezone

from apps.audit.models import OperationLog
from apps.booking.models import EquipmentSlot
from apps.booking.services import create_slot
from apps.equipment.models import Equipment


urlpatterns = [path("", include("apps.booking.urls"))]

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def reservation_web_settings(settings):
    """Supply only the foundation-owned URL/base-template pieces for isolated tests."""
    settings.ROOT_URLCONF = __name__
    template = deepcopy(settings.TEMPLATES[0])
    template["APP_DIRS"] = False
    template["DIRS"] = [Path(settings.BASE_DIR) / "templates"]
    template["OPTIONS"]["loaders"] = [
        (
            "django.template.loaders.locmem.Loader",
            {"base.html": "{% block title %}{% endblock %}<main>{% block content %}{% endblock %}</main>"},
        ),
        "django.template.loaders.filesystem.Loader",
        "django.template.loaders.app_directories.Loader",
    ]
    settings.TEMPLATES = [template]


@pytest.fixture
def web_data():
    user = get_user_model().objects.create_user(username="member")
    other = get_user_model().objects.create_user(username="other")
    equipment = Equipment.objects.create(code="E001", name="示波器")
    return user, other, equipment


def future_start():
    # HTML datetime-local inputs have minute precision in these tests.
    return timezone.now().replace(second=0, microsecond=0) + timedelta(days=1)


def form_payload(equipment, start, end, **extra):
    values = {
        "equipment": equipment.pk,
        "start": timezone.localtime(start).strftime("%Y-%m-%dT%H:%M"),
        "end": timezone.localtime(end).strftime("%Y-%m-%dT%H:%M"),
    }
    values.update(extra)
    return values


def seed_reservation(user, equipment, start, end):
    return create_slot(
        actor=user,
        equipment_id=equipment.pk,
        kind=EquipmentSlot.Kind.RESERVATION,
        start=start,
        end=end,
    )


def test_reservation_form_requires_login_and_contains_csrf(client, web_data):
    user, _, equipment = web_data
    url = reverse("booking:create-reservation")
    response = client.get(url)
    assert response.status_code == 302
    assert response.url.startswith("/accounts/login/")

    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200
    assertContains = response.content.decode()
    assert equipment.name in assertContains
    assert "csrfmiddlewaretoken" in assertContains


def test_anonymous_post_cannot_create(client, web_data):
    _, _, equipment = web_data
    start = future_start()
    response = client.post(
        reverse("booking:create-reservation-submit"),
        form_payload(equipment, start, start + timedelta(hours=1)),
    )
    assert response.status_code == 302
    assert response.url.startswith("/accounts/login/")
    assert EquipmentSlot.objects.count() == 0


def test_valid_post_ignores_forged_user_and_redirects_to_owned_detail(client, web_data):
    user, other, equipment = web_data
    client.force_login(user)
    start = future_start()
    response = client.post(
        reverse("booking:create-reservation-submit"),
        form_payload(equipment, start, start + timedelta(hours=1), user_id=other.pk),
    )

    slot = EquipmentSlot.objects.get()
    assert response.status_code == 303
    assert response.url == reverse("booking:reservation-detail", kwargs={"slot_id": slot.pk})
    assert slot.user == user
    assert slot.created_by == user
    assert slot.status == EquipmentSlot.Status.ACTIVE

    detail = client.get(response.url)
    assert detail.status_code == 200
    assert f"#{slot.pk}".encode() in detail.content
    assert equipment.name.encode() in detail.content


@pytest.mark.parametrize("overlap", ["exact", "partial"])
def test_overlapping_post_returns_409_without_partial_writes(client, web_data, overlap):
    user, _, equipment = web_data
    client.force_login(user)
    start = future_start()
    seed_reservation(user, equipment, start, start + timedelta(hours=2))
    requested_start = start if overlap == "exact" else start + timedelta(hours=1)
    requested_end = start + timedelta(hours=2) if overlap == "exact" else start + timedelta(hours=3)

    response = client.post(
        reverse("booking:create-reservation-submit"),
        form_payload(equipment, requested_start, requested_end),
    )
    assert response.status_code == 409
    assert "该设备时段已被占用" in response.content.decode()
    assert EquipmentSlot.objects.count() == 1
    assert OperationLog.objects.filter(action="CREATE_SLOT").count() == 1


def test_adjacent_post_is_allowed(client, web_data):
    user, _, equipment = web_data
    client.force_login(user)
    start = future_start()
    seed_reservation(user, equipment, start, start + timedelta(hours=2))

    response = client.post(
        reverse("booking:create-reservation-submit"),
        form_payload(equipment, start + timedelta(hours=2), start + timedelta(hours=3)),
    )
    assert response.status_code == 303
    assert EquipmentSlot.objects.count() == 2


@pytest.mark.parametrize(
    "payload_change,expected_message",
    [
        ({"missing_start": True}, "必填"),
        ({"end_before_start": True}, "开始时间必须早于结束时间"),
    ],
)
def test_invalid_form_returns_400_without_writes(client, web_data, payload_change, expected_message):
    user, _, equipment = web_data
    client.force_login(user)
    start = future_start()
    end = start - timedelta(hours=1) if payload_change.get("end_before_start") else start + timedelta(hours=1)
    payload = form_payload(equipment, start, end)
    if payload_change.get("missing_start"):
        del payload["start"]

    response = client.post(reverse("booking:create-reservation-submit"), payload)
    assert response.status_code == 400
    assert expected_message in response.content.decode()
    assert EquipmentSlot.objects.count() == 0
    assert OperationLog.objects.filter(action="CREATE_SLOT").count() == 0


def test_disabled_equipment_returns_400_without_writes(client, web_data):
    user, _, equipment = web_data
    equipment.status = Equipment.Status.DISABLED
    equipment.save(update_fields=["status", "updated_at"])
    client.force_login(user)
    start = future_start()

    response = client.post(
        reverse("booking:create-reservation-submit"),
        form_payload(equipment, start, start + timedelta(hours=1)),
    )
    assert response.status_code == 400
    assert "设备已停用" in response.content.decode()
    assert EquipmentSlot.objects.count() == 0
    assert OperationLog.objects.filter(action="CREATE_SLOT").count() == 0


def test_missing_equipment_returns_404(client, web_data):
    user, _, equipment = web_data
    client.force_login(user)
    start = future_start()
    payload = form_payload(equipment, start, start + timedelta(hours=1))
    payload["equipment"] = equipment.pk + 999

    response = client.post(reverse("booking:create-reservation-submit"), payload)
    assert response.status_code == 404
    assert EquipmentSlot.objects.count() == 0


def test_get_cannot_submit_reservation(client, web_data):
    user, _, _ = web_data
    client.force_login(user)
    response = client.get(reverse("booking:create-reservation-submit"))
    assert response.status_code == 405
    assert EquipmentSlot.objects.count() == 0


def test_csrf_is_required_for_creation(web_data):
    user, _, equipment = web_data
    csrf_client = Client(enforce_csrf_checks=True)
    csrf_client.force_login(user)
    start = future_start()

    response = csrf_client.post(
        reverse("booking:create-reservation-submit"),
        form_payload(equipment, start, start + timedelta(hours=1)),
    )
    assert response.status_code == 403
    assert EquipmentSlot.objects.count() == 0


def test_other_user_cannot_read_reservation_detail(client, web_data):
    user, other, equipment = web_data
    start = future_start()
    slot = seed_reservation(user, equipment, start, start + timedelta(hours=1))
    client.force_login(other)

    response = client.get(reverse("booking:reservation-detail", kwargs={"slot_id": slot.pk}))
    assert response.status_code == 403
    assert equipment.name.encode() not in response.content
    assert user.username.encode() not in response.content


def test_missing_and_anonymous_reservation_detail(client, web_data):
    user, _, equipment = web_data
    start = future_start()
    slot = seed_reservation(user, equipment, start, start + timedelta(hours=1))
    url = reverse("booking:reservation-detail", kwargs={"slot_id": slot.pk})

    response = client.get(url)
    assert response.status_code == 302
    assert response.url.startswith("/accounts/login/")

    client.force_login(user)
    response = client.get(reverse("booking:reservation-detail", kwargs={"slot_id": slot.pk + 999}))
    assert response.status_code == 404
