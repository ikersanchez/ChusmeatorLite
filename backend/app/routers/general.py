"""API router for general endpoints (user, map-data, search, categories)."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import httpx
from app import schemas
from app.database import get_db
from app.dependencies import get_current_user_id
from app.config import settings
from app.services.pin_service import PinService
from app.services.area_service import AreaService
from app.services.vote_service import VoteService
from app.models import CATEGORY_LABELS, CATEGORY_ICONS, CategoryType

router = APIRouter(prefix="/api", tags=["General"])


@router.get("/user", response_model=schemas.UserIdResponse)
def get_user_id(user_id: str = Depends(get_current_user_id)):
    """Get current user ID from header."""
    return schemas.UserIdResponse(user_id=user_id)


@router.get("/categories", response_model=List[schemas.CategoryInfo])
def get_categories():
    """Get all available categories with labels and icons."""
    return [
        schemas.CategoryInfo(
            slug=cat.value,
            label=CATEGORY_LABELS[cat],
            icon=CATEGORY_ICONS[cat]
        )
        for cat in CategoryType
    ]


@router.get("/map-data", response_model=schemas.MapData)
def get_map_data(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get all map data (pins and areas) with vote color counts."""
    # Vote aggregations
    pin_vote_colors = VoteService.get_vote_color_counts(db, "pin")
    area_vote_colors = VoteService.get_vote_color_counts(db, "area")
    pin_user_votes = VoteService.get_user_vote_colors(db, "pin", user_id)
    area_user_votes = VoteService.get_user_vote_colors(db, "area", user_id)

    # Get all pins
    pins = PinService.get_all_pins(db)
    default_vote_colors = {"red": 0, "blue": 0, "green": 0}
    
    pin_list = [
        schemas.Pin(
            id=pin.id,
            lat=pin.lat,
            lng=pin.lng,
            category=pin.category,
            color=pin.color,
            original_color=pin.original_color,
            user_id=pin.user_id,
            created_at=pin.created_at,
            vote_colors=pin_vote_colors.get(pin.id, dict(default_vote_colors)),
            user_vote_color=pin_user_votes.get(pin.id),
        )
        for pin in pins
    ]

    # Get all areas
    areas = AreaService.get_all_areas(db)
    area_list = [
        schemas.Area(
            id=area.id,
            latlngs=area.latlngs,
            color=area.color,
            original_color=area.original_color,
            category=area.category,
            font_size=area.font_size,
            user_id=area.user_id,
            created_at=area.created_at,
            vote_colors=area_vote_colors.get(area.id, dict(default_vote_colors)),
            user_vote_color=area_user_votes.get(area.id),
        )
        for area in areas
    ]

    return schemas.MapData(pins=pin_list, areas=area_list)


@router.get("/search", response_model=List[schemas.SearchResult])
async def search_address(q: str = Query(..., description="Search query")):
    """
    Search for addresses using LocationIQ.
    Proxies the request to protect the API key and avoid CORS issues.
    """
    if not q or not q.strip():
        raise HTTPException(status_code=400, detail="Search query is required")

    if not settings.locationiq_api_key:
        print("ERROR: locationiq_api_key is empty or None")
        raise HTTPException(status_code=500, detail="LocationIQ API key is not configured")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                settings.locationiq_url,
                params={
                    "key": settings.locationiq_api_key,
                    "q": q,
                    "format": "json"
                },
                headers={"User-Agent": "Chusmeator/1.0"},
                timeout=10.0
            )
            response.raise_for_status()
            results = response.json()
            
            # LocationIQ returns a list and might have identical keys to Nominatim
            if not isinstance(results, list):
                if isinstance(results, dict) and "error" in results:
                    return []
                results = []

            return [
                schemas.SearchResult(
                    lat=float(item["lat"]),
                    lon=float(item["lon"]),
                    display_name=item["display_name"]
                )
                for item in results
            ]
    except httpx.HTTPStatusError as e:
        print(f"HTTPStatusError: {e.response.status_code} - {e.response.text}")
        # LocationIQ returns 404 when no results are found
        if e.response.status_code == 404:
            return []
        raise HTTPException(status_code=500, detail=f"Search failed: {e.response.text}")
    except httpx.HTTPError as e:
        print(f"HTTPError: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
    except Exception as e:
        print(f"Generic Exception: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
