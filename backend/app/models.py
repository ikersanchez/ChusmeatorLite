from sqlalchemy import Column, String, Float, Integer, BigInteger, Text, DateTime, ForeignKey, JSON, CheckConstraint, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base
from enum import Enum

Base = declarative_base()


class PinColor(str, Enum):
    BLUE = "blue"
    GREEN = "green"
    RED = "red"


class User(Base):
    """User model."""
    __tablename__ = "users"

    id = Column(String(50), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PinModel(Base):
    """Pin model for map pins with location and text."""
    __tablename__ = "pins"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    text = Column(Text, nullable=False)
    color = Column(String(10), nullable=False, default=PinColor.BLUE.value)
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint(f"color IN ('{PinColor.BLUE.value}', '{PinColor.GREEN.value}', '{PinColor.RED.value}')", name="check_pin_color"),
    )


class AreaModel(Base):
    """Area model for polygonal regions with color and label."""
    __tablename__ = "areas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    latlngs = Column(JSON, nullable=False)
    color = Column(String(10), nullable=False)
    text = Column(Text, nullable=False)
    font_size = Column(String(20), nullable=False)
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint(f"color IN ('{PinColor.BLUE.value}', '{PinColor.GREEN.value}', '{PinColor.RED.value}')", name="check_area_color"),
    )


class CommentModel(Base):
    """Comment model for pins and areas."""
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    target_type = Column(String(10), nullable=False)  # "pin", "area"
    target_id = Column(BigInteger, nullable=False)
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    text = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("target_type IN ('pin', 'area')", name="check_comment_target_type"),
    )


class VoteModel(Base):
    """Vote model for community voting on pins and areas."""
    __tablename__ = "votes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    target_type = Column(String(10), nullable=False)  # "pin", "area"
    target_id = Column(Integer, nullable=False)
    value = Column(Integer, nullable=False, default=1)  # +1 = like, -1 = dislike
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("target_type IN ('pin', 'area')", name="check_vote_target_type"),
        CheckConstraint("value IN (1, -1)", name="check_vote_value"),
        UniqueConstraint("user_id", "target_type", "target_id", name="uq_vote"),
    )
