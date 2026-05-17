"""Register all ORM models so metadata is populated before create_all()."""
from . import user, org, student, fee, receipt, audit

__all__ = ["user", "org", "student", "fee", "receipt", "audit"]
