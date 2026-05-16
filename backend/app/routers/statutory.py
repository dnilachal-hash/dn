from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..database import get_db
from ..models.statutory import EPFSetting, ESISetting, PTStateSetting, LWFSetting, TDSSetting
from ..models.user import User
from ..schemas.statutory import (
    EPFSettingIn, EPFSettingOut, ESISettingIn, ESISettingOut,
    PTSettingIn, PTSettingOut, LWFSettingIn, LWFSettingOut,
    TDSSettingIn, TDSSettingOut
)
from ..core.permissions import require_permission, Permission
from ..services.audit_service import log_action

router = APIRouter(prefix="/statutory", tags=["statutory"])


@router.get("/epf", response_model=list[EPFSettingOut])
def list_epf(db: Session = Depends(get_db),
             current_user: User = Depends(require_permission(Permission.STATUTORY_VIEW))):
    return db.scalars(select(EPFSetting).order_by(EPFSetting.id.desc())).all()


@router.post("/epf", response_model=EPFSettingOut, status_code=201)
def save_epf(payload: EPFSettingIn, db: Session = Depends(get_db),
             current_user: User = Depends(require_permission(Permission.STATUTORY_EDIT))):
    existing = db.scalar(select(EPFSetting).where(
        EPFSetting.financial_year_id == payload.financial_year_id))
    if existing:
        old = {c.name: getattr(existing, c.name) for c in EPFSetting.__table__.columns}
        for k, v in payload.model_dump().items():
            setattr(existing, k, v)
        log_action(db, current_user, "EPF_UPDATE", "EPFSetting", existing.id, old, payload.model_dump(mode="json"))
        db.commit(); db.refresh(existing)
        return existing
    s = EPFSetting(**payload.model_dump())
    db.add(s); db.flush()
    log_action(db, current_user, "EPF_CREATE", "EPFSetting", s.id, None, payload.model_dump(mode="json"))
    db.commit(); db.refresh(s)
    return s


@router.get("/esi", response_model=list[ESISettingOut])
def list_esi(db: Session = Depends(get_db),
             current_user: User = Depends(require_permission(Permission.STATUTORY_VIEW))):
    return db.scalars(select(ESISetting).order_by(ESISetting.id.desc())).all()


@router.post("/esi", response_model=ESISettingOut, status_code=201)
def save_esi(payload: ESISettingIn, db: Session = Depends(get_db),
             current_user: User = Depends(require_permission(Permission.STATUTORY_EDIT))):
    existing = db.scalar(select(ESISetting).where(
        ESISetting.financial_year_id == payload.financial_year_id))
    if existing:
        old = {c.name: getattr(existing, c.name) for c in ESISetting.__table__.columns}
        for k, v in payload.model_dump().items():
            setattr(existing, k, v)
        log_action(db, current_user, "ESI_UPDATE", "ESISetting", existing.id, old, payload.model_dump(mode="json"))
        db.commit(); db.refresh(existing)
        return existing
    s = ESISetting(**payload.model_dump())
    db.add(s); db.flush()
    log_action(db, current_user, "ESI_CREATE", "ESISetting", s.id, None, payload.model_dump(mode="json"))
    db.commit(); db.refresh(s)
    return s


@router.get("/pt", response_model=list[PTSettingOut])
def list_pt(db: Session = Depends(get_db),
            current_user: User = Depends(require_permission(Permission.STATUTORY_VIEW))):
    return db.scalars(select(PTStateSetting).order_by(PTStateSetting.state_code)).all()


@router.post("/pt", response_model=PTSettingOut, status_code=201)
def save_pt(payload: PTSettingIn, db: Session = Depends(get_db),
            current_user: User = Depends(require_permission(Permission.STATUTORY_EDIT))):
    existing = db.scalar(select(PTStateSetting).where(
        PTStateSetting.state_code == payload.state_code,
        PTStateSetting.financial_year_id == payload.financial_year_id))
    data = payload.model_dump(mode="json")
    if existing:
        for k, v in data.items():
            setattr(existing, k, v)
        log_action(db, current_user, "PT_UPDATE", "PTSetting", existing.id, None, data)
        db.commit(); db.refresh(existing)
        return existing
    s = PTStateSetting(**data)
    db.add(s); db.flush()
    log_action(db, current_user, "PT_CREATE", "PTSetting", s.id, None, data)
    db.commit(); db.refresh(s)
    return s


@router.get("/lwf", response_model=list[LWFSettingOut])
def list_lwf(db: Session = Depends(get_db),
             current_user: User = Depends(require_permission(Permission.STATUTORY_VIEW))):
    return db.scalars(select(LWFSetting).order_by(LWFSetting.state_code)).all()


@router.post("/lwf", response_model=LWFSettingOut, status_code=201)
def save_lwf(payload: LWFSettingIn, db: Session = Depends(get_db),
             current_user: User = Depends(require_permission(Permission.STATUTORY_EDIT))):
    s = LWFSetting(**payload.model_dump())
    db.add(s); db.flush()
    log_action(db, current_user, "LWF_CREATE", "LWFSetting", s.id, None, payload.model_dump(mode="json"))
    db.commit(); db.refresh(s)
    return s


@router.get("/tds", response_model=list[TDSSettingOut])
def list_tds(db: Session = Depends(get_db),
             current_user: User = Depends(require_permission(Permission.STATUTORY_VIEW))):
    return db.scalars(select(TDSSetting).order_by(TDSSetting.id.desc())).all()


@router.post("/tds", response_model=TDSSettingOut, status_code=201)
def save_tds(payload: TDSSettingIn, db: Session = Depends(get_db),
             current_user: User = Depends(require_permission(Permission.STATUTORY_EDIT))):
    existing = db.scalar(select(TDSSetting).where(
        TDSSetting.financial_year_id == payload.financial_year_id))
    data = payload.model_dump(mode="json")
    if existing:
        for k, v in data.items():
            setattr(existing, k, v)
        log_action(db, current_user, "TDS_UPDATE", "TDSSetting", existing.id, None, data)
        db.commit(); db.refresh(existing)
        return existing
    s = TDSSetting(**data)
    db.add(s); db.flush()
    log_action(db, current_user, "TDS_CREATE", "TDSSetting", s.id, None, data)
    db.commit(); db.refresh(s)
    return s
