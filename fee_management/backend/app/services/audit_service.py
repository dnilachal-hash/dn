"""Audit logging service."""
import json
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session


def log_action(
    db: Session,
    user,
    action: str,
    entity_type: str = "",
    entity_id: Optional[Any] = None,
    old_val: Optional[Any] = None,
    new_val: Optional[Any] = None,
    reason: Optional[str] = None,
    request=None,
) -> None:
    """Write an AuditLog row. Silently ignores import errors to avoid circular deps."""
    try:
        from app.models.audit import AuditLog

        ip_address = None
        user_agent = None
        if request is not None:
            try:
                ip_address = request.client.host if request.client else None
                user_agent = request.headers.get("user-agent")
            except Exception:
                pass

        def _serialise(v):
            if v is None:
                return None
            if isinstance(v, dict):
                return v
            try:
                return json.loads(json.dumps(v, default=str))
            except Exception:
                return {"value": str(v)}

        log = AuditLog(
            user_id=getattr(user, "id", None),
            username=getattr(user, "username", None),
            role=str(getattr(user, "role", "")),
            action=action,
            entity_type=str(entity_type) if entity_type else None,
            entity_id=str(entity_id) if entity_id is not None else None,
            old_value=_serialise(old_val),
            new_value=_serialise(new_val),
            reason=reason,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.utcnow(),
        )
        db.add(log)
        db.flush()
    except Exception:
        pass  # Audit failures must never break the main flow
