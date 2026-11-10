from django.conf import settings
from django.db import models


class OperationLog(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(max_length=40)
    target_type = models.CharField(max_length=40)
    target_id = models.PositiveBigIntegerField()
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
