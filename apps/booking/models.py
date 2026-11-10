from django.conf import settings
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateTimeRangeField, RangeOperators
from django.db import models
from django.db.models import F, Q, Value


class EquipmentSlot(models.Model):
    class Kind(models.TextChoices):
        RESERVATION = "RESERVATION"
        MAINTENANCE = "MAINTENANCE"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE"
        CANCELLED = "CANCELLED"

    equipment = models.ForeignKey("equipment.Equipment", on_delete=models.PROTECT)
    kind = models.CharField(max_length=16, choices=Kind.choices)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACTIVE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="reservations")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    reason = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="slots_created")
    created_at = models.DateTimeField(auto_now_add=True)
    cancelled_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="slots_cancelled")
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(start_time__lt=F("end_time")), name="slot_positive_duration"),
            models.CheckConstraint(condition=Q(kind__in=["RESERVATION", "MAINTENANCE"]), name="slot_valid_kind"),
            models.CheckConstraint(condition=Q(status__in=["ACTIVE", "CANCELLED"]), name="slot_valid_status"),
            models.CheckConstraint(condition=(Q(kind="RESERVATION", user__isnull=False) | Q(kind="MAINTENANCE", user__isnull=True)), name="slot_owner_matches_kind"),
            ExclusionConstraint(name="slot_no_active_overlap", expressions=[
                ("equipment", RangeOperators.EQUAL),
                (models.Func(F("start_time"), F("end_time"), Value("[)"), function="TSTZRANGE", output_field=DateTimeRangeField()), RangeOperators.OVERLAPS),
            ], condition=Q(status="ACTIVE")),
        ]
