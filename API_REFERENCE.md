# REST API Reference

Base URL: `/api/v1` — All endpoints (except `/auth/login`) require `Authorization: Bearer <token>`.

## Auth
| Method | Path | Description |
|--------|------|-------------|
| POST | /auth/login | Login, returns access + refresh tokens |
| POST | /auth/refresh | Exchange refresh token for new access token |
| POST | /auth/logout | Invalidate session |
| POST | /auth/change-password | Change password (required on first login) |
| POST | /auth/forgot-password | Initiate password reset (Super Admin only) |
| GET | /auth/me | Current user profile + permissions |

## Users
| GET /users | List users |
| POST /users | Create user (Super Admin) |
| GET /users/{id} | Get user |
| PUT /users/{id} | Update user |
| DELETE /users/{id} | Soft-delete user |
| POST /users/{id}/reset-password | Reset password |
| GET /users/{id}/login-history | Login history |

## Departments
| GET /departments | List |
| POST /departments | Create |
| PUT /departments/{id} | Update |
| GET /departments/{id}/employees | Department roster |

## Employees
| GET /employees | Paginated list with filters |
| POST /employees | Create |
| GET /employees/{id} | Get with all details |
| PUT /employees/{id} | Update |
| DELETE /employees/{id} | Soft-delete (mark inactive) |
| POST /employees/import | Bulk Excel import |
| GET /employees/import/template | Download Excel template |
| GET /employees/{id}/payroll-history | All payroll records |
| GET /employees/{id}/salary-history | All structures |

## Salary Structures
| GET /salary-structures?employee_id= | List |
| POST /salary-structures | Create |
| GET /salary-structures/{id} | Get |
| PUT /salary-structures/{id} | Update (draft only) |
| POST /salary-structures/{id}/activate | Activate |
| POST /salary-structures/{id}/revise | Create revision |

## Payroll
| GET /payroll/months | List payroll months |
| POST /payroll/months | Create new payroll month |
| POST /payroll/months/{id}/generate | Generate all employee records |
| POST /payroll/months/{id}/preview | Preview without saving |
| POST /payroll/months/{id}/approve | Approve (HR Manager+) |
| POST /payroll/months/{id}/lock | Lock (Admin+) |
| POST /payroll/months/{id}/unlock | Unlock with reason |
| POST /payroll/months/{id}/mark-paid | Mark paid |
| GET /payroll/records/{id} | Single record |
| PUT /payroll/records/{id} | Edit (only if month is DRAFT/GENERATED) |
| GET /payroll/records/{id}/payslip | Stream PDF/Excel payslip |

## TDS
| GET /tds/settings | List by FY |
| POST /tds/settings | Create/update for FY |
| GET /tds/declarations/{employee_id}?fy_id= | Get declaration |
| POST /tds/declarations | Submit declaration |
| POST /tds/declarations/{id}/verify | Verify declaration |
| POST /tds/calculate/{employee_id}?month=&year= | Recalculate |
| GET /tds/projection/{employee_id}?fy_id= | Annual tax projection |

## Statutory Settings
| GET POST /statutory/epf | EPF settings |
| GET POST /statutory/esi | ESI settings |
| GET POST /statutory/pt | PT state settings |
| GET POST /statutory/lwf | LWF settings |
| GET POST /statutory/minimum-wage | Min wage matrix |

## Reports (73+)
Query: `?format=pdf|xlsx&fy_id=&month=&year=&department_id=&employee_id=`

**Employee-wise**: `/reports/employee/monthly`, `/annual-statement`, `/salary-history`, `/payslip-history`, `/deduction-history`, `/tax-projection`, `/pf-annual`, `/esi-annual`, `/ctc`, `/loan-statement`, `/fnf-statement`

**Month-wise**: `/reports/month/payroll-summary`, `/gross`, `/net`, `/taxable`, `/deductions`, `/employer-liability`, `/ctc`, `/bank-transfer`, `/status`

**Department-wise**: `/reports/department/gross`, `/net`, `/employer`, `/ctc`, `/headcount`, `/teaching-vs-non`

**Statutory**: `/reports/statutory/epf`, `/eps`, `/edli`, `/epf-admin`, `/epf-ecr`, `/esi`, `/esi-wage-register`, `/pt`, `/pt-challan`, `/lwf`, `/lwf-challan`, `/tds`, `/tds-challan`, `/bonus`, `/gratuity`, `/min-wage-compliance`, `/overtime`, `/wage-register`, `/deduction-register`

**Tax**: `/reports/tax/tds-monthly`, `/annual-computation`, `/declaration`, `/proof-status`, `/hra-exemption`, `/form-16-data`, `/variance`, `/previous-employer`, `/regime-comparison`

**Management**: `/reports/mgmt/variance`, `/revisions`, `/arrears`, `/loan-recovery`, `/advances`, `/reimbursement`, `/ctc-analysis`, `/location-cost`, `/yoy`

**Audit**: `/reports/audit/salary-edits`, `/payroll-generation`, `/approvals`, `/lock-unlock`, `/logins`, `/user-activity`, `/compliance-changes`, `/export-history`

## Compliance
| GET /compliance/alerts?severity= | List alerts |
| POST /compliance/check | Run checks on payroll month |
| POST /compliance/alerts/{id}/resolve | Mark resolved |

## Audit
| GET /audit/logs | Paginated audit trail |
| GET /audit/logs/export?format= | Export |

## Import
| POST /import/{entity} | entity: employees, salaries, attendance, historical-payroll, declarations |
| GET /import/{entity}/template | Excel template |

## Dashboard
| GET /dashboard/stats | KPIs |
| GET /dashboard/payroll-trend?months=12 | Trend data |
| GET /dashboard/department-headcount | Pie chart data |
