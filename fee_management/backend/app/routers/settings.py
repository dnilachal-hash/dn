"""Settings router: organisation, receipt format, backup/restore."""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from fastapi.responses import Response, FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.permissions import require_permission, Permission
from app.database import get_db
from app.models.org import Organisation
from app.services.audit_service import log_action
from app.services.backup_service import create_backup, list_backups, restore_backup

router = APIRouter(prefix="/settings", tags=["settings"])


class OrgUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pin: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    receipt_header: Optional[str] = None
    receipt_footer: Optional[str] = None
    gstin: Optional[str] = None
    receipt_numbering_format: Optional[str] = None


class ReceiptFormatUpdate(BaseModel):
    receipt_header: Optional[str] = None
    receipt_footer: Optional[str] = None
    receipt_numbering_format: Optional[str] = None


@router.get("/organisation")
def get_organisation(
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.VIEW_REPORTS)),
):
    org = db.scalar(select(Organisation).limit(1))
    if not org:
        return {}
    return {
        "id": org.id,
        "name": org.name,
        "address": org.address,
        "city": org.city,
        "state": org.state,
        "pin": org.pin,
        "phone": org.phone,
        "email": org.email,
        "website": org.website,
        "logo_path": org.logo_path,
        "receipt_header": org.receipt_header,
        "receipt_footer": org.receipt_footer,
        "receipt_numbering_format": org.receipt_numbering_format.value if hasattr(org.receipt_numbering_format, "value") else org.receipt_numbering_format,
        "gstin": org.gstin,
    }


@router.put("/organisation")
def update_organisation(
    payload: OrgUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.MANAGE_SETTINGS)),
):
    org = db.scalar(select(Organisation).limit(1))
    if not org:
        org = Organisation(name="College")
        db.add(org)
        db.flush()

    old = {"name": org.name}
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(org, k, v)

    log_action(db, current_user, "UPDATE_ORG", "organisation", org.id, old, request=request)
    db.commit()
    return {"message": "Organisation updated"}


@router.get("/receipt-format")
def get_receipt_format(
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.VIEW_REPORTS)),
):
    org = db.scalar(select(Organisation).limit(1))
    if not org:
        return {}
    return {
        "receipt_header": org.receipt_header,
        "receipt_footer": org.receipt_footer,
        "receipt_numbering_format": org.receipt_numbering_format.value if hasattr(org.receipt_numbering_format, "value") else org.receipt_numbering_format,
    }


@router.put("/receipt-format")
def update_receipt_format(
    payload: ReceiptFormatUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.MANAGE_SETTINGS)),
):
    org = db.scalar(select(Organisation).limit(1))
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not configured")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(org, k, v)
    log_action(db, current_user, "UPDATE_RECEIPT_FORMAT", "organisation", org.id, request=request)
    db.commit()
    return {"message": "Receipt format updated"}


@router.get("/backups")
def list_backup_files(
    current_user=Depends(require_permission(Permission.BACKUP_RESTORE)),
):
    return list_backups()


@router.post("/backup")
def trigger_backup(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.BACKUP_RESTORE)),
):
    try:
        result = create_backup(db)
        log_action(db, current_user, "CREATE_BACKUP", "backup", result["filename"], request=request)
        db.commit()
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/restore")
async def restore_backup_endpoint(
    file: UploadFile = File(...),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.BACKUP_RESTORE)),
):
    """Upload a .db backup file and restore it."""
    content = await file.read()
    filename = file.filename or "restore.db"

    # Save uploaded file to backups dir
    from pathlib import Path
    backup_dir = Path("./data/backups")
    backup_dir.mkdir(parents=True, exist_ok=True)
    upload_path = backup_dir / filename
    upload_path.write_bytes(content)

    try:
        result = restore_backup(filename, db)
        log_action(db, current_user, "RESTORE_BACKUP", "backup", filename, request=request)
        try:
            db.commit()
        except Exception:
            pass
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
