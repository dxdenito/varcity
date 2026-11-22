import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.core.db import SessionLocal
from app.main import app
from app.modules.settings.models import AppSetting, Asset

PROFILE, LOGO = "/api/v1/settings/university", "/api/v1/settings/university/logo"
GENERAL = "/api/v1/settings/general"
PUBLIC, PUBLIC_LOGO = "/api/v1/public/branding", "/api/v1/public/branding/logo"
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 100


def _reset():
    with SessionLocal() as session:
        session.execute(delete(AppSetting).where(AppSetting.key.in_(["branding", "general"])))
        session.execute(delete(Asset))
        session.commit()


@pytest.fixture
def clean():
    _reset()
    yield
    _reset()


@pytest.fixture
def admin(signed_in):
    return signed_in(is_superuser=True)


def _profile(**overrides):
    profile = {
        "university_name": "Test University",
        "short_name": "TU",
        "motto": "Knowledge first",
        "address": "P.O. Box 1, Nairobi",
        "website": "https://example.ac.ke",
        "primary_color": "#047857",
        "sidebar_color": "#022c22",
        "show_powered_by": False,
    }
    profile.update(overrides)
    return profile


def test_updating_the_profile_changes_the_public_branding(clean, admin):
    response = admin.put(PROFILE, json=_profile())
    assert response.status_code == 200
    assert response.json()["address"] == "P.O. Box 1, Nairobi"

    public = TestClient(app).get(PUBLIC).json()
    assert public["university_name"] == "Test University"
    assert public["motto"] == "Knowledge first"
    assert public["show_powered_by"] is False
    assert public["colors"]["primary"]["600"] == "#047857"
    assert "address" not in public


def test_invalid_profile_values_are_rejected(clean, admin):
    assert admin.put(PROFILE, json=_profile(primary_color="green")).status_code == 422
    assert admin.put(PROFILE, json=_profile(website="ftp://example.ac.ke")).status_code == 422
    assert admin.put(PROFILE, json=_profile(university_name="")).status_code == 422


def test_only_super_admins_can_change_the_profile(clean, signed_in):
    regular = signed_in()
    assert regular.get(PROFILE).status_code == 200
    assert regular.put(PROFILE, json=_profile()).status_code == 403
    assert regular.post(LOGO, files={"file": ("logo.png", PNG, "image/png")}).status_code == 403
    assert TestClient(app).get(PROFILE).status_code == 401


def test_logo_can_be_uploaded_served_and_removed(clean, admin):
    upload = admin.post(LOGO, files={"file": ("logo.png", PNG, "image/png")})
    assert upload.status_code == 204

    logo_url = TestClient(app).get(PUBLIC).json()["logo_url"]
    assert logo_url.startswith(PUBLIC_LOGO + "?v=")

    served = TestClient(app).get(logo_url)
    assert served.status_code == 200
    assert served.content == PNG
    assert served.headers["content-type"] == "image/png"

    assert admin.delete(LOGO).status_code == 204
    assert TestClient(app).get(PUBLIC).json()["logo_url"] is None
    assert TestClient(app).get(PUBLIC_LOGO).status_code == 404


def test_logo_must_really_be_an_image_of_a_small_size(clean, admin):
    not_an_image = admin.post(LOGO, files={"file": ("logo.png", b"hello world", "image/png")})
    too_big = admin.post(
        LOGO, files={"file": ("logo.png", PNG + b"0" * (600 * 1024), "image/png")}
    )
    empty = admin.post(LOGO, files={"file": ("logo.png", b"", "image/png")})

    assert not_an_image.status_code == 422
    assert too_big.status_code == 422
    assert empty.status_code == 422

def test_general_settings_are_validated_and_published(clean, admin):
    defaults = TestClient(app).get(PUBLIC).json()
    assert defaults["timezone"] == "Africa/Nairobi"
    assert defaults["date_format"] == "DD/MM/YYYY"

    unknown_zone = {"timezone": "Mars/Olympus", "date_format": "DD/MM/YYYY"}
    bad_format = {"timezone": "Africa/Nairobi", "date_format": "DD-MM"}
    assert admin.put(GENERAL, json=unknown_zone).status_code == 422
    assert admin.put(GENERAL, json=bad_format).status_code == 422

    saved = admin.put(GENERAL, json={"timezone": "Africa/Kampala", "date_format": "D MMM YYYY"})
    assert saved.status_code == 200
    public = TestClient(app).get(PUBLIC).json()
    assert public["timezone"] == "Africa/Kampala"
    assert public["date_format"] == "D MMM YYYY"


def test_only_super_admins_can_change_general_settings(clean, signed_in):
    regular = signed_in()
    unchanged = {"timezone": "Africa/Nairobi", "date_format": "DD/MM/YYYY"}
    assert regular.get(GENERAL).status_code == 200
    assert regular.put(GENERAL, json=unchanged).status_code == 403