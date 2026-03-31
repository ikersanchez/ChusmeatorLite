from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func
from app.models import VoteModel, PinModel, AreaModel
from app import schemas
from typing import Dict, Optional

class VoteService:
    @staticmethod
    def get_vote_color_counts(db: Session, target_type: str) -> Dict[int, Dict[str, int]]:
        """Get vote counts per color grouped by target_id for a given target_type.
        Returns: {target_id: {"red": N, "blue": N, "green": N}}
        """
        rows = (
            db.query(VoteModel.target_id, VoteModel.vote_color, sa_func.count(VoteModel.id))
            .filter(VoteModel.target_type == target_type)
            .group_by(VoteModel.target_id, VoteModel.vote_color)
            .all()
        )
        result: Dict[int, Dict[str, int]] = {}
        for target_id, vote_color, count in rows:
            if target_id not in result:
                result[target_id] = {"red": 0, "blue": 0, "green": 0}
            result[target_id][vote_color] = int(count)
        return result

    @staticmethod
    def get_user_vote_colors(db: Session, target_type: str, user_id: Optional[str]) -> Dict[int, str]:
        """Get mapping of target_id -> vote_color for a user's votes."""
        if not user_id:
            return {}
        rows = (
            db.query(VoteModel.target_id, VoteModel.vote_color)
            .filter(VoteModel.target_type == target_type, VoteModel.user_id == user_id)
            .all()
        )
        return {target_id: vote_color for target_id, vote_color in rows}

    @staticmethod
    def create_vote(db: Session, vote_data: schemas.VoteCreate, user_id: str) -> VoteModel:
        vote_color = vote_data.vote_color.value if hasattr(vote_data.vote_color, 'value') else vote_data.vote_color
        db_vote = VoteModel(
            user_id=user_id,
            target_type=vote_data.target_type,
            target_id=vote_data.target_id,
            vote_color=vote_color
        )
        db.add(db_vote)
        db.commit()
        db.refresh(db_vote)
        
        return db_vote

    @staticmethod
    def delete_vote(db: Session, target_type: str, target_id: int, user_id: str) -> bool:
        vote = db.query(VoteModel).filter(
            VoteModel.target_type == target_type,
            VoteModel.target_id == target_id,
            VoteModel.user_id == user_id
        ).first()
        if not vote:
            return False
        db.delete(vote)
        db.commit()
        
        return True
