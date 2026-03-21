from fastapi import Header, HTTPException, Depends, Request
from sqlalchemy.orm import Session
import uuid
from app.database import get_db
from app.models import User


def get_current_user_id(request: Request) -> str:
    """
    Extract or generate user ID from header or session cookie.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User ID string
    """
    # Check header first (useful for development/testing)
    user_id = request.headers.get("X-User-Id")
    
    if not user_id:
        # Fallback to session
        user_id = request.session.get("user_id")
    
    if not user_id:
        # Generate a new unique ID if not present
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        request.session["user_id"] = user_id
        
    return user_id


def ensure_user_exists(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """
    Ensure user exists in database, create if not.
    
    Args:
        user_id: Current user ID
        db: Database session
        
    Returns:
        User ID
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        # Create user if doesn't exist
        user = User(id=user_id)
        db.add(user)
        db.commit()
    return user_id
