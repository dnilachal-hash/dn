from typing import Any
from sqlalchemy.orm import Session
from ..models.user import AuditLog, User


def log_action(db: Session, user: User | None, action: str, entity_type: str,
               entity_id: Any = None, old: dict | None = None, new: dict | None = None,
               ip: str | None = None, remarks: str | None = None) -> AuditLog:
    entry = AuditLog(
        user_id=user.id if user else None,
        username=user.username if user else None,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        old_values=old,
        new_values=new,
        ip_address=ip,
        remarks=remarks,
    )
    db.add(entry)
    db.flush()
    return entry
