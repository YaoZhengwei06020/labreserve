from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier, Event
from unittest.mock import patch
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, OperationalError, close_old_connections, connection, transaction
from django.utils import timezone
from apps.audit.models import OperationLog
from apps.booking.models import EquipmentSlot
from apps.booking.policy import RuleViolation, SlotConflict
from apps.booking.services import cancel_slot, create_slot, set_equipment_enabled
from apps.equipment.models import Equipment

pytestmark = [pytest.mark.postgres, pytest.mark.django_db(transaction=True)]


@pytest.fixture
def data():
    assert connection.vendor == "postgresql", "Never use SQLite for these tests"
    assert 170000 <= connection.pg_version < 180000, "Acceptance target is PostgreSQL 17"
    user = get_user_model().objects.create_user(username="member")
    other = get_user_model().objects.create_user(username="other")
    admin = get_user_model().objects.create_user(username="admin", is_staff=False)
    admin.groups.add(Group.objects.create(name="ADMIN"))
    equipment = Equipment.objects.create(code="E001", name="设备")
    start = timezone.now() + timedelta(days=1)
    return user, other, admin, equipment, start


def make(data, **changes):
    user, _, _, equipment, start = data
    values = dict(actor=user, equipment_id=equipment.pk, kind="RESERVATION", start=start, end=start + timedelta(hours=1))
    values.update(changes)
    return create_slot(**values)


def test_database_constraint_and_adjacency(data):
    user, _, _, equipment, start = data
    make(data)
    with pytest.raises(IntegrityError) as info:
        with transaction.atomic():
            EquipmentSlot.objects.create(equipment=equipment, kind="RESERVATION", user=user, created_by=user, start_time=start, end_time=start + timedelta(minutes=30))
    assert info.value.__cause__.diag.constraint_name == "slot_no_active_overlap"
    make(data, start=start + timedelta(hours=1), end=start + timedelta(hours=2))
    second = Equipment.objects.create(code="E002", name="另一设备")
    make(data, equipment_id=second.pk)
    assert EquipmentSlot.objects.count() == 3


def test_zero_duration_rejected_by_database(data):
    user, _, _, equipment, start = data
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            EquipmentSlot.objects.create(equipment=equipment, kind="RESERVATION", user=user, created_by=user, start_time=start, end_time=start)


def test_maintenance_conflict_both_directions(data):
    _, _, admin, _, start = data
    slot = make(data)
    with pytest.raises(SlotConflict):
        make(data, actor=admin, kind="MAINTENANCE", reason="检修")
    cancel_slot(actor=admin, slot_id=slot.pk, reason="准备检修")
    make(data, actor=admin, kind="MAINTENANCE", reason="检修")
    with pytest.raises(SlotConflict):
        make(data)


def test_cancellation_audit_and_maintenance_no_restore(data):
    user, other, admin, _, _ = data
    reservation = make(data)
    with pytest.raises(PermissionDenied):
        cancel_slot(actor=other, slot_id=reservation.pk)
    with pytest.raises(RuleViolation):
        cancel_slot(actor=admin, slot_id=reservation.pk)
    cancel_slot(actor=admin, slot_id=reservation.pk, reason="检修")
    maintenance = make(data, actor=admin, kind="MAINTENANCE", reason="检修")
    with pytest.raises(PermissionDenied):
        cancel_slot(actor=user, slot_id=maintenance.pk)
    result = cancel_slot(actor=admin, slot_id=maintenance.pk, reason="撤销检修")
    first_time = result.cancelled_at
    count = OperationLog.objects.count()
    result = cancel_slot(actor=admin, slot_id=maintenance.pk, reason="重复")
    assert result.cancelled_at == first_time
    assert result.cancellation_reason == "撤销检修"
    assert OperationLog.objects.count() == count
    reservation.refresh_from_db()
    assert reservation.status == "CANCELLED"
    make(data)


def test_disable_preserves_slots_and_rejects_all_new_slots(data):
    user, _, admin, equipment, start = data
    slot = make(data)
    set_equipment_enabled(actor=admin, equipment_id=equipment.pk, enabled=False)
    slot.refresh_from_db()
    assert slot.status == "ACTIVE"
    for kind, actor in [("RESERVATION", user), ("MAINTENANCE", admin)]:
        with pytest.raises(RuleViolation):
            make(data, actor=actor, kind=kind, start=start + timedelta(hours=2), end=start + timedelta(hours=3), reason="检修")
    cancel_slot(actor=user, slot_id=slot.pk)
    set_equipment_enabled(actor=admin, equipment_id=equipment.pk, enabled=True)
    slot.refresh_from_db()
    assert slot.status == "CANCELLED"
    make(data)


