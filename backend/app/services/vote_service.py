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
    def compute_effective_color(vote_counts: Dict[str, int], original_color: str) -> str:
        """Compute the effective color based on vote counts and original color.
        Return original_color if total votes < 10.
        Otherwise, return the color with the most votes (simple majority).
        """
        total = sum(vote_counts.values())
        if total < 10:
            return original_color
        
        # Find the color with the most votes
        max_color = max(vote_counts, key=vote_counts.get)
        
        # Return the majority color
        return max_color

    @staticmethod
    def update_target_color(db: Session, target_type: str, target_id: int):
        """Recalculate and update the effective color of a target after a vote change."""
        # Get the target model
        model = PinModel if target_type == "pin" else AreaModel
        target = db.query(model).filter(model.id == target_id).first()
        if not target:
            return
        
        # Count votes
        rows = (
            db.query(VoteModel.vote_color, sa_func.count(VoteModel.id))
            .filter(VoteModel.target_type == target_type, VoteModel.target_id == target_id)
            .group_by(VoteModel.vote_color)
            .all()
        )
        vote_counts = {"red": 0, "blue": 0, "green": 0}
        for vote_color, count in rows:
            vote_counts[vote_color] = int(count)
        
        new_color = VoteService.compute_effective_color(vote_counts, target.original_color)
        if target.color != new_color:
            target.color = new_color
            db.commit()

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
        
        # Recalculate effective color
        VoteService.update_target_color(db, vote_data.target_type, vote_data.target_id)
        
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
        
        # Recalculate effective color
        VoteService.update_target_color(db, target_type, target_id)
        
        return True
