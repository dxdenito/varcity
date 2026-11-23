import io

import pytest
from openpyxl import load_workbook
from sqlalchemy import delete

from app.core import tabular
from app.core.db import SessionLocal
from app.modules.org.models import Node, NodeType, NodeTypeParent

NODES = "/api/v1/org/nodes"
HEADER = "Level,Name,Code,Parent"


def _wipe():
    with SessionLocal() as session:
        session.execute(delete(Node))
        session.execute(delete(NodeTypeParent))
        session.execute(delete(NodeType))
        session.commit()


@pytest.fixture
def clean_org():
    _wipe()
    yield
    _wipe()


@pytest.fixture
def admin(signed_in):
    return signed_in(is_superuser=True)


@pytest.fixture
def campus(clean_org, admin):
    admin.post("/api/v1/org/initialize", json={"template": "college", "institution_code": "ku"})
    types = {t["code"]: t["id"] for t in admin.get("/api/v1/org/node-types").json()}
    root = admin.get(NODES).json()[0]
    response = admin.post(
        NODES, json={"type_id": types["campus"], "parent_id": root["id"], "name": "Main Campus"}
    )
    return types, response.json()


def _csv(*rows):
    return "\n".join([HEADER] + [",".join(row) for row in rows]).encode("utf-8")


FULL_FILE = _csv(
    ("College", "Engineering", "", ""),
    ("School", "Computing", "", "Engineering"),
    ("Department", "Computer Science", "", "Engineering > Computing"),
)


def _url(node, action):
    return f"{NODES}/{node['id']}/{action}"


def _upload(client, node, action, content, name="entries.csv"):
    return client.post(_url(node, action), files={"file": (name, content, "text/csv")})


def _count(client):
    return len(client.get(NODES).json())


def test_preview_shows_what_would_happen_without_saving(campus, admin):
    _, main = campus
    before = _count(admin)

    response = _upload(admin, main, "import/preview", FULL_FILE)

    assert response.status_code == 200
    assert response.json()["summary"] == {"create": 3, "skip": 0, "error": 0}
    assert _count(admin) == before


def test_import_creates_entries_in_the_right_places_and_is_repeatable(campus, admin):
    _, main = campus
    first = _upload(admin, main, "import", FULL_FILE)
    assert first.status_code == 201
    assert first.json() == {"create": 3, "skip": 0, "error": 0}

    nodes = {n["name"]: n for n in admin.get(NODES).json()}
    assert nodes["Engineering"]["parent_id"] == main["id"]
    assert nodes["Computing"]["parent_id"] == nodes["Engineering"]["id"]
    assert nodes["Computer Science"]["parent_id"] == nodes["Computing"]["id"]

    again = _upload(admin, main, "import", FULL_FILE)
    assert again.json() == {"create": 0, "skip": 3, "error": 0}
    assert _count(admin) == 5


def test_one_bad_row_rejects_the_whole_file(campus, admin):
    _, main = campus
    bad = _csv(
        ("College", "Engineering", "e1", ""),
        ("Wizard", "Hogwarts", "", ""),
        ("School", "Computing", "", "Missing"),
        ("Department", "Physics", "", ""),
        ("College", "Law", "E1", ""),
    )
    before = _count(admin)

    response = _upload(admin, main, "import", bad)

    assert response.status_code == 422
    rows = response.json()["rows"]
    assert [r["status"] for r in rows] == ["create", "error", "error", "error", "error"]
    assert "Unknown level" in rows[1]["messages"][0]
    assert "not found" in rows[2]["messages"][0]
    assert "cannot be placed" in rows[3]["messages"][0]
    assert "already in use" in rows[4]["messages"][0]
    assert _count(admin) == before