def test_staff_flag_is_not_business_admin(data):
    user, _, _, equipment, _ = data
    user.is_staff = True
    user.save()
    with pytest.raises(PermissionDenied):
        set_equipment_enabled(actor=user, equipment_id=equipment.pk, enabled=False)


def test_audit_failure_rolls_back_create_and_cancel(data):
    user, _, _, _, _ = data
    with patch.object(OperationLog.objects, "create", side_effect=RuntimeError("audit unavailable")):
        with pytest.raises(RuntimeError):
            make(data)
    assert EquipmentSlot.objects.count() == 0
    slot = make(data)
    with patch.object(OperationLog.objects, "create", side_effect=RuntimeError("audit unavailable")):
        with pytest.raises(RuntimeError):
            cancel_slot(actor=user, slot_id=slot.pk)
    slot.refresh_from_db()
    assert slot.status == "ACTIVE"
    assert slot.cancelled_at is None


def race(data, kinds, *, direct=False):
    user, _, admin, equipment, start = data
    barrier = Barrier(len(kinds))

    def worker(kind):
        close_old_connections()
        try:
            actor = get_user_model().objects.get(pk=admin.pk if kind == "MAINTENANCE" else user.pk)
            with connection.cursor() as cursor:
                cursor.execute("SET statement_timeout = '30s'")
                cursor.execute("SELECT pg_backend_pid()")
                pid = cursor.fetchone()[0]
            barrier.wait(timeout=30)
            try:
                if direct:
                    with transaction.atomic():
                        EquipmentSlot.objects.create(equipment_id=equipment.pk, kind=kind, user=actor if kind == "RESERVATION" else None, created_by=actor, start_time=start, end_time=start + timedelta(hours=1))
                else:
                    create_slot(actor=actor, equipment_id=equipment.pk, kind=kind, start=start, end=start + timedelta(hours=1), reason="技术验证")
                return pid, "success"
            except SlotConflict:
                return pid, "conflict"
            except IntegrityError as exc:
                if direct and exc.__cause__.diag.constraint_name == "slot_no_active_overlap":
                    return pid, "conflict"
                raise
            except OperationalError as exc:
                # Two unsupported raw inserts can deadlock while PostgreSQL
                # checks the GiST exclusion constraint. This is an aborted
                # transaction, not a domain conflict or a successful write.
                # Service callers still MUST use the shared Equipment lock.
                if direct and getattr(exc.__cause__, "sqlstate", None) == "40P01":
                    return pid, "deadlock_aborted"
                raise
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=len(kinds)) as executor:
        results = list(executor.map(worker, kinds))
    assert len({pid for pid, _ in results}) == len(kinds), "Connections must be independent"
    assert [outcome for _, outcome in results].count("success") == 1
    outcomes = [outcome for _, outcome in results]
    if direct:
        assert sum(outcome in {"conflict", "deadlock_aborted"} for outcome in outcomes) == len(kinds) - 1
    else:
        assert outcomes.count("conflict") == len(kinds) - 1
    assert EquipmentSlot.objects.filter(equipment=equipment, status="ACTIVE", start_time=start).count() == 1
    return outcomes


def test_nfr01_20_connections_20_rounds(data, record_property):
    for round_index in range(20):
        # Each round starts with an actually empty target range.
        EquipmentSlot.objects.all().delete()
        race(data, ["RESERVATION"] * 20)
        record_property(f"round_{round_index + 1:02}", "20 distinct backend PIDs; 1 success; 19 conflicts; 1 ACTIVE slot")


def test_booking_maintenance_race(data):
    race(data, ["RESERVATION", "MAINTENANCE"] * 10)


def test_direct_database_race(data, record_property):
    outcomes = race(data, ["RESERVATION", "MAINTENANCE"], direct=True)
    record_property("raw_database_outcomes", ",".join(sorted(outcomes)))


@pytest.mark.parametrize("disable_first", [True, False])
def test_disable_create_serialization(data, disable_first):
    user, _, admin, equipment, start = data
    locked = Event()
    attempting = Event()

    def first():
        close_old_connections()
        try:
            with transaction.atomic():
                Equipment.objects.select_for_update().get(pk=equipment.pk)
                if disable_first:
                    set_equipment_enabled(actor=admin, equipment_id=equipment.pk, enabled=False)
                else:
                    make(data)
                locked.set()
                assert attempting.wait(20)
        finally:
            connection.close()

    def second():
        close_old_connections()
        try:
            assert locked.wait(20)
            attempting.set()
            if disable_first:
                with pytest.raises(RuleViolation, match="停用"):
                    make(data)
            else:
                set_equipment_enabled(actor=admin, equipment_id=equipment.pk, enabled=False)
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(first), executor.submit(second)]
        for future in futures:
            future.result(timeout=40)
    equipment.refresh_from_db()
    assert equipment.status == "DISABLED"
    assert EquipmentSlot.objects.count() == (0 if disable_first else 1)
