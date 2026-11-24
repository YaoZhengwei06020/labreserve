from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client
from django.urls import include, path, reverse

from apps.equipment.models import Equipment

BASE_DIR = Path(__file__).resolve().parents[1]
TEST_PASSWORD = "test-only-password"

urlpatterns = [
    path("accounts/", include("apps.accounts.urls", namespace="accounts")),
    path("equipment/", include("apps.equipment.urls", namespace="equipment")),
]

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def configure_web(settings):
    settings.ROOT_URLCONF = __name__
    settings.TEMPLATES = [
        {**settings.TEMPLATES[0], "DIRS": [str(BASE_DIR / "templates")]}
    ]


@pytest.fixture
def member():
    return get_user_model().objects.create_user(
        username="member", password=TEST_PASSWORD
    )


@pytest.fixture
def admin():
    user = get_user_model().objects.create_user(
        username="admin", password=TEST_PASSWORD, is_staff=False
    )
    user.groups.add(Group.objects.create(name="ADMIN"))
    return user


@pytest.fixture
def member_client(client, member):
    client.force_login(member)
    return client


@pytest.fixture
def admin_client(client, admin):
    client.force_login(admin)
    return client


def equipment_data(code="E100", **changes):
    data = {
        "code": code,
        "name": "精密示波器",
        "description": "用于信号测量",
        "location": "A-101",
    }
    data.update(changes)
    return data


def test_equipment_list(member_client):
    equipment = [
        Equipment.objects.create(
            code=f"E00{index}",
            name=f"设备 {index}",
            description=f"描述 {index}",
            location=f"位置 {index}",
        )
        for index in range(1, 4)
    ]

    response = member_client.get(reverse("equipment:list"))

    assert response.status_code == 200
    assert len(response.context["equipment_list"]) == 3
    for item in equipment:
        assert response.context["equipment_list"].filter(pk=item.pk).exists()
        for value in (item.code, item.name, item.description, item.location):
            assert value in response.content.decode(response.charset)


def test_equipment_empty_state(member_client):
    response = member_client.get(reverse("equipment:list"))
    assert response.status_code == 200
    assert "暂无设备" in response.content.decode(response.charset)


def test_equipment_detail(member_client):
    equipment = Equipment.objects.create(
        code="E001",
        name="高精度万用表",
        description="六位半台式万用表",
        location="B-203",
        status=Equipment.Status.DISABLED,
    )

    response = member_client.get(
        reverse("equipment:detail", kwargs={"code": "E001"})
    )

    assert response.status_code == 200
    content = response.content.decode(response.charset)
    for value in (
        equipment.code,
        equipment.name,
        equipment.description,
        equipment.location,
        equipment.get_status_display(),
    ):
        assert value in content


def test_equipment_not_found(member_client):
    response = member_client.get(
        reverse("equipment:detail", kwargs={"code": "MISSING"})
    )
    assert response.status_code == 404


def test_member_allowed_access(member_client):
    equipment = Equipment.objects.create(code="E001", name="设备", location="实验室")
    assert member_client.get(reverse("equipment:list")).status_code == 200
    assert (
        member_client.get(
            reverse("equipment:detail", kwargs={"code": equipment.code})
        ).status_code
        == 200
    )


def test_admin_allowed_access(admin_client):
    equipment = Equipment.objects.create(code="E001", name="设备")
    assert admin_client.get(reverse("equipment:create")).status_code == 200
    assert (
        admin_client.get(
            reverse("equipment:edit", kwargs={"code": equipment.code})
        ).status_code
        == 200
    )


def test_equipment_create(admin_client):
    response = admin_client.post(reverse("equipment:create"), equipment_data())

    equipment = Equipment.objects.get(code="E100")
    assert equipment.name == "精密示波器"
    assert equipment.description == "用于信号测量"
    assert equipment.location == "A-101"
    assert response.status_code == 302
    assert response.url == reverse("equipment:detail", kwargs={"code": "E100"})
    detail = admin_client.get(response.url)
    assert detail.status_code == 200
    assert "精密示波器" in detail.content.decode(detail.charset)


