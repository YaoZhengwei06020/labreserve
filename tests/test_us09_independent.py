"""Independent US-09 service, database, concurrency, and cancellation checks.

These tests intentionally require real PostgreSQL 17. They do not reuse the
implementation agent's race helper or treat SQLite/mock results as evidence.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import json
from threading import Barrier, Event
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.db import (
    IntegrityError,
    OperationalError,
    close_old_connections,
    connection,
    transaction,
)
from django.utils import timezone

from apps.audit.models import OperationLog
from apps.booking.models import EquipmentSlot
from apps.booking.policy import RuleViolation, SlotConflict
from apps.booking.services import cancel_slot, create_slot, set_equipment_enabled
from apps.equipment.models import Equipment


pytestmark = [pytest.mark.postgres, pytest.mark.django_db(transaction=True)]


@pytest.fixture
def us09_data():
    assert connection.vendor == "postgresql", "US-09 evidence requires PostgreSQL"
    assert 170000 <= connection.pg_version < 180000, "US-09 requires PostgreSQL 17"
    user_model = get_user_model()
    member = user_model.objects.create_user(username="us09-member")
    other = user_model.objects.create_user(username="us09-other")
    admin = user_model.objects.create_user(username="us09-admin", is_staff=False)
    admin.groups.add(Group.objects.create(name="ADMIN"))
    equipment = Equipment.objects.create(code="US09-E01", name="独立验证设备一")
    other_equipment = Equipment.objects.create(code="US09-E02", name="独立验证设备二")
    start = (timezone.now() + timedelta(days=1)).replace(microsecond=0)
    return SimpleNamespace(
        member=member,
        other=other,
        admin=admin,
        equipment=equipment,
        other_equipment=other_equipment,
        start=start,
    )


def make_slot(data, **changes):
    values = {
        "actor": data.member,
        "equipment_id": data.equipment.pk,
        "kind": EquipmentSlot.Kind.RESERVATION,
        "start": data.start,
        "end": data.start + timedelta(hours=2),
    }
    values.update(changes)
    return create_slot(**values)


def assert_no_extra_success_writes(slot_count, audit_count):
    assert EquipmentSlot.objects.count() == slot_count
    assert OperationLog.objects.filter(
        action="CREATE_SLOT", target_type="EquipmentSlot"
    ).count() == audit_count


@pytest.mark.parametrize(
    "candidate_start,candidate_end",
    [
        (timedelta(hours=0), timedelta(hours=2)),
        (timedelta(hours=1), timedelta(hours=3)),
        (timedelta(hours=-1), timedelta(hours=1)),
        (timedelta(hours=-1), timedelta(hours=3)),
        (timedelta(minutes=30), timedelta(hours=1)),
    ],
    ids=["exact", "extends-right", "extends-left", "covers-existing", "inside-existing"],
)
def test_overlap_variants_rejected_without_partial_writes(
    us09_data, candidate_start, candidate_end
):
    make_slot(us09_data)
    with pytest.raises(SlotConflict, match="占用"):
        make_slot(
            us09_data,
            actor=us09_data.other,
            start=us09_data.start + candidate_start,
            end=us09_data.start + candidate_end,
        )
    assert_no_extra_success_writes(slot_count=1, audit_count=1)


def test_half_open_adjacency_and_different_equipment_are_allowed(us09_data):
    make_slot(us09_data)
    make_slot(
        us09_data,
        actor=us09_data.other,
        start=us09_data.start + timedelta(hours=2),
        end=us09_data.start + timedelta(hours=3),
    )
    make_slot(
        us09_data,
        actor=us09_data.other,
        start=us09_data.start - timedelta(hours=1),
        end=us09_data.start,
    )
    make_slot(us09_data, actor=us09_data.other, equipment_id=us09_data.other_equipment.pk)
    assert EquipmentSlot.objects.filter(status="ACTIVE").count() == 4


def test_cancelled_reservation_releases_interval_for_rebooking(us09_data):
    original = make_slot(us09_data)
    cancel_slot(actor=us09_data.member, slot_id=original.pk, reason="首次取消")
    replacement = make_slot(us09_data, actor=us09_data.other)

    original.refresh_from_db()
    assert original.status == EquipmentSlot.Status.CANCELLED
    assert replacement.status == EquipmentSlot.Status.ACTIVE
    assert EquipmentSlot.objects.filter(
        equipment=us09_data.equipment,
        start_time=us09_data.start,
        status=EquipmentSlot.Status.ACTIVE,
    ).count() == 1


@pytest.mark.parametrize("existing_kind", ["RESERVATION", "MAINTENANCE"])
def test_reservation_and_maintenance_share_exclusion(us09_data, existing_kind):
    existing_actor = us09_data.admin if existing_kind == "MAINTENANCE" else us09_data.member
    make_slot(us09_data, actor=existing_actor, kind=existing_kind, reason="计划检修")

    competing_kind = "MAINTENANCE" if existing_kind == "RESERVATION" else "RESERVATION"
    competing_actor = us09_data.admin if competing_kind == "MAINTENANCE" else us09_data.other
    with pytest.raises(SlotConflict):
        make_slot(
            us09_data,
            actor=competing_actor,
            kind=competing_kind,
            start=us09_data.start + timedelta(hours=1),
            end=us09_data.start + timedelta(hours=3),
            reason="竞争检修",
        )
    assert_no_extra_success_writes(slot_count=1, audit_count=1)


def test_repeat_cancel_is_idempotent_and_preserves_first_audit(us09_data):
    slot = make_slot(us09_data)
    first = cancel_slot(actor=us09_data.member, slot_id=slot.pk, reason="首次取消")
    first_audit = OperationLog.objects.get(action="CANCEL_SLOT", target_id=slot.pk)

    second = cancel_slot(actor=us09_data.member, slot_id=slot.pk, reason="重复取消")
    assert second.status == EquipmentSlot.Status.CANCELLED
    assert second.cancelled_at == first.cancelled_at
    assert second.cancelled_by_id == first.cancelled_by_id
    assert second.cancellation_reason == "首次取消"
    assert OperationLog.objects.filter(action="CANCEL_SLOT", target_id=slot.pk).count() == 1
    assert OperationLog.objects.get(pk=first_audit.pk).created_at == first_audit.created_at


def test_unauthorized_and_started_cancel_leave_record_unchanged(us09_data):
    other_slot = make_slot(us09_data)
    with pytest.raises(PermissionDenied):
        cancel_slot(actor=us09_data.other, slot_id=other_slot.pk)
    other_slot.refresh_from_db()
    assert other_slot.status == EquipmentSlot.Status.ACTIVE
    assert other_slot.cancelled_at is None
    assert OperationLog.objects.filter(action="CANCEL_SLOT").count() == 0

    started_slot = make_slot(
        us09_data,
        start=us09_data.start + timedelta(hours=3),
        end=us09_data.start + timedelta(hours=4),
    )
    EquipmentSlot.objects.filter(pk=started_slot.pk).update(
        start_time=timezone.now() - timedelta(minutes=30),
        end_time=timezone.now() + timedelta(minutes=30),
    )
    started_slot.refresh_from_db()
    before = (
        started_slot.status,
        started_slot.cancelled_by_id,
        started_slot.cancelled_at,
        started_slot.cancellation_reason,
    )
    with pytest.raises(RuleViolation, match="开始后"):
        cancel_slot(actor=us09_data.member, slot_id=started_slot.pk)
    started_slot.refresh_from_db()
    assert before == (
        started_slot.status,
        started_slot.cancelled_by_id,
        started_slot.cancelled_at,
        started_slot.cancellation_reason,
    )
    assert OperationLog.objects.filter(action="CANCEL_SLOT").count() == 0


def test_audit_failure_rolls_back_create_and_cancel(us09_data):
    with patch.object(OperationLog.objects, "create", side_effect=RuntimeError("audit unavailable")):
        with pytest.raises(RuntimeError, match="audit unavailable"):
            make_slot(us09_data)
    assert_no_extra_success_writes(slot_count=0, audit_count=0)

    slot = make_slot(us09_data)
    with patch.object(OperationLog.objects, "create", side_effect=RuntimeError("audit unavailable")):
        with pytest.raises(RuntimeError, match="audit unavailable"):
            cancel_slot(actor=us09_data.member, slot_id=slot.pk)
    slot.refresh_from_db()
    assert slot.status == EquipmentSlot.Status.ACTIVE
    assert slot.cancelled_at is None
    assert OperationLog.objects.filter(action="CANCEL_SLOT", target_id=slot.pk).count() == 0


def test_non_exclusion_integrity_error_is_not_relabelled_as_conflict(us09_data):
    with patch.object(OperationLog.objects, "create", side_effect=IntegrityError("unrelated DB failure")):
        with pytest.raises(IntegrityError, match="unrelated DB failure"):
            make_slot(us09_data)
    assert_no_extra_success_writes(slot_count=0, audit_count=0)


def test_direct_illegal_overlap_is_stopped_by_database(us09_data):
    make_slot(us09_data)
    with pytest.raises(IntegrityError) as caught:
        with transaction.atomic():
            EquipmentSlot.objects.create(
                equipment=us09_data.equipment,
                kind=EquipmentSlot.Kind.RESERVATION,
                user=us09_data.other,
                created_by=us09_data.other,
                start_time=us09_data.start + timedelta(minutes=30),
                end_time=us09_data.start + timedelta(hours=1),
            )
    diag = getattr(caught.value.__cause__, "diag", None)
    assert getattr(diag, "constraint_name", None) == "slot_no_active_overlap"
    assert getattr(caught.value.__cause__, "sqlstate", None) == "23P01"
    assert_no_extra_success_writes(slot_count=1, audit_count=1)


def run_race(data, equipment, kinds, *, direct=False):
    """Run each request on its own thread-local Django database connection."""
    barrier = Barrier(len(kinds))

    def worker(kind):
        close_old_connections()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SET statement_timeout = '30s'")
                cursor.execute("SELECT pg_backend_pid()")
                pid = cursor.fetchone()[0]
            actor_id = data.admin.pk if kind == "MAINTENANCE" else data.member.pk
            actor = get_user_model().objects.get(pk=actor_id)
            barrier.wait(timeout=30)
            try:
                if direct:
                    with transaction.atomic():
                        EquipmentSlot.objects.create(
                            equipment_id=equipment.pk,
                            kind=kind,
                            user=actor if kind == "RESERVATION" else None,
                            created_by=actor,
                            start_time=data.start,
                            end_time=data.start + timedelta(hours=1),
                            reason="直接数据库竞争",
                        )
                else:
                    create_slot(
                        actor=actor,
                        equipment_id=equipment.pk,
                        kind=kind,
                        start=data.start,
                        end=data.start + timedelta(hours=1),
                        reason="独立混合竞争",
                    )
                outcome = "success"
            except SlotConflict:
                outcome = "business_conflict"
            except IntegrityError as exc:
                diag = getattr(exc.__cause__, "diag", None)
                if direct and getattr(diag, "constraint_name", None) == "slot_no_active_overlap":
                    outcome = "exclusion_violation"
                else:
                    raise
            except OperationalError as exc:
                if direct and getattr(exc.__cause__, "sqlstate", None) == "40P01":
                    outcome = "deadlock_aborted"
                else:
                    raise
            return {"pid": pid, "kind": kind, "outcome": outcome}
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=len(kinds)) as executor:
        futures = [executor.submit(worker, kind) for kind in kinds]
        results = [future.result(timeout=45) for future in futures]
    assert len({result["pid"] for result in results}) == len(kinds), (
        "Every competitor must use a distinct PostgreSQL backend connection"
    )
    return results


def assert_single_active_without_overlap(equipment):
    assert EquipmentSlot.objects.filter(
        equipment=equipment,
        status=EquipmentSlot.Status.ACTIVE,
    ).count() == 1
    table = connection.ops.quote_name(EquipmentSlot._meta.db_table)
    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM {table} AS first_slot
            JOIN {table} AS second_slot
              ON first_slot.equipment_id = second_slot.equipment_id
             AND first_slot.id < second_slot.id
             AND first_slot.status = 'ACTIVE'
             AND second_slot.status = 'ACTIVE'
             AND first_slot.start_time < second_slot.end_time
             AND second_slot.start_time < first_slot.end_time
            WHERE first_slot.equipment_id = %s
            """,
            [equipment.pk],
        )
        assert cursor.fetchone()[0] == 0


