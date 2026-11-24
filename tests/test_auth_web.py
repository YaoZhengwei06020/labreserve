from pathlib import Path

import pytest
from django.conf import settings as django_settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.urls import include, path, reverse

BASE_DIR = Path(__file__).resolve().parents[1]
TEST_PASSWORD = "test-only-password"

urlpatterns = [
    path("accounts/", include("apps.accounts.urls", namespace="accounts")),
    path("equipment/", include("apps.equipment.urls", namespace="equipment")),
]

@pytest.fixture(autouse=True)
def configure_web(settings):
    settings.ROOT_URLCONF = __name__
    settings.TEMPLATES = [
        {**settings.TEMPLATES[0], "DIRS": [str(BASE_DIR / "templates")]}
    ]


@pytest.fixture
def member(db):
    return get_user_model().objects.create_user(
        username="member", password=TEST_PASSWORD
    )


def test_login_page_renders(client):
    response = client.get(reverse("accounts:login"))

    assert response.status_code == 200
    content = response.content.decode(response.charset)
    assert "登录 LabReserve" in content
    assert 'name="username"' in content
    assert 'name="password"' in content
    assert 'name="csrfmiddlewaretoken"' in content


def test_login_success(client, member):
    response = client.post(
        reverse("accounts:login"),
        {"username": "member", "password": TEST_PASSWORD},
    )

    assert response.status_code == 302
    assert response.url == reverse("equipment:list")
    assert client.session["_auth_user_id"] == str(member.pk)
    assert client.get(reverse("equipment:list")).status_code == 200


def test_login_invalid_credentials(client, member):
    response = client.post(
        reverse("accounts:login"),
        {"username": "member", "password": "incorrect-test-password"},
    )

    assert response.status_code == 200
    assert "_auth_user_id" not in client.session
    content = response.content.decode(response.charset)
    assert "用户名或密码不正确" in content


def test_anonymous_access(client):
    equipment_url = reverse("equipment:list")
    response = client.get(equipment_url)

    assert response.status_code == 302
    assert response.url == f"{reverse('accounts:login')}?next={equipment_url}"

    json_response = client.get(equipment_url, HTTP_ACCEPT="application/json")
    assert json_response.status_code == 302
    assert json_response.content == b""


def test_logout_invalidates_session(client, member):
    client.post(
        reverse("accounts:login"),
        {"username": "member", "password": TEST_PASSWORD},
    )
    original_session_key = client.session.session_key
    assert Session.objects.filter(session_key=original_session_key).exists()

    response = client.post(reverse("accounts:logout"))

    assert response.status_code == 302
    assert response.url == reverse("accounts:login")
    assert not Session.objects.filter(session_key=original_session_key).exists()

    client.cookies[django_settings.SESSION_COOKIE_NAME] = original_session_key
    protected_response = client.get(reverse("equipment:list"))
    assert protected_response.status_code == 302
    assert protected_response.url.startswith(reverse("accounts:login"))


def test_logout_requires_post(client):
    assert client.get(reverse("accounts:logout")).status_code == 405
