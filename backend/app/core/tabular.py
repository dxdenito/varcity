import csv
import io
from itertools import islice

from fpdf import FPDF
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_ROWS = 5000
FORMULA_STARTS = ("=", "+", "-", "@", "\t", "\r")


class TableError(ValueError):
    pass


def _clean(value) -> str:
    return "" if value is None else str(value).strip()


def _read_csv(data: bytes) -> list[list]:
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = data.decode("cp1252", errors="replace")
    return list(islice(csv.reader(io.StringIO(text)), MAX_ROWS + 2))


def _read_xlsx(data: bytes) -> list[list]:
    try:
        workbook = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        sheet = workbook.active
        return [list(row) for row in islice(sheet.iter_rows(values_only=True), MAX_ROWS + 2)]
    except Exception:
        raise TableError("The file could not be read as an Excel workbook.")


def read_table(filename: str, data: bytes, required: list[str]) -> list[tuple[int, dict[str, str]]]:
    """Read a CSV or XLSX upload into (row number, {lowercase column: text}) pairs."""
    if len(data) > MAX_FILE_BYTES:
        raise TableError("The file is larger than 2 MB.")

    name = filename.lower()
    if name.endswith(".csv"):
        raw = _read_csv(data)
    elif name.endswith(".xlsx"):
        raw = _read_xlsx(data)
    else:
        raise TableError("Use a .csv or .xlsx file.")

    if not raw:
        raise TableError("The file is empty.")
    if len(raw) - 1 > MAX_ROWS:
        raise TableError(f"The file has more than {MAX_ROWS} rows.")

    header = [_clean(cell).lower() for cell in raw[0]]
    missing = [column for column in required if column.lower() not in header]
    if missing:
        raise TableError("Missing column(s): " + ", ".join(missing) + ".")

    rows = []
    for number, values in enumerate(raw[1:], start=2):
        record = {
            column: _clean(values[position]) if position < len(values) else ""
            for position, column in enumerate(header)
            if column
        }
        if any(record.values()):
            rows.append((number, record))

    if not rows:
        raise TableError("The file has no data rows.")
    return rows


def write_csv(headers: list[str], rows: list[list]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(
            ["'" + str(v) if str(v).startswith(FORMULA_STARTS) else str(v) for v in row]
        )
    return ("\ufeff" + buffer.getvalue()).encode("utf-8")


def write_xlsx(headers: list[str], rows: list[list], sheet_name: str = "Sheet1") -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = sheet_name[:31]
    sheet.append(list(headers))
    for cell in sheet[1]:
        cell.font = Font(bold=True)

    for row in rows:
        sheet.append([str(value) for value in row])
    for line in sheet.iter_rows(min_row=2):
        for cell in line:
            cell.data_type = "s"

    for position, header in enumerate(headers, start=1):
        sheet.column_dimensions[get_column_letter(position)].width = max(len(str(header)) + 4, 24)

    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def _latin(value) -> str:
    return str(value).encode("latin-1", "replace").decode("latin-1")


def write_pdf(title: str, headers: list[str], rows: list[list]) -> bytes:
    pdf = FPDF(orientation="L", format="A4")
    pdf.set_margins(12, 12, 12)
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, _latin(title), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=9)

    with pdf.table() as table:
        header_row = table.row()
        for header in headers:
            header_row.cell(_latin(header))
        for row in rows:
            table_row = table.row()
            for value in row:
                table_row.cell(_latin(value))

    return bytes(pdf.output())