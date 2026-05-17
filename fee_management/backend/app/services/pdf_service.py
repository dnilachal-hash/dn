"""PDF generation using ReportLab."""
import io
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Optional, List, Any, Dict

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, PageBreak,
)
from reportlab.platypus.flowables import Flowable


# ──────────────────────────────────────────
# Styles
# ──────────────────────────────────────────

def _styles():
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle(
            "title", parent=base["Normal"],
            fontSize=16, fontName="Helvetica-Bold",
            alignment=TA_CENTER, spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "subtitle", parent=base["Normal"],
            fontSize=10, fontName="Helvetica",
            alignment=TA_CENTER, spaceAfter=2,
        ),
        "heading": ParagraphStyle(
            "heading", parent=base["Normal"],
            fontSize=13, fontName="Helvetica-Bold",
            alignment=TA_CENTER, spaceAfter=6, spaceBefore=6,
            textColor=colors.HexColor("#1a237e"),
        ),
        "label": ParagraphStyle(
            "label", parent=base["Normal"],
            fontSize=8, fontName="Helvetica-Bold",
        ),
        "value": ParagraphStyle(
            "value", parent=base["Normal"],
            fontSize=9, fontName="Helvetica",
        ),
        "small": ParagraphStyle(
            "small", parent=base["Normal"],
            fontSize=7, fontName="Helvetica",
            alignment=TA_CENTER,
        ),
        "footer": ParagraphStyle(
            "footer", parent=base["Normal"],
            fontSize=8, fontName="Helvetica",
            alignment=TA_CENTER, textColor=colors.grey,
        ),
        "watermark": ParagraphStyle(
            "watermark", parent=base["Normal"],
            fontSize=48, fontName="Helvetica-Bold",
            textColor=colors.Color(1, 0, 0, alpha=0.25),
            alignment=TA_CENTER,
        ),
        "normal": base["Normal"],
        "right": ParagraphStyle(
            "right", parent=base["Normal"],
            fontSize=9, fontName="Helvetica",
            alignment=TA_RIGHT,
        ),
    }
    return styles


# ──────────────────────────────────────────
# Receipt PDF
# ──────────────────────────────────────────

