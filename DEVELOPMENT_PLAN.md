# Development & Module Plan

## Modules & Priority

### Phase 1 — Foundation (CRITICAL)
1. Database schema + migrations
2. Auth (JWT, RBAC, 6 roles)
3. User management
4. Audit log middleware
5. Organisation + FY setup

### Phase 2 — Master Data (HIGH)
6. Departments (22 NCH-mapped)
7. Designations & employee categories
8. Employee master CRUD with encrypted PII
9. Bank details
10. Bulk import (employees)

### Phase 3 — Statutory Engine (HIGH)
11. EPF settings (FY-wise)
12. ESI settings (FY-wise)
13. PT state matrix
14. LWF state matrix
15. Minimum wage matrix
16. TDS settings (regime, slabs, surcharge, cess)

### Phase 4 — Salary (HIGH)
17. Salary structure builder
18. Custom allowances
19. Salary revisions
20. Employee tax declarations

### Phase 5 — Payroll Engine (CRITICAL)
21. Payroll month creation
22. Payroll generation (full 20-step calc)
23. TDS engine (16-step)
24. Preview / Approve / Lock / Unlock / Pay workflow
25. Compliance checks pre-generation

### Phase 6 — Loans & Reimbursements
26. Loan/advance management
27. Reimbursement claims
28. Attendance import

### Phase 7 — Reports (CRITICAL)
29. PDF payslip
30. Excel payslip
31. All 73+ reports (Employee, Month, Department, Statutory, Tax, Mgmt, Audit)
32. Bulk payslip ZIP
33. EPF ECR export, ESI return, TDS challan
34. Bank transfer file (NEFT/RTGS)

### Phase 8 — Compliance & Audit
35. Compliance alerts dashboard
36. Audit log viewer
37. Login history

### Phase 9 — Frontend
38. Login + force change password
39. Dashboard with KPIs
40. Employee module pages
41. Salary structure UI
42. Payroll workflow UI
43. Statutory settings UI
44. Reports hub
45. Compliance dashboard
46. Audit log viewer
47. Settings (org, users)

### Phase 10 — Packaging
48. Docker compose
49. Inno Setup installer
50. Backup/restore scripts
51. User manual PDF

## Installer Build Plan

**Tool**: Inno Setup 6 (Windows only — script in `installer/setup.iss`).

**Bundled in installer**:
- Python 3.11 embeddable zip (~15 MB)
- All pip wheels (~80 MB) pre-downloaded for offline install
- PostgreSQL 16 portable (~200 MB)
- Backend source code (~5 MB)
- Frontend built dist (~3 MB)
- Inno Setup compiled binary stub

**Build steps**:
1. On a Windows machine, install Inno Setup 6
2. Place all bundled assets in `installer/payload/`
3. Run `installer/build_installer.bat`
4. Output: `PayrollSystemSetup_v2.0.0.exe` (~300 MB)

**Install flow** (defined in setup.iss):
1. Welcome → License → Install path (default C:\PayrollSystem)
2. Extract Python embeddable → C:\PayrollSystem\python\
3. Extract PostgreSQL portable → C:\PayrollSystem\postgres\
4. Run `pip install` from bundled wheels (offline)
5. Initialize PostgreSQL data directory + create DB
6. Run Alembic migrations
7. Run seed_data.py
8. Register Windows services (PayrollSystemPostgres, PayrollSystemBackend)
9. Create desktop + Start Menu shortcuts
10. Add firewall rule for port 8000
11. Place Help.pdf + Credentials.txt on desktop
12. Auto-launch browser to http://localhost:8000

## Tech Version Matrix
See ARCHITECTURE.md §2.