def test_equipment_code_unique(admin_client):
    Equipment.objects.create(code="E001", name="已有设备")

    response = admin_client.post(
        reverse("equipment:create"), equipment_data(code="E001", name="重复设备")
    )

    assert response.status_code == 200
    assert Equipment.objects.filter(code="E001").count() == 1
    assert Equipment.objects.filter(name="重复设备").count() == 0
    assert "设备编号已存在，请使用其他编号。" in response.content.decode(response.charset)


def test_equipment_edit(admin_client):
    equipment = Equipment.objects.create(
        code="E001", name="旧名称", description="旧描述", location="旧位置"
    )

    response = admin_client.post(
        reverse("equipment:edit", kwargs={"code": equipment.code}),
        equipment_data(code="E001", name="新名称", location="新位置"),
    )

    equipment.refresh_from_db()
    assert equipment.name == "新名称"
    assert equipment.location == "新位置"
    assert response.status_code == 302
    detail = admin_client.get(response.url)
    content = detail.content.decode(detail.charset)
    assert "新名称" in content
    assert "新位置" in content


def test_member_admin_forbidden(member_client):
    response = member_client.post(reverse("equipment:create"), equipment_data())

    assert response.status_code == 403
    assert Equipment.objects.count() == 0


def test_member_cannot_edit_equipment(member_client):
    equipment = Equipment.objects.create(code="E001", name="原名称", location="原位置")

    response = member_client.post(
        reverse("equipment:edit", kwargs={"code": equipment.code}),
        equipment_data(code="E001", name="篡改名称", location="篡改位置"),
    )

    equipment.refresh_from_db()
    assert response.status_code == 403
    assert equipment.name == "原名称"
    assert equipment.location == "原位置"


def test_role_parameter_tampering(member, member_client):
    response = member_client.post(
        reverse("equipment:create"),
        equipment_data(
            role="ADMIN",
            groups="ADMIN",
            is_staff="1",
            is_superuser="1",
        ),
    )

    member.refresh_from_db()
    assert response.status_code == 403
    assert not member.is_staff
    assert not member.is_superuser
    assert not member.groups.exists()
    assert Equipment.objects.count() == 0


def test_staff_flag_is_not_business_admin(client):
    staff_member = get_user_model().objects.create_user(
        username="staff-member", password=TEST_PASSWORD, is_staff=True
    )
    client.force_login(staff_member)

    response = client.post(reverse("equipment:create"), equipment_data())

    assert response.status_code == 403
    assert Equipment.objects.count() == 0


def test_create_cannot_set_status(admin_client):
    response = admin_client.post(
        reverse("equipment:create"),
        equipment_data(status=Equipment.Status.DISABLED),
    )

    equipment = Equipment.objects.get(code="E100")
    assert response.status_code == 302
    assert equipment.status == Equipment.Status.AVAILABLE


def test_edit_cannot_change_status(admin_client):
    equipment = Equipment.objects.create(
        code="E001", name="设备", status=Equipment.Status.AVAILABLE
    )

    response = admin_client.post(
        reverse("equipment:edit", kwargs={"code": equipment.code}),
        equipment_data(code="E001", status=Equipment.Status.DISABLED),
    )

    equipment.refresh_from_db()
    assert response.status_code == 302
    assert equipment.status == Equipment.Status.AVAILABLE


def test_equipment_required_fields(admin_client):
    response = admin_client.post(reverse("equipment:create"), {})

    assert response.status_code == 200
    assert Equipment.objects.count() == 0
    assert response.context["form"].errors["code"]
    assert response.context["form"].errors["name"]


def test_equipment_write_requires_csrf(admin):
    client = Client(enforce_csrf_checks=True)
    client.force_login(admin)

    response = client.post(reverse("equipment:create"), equipment_data())

    assert response.status_code == 403
    assert Equipment.objects.count() == 0