def test_nfr01_twenty_independent_connections_for_twenty_rounds(us09_data, record_property):
    for round_index in range(20):
        equipment = Equipment.objects.create(
            code=f"US09-R{round_index + 1:02}", name=f"并发轮次 {round_index + 1}"
        )
        results = run_race(us09_data, equipment, ["RESERVATION"] * 20)
        outcomes = [result["outcome"] for result in results]
        assert outcomes.count("success") == 1
        assert outcomes.count("business_conflict") == 19
        assert_single_active_without_overlap(equipment)
        assert EquipmentSlot.objects.filter(equipment=equipment).count() == 1
        slot = EquipmentSlot.objects.get(equipment=equipment)
        assert OperationLog.objects.filter(
            action="CREATE_SLOT", target_type="EquipmentSlot", target_id=slot.pk
        ).count() == 1
        assert OperationLog.objects.filter(
            action="CREATE_SLOT",
            target_type="EquipmentSlot",
            target_id__in=EquipmentSlot.objects.filter(equipment=equipment).values("pk"),
        ).count() == 1
        record_property(
            f"round_{round_index + 1:02}",
            json.dumps(
                {
                    "equipment_id": equipment.pk,
                    "distinct_backend_pids": len({r["pid"] for r in results}),
                    "success": outcomes.count("success"),
                    "business_conflict": outcomes.count("business_conflict"),
                    "active_slots": 1,
                    "create_audits": 1,
                    "requests": results,
                },
                ensure_ascii=False,
            ),
        )


