"""Compliance Rules Engine."""
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from ..models.employee import Employee
from ..models.salary import SalaryStructure
from ..models.statutory import MinimumWageSetting, EPFSetting, ESISetting, PTStateSetting
from ..models.compliance import ComplianceAlert


def check_employee(db: Session, employee: Employee, fy_id: int) -> list[ComplianceAlert]:
    alerts = []

    # PAN missing
    if employee.tds_applicable and not employee.pan_encrypted:
        alerts.append(ComplianceAlert(
            employee_id=employee.id, alert_type="PAN_MISSING", severity="CRITICAL",
            message=f"PAN missing for TDS-applicable employee {employee.emp_code}"))

    # State PT not configured
    if employee.pt_applicable and employee.state_for_pt:
        pt = db.scalar(select(PTStateSetting).where(
            and_(PTStateSetting.state_code == employee.state_for_pt,
                 PTStateSetting.financial_year_id == fy_id)))
        if not pt:
            alerts.append(ComplianceAlert(
                employee_id=employee.id, alert_type="PT_NOT_CONFIGURED", severity="WARNING",
                message=f"PT not configured for state {employee.state_for_pt}"))

    return alerts


def check_salary_structure(db: Session, structure: SalaryStructure, employee: Employee) -> list[ComplianceAlert]:
    alerts = []

    if employee.state_for_pt and employee.designation and employee.designation.min_wage_category:
        mw = db.scalar(select(MinimumWageSetting).where(
            and_(MinimumWageSetting.state_code == employee.state_for_pt,
                 MinimumWageSetting.financial_year_id == structure.financial_year_id,
                 MinimumWageSetting.category == employee.designation.min_wage_category)))
        if mw and Decimal(structure.basic) + Decimal(structure.da) < Decimal(mw.monthly_rate):
            alerts.append(ComplianceAlert(
                employee_id=employee.id, alert_type="MIN_WAGE_VIOLATION", severity="CRITICAL",
                message=f"Basic+DA ({structure.basic + structure.da}) < minimum wage {mw.monthly_rate}"))

    if employee.epf_applicable:
        epf = db.scalar(select(EPFSetting).where(EPFSetting.financial_year_id == structure.financial_year_id))
        if not epf:
            alerts.append(ComplianceAlert(
                employee_id=employee.id, alert_type="EPF_NOT_CONFIGURED", severity="CRITICAL",
                message="EPF settings missing for FY"))

    return alerts
