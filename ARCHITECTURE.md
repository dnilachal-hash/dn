# Homoeopathic Medical College — Payroll Management System
## Complete Architecture Document v2.0

---

## 1. SYSTEM OVERVIEW

A production-grade, NCH-compliant Indian Salary and Payroll Management System for a Homoeopathic Medical College. Designed for 50–500 employees across 22 teaching and non-teaching departments. Fully configurable statutory framework with no hard-coded rates.

### High-Level Layered Architecture

```
+--------------------------------------------------------------+
|                    PRESENTATION TIER                          |
|   React 18 + TypeScript + Tailwind + shadcn/ui (Vite SPA)     |
|   Pages: Login, Dashboard, Employees, Payroll, Salary,        |
|          TDS, Statutory, Reports, Compliance, Audit, Settings |
+----------------------------+---------------------------------+
                             |  HTTPS / JSON
                             |  JWT Bearer Token
+----------------------------v---------------------------------+
|                      API GATEWAY TIER                         |
|             FastAPI 0.111 (uvicorn ASGI server)               |
|   - Auth middleware (JWT + role validation)                   |
|   - Permission middleware (per-endpoint enforcement)          |
|   - Request validation (Pydantic v2)                          |
|   - Audit middleware (logs every mutation)                    |
|   - Rate limit middleware                                     |
+----------------------------+---------------------------------+
                             |
+----------------------------v---------------------------------+
|                   BUSINESS LOGIC TIER                         |
|   +------------------+  +--------------------+                |
|   | PayrollEngine    |  | TDSEngine          |                |
|   | - Pro-rata calc  |  | - Slab application |                |
|   | - EPF/ESI calc   |  | - HRA exemption    |                |
|   | - Custom comps   |  | - Regime compare   |                |
|   +------------------+  +--------------------+                |
|   +------------------+  +--------------------+                |
|   | ComplianceEngine |  | ReportEngine       |                |
|   | - Min wage check |  | - 73+ PDF reports  |                |
|   | - Alerts         |  | - 73+ Excel reports|                |
|   +------------------+  +--------------------+                |
|   +------------------+  +--------------------+                |
|   | ImportService    |  | AuditService       |                |
|   | - Bulk validate  |  | - Immutable log    |                |
|   +------------------+  +--------------------+                |
+----------------------------+---------------------------------+
                             |  SQLAlchemy 2.0 ORM
+----------------------------v---------------------------------+
|                     DATA TIER                                 |
|   PostgreSQL 16 (primary) / SQLite (dev fallback)             |
|   - 45+ relational tables, FK + indexes + check constraints   |
|   - NUMERIC(15,2) for money, NUMERIC(6,4) for percentages     |
|   - JSONB for tax slabs, PT slabs, audit diffs                |
|   - Encrypted columns for PAN, Aadhaar, bank account          |
+--------------------------------------------------------------+
```

---

## 2. TECHNOLOGY STACK (Pinned Versions)

| Layer       | Component           | Version   |
|-------------|---------------------|-----------|
| Backend     | Python              | 3.11.9    |
| Backend     | FastAPI             | 0.111.0   |
| Backend     | SQLAlchemy          | 2.0.30    |
| Backend     | Alembic             | 1.13.1    |
| Backend     | Pydantic            | 2.7.1     |
| Backend     | python-jose         | 3.3.0     |
| Backend     | passlib[bcrypt]     | 1.7.4     |
| Backend     | ReportLab           | 4.2.2     |
| Backend     | openpyxl            | 3.1.4     |
| Database    | PostgreSQL          | 16.3      |
| Frontend    | Node.js             | 20.13.1   |
| Frontend    | React               | 18.3.1    |
| Frontend    | TypeScript          | 5.4.5     |
| Frontend    | Vite                | 5.2.11    |
| Frontend    | Tailwind CSS        | 3.4.3     |
| Frontend    | @tanstack/react-query| 5.40.0   |
| Installer   | Inno Setup          | 6.2.2     |

---

## 3. SECURITY ARCHITECTURE

### Authentication
- **JWT** (HS256) with access (30 min) + refresh (7 days) tokens
- **bcrypt** password hashing (12 rounds)
- Force password change on first login
- Account lockout after 5 failed attempts (configurable)
- Session timeout after 30 min inactivity
- Login history with IP + user agent

### Authorization (RBAC)
Six roles with granular permission matrix:
| Role | Employees | Payroll | Approve | Lock | Settings | Audit |
|------|-----------|---------|---------|------|----------|-------|
| Super Admin | CRUD | CRUD | YES | YES | YES | RW |
| Admin | CRUD | CRUD | YES | YES | RO | RO |
| HR Manager | CRUD | RW | NO | NO | NO | RO |
| Payroll Exec | RO | RW | NO | NO | NO | NO |
| Accounts | RO | RO | NO | NO | NO | NO |
| Auditor | RO | RO | NO | NO | RO | RO |

### Data Protection
- PAN, Aadhaar, bank account stored with Fernet symmetric encryption
- Masked display by default (e.g., XXXXXX1234)
- TLS in transit (installer configures localhost cert)
- Audit log records every mutation with old/new value diff

---

## 4. PAYROLL CALCULATION ENGINE

Deterministic 20-step pipeline (`backend/app/services/payroll_service.py`):

