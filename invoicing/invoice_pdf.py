from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date
from pathlib import Path
import sys
from typing import Iterable, TYPE_CHECKING

try:
    from reportlab.lib.pagesizes import letter as rl_letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch as rl_inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib import colors as rl_colors
    _REPORTLAB_OK = True
except Exception:
    _REPORTLAB_OK = False

from invoicing.invoice_generator import PdfInvoiceData, build_pdf_invoice_data
from core.config import PDF_TEXT, PDF_HEADERS, PDF_COLORS, PDF_FONTS, PDF_LAYOUT

if TYPE_CHECKING:
    from data.database_service import DatabaseService
from core.app_logging import trace


@dataclass
class PdfGenerationResult:
    """Result of PDF generation operation."""
    success: bool
    message: str
    file_path: str | None = None
    error: Exception | None = None


@trace
def reportlab_available() -> bool:
    return _REPORTLAB_OK


@trace
def generate_customer_invoice_pdf(
    db: "DatabaseService",
    customer_id: int,
    file_path: str,
    as_of_date: date | None = None,
    payments_limit: int = 5
) -> PdfGenerationResult:
    """
    Generate a PDF invoice for a customer.
    
    This is the high-level orchestration function that:
    1. Checks if reportlab is available
    2. Builds invoice data from the database
    3. Renders the PDF to the specified file path
    
    Args:
        db: Database service instance
        customer_id: ID of the customer to generate invoice for
        file_path: Path where PDF should be saved
        as_of_date: Date to calculate invoice as of (defaults to today)
        payments_limit: Number of recent payments to include
        
    Returns:
        PdfGenerationResult with success status and message
    """
    # Check reportlab availability
    if not _REPORTLAB_OK:
        return PdfGenerationResult(
            success=False,
            message="reportlab is required to generate PDFs.\nInstall with: pip install reportlab"
        )
    
    # Use today's date if not specified
    if as_of_date is None:
        as_of_date = datetime.now().date()
    
    # Build invoice data
    invoice_data = build_pdf_invoice_data(db, customer_id, as_of_date, payments_limit)
    if not invoice_data:
        return PdfGenerationResult(
            success=False,
            message=f"Customer ID {customer_id} not found."
        )
    
    # Render PDF
    try:
        render_invoice_pdf(file_path, invoice_data)
        return PdfGenerationResult(
            success=True,
            message=f"Invoice PDF saved successfully.",
            file_path=file_path
        )
    except Exception as e:
        return PdfGenerationResult(
            success=False,
            message=f"Could not generate PDF: {str(e)}",
            error=e
        )


@trace
def get_default_invoice_filename(customer_name: str) -> str:
    """
    Generate a default filename for a customer invoice PDF.
    
    Args:
        customer_name: Name of the customer
        
    Returns:
        Formatted filename with timestamp
    """
    safe_name = customer_name.replace(' ', '_')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"invoice_{safe_name}_{timestamp}.pdf"


def _resolve_logo_path() -> Path | None:
    candidates: list[Path] = []

    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base_dir = Path(getattr(sys, "_MEIPASS"))
        candidates.extend(
            [
                base_dir / "app" / "logo.png",
                base_dir / "logo.png",
            ]
        )
    else:
        module_dir = Path(__file__).resolve().parent
        project_root = module_dir.parent
        candidates.extend(
            [
                project_root / "app" / "logo.png",
                module_dir / "app" / "logo.png",
                Path.cwd() / "app" / "logo.png",
            ]
        )

    for logo_path in candidates:
        if logo_path.exists():
            return logo_path
    return None


def _build_contracts_table(invoice_data: PdfInvoiceData) -> Table:
    table_data = [PDF_HEADERS["contracts"]]
    for contract_line in invoice_data.contracts:
        table_data.append(
            [
                str(contract_line.contract_id),
                contract_line.scope,
                f"${contract_line.monthly_rate:.2f}",
                contract_line.start_date,
                contract_line.end_date or PDF_TEXT["dash"],
                f"${contract_line.expected:.2f}",
                f"${contract_line.paid:.2f}",
                f"${contract_line.outstanding:.2f}",
            ]
        )

    table = Table(
        table_data,
        colWidths=[w * rl_inch for w in PDF_LAYOUT["contracts_col_widths"]],
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), rl_colors.HexColor(PDF_COLORS["contracts_header_bg"])),
                ("TEXTCOLOR", (0, 0), (-1, 0), rl_colors.HexColor(PDF_COLORS["header_text"])),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), PDF_FONTS["table_header_size"]),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, rl_colors.HexColor(PDF_COLORS["grid"])),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [rl_colors.white, rl_colors.HexColor(PDF_COLORS["row_alt"])]),
            ]
        )
    )
    return table


def _build_summary_table(invoice_data: PdfInvoiceData) -> Table:
    # Format the Total Outstanding label with as-of date
    outstanding_label = f"{PDF_HEADERS['summary'][2]} ({PDF_TEXT['outstanding_as_of']} {invoice_data.as_of_date.isoformat()})"
    
    summary_data = [
        [PDF_HEADERS["summary"][0], f"${invoice_data.total_expected:.2f}"],
        [PDF_HEADERS["summary"][1], f"${invoice_data.total_paid:.2f}"],
        [outstanding_label, f"${invoice_data.total_outstanding:.2f}"],
        [
            PDF_HEADERS["summary"][3],
            invoice_data.next_due_date.isoformat() if invoice_data.next_due_date else PDF_TEXT["dash"],
        ],
    ]
    summary_table = Table(summary_data, colWidths=[w * rl_inch for w in PDF_LAYOUT["summary_col_widths"]])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), rl_colors.HexColor(PDF_COLORS["summary_bg"])),
                ("BACKGROUND", (0, 2), (-1, 2), rl_colors.HexColor(PDF_COLORS["summary_outstanding_bg"])),
                ("TEXTCOLOR", (0, 0), (-1, -1), rl_colors.HexColor(PDF_COLORS["summary_text"])),
                ("TEXTCOLOR", (1, 2), (1, 2), rl_colors.HexColor(PDF_COLORS["summary_outstanding"])),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), PDF_FONTS["table_body_size"]),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("BOX", (0, 0), (-1, -1), 0.5, rl_colors.HexColor(PDF_COLORS["summary_border"])),
            ]
        )
    )
    return summary_table


