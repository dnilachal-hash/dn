"""PDF generation using ReportLab — payslips and all reports."""
from io import BytesIO
from decimal import Decimal
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

from ..models.payroll import PayrollRecord, PayrollMonth
from ..models.employee import Employee
from ..models.org import Organisation
from ..core.security import mask_pan, mask_aadhaar, decrypt


def _money(x) -> str:
    if x is None:
        return "0.00"
    return f"{Decimal(x):,.2f}"


def _month_name(m: int) -> str:
    return ["", "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"][m]


def _header(org: Organisation, title: str, styles):
    elems = []
    org_name = org.name if org else "Homoeopathic Medical College"
    elems.append(Paragraph(f"<b>{org_name}</b>", styles["org_name"]))
    if org:
        addr_lines = []
        if org.address:
            addr_lines.append(org.address)
        line2_parts = [p for p in [org.city, org.state_code, org.pin] if p]
        if line2_parts:
            addr_lines.append(", ".join(line2_parts))
        if org.phone or org.email:
            addr_lines.append(f"Phone: {org.phone or ''}  Email: {org.email or ''}")
        if org.pan or org.tan:
            addr_lines.append(f"PAN: {org.pan or '-'}   TAN: {org.tan or '-'}")
        for ln in addr_lines:
            elems.append(Paragraph(ln, styles["org_addr"]))
    elems.append(Spacer(1, 4 * mm))
    elems.append(Paragraph(f"<b>{title}</b>", styles["doc_title"]))
    elems.append(Spacer(1, 4 * mm))
    return elems


def _styles():
    base = getSampleStyleSheet()
    base.add(ParagraphStyle(name="org_name", parent=base["Title"], fontSize=14, alignment=TA_CENTER))
    base.add(ParagraphStyle(name="org_addr", parent=base["Normal"], fontSize=8, alignment=TA_CENTER))
    base.add(ParagraphStyle(name="doc_title", parent=base["Heading2"], fontSize=12, alignment=TA_CENTER,
                            textColor=colors.HexColor("#1f4e79")))
    base.add(ParagraphStyle(name="small", parent=base["Normal"], fontSize=8))
    base.add(ParagraphStyle(name="small_right", parent=base["Normal"], fontSize=8, alignment=TA_RIGHT))
    base.add(ParagraphStyle(name="footer", parent=base["Normal"], fontSize=7, alignment=TA_CENTER,
                            textColor=colors.gray))
    return base


