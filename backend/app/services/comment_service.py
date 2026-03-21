from datetime import datetime, timezone, timedelta
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models import CommentModel, PinModel, AreaModel
from app import schemas
from fastapi import HTTPException
from app.config import settings

class CommentService:
    @staticmethod
    def _validate_target(db: Session, target_type: str, target_id: int):
        """Validate that the target (pin or area) exists."""
        if target_type == "pin":
            target = db.query(PinModel).filter(PinModel.id == target_id).first()
            if not target:
                raise HTTPException(status_code=404, detail="Pin not found")
        elif target_type == "area":
            target = db.query(AreaModel).filter(AreaModel.id == target_id).first()
            if not target:
                raise HTTPException(status_code=404, detail="Area not found")
        else:
            raise HTTPException(status_code=400, detail="Invalid target_type")

    @staticmethod
    def get_comments(db: Session, target_type: str, target_id: int) -> list[CommentModel]:
        CommentService._validate_target(db, target_type, target_id)
        return db.query(CommentModel).filter(
            CommentModel.target_type == target_type,
            CommentModel.target_id == target_id
        ).order_by(CommentModel.created_at.desc()).all()

    @staticmethod
    def create_comment(db: Session, target_type: str, target_id: int, comment_data: schemas.CommentCreate, user_id: str) -> CommentModel:
        CommentService._validate_target(db, target_type, target_id)
            
        # Rate limit check: max comments per 24 hours (across all targets)
        # Using database time via func.now() avoids timezone mismatches between Python and DB
        one_day_ago = func.now() - timedelta(days=1)
        comment_count = db.query(func.count(CommentModel.id)).filter(
            CommentModel.user_id == user_id,
            CommentModel.created_at >= one_day_ago
        ).scalar()
        
        if comment_count >= settings.max_comments_per_day:
            raise HTTPException(
                status_code=429, 
                detail=f"Rate limit exceeded: Maximum {settings.max_comments_per_day} comments per day allowed."
            )
            
        db_comment = CommentModel(
            target_type=target_type,
            target_id=target_id,
            user_id=user_id,
            text=comment_data.text
        )
        
        db.add(db_comment)
        db.commit()
        db.refresh(db_comment)
        return db_comment

    @staticmethod
    def get_comment_counts(db: Session, target_type: str) -> dict[int, int]:
        """Get comment counts grouped by target_id for a given target_type."""
        rows = (
            db.query(CommentModel.target_id, func.count(CommentModel.id))
            .filter(CommentModel.target_type == target_type)
            .group_by(CommentModel.target_id)
            .all()
        )
        return {target_id: int(total) for target_id, total in rows}
