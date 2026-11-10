"""PROPOSED spike: write operations lock Equipment before EquipmentSlot.

No public write endpoint exists yet. Never register unrestricted model writes
in Django admin as a substitute for these services.
"""
from django.db import IntegrityError, transaction
from django.utils import timezone
from apps.accounts.policy import is_admin, require_actor
from apps.audit.models import OperationLog
from apps.equipment.models import Equipment
from .models import EquipmentSlot
from .policy import RuleViolation, SlotConflict, validate_interval, validate_cancellation


def create_slot(*, actor, equipment_id, kind, start, end, reason=""):
    require_actor(actor, admin=kind == EquipmentSlot.Kind.MAINTENANCE)
    if kind not in EquipmentSlot.Kind.values:
        raise RuleViolation("未知占用类型")
    if kind == EquipmentSlot.Kind.MAINTENANCE and not reason.strip():
        raise RuleViolation("维护原因必填")
    try:
        with transaction.atomic():
            equipment = Equipment.objects.select_for_update().get(pk=equipment_id)
            validate_interval(start, end, timezone.now())
            if equipment.status != Equipment.Status.AVAILABLE:
                raise RuleViolation("设备已停用")
            # Friendly early error; the exclusion constraint also protects direct writes.
            if EquipmentSlot.objects.filter(equipment=equipment, status="ACTIVE", start_time__lt=end, end_time__gt=start).exists():
                raise SlotConflict("该设备时段已被占用")
            slot = EquipmentSlot.objects.create(equipment=equipment, kind=kind,
                start_time=start, end_time=end, created_by=actor,
                user=actor if kind == EquipmentSlot.Kind.RESERVATION else None, reason=reason.strip())
            OperationLog.objects.create(actor=actor, action="CREATE_SLOT", target_type="EquipmentSlot", target_id=slot.pk, reason=reason.strip())
            return slot
    except IntegrityError as exc:
        if getattr(getattr(exc.__cause__, "diag", None), "constraint_name", None) == "slot_no_active_overlap":
            raise SlotConflict("该设备时段已被占用") from exc
        raise


@transaction.atomic
def cancel_slot(*, actor, slot_id, reason=""):
    require_actor(actor)
    equipment_id = EquipmentSlot.objects.values_list("equipment_id", flat=True).get(pk=slot_id)
    Equipment.objects.select_for_update().get(pk=equipment_id)
    slot = EquipmentSlot.objects.select_for_update().get(pk=slot_id)
    # Equipment FK is immutable in the business service; no move operation is exposed.
    if not validate_cancellation(is_admin=is_admin(actor), is_owner=slot.user_id == actor.pk,
        kind=slot.kind, status=slot.status, start=slot.start_time, now=timezone.now(), reason=reason):
        return slot
    slot.status = EquipmentSlot.Status.CANCELLED
    slot.cancelled_by = actor
    slot.cancelled_at = timezone.now()
    slot.cancellation_reason = reason.strip()
    slot.save(update_fields=["status", "cancelled_by", "cancelled_at", "cancellation_reason"])
    OperationLog.objects.create(actor=actor, action="CANCEL_SLOT", target_type="EquipmentSlot", target_id=slot.pk, reason=reason.strip())
    return slot


@transaction.atomic
def set_equipment_enabled(*, actor, equipment_id, enabled):
    require_actor(actor, admin=True)
    if type(enabled) is not bool:
        raise RuleViolation("启停参数必须为布尔值")
    equipment = Equipment.objects.select_for_update().get(pk=equipment_id)
    equipment.status = Equipment.Status.AVAILABLE if enabled else Equipment.Status.DISABLED
    equipment.save(update_fields=["status", "updated_at"])
    OperationLog.objects.create(actor=actor, action="ENABLE_EQUIPMENT" if enabled else "DISABLE_EQUIPMENT", target_type="Equipment", target_id=equipment.pk)
    return equipment