def _build_receipt_copy(receipt: Any, org: Any, copy_label: str, styles: dict) -> list:
    """Build flowable list for one receipt copy."""
    elements = []

    # Header
    org_name = getattr(org, "name", "College") if org else "College"
    org_addr = getattr(org, "address", "") or ""
    org_city = getattr(org, "city", "") or ""
    org_state = getattr(org, "state", "") or ""
    org_pin = getattr(org, "pin", "") or ""
    org_phone = getattr(org, "phone", "") or ""
    org_email = getattr(org, "email", "") or ""

    addr_line = ", ".join(filter(None, [org_addr, org_city, org_state, org_pin]))
    contact_line = " | ".join(filter(None, [
        f"Ph: {org_phone}" if org_phone else "",
        f"Email: {org_email}" if org_email else "",
    ]))
    receipt_header = getattr(org, "receipt_header", "") or ""

    elements.append(Paragraph(org_name, styles["title"]))
    if addr_line:
        elements.append(Paragraph(addr_line, styles["subtitle"]))
    if contact_line:
        elements.append(Paragraph(contact_line, styles["subtitle"]))
    if receipt_header:
        elements.append(Paragraph(receipt_header, styles["subtitle"]))

    elements.append(Spacer(1, 4))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1a237e")))
    elements.append(Spacer(1, 2))
    elements.append(Paragraph("FEE RECEIPT", styles["heading"]))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a237e")))
    elements.append(Spacer(1, 4))

    # Copy label
    copy_style = ParagraphStyle(
        "copylabel", fontSize=8, fontName="Helvetica-Bold",
        alignment=TA_RIGHT, textColor=colors.grey,
    )
    elements.append(Paragraph(f"[ {copy_label} ]", copy_style))

    # Receipt meta row
    r_date = receipt.receipt_date.strftime("%d/%m/%Y") if receipt.receipt_date else ""
    fy_name = ""
    if hasattr(receipt, "financial_year") and receipt.financial_year:
        fy_name = receipt.financial_year.name
    meta_data = [
        [Paragraph("<b>Receipt No:</b>", styles["label"]),
         Paragraph(str(receipt.receipt_number), styles["value"]),
         Paragraph("<b>Date:</b>", styles["label"]),
         Paragraph(r_date, styles["value"]),
         Paragraph("<b>F.Y.:</b>", styles["label"]),
         Paragraph(fy_name, styles["value"])],
    ]
    meta_table = Table(meta_data, colWidths=[25*mm, 35*mm, 15*mm, 30*mm, 15*mm, 30*mm])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f5f5f5")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 4))

    # Student info
    s_name = receipt.student_name or ""
    f_name = receipt.father_name or ""
    c_name = receipt.course_name or ""
    b_name = receipt.batch_name or ""
    sess_name = receipt.session_name or ""
    p_year = str(receipt.professional_year) if receipt.professional_year else ""
    roll = receipt.roll_number or ""
    adm_no = receipt.admission_number or ""

    student_data = [
        [Paragraph("<b>Student Name:</b>", styles["label"]),
         Paragraph(s_name, styles["value"]),
         Paragraph("<b>Father's Name:</b>", styles["label"]),
         Paragraph(f_name, styles["value"])],
        [Paragraph("<b>Course:</b>", styles["label"]),
         Paragraph(c_name, styles["value"]),
         Paragraph("<b>Batch:</b>", styles["label"]),
         Paragraph(b_name, styles["value"])],
        [Paragraph("<b>Session:</b>", styles["label"]),
         Paragraph(sess_name, styles["value"]),
         Paragraph("<b>Professional Year:</b>", styles["label"]),
         Paragraph(p_year, styles["value"])],
        [Paragraph("<b>Roll No:</b>", styles["label"]),
         Paragraph(roll, styles["value"]),
         Paragraph("<b>Admission No:</b>", styles["label"]),
         Paragraph(adm_no, styles["value"])],
    ]
    st_table = Table(student_data, colWidths=[32*mm, 58*mm, 38*mm, 42*mm])
    st_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e8eaf6")),
        ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#e8eaf6")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(st_table)
    elements.append(Spacer(1, 5))

    # Fee items table
    item_header = [
        Paragraph("<b>#</b>", styles["label"]),
        Paragraph("<b>Fee Head</b>", styles["label"]),
        Paragraph("<b>Amount (₹)</b>", styles["label"]),
    ]
    item_rows = [item_header]
    items = receipt.items if hasattr(receipt, "items") and receipt.items else []
    for idx, item in enumerate(items, 1):
        item_rows.append([
            Paragraph(str(idx), styles["value"]),
            Paragraph(str(item.fee_head_name), styles["value"]),
            Paragraph(f"{item.amount:,.2f}", styles["right"]),
        ])
    # Total row
    total = receipt.total_amount or Decimal("0")
    item_rows.append([
        Paragraph("", styles["label"]),
        Paragraph("<b>Total</b>", styles["label"]),
        Paragraph(f"<b>{total:,.2f}</b>", ParagraphStyle(
            "totalright", fontSize=10, fontName="Helvetica-Bold", alignment=TA_RIGHT,
        )),
    ])
    fee_table = Table(item_rows, colWidths=[12*mm, 120*mm, 38*mm])
    fee_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a237e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e3f2fd")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#fafafa")]),
    ]))
    elements.append(fee_table)
    elements.append(Spacer(1, 4))

    # Amount in words
    aiw = receipt.amount_in_words or ""
    elements.append(Paragraph(f"<b>Amount in Words:</b> {aiw}", styles["value"]))
    elements.append(Spacer(1, 3))

    # Payment details
    payments = receipt.payments if hasattr(receipt, "payments") and receipt.payments else []
    if payments:
        pmt_header = [
            Paragraph("<b>Mode</b>", styles["label"]),
            Paragraph("<b>Amount (₹)</b>", styles["label"]),
            Paragraph("<b>Reference</b>", styles["label"]),
            Paragraph("<b>Bank/Details</b>", styles["label"]),
        ]
        pmt_rows = [pmt_header]
        for pmt in payments:
            ref = pmt.reference_number or pmt.cheque_number or pmt.dd_number or pmt.transaction_id or ""
            bank = pmt.bank_name or ""
            if pmt.cheque_date:
                bank += f" {pmt.cheque_date.strftime('%d/%m/%Y')}"
            pmt_rows.append([
                Paragraph(str(pmt.payment_mode_name), styles["value"]),
                Paragraph(f"{pmt.amount:,.2f}", styles["right"]),
                Paragraph(ref, styles["value"]),
                Paragraph(bank, styles["value"]),
            ])
        pmt_table = Table(pmt_rows, colWidths=[28*mm, 30*mm, 50*mm, 62*mm])
        pmt_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#37474f")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(pmt_table)
        elements.append(Spacer(1, 4))

    # Remarks
    if receipt.remarks:
        elements.append(Paragraph(f"<b>Remarks:</b> {receipt.remarks}", styles["value"]))
        elements.append(Spacer(1, 3))

    # Signature row
    sig_data = [[
        Paragraph("", styles["value"]),
        Paragraph("<b>Collected by:</b><br/>" + (
            getattr(receipt.collector, "full_name", "") if hasattr(receipt, "collector") and receipt.collector else ""
        ), styles["value"]),
        Paragraph("<b>Authorised Signatory</b>", styles["label"]),
    ]]
    sig_table = Table(sig_data, colWidths=[50*mm, 70*mm, 50*mm])
    sig_table.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("ALIGN", (2, 0), (2, 0), "RIGHT"),
    ]))
    elements.append(sig_table)

    # Watermark for CANCELLED / CORRECTED
    status_val = receipt.status.value if hasattr(receipt.status, "value") else str(receipt.status)
    if status_val in ("CANCELLED", "CORRECTED"):
        elements.append(Spacer(1, 2))
        elements.append(Paragraph(status_val, styles["watermark"]))

    return elements


