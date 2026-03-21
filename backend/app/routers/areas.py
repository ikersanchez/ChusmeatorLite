from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import schemas
from app.database import get_db
from app.dependencies import ensure_user_exists
from app.services.area_service import AreaService
from app.services.moderation_service import ModerationService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Areas"])


@router.post("/areas", response_model=schemas.Area, status_code=201)
async def create_area(
    area_data: schemas.AreaCreate,
    user_id: str = Depends(ensure_user_exists),
    db: Session = Depends(get_db)
):
    """Create a new area."""
    try:
        logger.info(f"Creating area for user {user_id}: {area_data.text}")
        await ModerationService.check_text_for_pii(area_data.text)
        db_area = AreaService.create_area(db, area_data, user_id)
        return db_area
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ERROR creating area: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/areas/{area_id}", response_model=schemas.Area)
async def update_area(
    area_id: int,
    area_data: schemas.AreaUpdate,
    user_id: str = Depends(ensure_user_exists),
    db: Session = Depends(get_db)
):
    """Update an existing area. Only the owner can edit."""
    try:
        logger.info(f"Updating area {area_id} for user {user_id}")
        if area_data.text:
            await ModerationService.check_text_for_pii(area_data.text)
        db_area = AreaService.update_area(db, area_id, user_id, area_data)
        return db_area
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ERROR updating area: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/areas/{area_id}", response_model=schemas.SuccessResponse)
def delete_area(
    area_id: int,
    user_id: str = Depends(ensure_user_exists),
    db: Session = Depends(get_db)
):
    """Delete an area. Only the owner can delete their own areas."""
    success = AreaService.delete_area(db, area_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Area not found")
    
    return schemas.SuccessResponse(success=True)
