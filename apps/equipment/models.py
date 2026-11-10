from django.db import models


class Equipment(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "AVAILABLE"
        DISABLED = "DISABLED"

    code = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.AVAILABLE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(status__in=["AVAILABLE", "DISABLED"]), name="equipment_valid_status")]