def test_reservation_maintenance_mixed_race_has_one_winner(us09_data, record_property):
    results = run_race(us09_data, us09_data.equipment, ["RESERVATION", "MAINTENANCE"] * 10)
    outcomes = [result["outcome"] for result in results]
    assert outcomes.count("success") == 1
    assert outcomes.count("business_conflict") == 19
    assert_single_active_without_overlap(us09_data.equipment)
    assert EquipmentSlot.objects.filter(equipment=us09_data.equipment).count() == 1
    assert OperationLog.objects.filter(action="CREATE_SLOT").count() == 1
    record_property("mixed_race", json.dumps(results, ensure_ascii=False))


def test_direct_database_race_distinguishes_constraint_errors_and_deadlocks(
    us09_data, record_property
):
    results = run_race(
        us09_data,
        us09_data.equipment,
        ["RESERVATION", "MAINTENANCE"],
        direct=True,
    )
    outcomes = [result["outcome"] for result in results]
    assert outcomes.count("success") == 1
    assert len(outcomes) == 2
    assert outcomes[0] != "business_conflict" and outcomes[1] != "business_conflict"
    assert set(outcomes) <= {"success", "exclusion_violation", "deadlock_aborted"}
    assert_single_active_without_overlap(us09_data.equipment)
    assert EquipmentSlot.objects.filter(equipment=us09_data.equipment).count() == 1
    assert OperationLog.objects.count() == 0
    record_property("direct_database_race", json.dumps(results, ensure_ascii=False))


