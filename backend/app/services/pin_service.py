from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models import PinModel
from app import schemas
from app.config import settings

class PinService:
    @staticmethod
    def create_pin(db: Session, pin_data: schemas.PinCreate, user_id: str) -> PinModel:
        # Rate limit check: max 20 pins per 24 hours
        one_day_ago = datetime.now(timezone.utc) - timedelta(days=1)
        pin_count = db.query(func.count(PinModel.id)).filter(
            PinModel.user_id == user_id,
            PinModel.created_at >= one_day_ago
        ).scalar()
        
        if pin_count >= settings.max_pins_per_day:
            raise HTTPException(
                status_code=429, 
                detail=f"Rate limit exceeded: Maximum {settings.max_pins_per_day} pins per day allowed."
            )

        db_pin = PinModel(
            lat=pin_data.lat,
            lng=pin_data.lng,
            text=pin_data.text,
            color=pin_data.color.value if hasattr(pin_data.color, 'value') else pin_data.color,
            user_id=user_id
        )
        db.add(db_pin)
        db.commit()
        db.refresh(db_pin)
        return db_pin

    @staticmethod
    def get_all_pins(db: Session) -> list[PinModel]:
        return db.query(PinModel).all()

    @staticmethod
    def update_pin(db: Session, pin_id: int, user_id: str, update_data: schemas.PinUpdate) -> PinModel:
        pin = db.query(PinModel).filter(PinModel.id == pin_id).first()
        if not pin:
            raise HTTPException(status_code=404, detail="Pin not found")
        if pin.user_id != user_id:
            raise HTTPException(status_code=403, detail="Unauthorized: You can only edit your own pins")
        
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if key == 'color' and hasattr(value, 'value'):
                setattr(pin, key, value.value)
            else:
                setattr(pin, key, value)
                
        db.commit()
        db.refresh(pin)
        return pin

    @staticmethod
    def delete_pin(db: Session, pin_id: int, user_id: str) -> bool:
        pin = db.query(PinModel).filter(PinModel.id == pin_id).first()
        if not pin:
            return False
        if pin.user_id != user_id:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Unauthorized: You can only delete your own pins")
        
        db.delete(pin)
        db.commit()
        return True
