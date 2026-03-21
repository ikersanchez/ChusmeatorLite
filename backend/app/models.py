from sqlalchemy import Column, String, Float, Integer, BigInteger, Text, DateTime, ForeignKey, JSON, CheckConstraint, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base
from enum import Enum

Base = declarative_base()


class PinColor(str, Enum):
    BLUE = "blue"
    GREEN = "green"
    RED = "red"


class CategoryType(str, Enum):
    CRIME = "crime"
    ALCOHOL = "alcohol"
    SCREAMING = "screaming"
    LOUD_MUSIC = "loud_music"
    TRAFFIC = "traffic"
    POOR_LIGHTING = "poor_lighting"
    DIRTY = "dirty"
    CONSTRUCTION = "construction"
    DANGEROUS_ANIMALS = "dangerous_animals"
    GENERAL_WARNING = "general_warning"


# Human-readable labels for categories
CATEGORY_LABELS = {
    CategoryType.CRIME: "Crime / Delinquency",
    CategoryType.ALCOHOL: "Alcohol / Partying",
    CategoryType.SCREAMING: "Screaming / Disturbances",
    CategoryType.LOUD_MUSIC: "Loud Music",
    CategoryType.TRAFFIC: "Traffic / Noise",
    CategoryType.POOR_LIGHTING: "Poor Lighting",
    CategoryType.DIRTY: "Dirty / Trash",
    CategoryType.CONSTRUCTION: "Construction / Roadworks",
    CategoryType.DANGEROUS_ANIMALS: "Dangerous Animals",
    CategoryType.GENERAL_WARNING: "General Warning",
}

# Emoji icons for each category
CATEGORY_ICONS = {
    CategoryType.CRIME: "🔫",
    CategoryType.ALCOHOL: "🍺",
    CategoryType.SCREAMING: "😱",
    CategoryType.LOUD_MUSIC: "🎵",
    CategoryType.TRAFFIC: "🚗",
    CategoryType.POOR_LIGHTING: "💡",
    CategoryType.DIRTY: "🗑️",
    CategoryType.CONSTRUCTION: "🚧",
    CategoryType.DANGEROUS_ANIMALS: "🐕",
    CategoryType.GENERAL_WARNING: "⚠️",
}


CATEGORY_VALUES = ", ".join(f"'{c.value}'" for c in CategoryType)
COLOR_VALUES = ", ".join(f"'{c.value}'" for c in PinColor)


class User(Base):
    """User model."""
    __tablename__ = "users"

    id = Column(String(50), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PinModel(Base):
    """Pin model for map pins with location and category."""
    __tablename__ = "pins"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    category = Column(String(30), nullable=False)
    color = Column(String(10), nullable=False, default=PinColor.BLUE.value)
    original_color = Column(String(10), nullable=False, default=PinColor.BLUE.value)
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint(f"color IN ({COLOR_VALUES})", name="check_pin_color"),
        CheckConstraint(f"original_color IN ({COLOR_VALUES})", name="check_pin_original_color"),
        CheckConstraint(f"category IN ({CATEGORY_VALUES})", name="check_pin_category"),
    )


class AreaModel(Base):
    """Area model for polygonal regions with color and category."""
    __tablename__ = "areas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    latlngs = Column(JSON, nullable=False)
    color = Column(String(10), nullable=False)
    original_color = Column(String(10), nullable=False)
    category = Column(String(30), nullable=False)
    font_size = Column(String(20), nullable=False)
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint(f"color IN ({COLOR_VALUES})", name="check_area_color"),
        CheckConstraint(f"original_color IN ({COLOR_VALUES})", name="check_area_original_color"),
        CheckConstraint(f"category IN ({CATEGORY_VALUES})", name="check_area_category"),
    )


class VoteModel(Base):
    """Vote model for community color voting on pins and areas."""
    __tablename__ = "votes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    target_type = Column(String(10), nullable=False)  # "pin", "area"
    target_id = Column(Integer, nullable=False)
    vote_color = Column(String(10), nullable=False)  # "red", "blue", "green"
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("target_type IN ('pin', 'area')", name="check_vote_target_type"),
        CheckConstraint(f"vote_color IN ({COLOR_VALUES})", name="check_vote_color"),
        UniqueConstraint("user_id", "target_type", "target_id", name="uq_vote"),
    )
