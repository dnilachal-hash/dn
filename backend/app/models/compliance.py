from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base


class ComplianceAlert(Base):
    __tablename__ = "compliance_alerts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"), index=True)
    payroll_month_id: Mapped[int | None] = mapped_column(ForeignKey("payroll_months.id"), index=True)
    alert_type: Mapped[str] = mapped_column(String(60), index=True)
    severity: Mapped[str] = mapped_column(String(20), index=True)  # CRITICAL/WARNING/INFO
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    resolved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class ReportExportHistory(Base):
    __tablename__ = "report_export_history"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    report_type: Mapped[str] = mapped_column(String(80))
    parameters: Mapped[dict | None] = mapped_column(JSON)
    format: Mapped[str] = mapped_column(String(10))
    file_path: Mapped[str | None] = mapped_column(String(500))
    exported_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
