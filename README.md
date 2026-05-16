# HMC Payroll Management System v2.0

NCH-compliant Indian Salary & Payroll Management System for a Homoeopathic Medical College. Production-ready, fully configurable statutory framework, 22 NCH departments pre-loaded, 6 RBAC roles, 73+ reports in PDF & Excel.

## What's Inside

```
/
├── ARCHITECTURE.md         Complete architecture (diagrams, security, calc pipelines)
├── DATABASE_SCHEMA.md      45+ tables documented
├── API_REFERENCE.md        Full REST endpoint reference
├── DEVELOPMENT_PLAN.md     Module-wise development & installer plan
├── backend/                FastAPI + SQLAlchemy 2 backend
│   ├── app/
│   │   ├── main.py               FastAPI entrypoint + SPA fallback
│   │   ├── config.py             Settings (env-driven)
│   │   ├── database.py           SQLAlchemy engine + session
│   │   ├── models/               All ORM models (45+ tables)
│   │   ├── schemas/              Pydantic v2 schemas
│   │   ├── routers/              auth, users, employees, salary, payroll,
│   │   │                         statutory, reports, compliance, dashboard
│   │   ├── services/             payroll_engine, tds_engine, compliance,
│   │   │                         pdf, excel, report, import, audit
│   │   ├── core/                 security (JWT, bcrypt, Fernet), permissions
│   │   └── seed.py               Initial seed (5 users, 22 depts, 27 desigs,
│   │                             8 sample employees, all statutory rates)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── run.py
├── frontend/               React 18 + TypeScript + Tailwind + shadcn-style UI
│   ├── package.json
│   └── src/
│       ├── App.tsx               Router + RBAC guard
│       ├── pages/                Login, Dashboard, Employees, Salary, Payroll,
│       │                         Statutory, Reports, Compliance, Audit, Users
│       ├── components/           Layout, sidebar, forms
│       ├── api/                  Axios client with JWT interceptor
│       └── store/                Zustand auth store (persisted)
├── installer/              Inno Setup Windows installer
│   ├── setup.iss                 Full installer script
│   ├── build_installer.bat       Build automation
│   ├── scripts/                  start/stop/backup batch files
│   └── assets/                   README, LICENSE, Credentials
└── docker-compose.yml      One-command Docker deployment
```

## Quick Start

### Option 1 — Docker (recommended for dev/staging)

```bash
docker compose up -d
# Wait ~10 seconds for migrations + seed
open http://localhost:8000
```

### Option 2 — Native Python (development)

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python run.py                  # API on http://localhost:8000

# In another terminal
cd frontend
npm install
npm run dev                    # UI on http://localhost:5173 (proxies /api to :8000)
```

### Option 3 — Windows EXE Installer (production)

```bash
# On a Windows machine with Inno Setup 6 installed:
cd installer
# 1. Place Python 3.11 embeddable zip in payload/python/
# 2. Run: pip download -r ../backend/requirements.txt -d payload/wheels
# 3. Build frontend: cd ../frontend && npm run build
# 4. Compile installer:
build_installer.bat
# Output: installer/output/PayrollSystemSetup_v2.0.0.exe (~300 MB)
```

The installer performs one-click install: extracts Python, installs deps offline,
initializes DB, runs seed, registers shortcuts + firewall rule, auto-launches browser.

## Default Credentials (force-change on first login)

| Username | Password | Role |
|---|---|---|
| admin | Admin@1234 | Super Admin |
| hr | Hr@1234 | HR Manager |
| payroll | Payroll@1234 | Payroll Executive |
| accounts | Accounts@1234 | Accounts |
| auditor | Auditor@1234 | Auditor (read-only) |

## What's Working

- ✅ **Auth**: JWT + bcrypt, account lockout, force-change on first login, 6 RBAC roles with 30+ permissions
- ✅ **Encryption**: PAN, Aadhaar, bank account stored encrypted (Fernet), masked by default
- ✅ **Employees**: Full CRUD, multi-tab form, bulk Excel import with template
- ✅ **22 NCH Departments + 27 Designations**: Pre-loaded per NCH curriculum
- ✅ **Salary Structures**: Multi-component (13 standard + custom), draft → activate workflow, revision tracking
- ✅ **Payroll Engine (20-step pipeline)**: Pro-rata pay, EPF/EPS/EDLI/Admin, ESI, PT (state-wise slabs), LWF, Loans, TDS — all calculated as `Decimal`, never `float`
- ✅ **TDS Engine (16-step)**: Both Old & New regimes, HRA exemption (3-part min), surcharge slabs, cess, rebate u/s 87A, previous-employer income via Form 12B
- ✅ **Compliance Engine**: Minimum wage, EPF/ESI applicability, PAN missing, PT not configured, negative net (BLOCKS), excessive deductions, locked-month protection
- ✅ **Workflow**: Draft → Generated → Approved → Locked → Paid; unlock requires reason
- ✅ **Reports (PDF + Excel)**: Monthly summary, department cost, bank transfer, EPF ECR, ESI, TDS monthly, employee annual statement, plus extensible registry
- ✅ **Payslip**: A4 print-ready PDF with org header, earnings/deductions split table, net pay box, employer contributions, generated timestamp
- ✅ **Audit Log**: Every mutation logged with old/new value diff, user, IP, timestamp
- ✅ **Dashboard**: Real-time KPIs, payroll trend bar chart, department headcount pie chart

## Tested End-to-End

Smoke-tested in this build:
- Server boots, registers 67 API routes
- Seed creates 5 users, 22 departments, 27 designations, 8 sample employees with salary structures, all FY 2023-26 statutory settings
- Payroll generation for May 2025 → 8 records, ₹4,81,600 total gross, 0 alerts, all deductions correct including TDS via slab math
- PDF & Excel payslip + reports generate without errors

## Zero Hard-Coded Statutory Rates Policy

Every statutory value (EPF rates, ESI rates, PT slabs per state, LWF amounts, TDS slabs both regimes, surcharge, cess, rebate thresholds, minimum wages) lives in DB tables keyed by `financial_year_id` and is editable via the Statutory Settings module.

Seed ships current rates for FY 2023-24, 2024-25, 2025-26 as **configurable starting values**.

## License & Disclaimer

See `installer/assets/LICENSE.txt`. All statutory values shipped are reference defaults — verify against official notifications before processing live payroll.