def generate_payslip_pdf(org: Organisation, employee: Employee,
                          record: PayrollRecord, payroll_month: PayrollMonth) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=15 * mm, bottomMargin=15 * mm,
                            leftMargin=15 * mm, rightMargin=15 * mm)
    styles = _styles()
    elems = []
    title = f"Payslip for {_month_name(payroll_month.month)} {payroll_month.year}"
    elems.extend(_header(org, title, styles))

    # Employee details box
    full_name = f"{employee.first_name} {employee.last_name or ''}".strip()
    pan_disp = mask_pan(decrypt(employee.pan_encrypted)) or "-"
    dept = employee.department.name if employee.department else "-"
    desig = employee.designation.name if employee.designation else "-"

    emp_rows = [
        ["Employee Code:", employee.emp_code, "Date of Joining:",
         employee.date_of_joining.strftime("%d-%b-%Y") if employee.date_of_joining else "-"],
        ["Name:", full_name, "Department:", dept],
        ["Designation:", desig, "PAN:", pan_disp],
        ["UAN:", employee.uan or "-", "ESI IP:", employee.esi_ip_number or "-"],
        ["Working Days:", str(record.working_days), "Paid Days:", str(record.paid_days)],
        ["LOP Days:", str(record.lop_days), "Payment Status:", record.payment_status],
    ]
    t = Table(emp_rows, colWidths=[35 * mm, 55 * mm, 35 * mm, 55 * mm])
    t.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
        ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 9),
        ("FONT", (2, 0), (2, -1), "Helvetica-Bold", 9),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.whitesmoke, colors.white]),
    ]))
    elems.append(t)
    elems.append(Spacer(1, 6 * mm))

    # Earnings / Deductions tables
    earnings = [
        ("Basic", record.basic), ("DA", record.da), ("HRA", record.hra),
        ("Medical Allowance", record.medical_allowance),
        ("Conveyance Allowance", record.conveyance_allowance),
        ("Transport Allowance", record.transport_allowance),
        ("Special Allowance", record.special_allowance),
        ("Other Allowance", record.other_allowance),
        ("Children Education", record.children_education_allowance),
        ("Uniform Allowance", record.uniform_allowance),
        ("Telephone Allowance", record.telephone_allowance),
        ("Internet Allowance", record.internet_allowance),
        ("Research Allowance", record.research_allowance),
        ("Overtime", record.overtime_pay), ("Bonus", record.bonus),
        ("Arrears", record.arrears), ("Reimbursement", record.reimbursement),
    ]
    earnings = [(n, v) for n, v in earnings if v and Decimal(v) != 0]
    earnings.append(("GROSS EARNINGS", record.gross_salary))

    deductions = [
        ("EPF Employee (12%)", record.epf_employee),
        ("ESI Employee (0.75%)", record.esi_employee),
        ("TDS / Income Tax", record.tds),
        ("Professional Tax", record.professional_tax),
        ("LWF", record.lwf_employee),
        ("Loan EMI", record.loan_emi),
        ("Advance Recovery", record.advance_recovery),
        ("Other Deductions", record.other_deductions),
    ]
    deductions = [(n, v) for n, v in deductions if v and Decimal(v) != 0]
    deductions.append(("TOTAL DEDUCTIONS", record.total_deductions))

    # Pad to equal lengths
    while len(earnings) < len(deductions):
        earnings.insert(-1, ("", Decimal(0)))
    while len(deductions) < len(earnings):
        deductions.insert(-1, ("", Decimal(0)))

    table_rows = [["Earnings", "Amount (₹)", "Deductions", "Amount (₹)"]]
    for (en, ev), (dn, dv) in zip(earnings, deductions):
        table_rows.append([en, _money(ev) if en else "", dn, _money(dv) if dn else ""])

    t2 = Table(table_rows, colWidths=[55 * mm, 35 * mm, 55 * mm, 35 * mm])
    t2.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 10),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONT", (0, 1), (-1, -1), "Helvetica", 9),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("ALIGN", (3, 0), (3, -1), "RIGHT"),
        ("FONT", (0, -1), (-1, -1), "Helvetica-Bold", 9),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#dbe5f1")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
    ]))
    elems.append(t2)
    elems.append(Spacer(1, 4 * mm))

    # Net Pay
    net_box = [["NET PAY:", f"₹ {_money(record.net_salary)}"]]
    nb = Table(net_box, colWidths=[140 * mm, 40 * mm])
    nb.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica-Bold", 12),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#c6e0b4")),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("PAD", (0, 0), (-1, -1), 6),
    ]))
    elems.append(nb)
    elems.append(Spacer(1, 4 * mm))

    # Employer side
    elems.append(Paragraph("<b>Employer Contributions (CTC components)</b>", styles["small"]))
    er = [
        ["EPF Employer", _money(record.epf_employer)],
        ["EPS", _money(record.eps)],
        ["EDLI", _money(record.edli)],
        ["EPF Admin", _money(record.epf_admin)],
        ["ESI Employer", _money(record.esi_employer)],
        ["LWF Employer", _money(record.lwf_employer)],
        ["Gratuity Provision", _money(record.gratuity_provision)],
        ["Bonus Provision", _money(record.bonus_provision)],
        ["TOTAL EMPLOYER", _money(record.employer_total)],
        ["TOTAL CTC", _money(record.ctc)],
    ]
    et = Table(er, colWidths=[100 * mm, 80 * mm])
    et.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 8),
        ("FONT", (0, -2), (-1, -1), "Helvetica-Bold", 9),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
    ]))
    elems.append(et)
    elems.append(Spacer(1, 8 * mm))

    elems.append(Paragraph(
        "This is a system-generated payslip. No signature required. "
        f"Generated on: {datetime.now().strftime('%d-%b-%Y %H:%M')}",
        styles["footer"]))

    doc.build(elems)
    return buf.getvalue()


def generate_simple_report_pdf(title: str, columns: list[str], rows: list[list],
                                org: Organisation | None = None,
                                summary: dict | None = None) -> bytes:
    """Generic tabular PDF report."""
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=15 * mm, bottomMargin=15 * mm,
                            leftMargin=12 * mm, rightMargin=12 * mm)
    styles = _styles()
    elems = []
    elems.extend(_header(org, title, styles))

    if summary:
        srows = [[k, str(v)] for k, v in summary.items()]
        st = Table(srows, colWidths=[80 * mm, 80 * mm])
        st.setStyle(TableStyle([
            ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
            ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 9),
            ("BOX", (0, 0), (-1, -1), 0.25, colors.grey),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ]))
        elems.append(st)
        elems.append(Spacer(1, 4 * mm))

    data = [columns] + rows
    col_count = len(columns)
    col_widths = [(180 / col_count) * mm] * col_count
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONT", (0, 1), (-1, -1), "Helvetica", 8),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
    ]))
    elems.append(t)
    elems.append(Spacer(1, 6 * mm))
    elems.append(Paragraph(
        f"Generated on {datetime.now().strftime('%d-%b-%Y %H:%M')} | Page",
        styles["footer"]))
    doc.build(elems)
    return buf.getvalue()
