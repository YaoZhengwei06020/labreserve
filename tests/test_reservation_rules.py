from datetime import datetime, timedelta, timezone as dt_timezone
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from apps.audit.models import OperationLog
from apps.booking.models import EquipmentSlot
from apps.booking.policy import (
    RuleViolation,
    SlotConflict,
    validate_reservation_interval,
)
from apps.booking.services import create_slot
from apps.equipment.models import Equipment


NOW = datetime(2030, 1, 1, 9, 0, tzinfo=dt_timezone.utc)


@pytest.mark.parametrize(
    "start,end",
    [
        (NOW + timedelta(hours=1), NOW + timedelta(hours=1)),
        (NOW + timedelta(hours=2), NOW + timedelta(hours=1)),
        (NOW, NOW + timedelta(hours=1)),
        (NOW - timedelta(minutes=1), NOW + timedelta(hours=1)),
        (NOW.replace(tzinfo=None) + timedelta(hours=1), NOW + timedelta(hours=2)),
        (NOW + timedelta(hours=1), (NOW + timedelta(hours=2)).replace(tzinfo=None)),
        (None, NOW + timedelta(hours=1)),
    ],
)
def test_reservation_rejects_invalid_time_ranges(start, end):
    with pytest.raises(RuleViolation):
        validate_reservation_interval(start, end, NOW)


@pytest.mark.parametrize(
    "minutes,valid",
    [(29, False), (30, True), (240, True), (241, False)],
)
def test_reservation_duration_boundaries(minutes, valid):
    start = NOW + timedelta(hours=1)
    end = start + timedelta(minutes=minutes)
    if valid:
        validate_reservation_interval(start, end, NOW)
    else:
        with pytest.raises(RuleViolation, match="预约时长"):
            validate_reservation_interval(start, end, NOW)


def test_reservation_advance_boundaries():
    validate_reservation_interval(
        NOW + timedelta(days=7),
        NOW + timedelta(days=7, minutes=30),
        NOW,
    )
    with pytest.raises(RuleViolation, match="最多只能提前 7 天"):
        validate_reservation_interval(
            NOW + timedelta(days=7, seconds=1),
            NOW + timedelta(days=7, minutes=30, seconds=1),
            NOW,
        )


@pytest.fixture
def booking_data(db):
    user = get_user_model().objects.create_user(username="member")
    admin = get_user_model().objects.create_user(username="admin")
    admin.groups.add(Group.objects.create(name="ADMIN"))
    equipment = Equipment.objects.create(code="E001", name="示波器")
    return user, admin, equipment


def make_reservation(user, equipment, **changes):
    values = {
        "actor": user,
        "equipment_id": equipment.pk,
        "kind": EquipmentSlot.Kind.RESERVATION,
        "start": NOW + timedelta(hours=1),
        "end": NOW + timedelta(hours=2),
    }
    values.update(changes)
    with patch("apps.booking.services.timezone.now", return_value=NOW):
        return create_slot(**values)


def test_create_reservation_persists_current_actor_and_audit(booking_data):
    user, _, equipment = booking_data
    slot = make_reservation(user, equipment)

    assert slot.pk is not None
    assert slot.user == user
    assert slot.created_by == user
    assert slot.kind == EquipmentSlot.Kind.RESERVATION
    assert slot.status == EquipmentSlot.Status.ACTIVE
    assert EquipmentSlot.objects.get(pk=slot.pk).status == EquipmentSlot.Status.ACTIVE
    assert OperationLog.objects.filter(
        action="CREATE_SLOT", target_type="EquipmentSlot", target_id=slot.pk, actor=user
    ).exists()


def test_service_enforces_minimum_duration_without_partial_writes(booking_data):
    user, _, equipment = booking_data
    with pytest.raises(RuleViolation, match="不能少于 30 分钟"):
        make_reservation(
            user,
            equipment,
            end=NOW + timedelta(hours=1, minutes=29),
        )
    assert EquipmentSlot.objects.count() == 0
    assert OperationLog.objects.filter(action="CREATE_SLOT").count() == 0

    slot = make_reservation(
        user,
        equipment,
        end=NOW + timedelta(hours=1, minutes=30),
    )
    assert slot.status == EquipmentSlot.Status.ACTIVE


def test_maintenance_does_not_inherit_reservation_limits(booking_data):
    _, admin, equipment = booking_data
    with patch("apps.booking.services.timezone.now", return_value=NOW):
        slot = create_slot(
            actor=admin,
            equipment_id=equipment.pk,
            kind=EquipmentSlot.Kind.MAINTENANCE,
            start=NOW + timedelta(days=30),
            end=NOW + timedelta(days=30, minutes=10),
            reason="短时检修",
        )
    assert slot.kind == EquipmentSlot.Kind.MAINTENANCE
    assert slot.status == EquipmentSlot.Status.ACTIVE


def test_disabled_equipment_rejects_reservation_without_writes(booking_data):
    user, _, equipment = booking_data
    equipment.status = Equipment.Status.DISABLED
    equipment.save(update_fields=["status", "updated_at"])

    with pytest.raises(RuleViolation, match="设备已停用"):
        make_reservation(user, equipment)
    assert EquipmentSlot.objects.count() == 0
    assert OperationLog.objects.filter(action="CREATE_SLOT").count() == 0


def test_missing_equipment_rejects_reservation_without_writes(booking_data):
    user, _, equipment = booking_data
    with pytest.raises(Equipment.DoesNotExist):
        make_reservation(user, equipment, equipment_id=equipment.pk + 999)
    assert EquipmentSlot.objects.count() == 0
    assert OperationLog.objects.filter(action="CREATE_SLOT").count() == 0


def test_reservation_overlapping_maintenance_is_conflict_without_writes(booking_data):
    user, admin, equipment = booking_data
    with patch("apps.booking.services.timezone.now", return_value=NOW):
        maintenance = create_slot(
            actor=admin,
            equipment_id=equipment.pk,
            kind=EquipmentSlot.Kind.MAINTENANCE,
            start=NOW + timedelta(hours=1),
            end=NOW + timedelta(hours=3),
            reason="计划检修",
        )
    with pytest.raises(SlotConflict, match="该设备时段已被占用"):
        make_reservation(
            user,
            equipment,
            start=NOW + timedelta(hours=2),
            end=NOW + timedelta(hours=4),
        )

    assert EquipmentSlot.objects.get() == maintenance
    assert OperationLog.objects.filter(action="CREATE_SLOT").count() == 1
