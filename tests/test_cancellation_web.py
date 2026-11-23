from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.test import Client, RequestFactory
from django.urls import include, path, reverse
from django.utils import timezone

from apps.audit.models import OperationLog
from apps.booking.models import EquipmentSlot
from apps.booking.services import create_slot
from apps.booking.views.cancellation import cancel_reservation
from apps.equipment.models import Equipment


def reservation_detail(request, slot_id):
    return HttpResponse("reservation detail")


booking_patterns = (
    [
        path("reservations/<int:slot_id>/cancel/", cancel_reservation, name="cancel-reservation"),
        path("reservations/<int:slot_id>/", reservation_detail, name="reservation-detail"),
    ],
    "booking",
)
urlpatterns = [path("", include(booking_patterns, namespace="booking"))]

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def cancellation_test_configuration(settings):
    settings.ROOT_URLCONF = __name__
    settings.TEMPLATES = [{
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": False,
        "OPTIONS": {
            "loaders": [
                ("django.template.loaders.locmem.Loader", {
                    "base.html": "{% block content %}{% endblock %}",
                }),
                ("django.template.loaders.filesystem.Loader", [settings.BASE_DIR / "templates"]),
            ],
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }]


@pytest.fixture
def owner():
    return get_user_model().objects.create_user(username="owner", password="test-only-password")


@pytest.fixture
def other():
    return get_user_model().objects.create_user(username="other", password="test-only-password")


@pytest.fixture
def equipment():
    return Equipment.objects.create(code="PRIVATE-E001", name="私人设备名称")


@pytest.fixture
def reservation(owner, equipment):
    start = timezone.now() + timedelta(days=1)
    return create_slot(
        actor=owner,
        equipment_id=equipment.pk,
        kind=EquipmentSlot.Kind.RESERVATION,
        start=start,
        end=start + timedelta(hours=1),
    )


def cancel_url(slot_id):
    return reverse("booking:cancel-reservation", kwargs={"slot_id": slot_id})


def test_anonymous_cancellation_redirects_to_login(client, reservation):
    response = client.post(cancel_url(reservation.pk))

    assert response.status_code == 302
    assert response["Location"].startswith("/accounts/login/?next=")
    reservation.refresh_from_db()
    assert reservation.status == EquipmentSlot.Status.ACTIVE


@pytest.mark.parametrize("method", ["get", "put", "patch", "delete"])
def test_non_post_requests_do_not_cancel(client, owner, reservation, method):
    client.force_login(owner)

    response = getattr(client, method)(cancel_url(reservation.pk))

    assert response.status_code == 405
    reservation.refresh_from_db()
    assert reservation.status == EquipmentSlot.Status.ACTIVE
    assert not OperationLog.objects.filter(action="CANCEL_SLOT").exists()


def test_missing_csrf_token_is_rejected(owner, reservation):
    csrf_client = Client(enforce_csrf_checks=True)
    csrf_client.force_login(owner)

    response = csrf_client.post(cancel_url(reservation.pk))

    assert response.status_code == 403
    reservation.refresh_from_db()
    assert reservation.status == EquipmentSlot.Status.ACTIVE
    assert not OperationLog.objects.filter(action="CANCEL_SLOT").exists()


def test_success_uses_session_actor_and_redirects_with_303(client, owner, other, reservation):
    client.force_login(owner)

    response = client.post(cancel_url(reservation.pk), {"user_id": other.pk, "actor": other.pk})

    assert response.status_code == 303
    assert response["Location"] == reverse("booking:reservation-detail", kwargs={"slot_id": reservation.pk})
    assert "预约已取消" in str(list(get_messages(response.wsgi_request)))
    reservation.refresh_from_db()
    assert reservation.status == EquipmentSlot.Status.CANCELLED
    assert reservation.cancelled_by == owner
    log = OperationLog.objects.get(action="CANCEL_SLOT", target_id=reservation.pk)
    assert log.actor == owner


def test_cancel_other_user_is_generic_403_without_privacy_leak(client, other, owner, reservation, equipment):
    client.force_login(other)

    response = client.post(cancel_url(reservation.pk))

    assert response.status_code == 403
    content = response.content.decode()
    assert "你无权取消该预约" in content
    assert equipment.code not in content
    assert equipment.name not in content
    assert owner.username not in content
    reservation.refresh_from_db()
    assert reservation.status == EquipmentSlot.Status.ACTIVE
    assert reservation.cancelled_at is None
    assert not OperationLog.objects.filter(action="CANCEL_SLOT").exists()


def test_missing_reservation_returns_404(client, owner):
    client.force_login(owner)

    response = client.post(cancel_url(999999))

    assert response.status_code == 404


def test_started_reservation_shows_chinese_reason_and_does_not_change(client, owner, equipment):
    start = timezone.now() - timedelta(minutes=10)
    reservation = EquipmentSlot.objects.create(
        equipment=equipment,
        kind=EquipmentSlot.Kind.RESERVATION,
        user=owner,
        created_by=owner,
        start_time=start,
        end_time=start + timedelta(hours=1),
    )
    client.force_login(owner)

    response = client.post(cancel_url(reservation.pk))

    assert response.status_code == 400
    assert "开始后不可取消" in response.content.decode()
    reservation.refresh_from_db()
    assert reservation.status == EquipmentSlot.Status.ACTIVE
    assert reservation.cancelled_at is None
    assert not OperationLog.objects.filter(action="CANCEL_SLOT").exists()


def test_cancel_form_is_post_with_csrf_and_named_route(owner, reservation):
    request = RequestFactory().get(cancel_url(reservation.pk))
    request.user = owner

    content = render_to_string("booking/_cancel_form.html", {"slot": reservation}, request=request)

    assert 'method="post"' in content
    assert "csrfmiddlewaretoken" in content
    assert f'action="{cancel_url(reservation.pk)}"' in content
    assert "取消后时段将释放" in content
