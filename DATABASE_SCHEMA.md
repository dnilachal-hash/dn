# Database Schema — Payroll Management System

PostgreSQL 16. Money columns `NUMERIC(15,2)`. Percentages `NUMERIC(6,4)`. Timestamps `TIMESTAMPTZ`. JSON via `JSONB`.

## Core Tables

### organisations
| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL PK | |
| name | VARCHAR(255) NOT NULL | |
| logo_path | VARCHAR(500) | |
| pan | VARCHAR(10) | |
| tan | VARCHAR(10) | |
| epf_establishment_code | VARCHAR(20) | |
| esi_establishment_code | VARCHAR(20) | |
| gstin | VARCHAR(15) | |
| address | TEXT | |
| state_code | VARCHAR(2) | |
| city_tier | VARCHAR(20) | METRO/NON_METRO |
| financial_year_start_month | INT DEFAULT 4 | |
| created_at | TIMESTAMPTZ DEFAULT NOW() | |

### financial_years
| id | SERIAL PK |
| year_label | VARCHAR(10) UNIQUE | e.g., "2024-25" |
| start_date | DATE |
| end_date | DATE |
| tax_year_label | VARCHAR(10) | "AY 2025-26" |
| is_active | BOOLEAN |

### users
| id, username UNIQUE, email UNIQUE, password_hash, role, is_active, force_password_change, failed_login_attempts, locked_until, last_login, created_by FK, created_at |

### login_history
| id, user_id FK, login_at, ip_address, user_agent, success, failure_reason |

### audit_logs
| id, user_id FK, action, entity_type, entity_id, old_values JSONB, new_values JSONB, ip_address, timestamp |

## Department / Employee

### departments
| id, name, type (TEACHING/NON_TEACHING), description, is_active, created_at |

### designations
| id, name, department_id FK, category, is_teaching, min_wage_category, is_active |

### employees
| id, emp_code UNIQUE, first_name, last_name, full_name (generated), email, phone, dob, gender, marital_status, father_name, mother_name, spouse_name, address, state, pan_encrypted, aadhaar_encrypted, uan, esi_ip_number, department_id FK, designation_id FK, date_of_joining, date_of_exit, employment_type, is_active, epf_applicable BOOLEAN, esi_applicable BOOLEAN, pt_applicable BOOLEAN, lwf_applicable BOOLEAN, tds_applicable BOOLEAN, city_tier, state_for_pt, photo_path, created_at, updated_at |

### employee_bank_details
| id, employee_id FK, account_number_encrypted, ifsc, bank_name, branch, is_primary |

## Salary

### salary_structures
| id, employee_id FK, financial_year_id FK, effective_from, effective_to, basic, da, hra, medical_allowance, conveyance_allowance, transport_allowance, special_allowance, other_allowance, children_education_allowance, uniform_allowance, telephone_allowance, internet_allowance, research_allowance, gross_monthly, pf_wage_override, status (DRAFT/ACTIVE/EXPIRED), created_by, approved_by, approved_at |

### custom_allowances
| id, salary_structure_id FK, name, amount, is_taxable, is_pf_eligible |

### salary_revisions
| id, employee_id FK, old_structure_id FK, new_structure_id FK, revision_date, reason, revised_by, approved_by |

## Payroll

### payroll_months
| id, financial_year_id FK, month INT, year INT, status (DRAFT/GENERATED/APPROVED/LOCKED/PAID), working_days, generated_at, generated_by, approved_at, approved_by, locked_at, locked_by, unlock_reason, remarks |
| UNIQUE (financial_year_id, month, year) |

### payroll_records
| id, payroll_month_id FK, employee_id FK, salary_structure_id FK, working_days, paid_days, lop_days, is_new_joiner, is_exit_month, basic, da, hra, medical_allowance, conveyance_allowance, transport_allowance, special_allowance, other_allowance, children_education_allowance, uniform_allowance, telephone_allowance, internet_allowance, research_allowance, overtime_pay, bonus, arrears, reimbursement, gross_salary, pf_wage, epf_employee, esi_wage, esi_employee, tds, professional_tax, lwf_employee, loan_emi, advance_recovery, other_deductions, total_deductions, net_salary, epf_employer, eps, edli, epf_admin, esi_employer, lwf_employer, gratuity_provision, bonus_provision, employer_total, ctc, status, payment_status, payment_date, payment_reference, remarks, data_source (LIVE/IMPORTED), created_at |
| UNIQUE (payroll_month_id, employee_id) |

### payroll_custom_components
| id, payroll_record_id FK, name, amount, type (EARNING/DEDUCTION), is_taxable |

## TDS

### tds_settings
| id, financial_year_id FK, tax_regime_default, standard_deduction_old, standard_deduction_new, basic_exemption_old, basic_exemption_new, cess_rate, tax_slabs_old JSONB, tax_slabs_new JSONB, surcharge_slabs JSONB, rebate_87a_limit_old, rebate_87a_amount_old, rebate_87a_limit_new, rebate_87a_amount_new |

### employee_tax_declarations
| id, employee_id FK, financial_year_id FK, tax_regime, hra_rent_paid, hra_city_tier, sec_80c, sec_80d, sec_80g, sec_80e, nps_80ccd1b, other_deductions JSONB, previous_employer_income, previous_employer_tds, form_12b_received, declaration_submitted_at, verified_by, verified_at |

### tds_calculations
| id, payroll_record_id FK, employee_id FK, financial_year_id FK, month, year, projected_annual_gross, hra_exemption, standard_deduction, chapter_via_deduction, taxable_income, tax_old_regime, tax_new_regime, tax_regime_applied, surcharge, cess, rebate, annual_tax, tds_to_date, remaining_months, monthly_tds, created_at |

## Statutory

### epf_settings
| id, financial_year_id FK, employee_rate, employer_rate, eps_rate, eps_wage_ceiling, edli_rate, edli_wage_ceiling, admin_charge_rate, pf_wage_ceiling, voluntary_pf_allowed, applicable_from |

### esi_settings
| id, financial_year_id FK, employee_rate, employer_rate, wage_ceiling, applicable_from |

### pt_state_settings
| id, state_code, financial_year_id FK, slabs JSONB, periodicity, applicable_from |

### lwf_settings
| id, state_code, financial_year_id FK, employee_amount, employer_amount, periodicity, applicable_from |

### minimum_wage_settings
| id, state_code, financial_year_id FK, category, skill_level, daily_rate, monthly_rate, applicable_from |

## Loans / Compliance / Misc

### employee_loans
| id, employee_id FK, loan_type, principal_amount, emi_amount, interest_rate, start_month, start_year, total_installments, paid_installments, outstanding_balance, status, sanctioned_by, sanctioned_at |

### loan_transactions
| id, loan_id FK, payroll_record_id FK, month, year, emi_deducted, outstanding_after |

### compliance_alerts
| id, employee_id FK NULL, payroll_month_id FK NULL, alert_type, severity, message, is_resolved, resolved_by, resolved_at, created_at |

### report_export_history
| id, user_id FK, report_type, parameters JSONB, format, file_path, exported_at |

### attendance_records
| id, employee_id FK, month, year, working_days, present_days, lop_days, overtime_hours, leave_paid, leave_unpaid |

### reimbursement_claims
| id, employee_id FK, claim_date, category, amount, status, approved_by, payroll_record_id FK NULL |

## Indexes
- employees(emp_code, department_id, is_active)
- payroll_records(payroll_month_id, employee_id)
- audit_logs(user_id, timestamp)
- tds_calculations(employee_id, financial_year_id, month, year)
- compliance_alerts(severity, is_resolved)
