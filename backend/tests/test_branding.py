import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.core.db import SessionLocal
from app.main import app
from app.modules.settings.branding import (
    build_palette,
    contrast_ratio,
    luminance,
    readable_text_color,
)
from app.modules.settings.models import AppSetting

client = TestClient(app)


def _set_branding(value) -> None:
    with SessionLocal() as session:
        session.merge(AppSetting(key="branding", value=value))
        session.commit()


def _clear_branding() -> None:
    with SessionLocal() as session:
        session.execute(delete(AppSetting).where(AppSetting.key == "branding"))
        session.commit()


@pytest.fixture
def clean_branding():
    _clear_branding()
    yield
    _clear_branding()


def test_palette_has_all_shades_and_keeps_the_base_colour():
    palette = build_palette("#1D4ED8")
    assert list(palette) == [
        "50", "100", "200", "300", "400", "500", "600", "700", "800", "900", "950",
    ]
    assert palette["600"] == "#1d4ed8"
    assert luminance(palette["50"]) > luminance(palette["600"]) > luminance(palette["950"])


def test_contrast_ratio_extremes():
    assert contrast_ratio("#000000", "#ffffff") == pytest.approx(21.0)
    assert contrast_ratio("#ffffff", "#ffffff") == pytest.approx(1.0)


def test_readable_text_color_picks_the_better_contrast():
    assert readable_text_color("#0f2557") == "#ffffff"  # dark navy -> white text
    assert readable_text_color("#fde047") == "#111827"  # pale yellow -> dark text


def test_default_branding_when_nothing_is_configured(clean_branding):
    response = client.get("/api/v1/public/branding")
    assert response.status_code == 200
    body = response.json()
    assert body["university_name"] == "Your University"
    assert body["show_powered_by"] is True
    assert body["colors"]["primary"]["600"] == "#1d4ed8"


def test_configured_branding_is_returned(clean_branding):
    _set_branding(
        {
            "university_name": "Kenya University",
            "short_name": "KU",
            "primary_color": "#047857",
            "sidebar_color": "#022c22",
            "show_powered_by": False,
        }
    )
    body = client.get("/api/v1/public/branding").json()
    assert body["university_name"] == "Kenya University"
    assert body["short_name"] == "KU"
    assert body["show_powered_by"] is False
    assert body["colors"]["primary"]["600"] == "#047857"
    assert body["colors"]["sidebar"] == "#022c22"


def test_invalid_stored_branding_falls_back_to_defaults(clean_branding):
    _set_branding({"university_name": "Broken", "primary_color": "not-a-colour"})
    response = client.get("/api/v1/public/branding")
    assert response.status_code == 200
    assert response.json()["university_name"] == "Your University"