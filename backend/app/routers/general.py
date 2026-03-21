"""API router for general endpoints (user, map-data, search)."""
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
from app.services.comment_service import CommentService

router = APIRouter(prefix="/api", tags=["General"])


@router.get("/user", response_model=schemas.UserIdResponse)
def get_user_id(user_id: str = Depends(get_current_user_id)):
    """Get current user ID from header."""
    return schemas.UserIdResponse(user_id=user_id)


@router.get("/map-data", response_model=schemas.MapData)
def get_map_data(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get all map data (pins and areas) with vote counts."""
    # Vote aggregations
    pin_votes = VoteService.get_vote_counts(db, "pin")
    area_votes = VoteService.get_vote_counts(db, "area")
    pin_user_vote_values = VoteService.get_user_vote_values(db, "pin", user_id)
    area_user_vote_values = VoteService.get_user_vote_values(db, "area", user_id)

    # Comment counts
    pin_comments = CommentService.get_comment_counts(db, "pin")
    area_comments = CommentService.get_comment_counts(db, "area")

    # Get all pins
    pins = PinService.get_all_pins(db)
    pin_list = [
        schemas.Pin(
            id=pin.id,
            lat=pin.lat,
            lng=pin.lng,
            text=pin.text,
            color=pin.color,
            user_id=pin.user_id,
            created_at=pin.created_at,
            votes=pin_votes.get(pin.id, 0),
            user_vote_value=pin_user_vote_values.get(pin.id, 0),
            comment_count=pin_comments.get(pin.id, 0),
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
            text=area.text,
            font_size=area.font_size,
            user_id=area.user_id,
            created_at=area.created_at,
            votes=area_votes.get(area.id, 0),
            user_vote_value=area_user_vote_values.get(area.id, 0),
            comment_count=area_comments.get(area.id, 0),
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
