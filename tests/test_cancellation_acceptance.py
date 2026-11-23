from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.http import HttpResponse
from django.urls import include, path, reverse
from django.utils import timezone

from apps.audit.models import OperationLog
from apps.booking.models import EquipmentSlot
from apps.booking.policy import RuleViolation
from apps.booking.services import cancel_slot, create_slot, set_equipment_enabled
from apps.booking.views.cancellation import cancel_reservation
from apps.equipment.models import Equipment


def reservation_detail(request, slot_id):
    return HttpResponse("reservation detail")


booking_patterns = (
    [
        path("reservations/<int:slot_id>/cancel/", cancel_reservation, name="cancel-reservation"),
        path("reservations/<int:slot_id>/", reservation_detail, name="reservation-detail"),
    ],
    "booking",
)
urlpatterns = [path("", include(booking_patterns, namespace="booking"))]

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def cancellation_test_configuration(settings):
    settings.ROOT_URLCONF = __name__
    settings.TEMPLATES = [{
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": False,
        "OPTIONS": {
            "loaders": [
                ("django.template.loaders.locmem.Loader", {
                    "base.html": "{% block content %}{% endblock %}",
                }),
                ("django.template.loaders.filesystem.Loader", [settings.BASE_DIR / "templates"]),
            ],
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }]


@pytest.fixture
def owner():
    return get_user_model().objects.create_user(username="owner", password="test-only-password")


@pytest.fixture
def other():
    return get_user_model().objects.create_user(username="other", password="test-only-password")


@pytest.fixture
def admin():
    user = get_user_model().objects.create_user(username="admin", password="test-only-password")
    user.groups.add(Group.objects.create(name="ADMIN"))
    return user


@pytest.fixture
def equipment():
    return Equipment.objects.create(code="E001", name="设备")


@pytest.fixture
def start():
    return timezone.now() + timedelta(days=1)


@pytest.fixture
def reservation(owner, equipment, start):
    return create_slot(
        actor=owner,
        equipment_id=equipment.pk,
        kind=EquipmentSlot.Kind.RESERVATION,
        start=start,
        end=start + timedelta(hours=1),
        reason="原始预约备注",
    )


def cancel_url(slot_id):
    return reverse("booking:cancel-reservation", kwargs={"slot_id": slot_id})


def cancellation_logs(slot_id):
    return OperationLog.objects.filter(action="CANCEL_SLOT", target_type="EquipmentSlot", target_id=slot_id)


def test_cancel_own_reservation(client, owner, reservation):
    client.force_login(owner)

    response = client.post(cancel_url(reservation.pk))

    assert response.status_code == 303
    reservation.refresh_from_db()
    assert EquipmentSlot.objects.filter(pk=reservation.pk).exists()
    assert reservation.status == EquipmentSlot.Status.CANCELLED
    assert reservation.cancelled_by == owner
    assert reservation.cancelled_at is not None
    assert reservation.reason == "原始预约备注"
    assert reservation.cancellation_reason == ""
    log = cancellation_logs(reservation.pk).get()
    assert log.actor == owner
    assert log.target_id == reservation.pk
    assert log.reason == ""


def test_rebook_after_cancel(client, owner, other, equipment, reservation, start):
    client.force_login(owner)
    response = client.post(cancel_url(reservation.pk))
    assert response.status_code == 303

    replacement = create_slot(
        actor=other,
        equipment_id=equipment.pk,
        kind=EquipmentSlot.Kind.RESERVATION,
        start=start,
        end=start + timedelta(hours=1),
    )

    assert replacement.status == EquipmentSlot.Status.ACTIVE
    assert replacement.user == other
    reservation.refresh_from_db()
    assert reservation.status == EquipmentSlot.Status.CANCELLED


def test_rebook_failure_after_cancel_distinguishes_disabled_equipment(client, owner, other, admin, equipment, reservation, start):
    client.force_login(owner)
    client.post(cancel_url(reservation.pk))
    set_equipment_enabled(actor=admin, equipment_id=equipment.pk, enabled=False)

    with pytest.raises(RuleViolation, match="设备已停用"):
        create_slot(
            actor=other,
            equipment_id=equipment.pk,
            kind=EquipmentSlot.Kind.RESERVATION,
            start=start,
            end=start + timedelta(hours=1),
        )


def test_cancel_other_user_forbidden(client, other, reservation):
    client.force_login(other)

    response = client.post(cancel_url(reservation.pk))

    assert response.status_code == 403
    reservation.refresh_from_db()
    assert reservation.status == EquipmentSlot.Status.ACTIVE
    assert reservation.cancelled_by is None
    assert reservation.cancelled_at is None
    assert reservation.cancellation_reason == ""
    assert not cancellation_logs(reservation.pk).exists()


def test_cancel_started_reservation(client, owner, equipment):
    started_at = timezone.now() - timedelta(minutes=1)
    reservation = EquipmentSlot.objects.create(
        equipment=equipment,
        kind=EquipmentSlot.Kind.RESERVATION,
        user=owner,
        created_by=owner,
        start_time=started_at,
        end_time=started_at + timedelta(hours=1),
        reason="原始预约备注",
    )
    client.force_login(owner)

    response = client.post(cancel_url(reservation.pk))

    assert response.status_code == 400
    reservation.refresh_from_db()
    assert reservation.status == EquipmentSlot.Status.ACTIVE
    assert reservation.cancelled_by is None
    assert reservation.cancelled_at is None
    assert reservation.reason == "原始预约备注"
    assert not cancellation_logs(reservation.pk).exists()


def test_cancel_idempotent_state(client, owner, reservation):
    cancel_slot(actor=owner, slot_id=reservation.pk, reason="首次取消原因")
    reservation.refresh_from_db()
    first_cancelled_at = reservation.cancelled_at
    first_log = cancellation_logs(reservation.pk).get()
    client.force_login(owner)

    response = client.post(cancel_url(reservation.pk), {"reason": "试图覆盖首次原因"})

    assert response.status_code == 303
    reservation.refresh_from_db()
    assert reservation.status == EquipmentSlot.Status.CANCELLED
    assert reservation.cancelled_at == first_cancelled_at
    assert reservation.cancelled_by == owner
    assert reservation.cancellation_reason == "首次取消原因"
    assert reservation.reason == "原始预约备注"
    assert cancellation_logs(reservation.pk).count() == 1
    assert OperationLog.objects.get(pk=first_log.pk).reason == "首次取消原因"


def test_repeat_request_cannot_bypass_owner_or_maintenance_authorization(client, owner, other, admin, equipment, reservation, start):
    cancel_slot(actor=owner, slot_id=reservation.pk, reason="首次取消")
    client.force_login(other)

    response = client.post(cancel_url(reservation.pk))

    assert response.status_code == 403
    reservation.refresh_from_db()
    assert reservation.cancellation_reason == "首次取消"
    assert cancellation_logs(reservation.pk).count() == 1

    maintenance = create_slot(
        actor=admin,
        equipment_id=equipment.pk,
        kind=EquipmentSlot.Kind.MAINTENANCE,
        start=start + timedelta(hours=2),
        end=start + timedelta(hours=3),
        reason="设备检修",
    )
    cancel_slot(actor=admin, slot_id=maintenance.pk, reason="检修撤销")
    response = client.post(cancel_url(maintenance.pk))

    assert response.status_code == 403
    maintenance.refresh_from_db()
    assert maintenance.cancellation_reason == "检修撤销"
    assert maintenance.cancelled_by == admin
    assert cancellation_logs(maintenance.pk).count() == 1


def test_audit_failure_rolls_back_http_cancellation(client, owner, reservation):
    client.force_login(owner)

    with patch.object(OperationLog.objects, "create", side_effect=RuntimeError("audit unavailable")):
        with pytest.raises(RuntimeError, match="audit unavailable"):
            client.post(cancel_url(reservation.pk))

    reservation.refresh_from_db()
    assert reservation.status == EquipmentSlot.Status.ACTIVE
    assert reservation.cancelled_by is None
    assert reservation.cancelled_at is None
    assert reservation.cancellation_reason == ""
    assert not cancellation_logs(reservation.pk).exists()