@pytest.mark.parametrize("create_first", [False, True], ids=["disable-commits-first", "create-commits-first"])
def test_disable_and_create_are_serialized_by_equipment_lock(us09_data, create_first):
    locked = Event()
    attempting = Event()

    def first():
        close_old_connections()
        try:
            with transaction.atomic():
                Equipment.objects.select_for_update().get(pk=us09_data.equipment.pk)
                if create_first:
                    make_slot(us09_data)
                else:
                    set_equipment_enabled(
                        actor=us09_data.admin, equipment_id=us09_data.equipment.pk, enabled=False
                    )
                locked.set()
                assert attempting.wait(20)
        finally:
            connection.close()

    def second():
        close_old_connections()
        try:
            assert locked.wait(20)
            attempting.set()
            if create_first:
                set_equipment_enabled(
                    actor=us09_data.admin, equipment_id=us09_data.equipment.pk, enabled=False
                )
                return "disable_succeeded"
            try:
                make_slot(us09_data)
            except RuleViolation as exc:
                return f"create_rejected:{exc}"
            return "create_succeeded"
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        first_future = executor.submit(first)
        second_future = executor.submit(second)
        first_future.result(timeout=40)
        second_result = second_future.result(timeout=40)

    us09_data.equipment.refresh_from_db()
    assert us09_data.equipment.status == Equipment.Status.DISABLED
    if create_first:
        assert second_result == "disable_succeeded"
        assert EquipmentSlot.objects.filter(status=EquipmentSlot.Status.ACTIVE).count() == 1
    else:
        assert second_result == "create_rejected:设备已停用"
        assert EquipmentSlot.objects.count() == 0
        assert OperationLog.objects.filter(action="CREATE_SLOT").count() == 0
