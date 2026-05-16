"""Initial seed data — runs only when DB is empty."""
from datetime import date
from decimal import Decimal
from sqlalchemy.orm import Session

from .core.security import hash_password, encrypt
from .models.user import User
from .models.org import Organisation, FinancialYear
from .models.employee import Department, Designation, Employee, EmployeeBankDetail
from .models.salary import SalaryStructure
from .models.statutory import (
    EPFSetting, ESISetting, PTStateSetting, LWFSetting, TDSSetting, MinimumWageSetting
)


NCH_TEACHING_DEPARTMENTS = [
    ("Organon of Medicine and Homoeopathic Philosophy", "Foundational subject covering principles per Organon"),
    ("Materia Medica", "Drug knowledge — Hahnemannian and contemporary"),
    ("Repertory", "Use of repertories for case analysis"),
    ("Practice of Medicine (Homoeopathic)", "Clinical practice of homoeopathy"),
    ("Surgery and Allied Subjects", "General surgery and allied clinical disciplines"),
    ("Obstetrics and Gynaecology", "Maternal health & women's diseases"),
    ("Community Medicine (Preventive and Social Medicine)", "Public health & community programmes"),
    ("Anatomy", "Human anatomy"),
    ("Physiology and Biochemistry", "Body function & biochemical processes"),
    ("Pathology and Microbiology", "Disease processes & microbial pathology"),
    ("Forensic Medicine and Toxicology", "Medico-legal and poison studies"),
    ("Pharmacy (Homoeopathic)", "Drug preparation per HPI"),
]

NCH_NON_TEACHING = [
    ("Administration", ""),
    ("Accounts and Finance", ""),
    ("Library", ""),
    ("Hospital / OPD / IPD / Emergency / Pharmacy Counter", ""),
    ("Security", ""),
    ("Non-Teaching Academic Support", ""),
    ("Housekeeping and Sanitation", ""),
    ("IT and Technical Support", ""),
    ("Store and Purchase", ""),
    ("Transport", ""),
]

DESIGNATIONS = [
    ("Principal", "Teaching", True, "HIGHLY_SKILLED"),
    ("Professor", "Teaching", True, "HIGHLY_SKILLED"),
    ("HOD", "Teaching", True, "HIGHLY_SKILLED"),
    ("Associate Professor", "Teaching", True, "HIGHLY_SKILLED"),
    ("Assistant Professor", "Teaching", True, "SKILLED"),
    ("Demonstrator/Tutor/Lecturer", "Teaching", True, "SKILLED"),
    ("Medical Officer", "Clinical", False, "SKILLED"),
    ("Resident Doctor", "Clinical", False, "SKILLED"),
    ("Pharmacist (Homoeopathic)", "Pharmacy", False, "SEMI_SKILLED"),
    ("Lab Technician", "Lab", False, "SEMI_SKILLED"),
    ("Pathologist", "Lab", False, "SKILLED"),
    ("Nursing Staff", "Clinical", False, "SEMI_SKILLED"),
    ("Para-Medical", "Clinical", False, "SEMI_SKILLED"),
    ("Administrative Officer/Manager", "Admin", False, "SKILLED"),
    ("Accountant", "Accounts", False, "SKILLED"),
    ("Cashier", "Accounts", False, "SEMI_SKILLED"),
    ("Librarian", "Library", False, "SEMI_SKILLED"),
    ("Library Assistant", "Library", False, "UNSKILLED"),
    ("Security Guard", "Security", False, "UNSKILLED"),
    ("Security Supervisor", "Security", False, "SEMI_SKILLED"),
    ("Housekeeping Staff", "Housekeeping", False, "UNSKILLED"),
    ("Sanitation Worker", "Housekeeping", False, "UNSKILLED"),
    ("Peon/Attendant/Helper", "Support", False, "UNSKILLED"),
    ("Driver", "Transport", False, "SEMI_SKILLED"),
    ("Computer Operator", "IT", False, "SEMI_SKILLED"),
    ("Data Entry Operator", "IT", False, "SEMI_SKILLED"),
    ("Store Keeper", "Store", False, "SEMI_SKILLED"),
]


def _tax_slabs_new_fy25():
    return [
        {"upto": 300000, "rate": 0},
        {"upto": 700000, "rate": 5},
        {"upto": 1000000, "rate": 10},
        {"upto": 1200000, "rate": 15},
        {"upto": 1500000, "rate": 20},
        {"upto": 0, "rate": 30},  # 0 = no upper cap
    ]


def _tax_slabs_old_fy25():
    return [
        {"upto": 250000, "rate": 0},
        {"upto": 500000, "rate": 5},
        {"upto": 1000000, "rate": 20},
        {"upto": 0, "rate": 30},
    ]


def _surcharge_slabs():
    return [
        {"above": 50000000, "rate": 37},
        {"above": 20000000, "rate": 25},
        {"above": 10000000, "rate": 15},
        {"above": 5000000, "rate": 10},
    ]


def _pt_slabs_maharashtra():
    return [
        {"min": 0, "max": 7500, "amount": 0},
        {"min": 7501, "max": 10000, "amount": 175},
        {"min": 10001, "max": None, "amount": 200},  # 300 in Feb
    ]


