from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app import schemas
from app.models import PinModel, AreaModel
from app.database import get_db
from app.dependencies import ensure_user_exists
from app.services.vote_service import VoteService

router = APIRouter(prefix="/api", tags=["Votes"])

# Map target types to their models for existence checks
TARGET_MODELS = {
    "pin": PinModel,
    "area": AreaModel,
}


@router.post("/votes", response_model=schemas.VoteResponse, status_code=201)
def create_vote(
    vote_data: schemas.VoteCreate,
    user_id: str = Depends(ensure_user_exists),
    db: Session = Depends(get_db)
):
    """Create a vote on a pin or area. One vote per user per item."""
    # Verify target exists
    model = TARGET_MODELS.get(vote_data.target_type)
    if not model:
        raise HTTPException(status_code=400, detail="Invalid target type")

    target = db.query(model).filter(model.id == vote_data.target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail=f"{vote_data.target_type.capitalize()} not found")

    try:
        db_vote = VoteService.create_vote(db, vote_data, user_id)
        return db_vote
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="You have already voted on this item")


@router.delete("/votes/{target_type}/{target_id}", response_model=schemas.SuccessResponse)
def delete_vote(
    target_type: str,
    target_id: int,
    user_id: str = Depends(ensure_user_exists),
    db: Session = Depends(get_db)
):
    """Remove the calling user's vote from an item."""
    if target_type not in TARGET_MODELS:
        raise HTTPException(status_code=400, detail="Invalid target type")

    success = VoteService.delete_vote(db, target_type, target_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Vote not found")

    return schemas.SuccessResponse(success=True)