def test_exports_in_every_format(campus, admin):
    _, main = campus
    _upload(admin, main, "import", FULL_FILE)

    as_csv = admin.get(_url(main, "export"), params={"format": "csv"})
    assert as_csv.status_code == 200
    assert as_csv.content.startswith(b"\xef\xbb\xbf")
    text = as_csv.content.decode("utf-8-sig")
    assert text.splitlines()[0] == "Level,Name,Code,Parent,Status"
    assert "Computer Science,,Engineering > Computing,Active" in text

    as_xlsx = admin.get(_url(main, "export"), params={"format": "xlsx"})
    sheet = load_workbook(io.BytesIO(as_xlsx.content)).active
    assert [cell.value for cell in sheet[1]][:2] == ["Level", "Name"]
    assert sheet.max_row == 4

    as_pdf = admin.get(_url(main, "export"), params={"format": "pdf"})
    assert as_pdf.content.startswith(b"%PDF")
    assert "attachment" in as_pdf.headers["content-disposition"]


def test_an_export_can_be_imported_elsewhere(campus, admin):
    types, main = campus
    _upload(admin, main, "import", FULL_FILE)
    exported = admin.get(_url(main, "export"), params={"format": "csv"}).content

    root = next(n for n in admin.get(NODES).json() if n["parent_id"] is None)
    other = admin.post(
        NODES, json={"type_id": types["campus"], "parent_id": root["id"], "name": "Other Campus"}
    ).json()

    response = _upload(admin, other, "import", exported)
    assert response.status_code == 201
    assert response.json()["create"] == 3


def test_spreadsheet_formulas_are_neutralised_in_exports(campus, admin):
    types, main = campus
    admin.post(
        NODES,
        json={"type_id": types["college"], "parent_id": main["id"], "name": "=HYPERLINK(1)"},
    )

    text = admin.get(_url(main, "export"), params={"format": "csv"}).content.decode("utf-8-sig")
    assert "'=HYPERLINK(1)" in text

    xlsx = admin.get(_url(main, "export"), params={"format": "xlsx"}).content
    cell = load_workbook(io.BytesIO(xlsx)).active["B2"]
    assert cell.value == "=HYPERLINK(1)"
    assert cell.data_type == "s"


def test_excel_files_and_windows_csv_files_can_be_imported(campus, admin):
    _, main = campus
    xlsx = tabular.write_xlsx(
        ["Level", "Name", "Code", "Parent"], [["College", "Engineering", "", ""]]
    )
    response = _upload(admin, main, "import", xlsx, name="entries.xlsx")
    assert response.status_code == 201

    windows_csv = _csv(("College", "École Supérieure", "", "")).decode("utf-8").encode("cp1252")
    preview = _upload(admin, main, "import/preview", windows_csv)
    assert preview.json()["rows"][0]["name"] == "École Supérieure"


def test_unusable_files_are_rejected_with_a_reason(campus, admin):
    _, main = campus
    assert _upload(admin, main, "import/preview", b"x", name="notes.txt").status_code == 422
    no_level = b"Name,Code\nEngineering,E1\n"
    missing = _upload(admin, main, "import/preview", no_level)
    assert missing.status_code == 422
    assert "Missing column" in missing.json()["detail"]
    fake = _upload(admin, main, "import/preview", b"not a workbook", name="entries.xlsx")
    assert fake.status_code == 422


def test_export_and_import_follow_permissions(campus, signed_in, grant):
    _, main = campus
    regular = signed_in()

    assert regular.get(_url(main, "export")).status_code == 403
    assert regular.get("/api/v1/org/import-template").status_code == 403

    grant(regular.user, "org.node.view")
    grant(regular.user, "org.node.export")
    assert regular.get(_url(main, "export")).status_code == 200
    assert regular.get("/api/v1/org/import-template").status_code == 200
    assert _upload(regular, main, "import/preview", FULL_FILE).status_code == 403
    assert _upload(regular, main, "import", FULL_FILE).status_code == 403


def test_the_import_template_has_the_expected_columns(campus, admin):
    as_xlsx = admin.get("/api/v1/org/import-template", params={"format": "xlsx"})
    sheet = load_workbook(io.BytesIO(as_xlsx.content)).active
    assert [cell.value for cell in sheet[1]] == ["Level", "Name", "Code", "Parent"]

    as_csv = admin.get("/api/v1/org/import-template", params={"format": "csv"})
    assert as_csv.content.decode("utf-8-sig").splitlines()[0] == HEADER