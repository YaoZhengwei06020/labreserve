"""Integration tests using the real config.urls and template settings."""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.template.loader import get_template
from django.urls import reverse
from django.utils import timezone

from apps.audit.models import OperationLog
from apps.booking.models import EquipmentSlot
from apps.equipment.models import Equipment

pytestmark = pytest.mark.django_db


@pytest.fixture
def member():
    return get_user_model().objects.create_user(
        username="integration-member", password="test-only-password"
    )


@pytest.fixture
def equipment():
    return Equipment.objects.create(
        code="INTEGRATION-E001",
        name="集成验收设备",
        description="用于真实配置端到端测试",
        location="A-101",
    )


def reservation_payload(equipment, start, end):
    return {
        "equipment": equipment.pk,
        "start": timezone.localtime(start).strftime("%Y-%m-%dT%H:%M"),
        "end": timezone.localtime(end).strftime("%Y-%m-%dT%H:%M"),
    }


def test_real_configuration_loads_templates_and_named_routes(client):
    get_template("base.html")
    get_template("equipment/list.html")
    get_template("booking/reservation_form.html")
    get_template("booking/reservation_detail.html")

    response = client.get(reverse("accounts:login"))
    assert response.status_code == 200
    assert "登录 LabReserve" in response.content.decode()
    assert reverse("booking:create-reservation") == "/reservations/new/"
    assert reverse("booking:create-reservation-submit") == "/reservations/"
    assert reverse("booking:cancel-reservation", kwargs={"slot_id": 1}) == "/reservations/1/cancel/"


def test_home_redirects_to_equipment_list(client):
    response = client.get("/")
    assert response.status_code == 302
    assert response.url == reverse("equipment:list")


def test_complete_reservation_cancel_and_rebook_flow(client, member, equipment):
    client.force_login(member)

    equipment_response = client.get(reverse("equipment:detail", kwargs={"code": equipment.code}))
    assert equipment_response.status_code == 200
    assert "预约该设备" in equipment_response.content.decode()

    form_response = client.get(reverse("booking:create-reservation"), {"equipment": equipment.pk})
    assert form_response.status_code == 200
    assert equipment.name in form_response.content.decode()

    start = timezone.now().replace(second=0, microsecond=0) + timedelta(days=1)
    payload = reservation_payload(equipment, start, start + timedelta(hours=1))
    create_response = client.post(reverse("booking:create-reservation-submit"), payload)
    assert create_response.status_code == 303

    slot = EquipmentSlot.objects.get(status=EquipmentSlot.Status.ACTIVE)
    assert slot.user == member
    detail_url = reverse("booking:reservation-detail", kwargs={"slot_id": slot.pk})
    assert create_response.url == detail_url

    detail_response = client.get(detail_url)
    assert detail_response.status_code == 200
    detail_html = detail_response.content.decode()
    assert "取消该预约" in detail_html
    assert reverse("booking:cancel-reservation", kwargs={"slot_id": slot.pk}) in detail_html

    cancel_response = client.post(reverse("booking:cancel-reservation", kwargs={"slot_id": slot.pk}))
    assert cancel_response.status_code == 303
    slot.refresh_from_db()
    assert slot.status == EquipmentSlot.Status.CANCELLED
    assert slot.cancelled_by == member
    assert OperationLog.objects.filter(action="CANCEL_SLOT", target_id=slot.pk).count() == 1

    cancelled_detail = client.get(detail_url)
    assert cancelled_detail.status_code == 200
    assert "取消该预约" not in cancelled_detail.content.decode()

    rebook_response = client.post(reverse("booking:create-reservation-submit"), payload)
    assert rebook_response.status_code == 303
    assert EquipmentSlot.objects.count() == 2
    assert EquipmentSlot.objects.filter(status=EquipmentSlot.Status.ACTIVE).count() == 1
    assert EquipmentSlot.objects.filter(status=EquipmentSlot.Status.CANCELLED).count() == 1


def test_started_reservation_does_not_render_cancel_form(client, member, equipment):
    start = timezone.now() - timedelta(minutes=30)
    slot = EquipmentSlot.objects.create(
        equipment=equipment,
        kind=EquipmentSlot.Kind.RESERVATION,
        user=member,
        created_by=member,
        start_time=start,
        end_time=start + timedelta(hours=2),
    )
    client.force_login(member)

    response = client.get(reverse("booking:reservation-detail", kwargs={"slot_id": slot.pk}))
    assert response.status_code == 200
    assert "取消该预约" not in response.content.decode()
