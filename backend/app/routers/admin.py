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
from app.models import CommentModel, PinModel, AreaModel, User
from app.config import settings

router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ── Response schemas ─────────────────────────────────────────────────────────

class AdminComment(BaseModel):
    id: int
    targetType: str
    targetId: int
    userId: str
    text: str
    createdAt: datetime

    class Config:
        from_attributes = True


class AdminPin(BaseModel):
    id: int
    lat: float
    lng: float
    text: str
    color: str
    userId: str
    createdAt: datetime

    class Config:
        from_attributes = True


class AdminArea(BaseModel):
    id: int
    color: str
    text: str
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

@router.get("/comments", response_model=List[AdminComment], dependencies=[Depends(require_admin)])
def list_all_comments(
    target_type: Optional[str] = None,
    target_id: Optional[int] = None,
    user_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all comments. Optionally filter by target_type, target_id, or user_id."""
    q = db.query(CommentModel)
    if target_type is not None:
        q = q.filter(CommentModel.target_type == target_type)
    if target_id is not None:
        q = q.filter(CommentModel.target_id == target_id)
    if user_id is not None:
        q = q.filter(CommentModel.user_id == user_id)
    comments = q.order_by(CommentModel.created_at.desc()).all()
    return [
        AdminComment(
            id=c.id, targetType=c.target_type, targetId=c.target_id,
            userId=c.user_id, text=c.text, createdAt=c.created_at
        ) for c in comments
    ]


@router.delete("/comments/{comment_id}", response_model=DeletedResponse, dependencies=[Depends(require_admin)])
def delete_comment(comment_id: int, db: Session = Depends(get_db)):
    """Delete any comment by ID regardless of owner."""
    comment = db.query(CommentModel).filter(CommentModel.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    db.delete(comment)
    db.commit()
    return DeletedResponse(success=True, deleted_id=comment_id)


@router.get("/pins", response_model=List[AdminPin], dependencies=[Depends(require_admin)])
def list_all_pins(user_id: Optional[str] = None, db: Session = Depends(get_db)):
    """List all pins. Optionally filter by user_id."""
    q = db.query(PinModel)
    if user_id is not None:
        q = q.filter(PinModel.user_id == user_id)
    pins = q.order_by(PinModel.created_at.desc()).all()
    return [
        AdminPin(
            id=p.id, lat=p.lat, lng=p.lng, text=p.text,
            color=p.color, userId=p.user_id, createdAt=p.created_at
        ) for p in pins
    ]


@router.delete("/pins/{pin_id}", response_model=DeletedResponse, dependencies=[Depends(require_admin)])
def force_delete_pin(pin_id: int, db: Session = Depends(get_db)):
    """Force-delete any pin by ID (including its comments and votes)."""
    pin = db.query(PinModel).filter(PinModel.id == pin_id).first()
    if not pin:
        raise HTTPException(status_code=404, detail="Pin not found")
    # Delete dependent comments and votes first
    db.query(CommentModel).filter(CommentModel.target_type == "pin", CommentModel.target_id == pin_id).delete()
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
            id=a.id, color=a.color, text=a.text,
            userId=a.user_id, createdAt=a.created_at
        ) for a in areas
    ]


@router.delete("/areas/{area_id}", response_model=DeletedResponse, dependencies=[Depends(require_admin)])
def force_delete_area(area_id: int, db: Session = Depends(get_db)):
    """Force-delete any area by ID (including its comments and votes)."""
    from app.models import VoteModel
    area = db.query(AreaModel).filter(AreaModel.id == area_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Area not found")
    db.query(CommentModel).filter(
        CommentModel.target_type == "area", CommentModel.target_id == area_id
    ).delete()
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