```
1. Fetch active salary_structure for employee on payroll_month
2. Read working_days for month from calendar
3. paid_days = working_days - lop_days
4. Pro-rate all earning components by (paid_days / working_days)
5. PF_wage = (basic + da) capped at EPF wage ceiling (or override)
6. EPF_employee = PF_wage × epf_settings.employee_rate
7. EPF_employer = PF_wage × epf_settings.employer_rate
8. EPS = min(PF_wage × eps_rate, eps_wage_ceiling × eps_rate)
9. EPF_to_trust = EPF_employer - EPS
10. EDLI = min(PF_wage, edli_wage_ceiling) × edli_rate
11. EPF_admin = PF_wage × admin_charge_rate
12. ESI_wage = gross if (gross <= esi_ceiling) else 0
13. ESI_employee = ESI_wage × esi_settings.employee_rate
14. ESI_employer = ESI_wage × esi_settings.employer_rate
15. PT = lookup pt_state_settings.slabs for gross
16. LWF = lwf_settings.employee_amount (per periodicity)
17. TDS = call TDSEngine.calculate(employee, month, year)
18. total_deductions = sum(all employee deductions)
19. net_salary = gross - total_deductions  [ALERT if < 0]
20. CTC = gross + EPF_employer + EDLI + EPF_admin + ESI_employer + LWF_employer + provisions
```

All math uses `decimal.Decimal` with `ROUND_HALF_UP` quantize to 2 dp.

---

## 5. TDS CALCULATION ENGINE

16-step pipeline (`backend/app/services/tds_service.py`):

```
1. projected_gross = past_actual_gross + (current_gross × remaining_months)
2. add taxable perquisites + declared other income
3. HRA exemption = min(actual_hra, [50% or 40%] × (basic+da), rent - 10% × (basic+da))
4. subtract professional_tax paid in FY
5. subtract standard_deduction (regime-specific, from settings)
6. subtract Chapter VI-A (80C, 80D, etc. — old regime only)
7. taxable_income = projected - exemptions
8. apply tax_slabs (from tds_settings JSON, regime-specific)
9. add surcharge (slab-based from settings)
10. add cess (configurable, default 4%)
11. apply rebate u/s 87A (configurable threshold)
12. annual_tax_liability finalized
13. subtract tds_already_deducted_this_fy
14. subtract previous_employer_tds (from Form 12B)
15. remaining_tax / remaining_months = monthly_tds
16. persist to tds_calculations table
```

Regime selection: employee declaration → fallback to system default.

---

## 6. COMPLIANCE RULES ENGINE

Stateless evaluator (`backend/app/services/compliance_service.py`) runs on:
- Employee create/update
- Salary structure save
- Payroll generation
- On-demand via `/api/compliance/check`

Rule catalogue:
| Code | Severity | Message |
|------|----------|---------|
| MIN_WAGE_VIOLATION | CRITICAL | Basic below state minimum wage for category |
| EPF_NOT_ENABLED | WARNING | Salary < ₹15000 but EPF disabled |
| ESI_NOT_ENABLED | WARNING | Salary ≤ ₹21000 but ESI disabled |
| PAN_MISSING | CRITICAL | TDS applicable but PAN missing |
| PT_NOT_CONFIGURED | WARNING | PT applicable but state PT not configured |
| TDS_MISSED | WARNING | Taxable income but TDS = 0 |
| NEGATIVE_NET | CRITICAL | Net salary would be negative — BLOCKS payroll |
| EXCESS_DEDUCTION | WARNING | Deduction > 50% of gross |
| DUPLICATE_PAYROLL | CRITICAL | Payroll already generated for month — BLOCKS |
| MONTH_LOCKED | CRITICAL | Month is locked — BLOCKS |
| NO_SALARY_STRUCTURE | CRITICAL | No active structure — BLOCKS |
| EXIT_BEFORE_MONTH | CRITICAL | Exit date before payroll month — BLOCKS |

---

## 7. REPORT GENERATION PIPELINE

```
User → ReportsHub → /api/reports/{category}/{report_id}?format=pdf|xlsx
                       │
                       ├── ReportService.dispatch()
                       │     │
                       │     ├── DataQuery (SQLAlchemy)
                       │     ├── DataTransform (pandas)
                       │     └── Render
                       │         ├── PDF: ReportLab (A4, org header, page#)
                       │         └── XLSX: openpyxl (freeze panes, auto-filter)
                       │
                       └── ReportExportHistory log entry
                       └── Stream file to client
```

73+ report categories documented in `API_REFERENCE.md`.

---

## 8. DEPLOYMENT TOPOLOGY (Single-Machine Install)

```
Windows 10/11 host
 ├── C:\PayrollSystem\
 │    ├── python\          (embeddable Python 3.11)
 │    ├── postgres\        (portable PostgreSQL 16)
 │    ├── backend\         (FastAPI app)
 │    ├── frontend\dist\   (built static SPA, served by FastAPI)
 │    ├── data\            (db, uploads, reports, backups)
 │    └── start.bat        (launcher)
 ├── Windows Service: PayrollSystemBackend (uvicorn on :8000)
 ├── Windows Service: PayrollSystemPostgres
 └── Browser → http://localhost:8000
```

Inno Setup installer (`installer/setup.iss`) bundles everything, runs migrations + seed on first install, creates Windows services, opens browser.

---

## 9. ZERO HARD-CODED RATES POLICY

All statutory values live in DB tables keyed by `financial_year_id`:
- `epf_settings` — rates, ceilings
- `esi_settings` — rates, ceiling
- `pt_state_settings` — state-wise slab JSON
- `lwf_settings` — state-wise amounts
- `tds_settings` — slabs JSON for old + new regime
- `minimum_wage_settings` — state × category × skill level

Seed data ships current rates as **starting configurable values**. Admin must verify against official notifications.
