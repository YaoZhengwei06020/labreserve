from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import pytest
from django.core.exceptions import PermissionDenied
from apps.accounts.policy import require_actor
from apps.booking.policy import RuleViolation, validate_cancellation, validate_interval

NOW = datetime(2030, 1, 1, tzinfo=timezone.utc)


@pytest.mark.parametrize("start,end", [(NOW, NOW + timedelta(hours=1)), (NOW - timedelta(hours=1), NOW), (NOW + timedelta(hours=1), NOW + timedelta(hours=1)), (NOW + timedelta(hours=2), NOW + timedelta(hours=1)), (NOW.replace(tzinfo=None), NOW + timedelta(hours=1)), (None, NOW)])
def test_invalid_interval(start, end):
    with pytest.raises(RuleViolation):
        validate_interval(start, end, NOW)


def test_future_interval():
    validate_interval(NOW + timedelta(hours=1), NOW + timedelta(hours=2), NOW)


def cancel(**overrides):
    values = dict(is_admin=False, is_owner=True, kind="RESERVATION", status="ACTIVE", start=NOW + timedelta(hours=1), now=NOW, reason="")
    values.update(overrides)
    return validate_cancellation(**values)


@pytest.mark.parametrize("overrides,error", [
    ({"is_owner": False}, PermissionDenied),
    ({"kind": "MAINTENANCE"}, PermissionDenied),
    ({"is_admin": True, "reason": "   "}, RuleViolation),
    ({"start": NOW}, RuleViolation),
    ({"is_admin": True, "reason": "故障", "start": NOW}, RuleViolation),
    ({"is_owner": False, "status": "CANCELLED"}, PermissionDenied),
])
def test_cancellation_restrictions(overrides, error):
    with pytest.raises(error):
        cancel(**overrides)


def test_owner_cancel():
    assert cancel() is True


def test_admin_maintenance_cancel():
    assert cancel(is_admin=True, is_owner=False, kind="MAINTENANCE", reason="检修完成") is True


def test_repeat_cancellation_preserves_audit_even_after_start():
    assert cancel(status="CANCELLED", start=NOW) is False


@pytest.mark.parametrize("actor", [SimpleNamespace(is_authenticated=False, is_active=True), SimpleNamespace(is_authenticated=True, is_active=False)])
def test_invalid_actor(actor):
    with pytest.raises(PermissionDenied):
        require_actor(actor)


def test_health_is_process_only(client):
    assert client.get("/health/").json()["stage"] == "technical-spike"
