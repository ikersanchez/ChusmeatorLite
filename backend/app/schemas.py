"""Pydantic schemas matching the OpenAPI specification."""
from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator
from pydantic.alias_generators import to_camel
from app.models import PinColor, CategoryType


class BaseSchema(BaseModel):
    """Base schema with camelCase configuration."""
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )


# Pin Schemas
class PinCreate(BaseModel):
    """Schema for creating a new pin."""
    lat: float = Field(..., description="Latitude coordinate")
    lng: float = Field(..., description="Longitude coordinate")
    category: CategoryType = Field(..., description="Pin category")
    color: PinColor = PinColor.BLUE


class PinUpdate(BaseModel):
    """Schema for updating an existing pin."""
    lat: Optional[float] = Field(None, description="Latitude coordinate")
    lng: Optional[float] = Field(None, description="Longitude coordinate")
    category: Optional[CategoryType] = None
    color: Optional[PinColor] = None


class Pin(BaseSchema):
    """Schema for a pin response."""
    id: int
    lat: float
    lng: float
    category: str
    color: str
    original_color: str
    user_id: str
    created_at: datetime
    vote_colors: Dict[str, int] = {"red": 0, "blue": 0, "green": 0}
    user_vote_color: Optional[str] = None  # None = no vote, or "red"/"blue"/"green"


# Area Schemas
class AreaCreate(BaseSchema):
    """Schema for creating a new area."""
    latlngs: List[Any]  # Flexible for different Leaflet structures
    color: PinColor
    category: CategoryType
    font_size: str


class AreaUpdate(BaseSchema):
    """Schema for updating an existing area."""
    latlngs: Optional[List[Any]] = None
    color: Optional[PinColor] = None
    category: Optional[CategoryType] = None
    font_size: Optional[str] = None


class Area(BaseSchema):
    """Schema for an area response."""
    id: int
    latlngs: List[Any]
    color: str
    original_color: str
    category: str
    font_size: str
    user_id: str
    created_at: datetime
    vote_colors: Dict[str, int] = {"red": 0, "blue": 0, "green": 0}
    user_vote_color: Optional[str] = None


# Map Data Schema
class MapData(BaseSchema):
    """Schema for all map data."""
    pins: List[Pin]
    areas: List[Area]


# User Schema
class UserIdResponse(BaseSchema):
    """Schema for user ID response."""
    user_id: str


# Search Schemas
class SearchResult(BaseModel):
    """Schema for search result."""
    lat: float
    lon: float  # Note: LocationIQ (like Nominatim) uses 'lon' not 'lng'
    display_name: str


# Error Schema
class ErrorResponse(BaseModel):
    """Schema for error responses."""
    error: str
    detail: Optional[str] = None


# Success Schema
class SuccessResponse(BaseModel):
    """Schema for successful deletion."""
    success: bool = True


# Vote Schemas
class VoteCreate(BaseSchema):
    """Schema for creating a color vote."""
    target_type: str = Field(..., pattern="^(pin|area)$")
    target_id: int
    vote_color: PinColor = Field(..., description="Color to vote: red, blue, or green")


class VoteResponse(BaseSchema):
    """Schema for a vote response."""
    id: int
    user_id: str
    target_type: str
    target_id: int
    vote_color: str
    created_at: datetime


# Categories list endpoint
class CategoryInfo(BaseModel):
    """Schema for category information."""
    slug: str
    label: str
    icon: str
