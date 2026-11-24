"""Independent HTTP integration checks for US-09 and cancellation consistency."""

from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, connection
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.audit.models import OperationLog
from apps.booking.models import EquipmentSlot
from apps.booking.services import cancel_slot, create_slot
from apps.equipment.models import Equipment


pytestmark = [pytest.mark.postgres, pytest.mark.django_db(transaction=True)]


@pytest.fixture
def http_data(client):
    assert connection.vendor == "postgresql", "HTTP acceptance must use PostgreSQL"
    assert 170000 <= connection.pg_version < 180000, "HTTP acceptance requires PostgreSQL 17"
    user_model = get_user_model()
    member = user_model.objects.create_user(username="us09-http-member", password="test-only-password")
    other = user_model.objects.create_user(username="us09-http-other", password="test-only-password")
    equipment = Equipment.objects.create(code="US09-HTTP-E01", name="HTTP 独立验证设备")
    start = (timezone.now() + timedelta(days=1)).replace(second=0, microsecond=0)
    client.force_login(member)
    return SimpleNamespace(
        client=client,
        member=member,
        other=other,
        equipment=equipment,
        start=start,
    )


def form_time(value):
    return timezone.localtime(value).strftime("%Y-%m-%dT%H:%M")


def reservation_payload(data, **changes):
    values = {
        "equipment": str(data.equipment.pk),
        "start": form_time(data.start),
        "end": form_time(data.start + timedelta(hours=2)),
    }
    values.update(changes)
    return values


def create_reservation(data, **changes):
    values = {
        "actor": data.member,
        "equipment_id": data.equipment.pk,
        "kind": EquipmentSlot.Kind.RESERVATION,
        "start": data.start,
        "end": data.start + timedelta(hours=2),
    }
    values.update(changes)
    return create_slot(**values)


@pytest.mark.parametrize(
    "start_offset,end_offset",
    [
        (timedelta(hours=0), timedelta(hours=2)),
        (timedelta(hours=1), timedelta(hours=3)),
        (timedelta(hours=-1), timedelta(hours=1)),
    ],
    ids=["exact", "partial-right", "partial-left"],
)
def test_http_overlap_returns_409_without_success_writes(http_data, start_offset, end_offset):
    create_reservation(http_data)
    response = http_data.client.post(
        reverse("booking:create-reservation-submit"),
        reservation_payload(
            http_data,
            start=form_time(http_data.start + start_offset),
            end=form_time(http_data.start + end_offset),
        ),
    )

    assert response.status_code == 409
    assert "占用" in response.content.decode()
    assert EquipmentSlot.objects.count() == 1
    assert OperationLog.objects.filter(action="CREATE_SLOT").count() == 1


def test_http_adjacent_reservation_returns_303_and_persists(http_data):
    create_reservation(http_data)
    response = http_data.client.post(
        reverse("booking:create-reservation-submit"),
        reservation_payload(
            http_data,
            start=form_time(http_data.start + timedelta(hours=2)),
            end=form_time(http_data.start + timedelta(hours=3)),
        ),
    )

    assert response.status_code == 303
    slot = EquipmentSlot.objects.exclude(start_time=http_data.start).get()
    assert response["Location"] == reverse("booking:reservation-detail", kwargs={"slot_id": slot.pk})
    assert slot.user_id == http_data.member.pk
    assert slot.status == EquipmentSlot.Status.ACTIVE
    assert EquipmentSlot.objects.count() == 2


def test_http_forged_user_id_cannot_change_reservation_owner(http_data):
    response = http_data.client.post(
        reverse("booking:create-reservation-submit"),
        reservation_payload(http_data, user_id=str(http_data.other.pk)),
    )

    assert response.status_code == 303
    slot = EquipmentSlot.objects.get()
    assert slot.user_id == http_data.member.pk
    assert slot.created_by_id == http_data.member.pk


def test_anonymous_create_is_redirected_without_writes(http_data):
    anonymous = Client()
    response = anonymous.post(
        reverse("booking:create-reservation-submit"), reservation_payload(http_data)
    )

    assert response.status_code == 302
    assert "login" in response["Location"]
    assert EquipmentSlot.objects.count() == 0
    assert OperationLog.objects.count() == 0


def test_create_submit_rejects_get_and_requires_csrf(http_data):
    submit_url = reverse("booking:create-reservation-submit")
    get_response = http_data.client.get(submit_url)
    csrf_client = Client(enforce_csrf_checks=True)
    csrf_client.force_login(http_data.member)
    csrf_response = csrf_client.post(submit_url, reservation_payload(http_data))

    assert get_response.status_code == 405
    assert csrf_response.status_code == 403
    assert EquipmentSlot.objects.count() == 0


