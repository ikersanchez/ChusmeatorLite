"""Pydantic schemas matching the OpenAPI specification."""
from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator
from pydantic.alias_generators import to_camel
from app.models import PinColor


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
    text: str = Field(..., max_length=35, description="Pin description text")
    color: PinColor = PinColor.BLUE


class PinUpdate(BaseModel):
    """Schema for updating an existing pin."""
    lat: Optional[float] = Field(None, description="Latitude coordinate")
    lng: Optional[float] = Field(None, description="Longitude coordinate")
    text: Optional[str] = Field(None, max_length=35, description="Pin description text")
    color: Optional[PinColor] = None



class Pin(BaseSchema):
    """Schema for a pin response."""
    id: int
    lat: float
    lng: float
    text: str
    color: str
    user_id: str
    created_at: datetime
    votes: int = 0
    user_vote_value: int = 0  # 0 = no vote, 1 = liked, -1 = disliked
    comment_count: int = 0


# Area Schemas
class AreaCreate(BaseSchema):
    """Schema for creating a new area."""
    latlngs: List[Any]  # Flexible for different Leaflet structures
    color: PinColor
    text: str = Field(..., max_length=35)
    font_size: str


class AreaUpdate(BaseSchema):
    """Schema for updating an existing area."""
    latlngs: Optional[List[Any]] = None
    color: Optional[PinColor] = None
    text: Optional[str] = Field(None, max_length=35)
    font_size: Optional[str] = None



class Area(BaseSchema):
    """Schema for an area response."""
    id: int
    latlngs: List[Any]
    color: str
    text: str
    font_size: str
    user_id: str
    created_at: datetime
    votes: int = 0
    user_vote_value: int = 0  # 0 = no vote, 1 = liked, -1 = disliked
    comment_count: int = 0


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
    """Schema for creating a vote."""
    target_type: str = Field(..., pattern="^(pin|area)$")
    target_id: int
    value: int = Field(default=1, description="1 = like, -1 = dislike")

    @field_validator('value')
    @classmethod
    def value_must_be_plus_or_minus_one(cls, v):
        if v not in (1, -1):
            raise ValueError('value must be 1 (like) or -1 (dislike)')
        return v


class VoteResponse(BaseSchema):
    """Schema for a vote response."""
    id: int
    user_id: str
    target_type: str
    target_id: int
    value: int
    created_at: datetime


# Comment Schemas
class CommentCreate(BaseModel):
    """Schema for creating a comment on a pin."""
    text: str = Field(..., max_length=100, description="Comment text (max 100 characters)")


class Comment(BaseSchema):
    """Schema for a comment response."""
    id: int
    target_type: str
    target_id: int
    user_id: str
    text: str
    created_at: datetime
