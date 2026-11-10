from datetime import datetime
from django.utils import timezone


class RuleViolation(ValueError):
    pass


class SlotConflict(RuleViolation):
    pass


def validate_interval(start, end, now):
    if not all(isinstance(x, datetime) and timezone.is_aware(x) for x in (start, end, now)):
        raise RuleViolation("必须提供带时区的时间")
    if start >= end:
        raise RuleViolation("开始时间必须早于结束时间")
    if start <= now:
        raise RuleViolation("新占用必须在未来开始")


def validate_cancellation(*, is_admin, is_owner, kind, status, start, now, reason):
    from django.core.exceptions import PermissionDenied
    if not is_admin and (kind == "MAINTENANCE" or not is_owner):
        raise PermissionDenied
    if is_admin and not reason.strip():
        raise RuleViolation("管理员取消必须填写原因")
    if status == "CANCELLED":
        return False
    if now >= start:
        raise RuleViolation("开始后不可取消；异常中止暂不在范围内")
    return True