def _pt_slabs_karnataka():
    return [
        {"min": 0, "max": 14999, "amount": 0},
        {"min": 15000, "max": None, "amount": 200},
    ]


def run(db: Session):
    # ---- Users ----
    admin = User(username="admin", email="admin@hmc.local", full_name="Super Administrator",
                 password_hash=hash_password("Admin@1234"), role="super_admin",
                 force_password_change=True)
    hr = User(username="hr", email="hr@hmc.local", full_name="HR Manager",
              password_hash=hash_password("Hr@1234"), role="hr_manager",
              force_password_change=True)
    payroll_exec = User(username="payroll", email="payroll@hmc.local", full_name="Payroll Executive",
                        password_hash=hash_password("Payroll@1234"), role="payroll_executive",
                        force_password_change=True)
    accounts = User(username="accounts", email="accounts@hmc.local", full_name="Accounts",
                    password_hash=hash_password("Accounts@1234"), role="accounts_user",
                    force_password_change=True)
    auditor = User(username="auditor", email="auditor@hmc.local", full_name="Auditor",
                   password_hash=hash_password("Auditor@1234"), role="auditor",
                   force_password_change=True)
    db.add_all([admin, hr, payroll_exec, accounts, auditor])

    # ---- Organisation ----
    org = Organisation(
        name="Homoeopathic Medical College & Hospital",
        pan="AAACH0000A", tan="ABCD12345E",
        epf_establishment_code="MHBAN0123456000",
        esi_establishment_code="31000123456000",
        address="College Campus, Sector 1",
        city="Mumbai", state_code="MH", pin="400001",
        city_tier="METRO",
        phone="022-12345678", email="info@hmc.local",
        nch_registration_no="NCH/REG/000",
    )
    db.add(org)

    # ---- Financial Years ----
    fy24 = FinancialYear(year_label="2023-24", start_date=date(2023, 4, 1),
                         end_date=date(2024, 3, 31), tax_year_label="AY 2024-25", is_active=False)
    fy25 = FinancialYear(year_label="2024-25", start_date=date(2024, 4, 1),
                         end_date=date(2025, 3, 31), tax_year_label="AY 2025-26", is_active=False)
    fy26 = FinancialYear(year_label="2025-26", start_date=date(2025, 4, 1),
                         end_date=date(2026, 3, 31), tax_year_label="AY 2026-27", is_active=True)
    db.add_all([fy24, fy25, fy26])
    db.flush()

    # ---- Departments ----
    dept_objs = {}
    for name, desc in NCH_TEACHING_DEPARTMENTS:
        d = Department(name=name, type="TEACHING", description=desc)
        db.add(d); dept_objs[name] = d
    for name, desc in NCH_NON_TEACHING:
        d = Department(name=name, type="NON_TEACHING", description=desc)
        db.add(d); dept_objs[name] = d
    db.flush()

    # ---- Designations ----
    desig_objs = {}
    for name, cat, is_teaching, mw_cat in DESIGNATIONS:
        d = Designation(name=name, category=cat, is_teaching=is_teaching,
                        min_wage_category=mw_cat)
        db.add(d); desig_objs[name] = d
    db.flush()

    # ---- EPF/ESI/TDS settings for each FY ----
    for fy in [fy24, fy25, fy26]:
        db.add(EPFSetting(financial_year_id=fy.id,
                          employee_rate=Decimal("12"), employer_rate=Decimal("12"),
                          eps_rate=Decimal("8.33"), eps_wage_ceiling=Decimal("15000"),
                          edli_rate=Decimal("0.5"), edli_wage_ceiling=Decimal("15000"),
                          admin_charge_rate=Decimal("0.5"),
                          pf_wage_ceiling=Decimal("15000"),
                          applicable_from=fy.start_date))
        db.add(ESISetting(financial_year_id=fy.id,
                          employee_rate=Decimal("0.75"), employer_rate=Decimal("3.25"),
                          wage_ceiling=Decimal("21000"),
                          applicable_from=fy.start_date))
        db.add(TDSSetting(financial_year_id=fy.id, tax_regime_default="NEW",
                          standard_deduction_old=Decimal("50000"),
                          standard_deduction_new=Decimal("75000"),
                          basic_exemption_old=Decimal("250000"),
                          basic_exemption_new=Decimal("300000"),
                          cess_rate=Decimal("4"),
                          tax_slabs_old=_tax_slabs_old_fy25(),
                          tax_slabs_new=_tax_slabs_new_fy25(),
                          surcharge_slabs=_surcharge_slabs(),
                          rebate_87a_limit_old=Decimal("500000"),
                          rebate_87a_amount_old=Decimal("12500"),
                          rebate_87a_limit_new=Decimal("700000"),
                          rebate_87a_amount_new=Decimal("25000")))
        # PT for major states
        db.add(PTStateSetting(state_code="MH", financial_year_id=fy.id,
                              slabs=_pt_slabs_maharashtra(), applicable_from=fy.start_date))
        db.add(PTStateSetting(state_code="KA", financial_year_id=fy.id,
                              slabs=_pt_slabs_karnataka(), applicable_from=fy.start_date))
        db.add(PTStateSetting(state_code="DL", financial_year_id=fy.id,
                              slabs=[{"min": 0, "max": None, "amount": 0}],
                              applicable_from=fy.start_date))
        # LWF
        db.add(LWFSetting(state_code="MH", financial_year_id=fy.id,
                          employee_amount=Decimal("25"), employer_amount=Decimal("75"),
                          periodicity="SEMI_ANNUAL", applicable_from=fy.start_date))
        # Minimum wage (illustrative, configurable)
        for skill, mw in [("UNSKILLED", 13000), ("SEMI_SKILLED", 15000),
                          ("SKILLED", 18000), ("HIGHLY_SKILLED", 22000)]:
            db.add(MinimumWageSetting(state_code="MH", financial_year_id=fy.id,
                                      category=skill, skill_level=skill,
                                      monthly_rate=Decimal(mw), daily_rate=Decimal(mw) / Decimal(26),
                                      applicable_from=fy.start_date))

    db.flush()

    # ---- Sample Employees ----
    samples = [
        ("HMC001", "Rajesh", "Sharma", "rajesh@hmc.local", "9876543210",
         "Principal", "Organon of Medicine and Homoeopathic Philosophy",
         Decimal(80000), Decimal(0), Decimal(40000), Decimal(2000), Decimal(15000)),
        ("HMC002", "Priya", "Iyer", "priya@hmc.local", "9876543211",
         "Professor", "Materia Medica",
         Decimal(60000), Decimal(0), Decimal(30000), Decimal(2000), Decimal(10000)),
        ("HMC003", "Anil", "Kumar", "anil@hmc.local", "9876543212",
         "Associate Professor", "Repertory",
         Decimal(45000), Decimal(0), Decimal(22500), Decimal(1500), Decimal(8000)),
        ("HMC004", "Sunita", "Patel", "sunita@hmc.local", "9876543213",
         "Assistant Professor", "Practice of Medicine (Homoeopathic)",
         Decimal(35000), Decimal(0), Decimal(17500), Decimal(1500), Decimal(6000)),
        ("HMC005", "Vikram", "Singh", "vikram@hmc.local", "9876543214",
         "Demonstrator/Tutor/Lecturer", "Anatomy",
         Decimal(25000), Decimal(0), Decimal(12500), Decimal(1000), Decimal(4000)),
        ("HMC006", "Meena", "Devi", "meena@hmc.local", "9876543215",
         "Accountant", "Accounts and Finance",
         Decimal(20000), Decimal(0), Decimal(8000), Decimal(1000), Decimal(3000)),
        ("HMC007", "Ramu", "Yadav", "ramu@hmc.local", "9876543216",
         "Security Guard", "Security",
         Decimal(9000), Decimal(2000), Decimal(3000), Decimal(800), Decimal(1500)),
        ("HMC008", "Lakshmi", "Bai", "lakshmi@hmc.local", "9876543217",
         "Housekeeping Staff", "Housekeeping and Sanitation",
         Decimal(8500), Decimal(2000), Decimal(2500), Decimal(800), Decimal(1000)),
    ]

    for emp_code, fn, ln, email, phone, desig_name, dept_name, basic, da, hra, conv, spec in samples:
        emp = Employee(
            emp_code=emp_code, first_name=fn, last_name=ln,
            email=email, phone=phone,
            dob=date(1980, 1, 1), gender="M" if emp_code.endswith(("1", "3", "5", "7")) else "F",
            marital_status="MARRIED",
            father_name="Father " + fn, address="Mumbai", state="Maharashtra",
            pan_encrypted=encrypt(f"ABCDE{emp_code[-3:]}F"),
            aadhaar_encrypted=encrypt(f"1234567890{emp_code[-2:]}"),
            uan=f"10001{emp_code[-5:]}", esi_ip_number=f"31000{emp_code[-5:]}",
            department_id=dept_objs[dept_name].id,
            designation_id=desig_objs[desig_name].id,
            date_of_joining=date(2022, 4, 1),
            employment_type="PERMANENT",
            city_tier="METRO", state_for_pt="MH",
            epf_applicable=True, esi_applicable=(basic + da + hra + conv + spec) <= Decimal(21000),
            pt_applicable=True, lwf_applicable=True, tds_applicable=True,
        )
        emp.bank_details.append(EmployeeBankDetail(
            account_number_encrypted=encrypt(f"123456789012{emp_code[-3:]}"),
            ifsc="HDFC0001234", bank_name="HDFC Bank", branch="Mumbai Main",
            is_primary=True,
        ))
        db.add(emp); db.flush()

        # Salary structure
        gross = basic + da + hra + conv + spec
        ss = SalaryStructure(
            employee_id=emp.id, financial_year_id=fy26.id,
            effective_from=date(2025, 4, 1),
            basic=basic, da=da, hra=hra,
            conveyance_allowance=conv, special_allowance=spec,
            gross_monthly=gross,
            status="ACTIVE", approved_by=admin.id,
        )
        db.add(ss)

    db.flush()