def _build_payments_table(payments: Iterable) -> Table:
    payments_table = [PDF_HEADERS["payments"]]
    for payment in payments:
        ref_notes = " | ".join(filter(None, [payment.reference, payment.notes]))
        contract_label = f"#{payment.contract_id}"
        if getattr(payment, "plate", ""):
            contract_label = f"{contract_label} ({payment.plate})"
        payments_table.append(
            [
                payment.paid_at[:10],
                f"${payment.amount:.2f}",
                payment.method,
                contract_label,
                ref_notes or PDF_TEXT["dash"],
            ]
        )

    table = Table(
        payments_table,
        colWidths=[w * rl_inch for w in PDF_LAYOUT["payments_col_widths"]],
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), rl_colors.HexColor(PDF_COLORS["payments_header_bg"])),
                ("TEXTCOLOR", (0, 0), (-1, 0), rl_colors.HexColor(PDF_COLORS["header_text"])),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), PDF_FONTS["table_header_size"]),
                ("GRID", (0, 0), (-1, -1), 0.5, rl_colors.HexColor(PDF_COLORS["grid"])),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [rl_colors.white, rl_colors.HexColor(PDF_COLORS["row_alt"])]),
            ]
        )
    )
    return table


@trace
def render_invoice_pdf(file_path: str, invoice_data: PdfInvoiceData) -> None:
    if not _REPORTLAB_OK:
        raise ImportError("reportlab is not available")

    doc = SimpleDocTemplate(
        file_path,
        pagesize=rl_letter,
        topMargin=PDF_LAYOUT["margin_top"] * rl_inch,
        bottomMargin=PDF_LAYOUT["margin_bottom"] * rl_inch,
        leftMargin=PDF_LAYOUT["margin_left"] * rl_inch,
        rightMargin=PDF_LAYOUT["margin_right"] * rl_inch,
    )
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=PDF_FONTS["title_size"],
        textColor=rl_colors.HexColor(PDF_COLORS["title"]),
        spaceAfter=6,
        fontName="Helvetica-Bold",
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=PDF_FONTS["subtitle_size"],
        textColor=rl_colors.HexColor(PDF_COLORS["subtitle"]),
        spaceAfter=10,
    )
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading3"],
        fontSize=PDF_FONTS["section_size"],
        textColor=rl_colors.HexColor(PDF_COLORS["section"]),
        spaceAfter=6,
    )

    logo_path = _resolve_logo_path()
    title_para = Paragraph(PDF_TEXT["title"], title_style)
    subtitle_para = Paragraph(
        f"{PDF_TEXT['subtitle_prefix']} • {invoice_data.as_of_date.strftime('%Y-%m-%d')}",
        subtitle_style,
    )

    if logo_path:
        logo_img = Image(str(logo_path), width=1.8 * rl_inch, height=1.8 * rl_inch)
        logo_img.hAlign = "RIGHT"
        header_table = Table(
            [[title_para, logo_img], [subtitle_para, ""]],
            colWidths=[5.0 * rl_inch, 1.8 * rl_inch],
        )
        header_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                    ("SPAN", (1, 0), (1, 1)),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        elements.append(header_table)
    else:
        elements.append(title_para)
        elements.append(subtitle_para)

    info_text = (
        f"<b>{PDF_TEXT['label_customer']}</b> {invoice_data.customer_name}<br/>"
        f"<b>{PDF_TEXT['label_phone']}</b> {invoice_data.phone or PDF_TEXT['dash']}<br/>"
        f"<b>{PDF_TEXT['label_company']}</b> {invoice_data.company or PDF_TEXT['dash']}<br/>"
        f"<b>{PDF_TEXT['label_invoice_uuid']}</b> {invoice_data.invoice_uuid}"
    )
    elements.append(Paragraph(info_text, styles["Normal"]))
    elements.append(Spacer(1, PDF_LAYOUT["section_spacer"] * rl_inch))

    if invoice_data.contracts:
        elements.append(Paragraph(PDF_TEXT["section_contracts"], section_style))
        elements.append(_build_contracts_table(invoice_data))
        elements.append(Spacer(1, PDF_LAYOUT["section_spacer"] * rl_inch))
        elements.append(_build_summary_table(invoice_data))
        elements.append(Spacer(1, PDF_LAYOUT["summary_spacer"] * rl_inch))

        if invoice_data.recent_payments:
            elements.append(Paragraph(PDF_TEXT["section_payments"], section_style))
            elements.append(_build_payments_table(invoice_data.recent_payments))
    else:
        elements.append(Paragraph(PDF_TEXT["no_contracts"], styles["Normal"]))

    elements.append(Spacer(1, PDF_LAYOUT["footer_spacer"] * rl_inch))
    footer_text = f"{PDF_TEXT['footer_prefix']} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    elements.append(
        Paragraph(
            footer_text,
            ParagraphStyle(
                "Footer",
                parent=styles["Normal"],
                fontSize=PDF_FONTS["footer_size"],
                textColor=rl_colors.HexColor(PDF_COLORS["footer"]),
                alignment=1,
            ),
        )
    )

    doc.build(elements)