def generate_receipt_pdf(receipt: Any, org: Any = None) -> bytes:
    """Generate A4 PDF with student copy and office copy."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        rightMargin=15*mm, leftMargin=15*mm,
        topMargin=15*mm, bottomMargin=15*mm,
    )
    styles = _styles()
    elements = []

    # Student copy
    elements.extend(_build_receipt_copy(receipt, org, "STUDENT COPY", styles))
    elements.append(Spacer(1, 6))
    elements.append(HRFlowable(width="100%", thickness=1, dash=[3, 3], color=colors.grey))
    elements.append(Paragraph("✂ ─────────────────────────────────── ✂", styles["small"]))
    elements.append(HRFlowable(width="100%", thickness=1, dash=[3, 3], color=colors.grey))
    elements.append(Spacer(1, 6))

    # Office copy
    elements.extend(_build_receipt_copy(receipt, org, "OFFICE COPY", styles))

    doc.build(elements)
    return buf.getvalue()


# ──────────────────────────────────────────
# Generic report PDF
# ──────────────────────────────────────────

def generate_report_pdf(
    title: str,
    headers: List[str],
    rows: List[List[Any]],
    filters_desc: str = "",
) -> bytes:
    """Generate a generic A4 landscape table PDF."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=landscape(A4),
        rightMargin=15*mm, leftMargin=15*mm,
        topMargin=15*mm, bottomMargin=15*mm,
    )
    styles = _styles()
    elements = []

    elements.append(Paragraph(title, styles["heading"]))
    if filters_desc:
        elements.append(Paragraph(filters_desc, styles["subtitle"]))
    elements.append(Spacer(1, 4))

    header_row = [Paragraph(f"<b>{h}</b>", ParagraphStyle(
        "th", fontSize=8, fontName="Helvetica-Bold",
        textColor=colors.white, alignment=TA_CENTER,
    )) for h in headers]

    data = [header_row]
    for row in rows:
        data.append([Paragraph(str(cell) if cell is not None else "", styles["value"]) for cell in row])

    n_cols = len(headers)
    page_w = landscape(A4)[0] - 30*mm
    col_w = page_w / n_cols

    table = Table(data, colWidths=[col_w] * n_cols, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a237e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
    ]))
    elements.append(table)

    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        f"Generated on: {date.today().strftime('%d %B %Y')} | Total rows: {len(rows)}",
        styles["footer"],
    ))

    doc.build(elements)
    return buf.getvalue()