def test_disabled_equipment_http_failure_leaves_no_slot_or_audit(http_data):
    http_data.equipment.status = Equipment.Status.DISABLED
    http_data.equipment.save(update_fields=["status", "updated_at"])
    response = http_data.client.post(
        reverse("booking:create-reservation-submit"), reservation_payload(http_data)
    )

    assert response.status_code == 400
    assert "停用" in response.content.decode()
    assert EquipmentSlot.objects.count() == 0
    assert OperationLog.objects.filter(action="CREATE_SLOT").count() == 0


def test_http_does_not_relabel_unexpected_database_error_as_409(http_data):
    with patch(
        "apps.booking.views.reservation.create_slot",
        side_effect=IntegrityError("unexpected independent failure"),
    ):
        with pytest.raises(IntegrityError, match="unexpected independent failure"):
            http_data.client.post(
                reverse("booking:create-reservation-submit"), reservation_payload(http_data)
            )
    assert EquipmentSlot.objects.count() == 0
    assert OperationLog.objects.filter(action="CREATE_SLOT").count() == 0


def test_http_cancel_rebooking_and_repeat_cancel_regressions(http_data):
    slot = create_reservation(http_data)
    cancel_url = reverse("booking:cancel-reservation", kwargs={"slot_id": slot.pk})

    first = http_data.client.post(cancel_url)
    assert first.status_code == 303
    slot.refresh_from_db()
    first_cancelled_at = slot.cancelled_at
    first_cancelled_by_id = slot.cancelled_by_id
    first_reason = slot.cancellation_reason
    assert slot.status == EquipmentSlot.Status.CANCELLED

    second = http_data.client.post(cancel_url, {"reason": "重复请求不得覆盖首次审计"})
    assert second.status_code == 303
    slot.refresh_from_db()
    assert slot.cancelled_at == first_cancelled_at
    assert slot.cancelled_by_id == first_cancelled_by_id
    assert slot.cancellation_reason == first_reason
    assert OperationLog.objects.filter(action="CANCEL_SLOT", target_id=slot.pk).count() == 1

    replacement = http_data.client.post(
        reverse("booking:create-reservation-submit"), reservation_payload(http_data)
    )
    assert replacement.status_code == 303
    assert EquipmentSlot.objects.filter(
        equipment=http_data.equipment,
        start_time=http_data.start,
        status=EquipmentSlot.Status.ACTIVE,
    ).count() == 1


def test_http_forbidden_and_started_cancel_leave_record_unchanged(http_data):
    other_slot = create_reservation(http_data)
    http_data.client.force_login(http_data.other)
    forbidden = http_data.client.post(
        reverse("booking:cancel-reservation", kwargs={"slot_id": other_slot.pk})
    )
    assert forbidden.status_code == 403
    other_slot.refresh_from_db()
    assert other_slot.status == EquipmentSlot.Status.ACTIVE
    assert other_slot.cancelled_at is None

    http_data.client.force_login(http_data.member)
    started_slot = create_reservation(
        http_data,
        start=http_data.start + timedelta(hours=3),
        end=http_data.start + timedelta(hours=4),
    )
    EquipmentSlot.objects.filter(pk=started_slot.pk).update(
        start_time=timezone.now() - timedelta(minutes=30),
        end_time=timezone.now() + timedelta(minutes=30),
    )
    started = http_data.client.post(
        reverse("booking:cancel-reservation", kwargs={"slot_id": started_slot.pk})
    )
    assert started.status_code == 400
    started_slot.refresh_from_db()
    assert started_slot.status == EquipmentSlot.Status.ACTIVE
    assert started_slot.cancelled_at is None
    assert OperationLog.objects.filter(action="CANCEL_SLOT").count() == 0


def test_http_cancel_audit_failure_rolls_back_state(http_data):
    slot = create_reservation(http_data)
    with patch.object(OperationLog.objects, "create", side_effect=RuntimeError("cancel audit unavailable")):
        with pytest.raises(RuntimeError, match="cancel audit unavailable"):
            http_data.client.post(reverse("booking:cancel-reservation", kwargs={"slot_id": slot.pk}))

    slot.refresh_from_db()
    assert slot.status == EquipmentSlot.Status.ACTIVE
    assert slot.cancelled_at is None
    assert OperationLog.objects.filter(action="CANCEL_SLOT", target_id=slot.pk).count() == 0
