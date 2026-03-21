"""Admin API router — content moderation endpoints.

All endpoints require the X-Admin-Key header matching the ADMIN_KEY env variable.
These endpoints allow an administrator to view and remove any stored user content.
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.database import get_db
from app.models import PinModel, AreaModel, VoteModel, User
from app.config import settings

router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ── Response schemas ─────────────────────────────────────────────────────────

class AdminPin(BaseModel):
    id: int
    lat: float
    lng: float
    category: str
    color: str
    original_color: str
    userId: str
    createdAt: datetime

    class Config:
        from_attributes = True


class AdminArea(BaseModel):
    id: int
    color: str
    original_color: str
    category: str
    userId: str
    createdAt: datetime

    class Config:
        from_attributes = True


class AdminUser(BaseModel):
    id: str
    createdAt: datetime

    class Config:
        from_attributes = True


class DeletedResponse(BaseModel):
    success: bool = True
    deleted_id: int


# ── Auth dependency ───────────────────────────────────────────────────────────

def require_admin(x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")):
    """Verify the admin key header."""
    if not settings.admin_key:
        raise HTTPException(
            status_code=503,
            detail="Admin access is not configured. Set the ADMIN_KEY environment variable."
        )
    if x_admin_key != settings.admin_key:
        raise HTTPException(status_code=403, detail="Invalid or missing X-Admin-Key header")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/pins", response_model=List[AdminPin], dependencies=[Depends(require_admin)])
def list_all_pins(user_id: Optional[str] = None, db: Session = Depends(get_db)):
    """List all pins. Optionally filter by user_id."""
    q = db.query(PinModel)
    if user_id is not None:
        q = q.filter(PinModel.user_id == user_id)
    pins = q.order_by(PinModel.created_at.desc()).all()
    return [
        AdminPin(
            id=p.id, lat=p.lat, lng=p.lng, category=p.category,
            color=p.color, original_color=p.original_color,
            userId=p.user_id, createdAt=p.created_at
        ) for p in pins
    ]


@router.delete("/pins/{pin_id}", response_model=DeletedResponse, dependencies=[Depends(require_admin)])
def force_delete_pin(pin_id: int, db: Session = Depends(get_db)):
    """Force-delete any pin by ID (including its votes)."""
    pin = db.query(PinModel).filter(PinModel.id == pin_id).first()
    if not pin:
        raise HTTPException(status_code=404, detail="Pin not found")
    # Delete dependent votes first
    db.query(VoteModel).filter(VoteModel.target_type == "pin", VoteModel.target_id == pin_id).delete()
    db.delete(pin)
    db.commit()
    return DeletedResponse(success=True, deleted_id=pin_id)


@router.get("/areas", response_model=List[AdminArea], dependencies=[Depends(require_admin)])
def list_all_areas(user_id: Optional[str] = None, db: Session = Depends(get_db)):
    """List all areas. Optionally filter by user_id."""
    q = db.query(AreaModel)
    if user_id is not None:
        q = q.filter(AreaModel.user_id == user_id)
    areas = q.order_by(AreaModel.created_at.desc()).all()
    return [
        AdminArea(
            id=a.id, color=a.color, original_color=a.original_color,
            category=a.category, userId=a.user_id, createdAt=a.created_at
        ) for a in areas
    ]


@router.delete("/areas/{area_id}", response_model=DeletedResponse, dependencies=[Depends(require_admin)])
def force_delete_area(area_id: int, db: Session = Depends(get_db)):
    """Force-delete any area by ID (including its votes)."""
    area = db.query(AreaModel).filter(AreaModel.id == area_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Area not found")
    db.query(VoteModel).filter(
        VoteModel.target_type == "area", VoteModel.target_id == area_id
    ).delete()
    db.delete(area)
    db.commit()
    return DeletedResponse(success=True, deleted_id=area_id)


@router.get("/users", response_model=List[AdminUser], dependencies=[Depends(require_admin)])
def list_all_users(db: Session = Depends(get_db)):
    """List all registered users with their creation timestamps."""
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [AdminUser(id=u.id, createdAt=u.created_at) for u in users]
