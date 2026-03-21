from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import schemas
from app.database import get_db
from app.dependencies import ensure_user_exists
from app.services.comment_service import CommentService
from app.services.moderation_service import ModerationService

router = APIRouter(prefix="/api", tags=["Comments"])


# --- Pin Comments ---

@router.get("/pins/{pin_id}/comments", response_model=list[schemas.Comment])
def get_pin_comments(
    pin_id: int,
    db: Session = Depends(get_db)
):
    """Get all comments for a specific pin."""
    return CommentService.get_comments(db, "pin", pin_id)


@router.post("/pins/{pin_id}/comments", response_model=schemas.Comment, status_code=201)
async def create_pin_comment(
    pin_id: int,
    comment_data: schemas.CommentCreate,
    user_id: str = Depends(ensure_user_exists),
    db: Session = Depends(get_db)
):
    """Add a new comment to a pin."""
    await ModerationService.check_text_for_pii(comment_data.text)
    return CommentService.create_comment(db, "pin", pin_id, comment_data, user_id)


# --- Area Comments ---

@router.get("/areas/{area_id}/comments", response_model=list[schemas.Comment])
def get_area_comments(
    area_id: int,
    db: Session = Depends(get_db)
):
    """Get all comments for a specific area."""
    return CommentService.get_comments(db, "area", area_id)


@router.post("/areas/{area_id}/comments", response_model=schemas.Comment, status_code=201)
async def create_area_comment(
    area_id: int,
    comment_data: schemas.CommentCreate,
    user_id: str = Depends(ensure_user_exists),
    db: Session = Depends(get_db)
):
    """Add a new comment to an area."""
    await ModerationService.check_text_for_pii(comment_data.text)
    return CommentService.create_comment(db, "area", area_id, comment_data, user_id)
