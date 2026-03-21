from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from shapely.geometry import Polygon as ShapelyPolygon
from app.models import AreaModel
from app import schemas
from app.config import settings

class AreaService:
    @staticmethod
    def create_area(db: Session, area_data: schemas.AreaCreate, user_id: str) -> AreaModel:
        # 1. Size check
        if area_data.latlngs:
            # Flatten latlngs if it's a nested list (Leaflet often sends [[p1, p2, ...]])
            coords = []
            for sublist in area_data.latlngs:
                if isinstance(sublist, list):
                    for p in sublist:
                        if isinstance(p, dict):
                            coords.append(p)
                elif isinstance(sublist, dict):
                    coords.append(sublist)
            
            if coords:
                lats = [c.get('lat') for c in coords if 'lat' in c]
                lngs = [c.get('lng') for c in coords if 'lng' in c]
                
                if lats and lngs:
                    lat_delta = max(lats) - min(lats)
                    lng_delta = max(lngs) - min(lngs)
                    
                    if max(lat_delta, lng_delta) > settings.max_area_size_deg:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Area too large: Bounding box must be smaller than {settings.max_area_size_deg} degrees."
                        )

        # 2. Rate limit check: max 20 areas per 24 hours
        one_day_ago = datetime.now(timezone.utc) - timedelta(days=1)
        area_count = db.query(func.count(AreaModel.id)).filter(
            AreaModel.user_id == user_id,
            AreaModel.created_at >= one_day_ago
        ).scalar()
        
        if area_count >= settings.max_areas_per_day:
            raise HTTPException(
                status_code=429, 
                detail=f"Rate limit exceeded: Maximum {settings.max_areas_per_day} areas per day allowed."
            )

        # 3. Overlap check
        if area_data.latlngs:
            new_poly = AreaService._to_shapely_polygon(area_data.latlngs)
            if new_poly:
                existing_areas = db.query(AreaModel).all()
                for existing in existing_areas:
                    existing_poly = AreaService._to_shapely_polygon(existing.latlngs)
                    if existing_poly and new_poly.intersects(existing_poly):
                        # Calculate intersection area to avoid tiny overlaps due to floating point errors
                        # but for neighborhoods, even a small overlap might be intentional? 
                        # Shapely's intersects is usually what we want.
                        # If they just touch, it's fine. Overlap means intersection area > 0.
                        if new_poly.intersection(existing_poly).area > 1e-9:
                            raise HTTPException(
                                status_code=400,
                                detail="Area overlaps with an existing one. Please draw in a clear spot!"
                            )

        db_area = AreaModel(
            latlngs=area_data.latlngs,
            color=area_data.color.value if hasattr(area_data.color, 'value') else area_data.color,
            text=area_data.text,
            font_size=area_data.font_size,
            user_id=user_id
        )
        db.add(db_area)
        db.commit()
        db.refresh(db_area)
        return db_area

    @staticmethod
    def get_all_areas(db: Session) -> list[AreaModel]:
        return db.query(AreaModel).all()

    @staticmethod
    def update_area(db: Session, area_id: int, user_id: str, update_data: schemas.AreaUpdate) -> AreaModel:
        area = db.query(AreaModel).filter(AreaModel.id == area_id).first()
        if not area:
            raise HTTPException(status_code=404, detail="Area not found")
        if area.user_id != user_id:
            raise HTTPException(status_code=403, detail="Unauthorized: You can only edit your own areas")
            
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if key == 'color' and hasattr(value, 'value'):
                setattr(area, key, value.value)
            else:
                setattr(area, key, value)
                
        db.commit()
        db.refresh(area)
        return area

    @staticmethod
    def delete_area(db: Session, area_id: int, user_id: str) -> bool:
        area = db.query(AreaModel).filter(AreaModel.id == area_id).first()
        if not area:
            return False
        if area.user_id != user_id:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Unauthorized: You can only delete your own areas")
        
        db.delete(area)
        db.commit()
        return True

    @staticmethod
    def _to_shapely_polygon(latlngs) -> ShapelyPolygon | None:
        """Convert Leaflet-style latlngs to a Shapely Polygon."""
        try:
            # Flatten latlngs if it's a nested list
            coords = []
            for sublist in latlngs:
                if isinstance(sublist, list):
                    for p in sublist:
                        if isinstance(p, dict):
                            coords.append((p.get('lng'), p.get('lat')))
                elif isinstance(sublist, dict):
                    coords.append((sublist.get('lng'), sublist.get('lat')))
            
            if len(coords) < 3:
                return None
            
            # Ensure it's a closed ring for Shapely
            if coords[0] != coords[-1]:
                coords.append(coords[0])
                
            return ShapelyPolygon(coords)
        except Exception as e:
            print(f"Error converting to shapely polygon: {e}")
            return None
