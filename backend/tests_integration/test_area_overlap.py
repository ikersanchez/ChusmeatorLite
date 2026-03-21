import pytest
from fastapi import HTTPException
from app.services.area_service import AreaService
from app.schemas import AreaCreate
from app.models import PinColor

def test_area_overlap_prevention(db_session):
    """Verify that overlapping areas are rejected."""
    user_id = "test_user"
    
    # 1. Create first area (0.005 x 0.005 deg)
    area1_data = AreaCreate(
        latlngs=[[{"lat": 40.0, "lng": -3.0}, {"lat": 40.005, "lng": -3.0}, {"lat": 40.005, "lng": -2.995}, {"lat": 40.0, "lng": -2.995}]],
        color=PinColor.BLUE,
        text="Area 1",
        font_size="16px"
    )
    AreaService.create_area(db_session, area1_data, user_id)
    
    # 2. Try to create an overlapping area
    area2_data = AreaCreate(
        latlngs=[[{"lat": 40.002, "lng": -2.998}, {"lat": 40.007, "lng": -2.998}, {"lat": 40.007, "lng": -2.993}, {"lat": 40.002, "lng": -2.993}]],
        color=PinColor.RED,
        text="Overlapping Area",
        font_size="16px"
    )
    
    with pytest.raises(HTTPException) as excinfo:
        AreaService.create_area(db_session, area2_data, user_id)
    
    assert excinfo.value.status_code == 400
    assert "overlaps" in excinfo.value.detail.lower()

def test_area_touching_allowed(db_session):
    """Verify that areas touching at edges are allowed."""
    user_id = "test_user_2"
    
    # 1. Create first area (0.005 x 0.005 deg)
    area1_data = AreaCreate(
        latlngs=[[{"lat": 40.0, "lng": -3.0}, {"lat": 40.005, "lng": -3.0}, {"lat": 40.005, "lng": -2.995}, {"lat": 40.0, "lng": -2.995}]],
        color=PinColor.BLUE,
        text="Area 1",
        font_size="16px"
    )
    AreaService.create_area(db_session, area1_data, user_id)
    
    # 2. Create second area touching the first one
    area2_data = AreaCreate(
        latlngs=[[{"lat": 40.005, "lng": -3.0}, {"lat": 40.01, "lng": -3.0}, {"lat": 40.01, "lng": -2.995}, {"lat": 40.005, "lng": -2.995}]],
        color=PinColor.GREEN,
        text="Touching Area",
        font_size="16px"
    )
    
    # This should succeed
    saved_area = AreaService.create_area(db_session, area2_data, user_id)
    assert saved_area.text == "Touching Area"
