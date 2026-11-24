from datetime import datetime, timedelta

from django.conf import settings
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


def reservation_rule_limits():
    """Return PROPOSED reservation limits; these values are not team-approved."""
    return {
        "min_minutes": getattr(settings, "RESERVATION_MIN_MINUTES", 30),
        "max_minutes": getattr(settings, "RESERVATION_MAX_MINUTES", 240),
        "advance_days": getattr(settings, "RESERVATION_ADVANCE_DAYS", 7),
    }


def validate_reservation_interval(start, end, now):
    validate_interval(start, end, now)
    limits = reservation_rule_limits()
    duration = end - start
    if duration < timedelta(minutes=limits["min_minutes"]):
        raise RuleViolation(f"预约时长不能少于 {limits['min_minutes']} 分钟")
    if duration > timedelta(minutes=limits["max_minutes"]):
        raise RuleViolation(f"预约时长不能超过 {limits['max_minutes']} 分钟")
    if start > now + timedelta(days=limits["advance_days"]):
        raise RuleViolation(f"预约最多只能提前 {limits['advance_days']} 天")


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
