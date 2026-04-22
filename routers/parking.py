"""
Controllers for parking lot discovery endpoints.
"""

import math
from typing import List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from db_models import ParkingConfiguration
from models import FetchParkingResponse, LocationRequest, ParkingLot

router = APIRouter(tags=["Parking"])


def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate distance between two coordinates using Haversine formula (in km).
    
    Args:
        lat1, lng1: First coordinate (latitude, longitude)
        lat2, lng2: Second coordinate (latitude, longitude)
        
    Returns:
        Distance in kilometers
    """
    R = 6371  # Earth's radius in km
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


def parse_lat_lng(address: str) -> Optional[Tuple[float, float]]:
    """Parse coordinates stored as 'lat, lng' in the parking_lot_address field."""
    if not address:
        return None

    parts = [part.strip() for part in address.split(", ")]
    if len(parts) != 2:
        return None

    try:
        latitude = float(parts[0])
        longitude = float(parts[1])
    except (TypeError, ValueError):
        return None

    return latitude, longitude


@router.post("/fetch_parking", response_model=FetchParkingResponse, response_model_exclude_none=True)
async def fetch_nearby_parking_lots(request: LocationRequest, db: Session = Depends(get_db)) -> FetchParkingResponse:
    """
    Fetch nearby parking lots based on current location.
    
    Args:
        request: Location request containing latitude and longitude
        
    Returns:
        List of nearby parking lots with availability information
        
    Raises:
        HTTPException: If location is invalid or query fails
    """
    try:
        # Extract coordinates - try multiple field names for flexibility
        latitude = request.latitude or request.lat
        longitude = request.longitude or request.lng
        
        if request.current_location:
            latitude = latitude or request.current_location.get("lat")
            longitude = longitude or request.current_location.get("lng")
        
        # Validate coordinates
        if latitude is None or longitude is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Latitude and longitude are required"
            )
        
        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Latitude and longitude must be valid numbers"
            )
        
        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid coordinate ranges. Latitude must be -90 to 90, Longitude must be -180 to 180"
            )
        
        parking_configurations = db.query(ParkingConfiguration).all()

        parking_lots: List[ParkingLot] = []
        for configuration in parking_configurations:
            coordinates = parse_lat_lng(configuration.parking_lot_address)
            if coordinates is None:
                continue

            lot_lat, lot_lng = coordinates
            parking_lots.append(
                ParkingLot(
                    id=configuration.uuid,
                    name=configuration.parking_lot_name,
                    lat=lot_lat,
                    lng=lot_lng,
                    vacantSlots=configuration.vacant_lot,
                )
            )

        # Use Haversine distance to keep and rank nearby lots.
        max_distance_km = 20.0
        lots_with_distance = [
            (lot, calculate_distance(latitude, longitude, lot.lat, lot.lng))
            for lot in parking_lots
        ]

        nearby_lots = [
            lot for lot, distance_km in lots_with_distance if distance_km <= max_distance_km
        ]

        return FetchParkingResponse(parkingLots=nearby_lots)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch parking lots: {str(e)}"
        )
