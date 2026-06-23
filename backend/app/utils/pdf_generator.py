from datetime import date
from pathlib import Path

from app.core.config import settings


def generate_report_pdf(
    title: str,
    data: dict,
    filename: str,
) -> str:
    try:
        from fpdf import FPDF
    except ImportError:
        simple = _simple_text_report(title, data, filename)
        return simple

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Generated: {date.today().isoformat()}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)

    for key, value in data.items():
        if isinstance(value, dict):
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, key.replace("_", " ").title(), new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 10)
            for k, v in _flatten(value).items():
                line = f"  {k}: {v}"
                pdf.cell(0, 5, line, new_x="LMARGIN", new_y="NEXT")
        else:
            label = key.replace("_", " ").title()
            pdf.cell(0, 5, f"{label}: {value}", new_x="LMARGIN", new_y="NEXT")

    pdf_dir = Path(settings.storage_local_path) / "reports"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    path = pdf_dir / filename
    pdf.output(str(path))
    return str(path)


def _simple_text_report(title: str, data: dict, filename: str) -> str:
    lines = [f"{title}", f"{'=' * len(title)}", f"Generated: {date.today().isoformat()}", ""]
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"\n{key.replace('_', ' ').title()}:")
            for k, v in _flatten(value).items():
                lines.append(f"  {k}: {v}")
        else:
            lines.append(f"{key.replace('_', ' ').title()}: {value}")

    pdf_dir = Path(settings.storage_local_path) / "reports"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    path = pdf_dir / filename.replace(".pdf", ".txt")
    path.write_text("\n".join(lines))
    return str(path)


def _flatten(d: dict, parent_key: str = "") -> dict:
    items: dict = {}
    for k, v in d.items():
        new_key = f"{parent_key}.{k}" if parent_key else k.replace("_", " ").title()
        if isinstance(v, dict):
            items.update(_flatten(v, new_key))
        else:
            items[new_key] = v
    return items
