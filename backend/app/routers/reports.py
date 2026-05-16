from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO

from ..database import get_db
from ..models.user import User
from ..core.permissions import require_permission, Permission
from ..services import report_service, pdf_service, excel_service
from ..services.audit_service import log_action

router = APIRouter(prefix="/reports", tags=["reports"])


def _stream(data: bytes, fname: str, format: str):
    if format == "xlsx":
        return StreamingResponse(BytesIO(data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={fname}.xlsx"})
    return StreamingResponse(BytesIO(data), media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={fname}.pdf"})


def _render(format: str, result):
    if not result:
        raise HTTPException(status_code=404, detail="No data")
    title, columns, rows, summary = result
    if format == "xlsx":
        return excel_service.generate_excel_report(title, columns, rows, summary=summary)
    org = None  # could pass in here
    return pdf_service.generate_simple_report_pdf(title, columns, rows, org=org, summary=summary)


@router.get("/month/payroll-summary")
def monthly_summary(payroll_month_id: int, format: str = "pdf",
                    db: Session = Depends(get_db),
                    current_user: User = Depends(require_permission(Permission.REPORT_VIEW))):
    res = report_service.monthly_payroll_summary(db, payroll_month_id)
    data = _render(format, res)
    log_action(db, current_user, "REPORT_EXPORT", "MonthlyPayrollSummary", payroll_month_id,
               None, {"format": format})
    db.commit()
    return _stream(data, f"payroll_summary_{payroll_month_id}", format)


@router.get("/department/cost")
def department_cost(payroll_month_id: int, format: str = "pdf",
                    db: Session = Depends(get_db),
                    current_user: User = Depends(require_permission(Permission.REPORT_VIEW))):
    res = report_service.department_cost_report(db, payroll_month_id)
    data = _render(format, res)
    return _stream(data, f"department_cost_{payroll_month_id}", format)


@router.get("/month/bank-transfer")
def bank_transfer(payroll_month_id: int, format: str = "xlsx",
                  db: Session = Depends(get_db),
                  current_user: User = Depends(require_permission(Permission.REPORT_EXPORT))):
    res = report_service.bank_transfer_report(db, payroll_month_id)
    data = _render(format, res)
    return _stream(data, f"bank_transfer_{payroll_month_id}", format)


@router.get("/statutory/epf-ecr")
def epf_ecr(payroll_month_id: int, format: str = "xlsx",
            db: Session = Depends(get_db),
            current_user: User = Depends(require_permission(Permission.REPORT_EXPORT))):
    res = report_service.epf_ecr_report(db, payroll_month_id)
    data = _render(format, res)
    return _stream(data, f"epf_ecr_{payroll_month_id}", format)


@router.get("/statutory/esi")
def esi_report(payroll_month_id: int, format: str = "xlsx",
               db: Session = Depends(get_db),
               current_user: User = Depends(require_permission(Permission.REPORT_EXPORT))):
    res = report_service.esi_report(db, payroll_month_id)
    data = _render(format, res)
    return _stream(data, f"esi_{payroll_month_id}", format)


@router.get("/statutory/tds-monthly")
def tds_monthly(payroll_month_id: int, format: str = "pdf",
                db: Session = Depends(get_db),
                current_user: User = Depends(require_permission(Permission.REPORT_VIEW))):
    res = report_service.tds_monthly_report(db, payroll_month_id)
    data = _render(format, res)
    return _stream(data, f"tds_monthly_{payroll_month_id}", format)


@router.get("/employee/annual-statement")
def annual_statement(employee_id: int, fy_id: int, format: str = "pdf",
                     db: Session = Depends(get_db),
                     current_user: User = Depends(require_permission(Permission.REPORT_VIEW))):
    res = report_service.employee_annual_statement(db, employee_id, fy_id)
    data = _render(format, res)
    return _stream(data, f"annual_{employee_id}_{fy_id}", format)


# Catalog endpoint
@router.get("/catalog")
def report_catalog(current_user: User = Depends(require_permission(Permission.REPORT_VIEW))):
    return {
        "employee": [
            {"id": "annual-statement", "name": "Annual Salary Statement",
             "params": ["employee_id", "fy_id"]},
        ],
        "month": [
            {"id": "payroll-summary", "name": "Monthly Payroll Summary",
             "params": ["payroll_month_id"]},
            {"id": "bank-transfer", "name": "Bank Transfer File",
             "params": ["payroll_month_id"]},
        ],
        "department": [
            {"id": "cost", "name": "Department-wise Cost",
             "params": ["payroll_month_id"]},
        ],
        "statutory": [
            {"id": "epf-ecr", "name": "EPF Monthly Return (ECR)",
             "params": ["payroll_month_id"]},
            {"id": "esi", "name": "ESI Monthly",
             "params": ["payroll_month_id"]},
            {"id": "tds-monthly", "name": "TDS Monthly",
             "params": ["payroll_month_id"]},
        ],
    }
