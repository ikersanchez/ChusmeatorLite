from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import schemas
from app.database import get_db
from app.dependencies import ensure_user_exists
from app.services.pin_service import PinService
from app.services.moderation_service import ModerationService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Pins"])


@router.post("/pins", response_model=schemas.Pin, status_code=201)
async def create_pin(
    pin_data: schemas.PinCreate,
    user_id: str = Depends(ensure_user_exists),
    db: Session = Depends(get_db)
):
    """Create a new pin."""
    logger.info(f"Creating pin for user {user_id}: {pin_data.text}")
    await ModerationService.check_text_for_pii(pin_data.text)
    db_pin = PinService.create_pin(db, pin_data, user_id)
    return db_pin


@router.put("/pins/{pin_id}", response_model=schemas.Pin)
async def update_pin(
    pin_id: int,
    pin_data: schemas.PinUpdate,
    user_id: str = Depends(ensure_user_exists),
    db: Session = Depends(get_db)
):
    """Update an existing pin. Only the owner can edit."""
    logger.info(f"Updating pin {pin_id} for user {user_id}")
    if pin_data.text:
        await ModerationService.check_text_for_pii(pin_data.text)
    db_pin = PinService.update_pin(db, pin_id, user_id, pin_data)
    return db_pin


@router.delete("/pins/{pin_id}", response_model=schemas.SuccessResponse)
def delete_pin(
    pin_id: int,
    user_id: str = Depends(ensure_user_exists),
    db: Session = Depends(get_db)
):
    """Delete a pin. Only the owner can delete their own pins."""
    success = PinService.delete_pin(db, pin_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Pin not found")
    
    return schemas.SuccessResponse(success=True)
