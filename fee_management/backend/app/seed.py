"""Seed initial data for the Fee Management System."""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User, UserRole
from app.models.org import Organisation, FinancialYear, PaymentMode, ReceiptNumberingFormat, PaymentModeCode
from app.models.student import Course, Batch, AcademicSession, StudentCategory, Student
from app.models.fee import (
    FeeHead, FeeStructure, FeeStructureItem,
    StudentFeeAssignment, FeeType, FeeFrequency,
)
from app.models.receipt import Receipt, ReceiptItem, ReceiptPayment, ReceiptStatus


def run(db: Session):
    # ──────────────────────────────────────────
    # Organisation
    # ──────────────────────────────────────────
    org = Organisation(
        name="Homoeopathic Medical College & Hospital",
        address="College Road, Medical Campus",
        city="Kolkata",
        state="West Bengal",
        pin="700001",
        phone="033-22001234",
        email="info@hmchospital.edu.in",
        website="https://www.hmchospital.edu.in",
        receipt_header="Recognised by Central Council of Homoeopathy, Govt. of India",
        receipt_footer="This is a computer generated receipt. No signature required.",
        receipt_numbering_format=ReceiptNumberingFormat.PREFIXED,
    )
    db.add(org)
    db.flush()

    # ──────────────────────────────────────────
    # Users
    # ──────────────────────────────────────────
    users = [
        User(
            username="admin",
            full_name="System Administrator",
            email="admin@hmchospital.edu.in",
            password_hash=hash_password("Admin@1234"),
            role=UserRole.super_admin,
            is_active=True,
            force_password_change=True,
        ),
        User(
            username="accounts",
            full_name="Accounts User",
            email="accounts@hmchospital.edu.in",
            password_hash=hash_password("Accounts@1234"),
            role=UserRole.accounts_user,
            is_active=True,
            force_password_change=True,
        ),
        User(
            username="principal",
            full_name="Principal",
            email="principal@hmchospital.edu.in",
            password_hash=hash_password("Principal@1234"),
            role=UserRole.viewer,
            is_active=True,
            force_password_change=True,
        ),
        User(
            username="auditor",
            full_name="Auditor",
            email="auditor@hmchospital.edu.in",
            password_hash=hash_password("Auditor@1234"),
            role=UserRole.auditor,
            is_active=True,
            force_password_change=True,
        ),
    ]
    for u in users:
        db.add(u)
    db.flush()
    admin_user = users[0]

    # ──────────────────────────────────────────
    # Course: BHMS
    # ──────────────────────────────────────────
    bhms = Course(
        name="Bachelor of Homoeopathic Medicine and Surgery",
        code="BHMS",
        duration_years=5,
        is_active=True,
        description="5-year undergraduate program in Homoeopathic Medicine",
    )
    db.add(bhms)
    db.flush()

    # ──────────────────────────────────────────
    # Batches
    # ──────────────────────────────────────────
    batch_data = [
        (2020, 2025), (2021, 2026), (2022, 2027), (2023, 2028), (2024, 2029),
    ]
    batches = []
    for start, end in batch_data:
        b = Batch(
            course_id=bhms.id,
            name=f"{start}-{end}",
            start_year=start,
            end_year=end,
            is_active=True,
        )
        db.add(b)
        batches.append(b)
    db.flush()

    # ──────────────────────────────────────────
    # Academic Sessions
    # ──────────────────────────────────────────
    sessions = []
    session_data = [
        ("2023-2024", date(2023, 7, 1), date(2024, 6, 30), False),
        ("2024-2025", date(2024, 7, 1), date(2025, 6, 30), False),
        ("2025-2026", date(2025, 7, 1), date(2026, 6, 30), True),
    ]
    for name, start, end, active in session_data:
        s = AcademicSession(name=name, start_date=start, end_date=end, is_active=active)
        db.add(s)
        sessions.append(s)
    db.flush()

    # ──────────────────────────────────────────
    # Student Categories
    # ──────────────────────────────────────────
    cat_data = [
        ("General", "General category students"),
        ("OBC", "Other Backward Classes"),
        ("SC/ST", "Scheduled Caste / Scheduled Tribe"),
        ("EWS", "Economically Weaker Section"),
        ("Management Quota", "Management quota admissions"),
    ]
    categories = []
    for name, desc in cat_data:
        c = StudentCategory(name=name, description=desc, is_active=True)
        db.add(c)
        categories.append(c)
    db.flush()

    # ──────────────────────────────────────────
    # Financial Years
    # ──────────────────────────────────────────
    fy_data = [
        ("2023-2024", date(2023, 4, 1), date(2024, 3, 31), False, True),
        ("2024-2025", date(2024, 4, 1), date(2025, 3, 31), False, False),
        ("2025-2026", date(2025, 4, 1), date(2026, 3, 31), True, False),
    ]
    fys = []
    for name, start, end, active, locked in fy_data:
        fy = FinancialYear(
            name=name, start_date=start, end_date=end,
            is_active=active, is_locked=locked, next_receipt_number=1,
        )
        db.add(fy)
        fys.append(fy)
    db.flush()
    active_fy = fys[2]  # 2025-2026

    # ──────────────────────────────────────────
    # Payment Modes
    # ──────────────────────────────────────────
    pmode_data = [
        ("Cash", PaymentModeCode.CASH, False, False, False, 1),
        ("Bank Transfer", PaymentModeCode.BANK, True, True, True, 2),
        ("Cheque", PaymentModeCode.CHEQUE, True, True, True, 3),
        ("Demand Draft", PaymentModeCode.DD, True, True, True, 4),
        ("UPI", PaymentModeCode.UPI, True, False, False, 5),
        ("Card (Debit/Credit)", PaymentModeCode.CARD, True, False, False, 6),
        ("Other", PaymentModeCode.OTHER, False, False, False, 7),
    ]
    pmodes = []
    for name, code, req_ref, req_bank, req_date, sort in pmode_data:
        pm = PaymentMode(
            name=name, code=code, is_active=True, sort_order=sort,
            requires_reference=req_ref, requires_bank_name=req_bank, requires_date=req_date,
        )
        db.add(pm)
        pmodes.append(pm)
    db.flush()

    # ──────────────────────────────────────────
    # Fee Heads
    # ──────────────────────────────────────────
    fh_data = [
        ("Admission Fee", "ADM", FeeType.REGISTRATION, False, FeeFrequency.ONE_TIME, True, 1),
        ("Tuition Fee", "TUT", FeeType.TUITION, False, FeeFrequency.YEARLY, True, 2),
        ("Development Fee", "DEV", FeeType.MISC, False, FeeFrequency.YEARLY, True, 3),
        ("Examination Fee", "EXAM", FeeType.EXAM, False, FeeFrequency.YEARLY, True, 4),
        ("Library Fee", "LIB", FeeType.LIBRARY, False, FeeFrequency.YEARLY, True, 5),
        ("Lab Fee", "LAB", FeeType.LAB, False, FeeFrequency.YEARLY, True, 6),
        ("University Fee", "UNI", FeeType.MISC, False, FeeFrequency.YEARLY, True, 7),
        ("Registration Fee", "REG", FeeType.REGISTRATION, False, FeeFrequency.ONE_TIME, True, 8),
        ("Hostel Fee", "HST", FeeType.HOSTEL, False, FeeFrequency.YEARLY, False, 9),
        ("Mess Fee", "MESS", FeeType.HOSTEL, False, FeeFrequency.YEARLY, False, 10),
        ("Transport Fee", "TRN", FeeType.TRANSPORT, False, FeeFrequency.YEARLY, False, 11),
        ("Caution Money", "CAU", FeeType.MISC, True, FeeFrequency.ONE_TIME, False, 12),
        ("Identity Card Fee", "IDC", FeeType.MISC, False, FeeFrequency.ONE_TIME, True, 13),
        ("Sports Fee", "SPT", FeeType.MISC, False, FeeFrequency.YEARLY, True, 14),
        ("Miscellaneous Fee", "MISC", FeeType.MISC, False, FeeFrequency.CUSTOM, False, 15),
    ]
    fee_heads = []
    for name, code, ftype, refundable, freq, compulsory, sort in fh_data:
        fh = FeeHead(
            name=name, code=code, fee_type=ftype,
            is_refundable=refundable, frequency=freq,
            is_compulsory=compulsory, is_active=True, sort_order=sort,
        )
        db.add(fh)
        fee_heads.append(fh)
    db.flush()

    # ──────────────────────────────────────────
    # Fee Structure for BHMS 2025-2026
    # ──────────────────────────────────────────
    fs = FeeStructure(
        name="BHMS General Fee Structure 2025-2026",
        course_id=bhms.id,
        batch_id=batches[4].id,  # 2024-2029
        academic_session_id=sessions[2].id,  # 2025-2026
        financial_year_id=active_fy.id,
        is_active=True,
        is_frozen=False,
        created_by=admin_user.id,
    )
    db.add(fs)
    db.flush()

    # Fee amounts for BHMS
    fee_amounts = {
        "ADM": Decimal("5000.00"),
        "TUT": Decimal("50000.00"),
        "DEV": Decimal("10000.00"),
        "EXAM": Decimal("8000.00"),
        "LIB": Decimal("2000.00"),
        "LAB": Decimal("5000.00"),
        "UNI": Decimal("3000.00"),
        "REG": Decimal("2000.00"),
        "IDC": Decimal("500.00"),
        "SPT": Decimal("1000.00"),
    }

    for i, fh in enumerate(fee_heads):
        if fh.code in fee_amounts:
            fi = FeeStructureItem(
                fee_structure_id=fs.id,
                fee_head_id=fh.id,
                amount=fee_amounts[fh.code],
                is_compulsory=fh.is_compulsory,
                sort_order=i,
            )
            db.add(fi)
    db.flush()

    # ──────────────────────────────────────────
    # Sample Students (5)
    # ──────────────────────────────────────────
    student_data = [
        ("HMC-FEE-001", "Priya Sharma", "Ramesh Sharma", "F", date(2002, 5, 12), 1),
        ("HMC-FEE-002", "Rohit Verma", "Suresh Verma", "M", date(2001, 8, 22), 2),
        ("HMC-FEE-003", "Anita Das", "Bipin Das", "F", date(2002, 11, 3), 1),
        ("HMC-FEE-004", "Sanjay Gupta", "Mohan Gupta", "M", date(2000, 3, 15), 3),
        ("HMC-FEE-005", "Kavita Singh", "Ajay Singh", "F", date(2001, 7, 28), 1),
    ]

    students = []
    for i, (adm, name, father, gender, dob, prof_yr) in enumerate(student_data, 1):
        s = Student(
            admission_number=adm,
            student_name=name,
            father_name=father,
            gender=gender,
            dob=dob,
            category_id=categories[0].id,  # General
            course_id=bhms.id,
            batch_id=batches[4].id,  # 2024-2029
            academic_session_id=sessions[2].id,  # 2025-2026
            professional_year=prof_yr,
            roll_number=f"BHMS{2024}{i:03d}",
            admission_date=date(2024, 8, 1),
            student_status="ACTIVE",
            mobile=f"98765{i:05d}",
            email=f"student{i}@hmchospital.edu.in",
            created_by=admin_user.id,
        )
        db.add(s)
        students.append(s)
    db.flush()

    # Assign fee structure to all 5 students
    for s in students:
        asgn = StudentFeeAssignment(
            student_id=s.id,
            fee_structure_id=fs.id,
            financial_year_id=active_fy.id,
            assigned_by=admin_user.id,
            is_active=True,
        )
        db.add(asgn)
    db.flush()

    # ──────────────────────────────────────────
    # Sample Receipts (3)
    # ──────────────────────────────────────────
    from app.services.receipt_service import _amount_in_words, get_receipt_number_str

    receipts_to_create = [
        (students[0], date(2025, 4, 10), [
            ("Tuition Fee", fee_heads[1], Decimal("50000.00")),
            ("Development Fee", fee_heads[2], Decimal("10000.00")),
        ], "CASH"),
        (students[1], date(2025, 4, 12), [
            ("Tuition Fee", fee_heads[1], Decimal("50000.00")),
            ("Examination Fee", fee_heads[3], Decimal("8000.00")),
        ], "UPI"),
        (students[2], date(2025, 4, 15), [
            ("Tuition Fee", fee_heads[1], Decimal("50000.00")),
        ], "CHEQUE"),
    ]

    for student, r_date, items, mode in receipts_to_create:
        total = sum(amt for _, _, amt in items)
        next_num = active_fy.next_receipt_number
        active_fy.next_receipt_number = next_num + 1
        receipt_num = get_receipt_number_str(active_fy, org, next_num)

        r = Receipt(
            receipt_number=receipt_num,
            financial_year_id=active_fy.id,
            student_id=student.id,
            student_name=student.student_name,
            father_name=student.father_name,
            course_name=bhms.name,
            batch_name=batches[4].name,
            session_name=sessions[2].name,
            professional_year=student.professional_year,
            roll_number=student.roll_number,
            admission_number=student.admission_number,
            receipt_date=r_date,
            total_amount=total,
            amount_in_words=_amount_in_words(total),
            status=ReceiptStatus.ACTIVE,
            collected_by=admin_user.id,
        )
        db.add(r)
        db.flush()

        for i, (fh_name, fh_obj, amount) in enumerate(items):
            ri = ReceiptItem(
                receipt_id=r.id,
                fee_head_id=fh_obj.id,
                fee_head_name=fh_name,
                amount=amount,
                sort_order=i,
            )
            db.add(ri)

        pmt = ReceiptPayment(
            receipt_id=r.id,
            payment_mode_name=mode,
            amount=total,
            payment_status="CLEARED",
        )
        if mode == "CHEQUE":
            pmt.cheque_number = "123456"
            pmt.cheque_date = r_date
            pmt.bank_name = "State Bank of India"
            pmt.payment_status = "PENDING"
        elif mode == "UPI":
            pmt.transaction_id = "UPI123456789"
            pmt.upi_id = "student@okaxis"
        db.add(pmt)

    db.flush()
    print("Seed data created successfully.")
    print("  Users: admin/Admin@1234, accounts/Accounts@1234, principal/Principal@1234, auditor/Auditor@1234")
