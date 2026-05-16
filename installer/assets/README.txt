HMC Payroll Management System v2.0
====================================
Homoeopathic Medical College & Hospital

This installer will deploy a complete, NCH-compliant Indian payroll
management system on your Windows machine.

WHAT WILL BE INSTALLED
----------------------
- Application files to C:\PayrollSystem\
- Python 3.11 runtime (bundled, isolated from system Python)
- SQLite database (or PostgreSQL if available)
- All Python dependencies (installed offline)
- Windows Firewall rule for port 8000
- Desktop and Start Menu shortcuts

AFTER INSTALLATION
------------------
- Browser opens to http://localhost:8000 automatically
- Default credentials (force-change on first login):
    admin    / Admin@1234     (Super Admin — full access)
    hr       / Hr@1234        (HR Manager)
    payroll  / Payroll@1234   (Payroll Executive)
    accounts / Accounts@1234  (Accounts)
    auditor  / Auditor@1234   (Read-only)

- 22 NCH departments pre-loaded (12 teaching + 10 non-teaching)
- 27 designations pre-loaded
- Sample employees with salary structures for demo
- All statutory rates pre-loaded as configurable starting values
  (EPF 12%, ESI 0.75%/3.25%, PT slabs for MH/KA/DL, TDS slabs FY2025-26)

LEGAL DISCLAIMER
----------------
All statutory rates, slabs, and ceilings pre-loaded in this system
are provided as configurable starting values for reference only.
The system administrator must verify all rates against the latest
official government notifications before processing any payroll
for compliance purposes.

This software provides a configurable compliance framework and does
not constitute legal advice.

SUPPORT
-------
For support, contact your IT administrator or the system installer.
Documentation: See User_Manual.pdf placed on Desktop after install.
