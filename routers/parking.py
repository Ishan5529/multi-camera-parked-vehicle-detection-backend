"""
Controllers for parking lot discovery endpoints.
"""

from fastapi import APIRouter, HTTPException, status
from models import LocationRequest, ParkingLot, FetchParkingResponse
from typing import List
import math

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


@router.post("/fetch_parking", response_model=FetchParkingResponse, response_model_exclude_none=True)
async def fetch_nearby_parking_lots(request: LocationRequest) -> FetchParkingResponse:
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
        
        # TODO: Implement actual parking lot database query
        # This would typically:
        # 1. Query parking lot database
        # 2. Filter by proximity to user location
        # 3. Calculate actual distances
        # 4. Fetch real-time availability data
        
        # Mock parking lots data
        mock_parking_lots: List[ParkingLot] = [
            ParkingLot(
                id="parking-lot-1",
                name="Downtown Parking",
                lat=latitude + 0.01,
                lng=longitude + 0.01,
                vacantSlots=25
            ),
            ParkingLot(
                id="parking-lot-2",
                name="Mall Parking",
                lat=latitude - 0.02,
                lng=longitude + 0.02,
                vacantSlots=42
            ),
            ParkingLot(
                id="parking-lot-3",
                name="Airport Parking",
                lat=latitude + 0.03,
                lng=longitude - 0.03,
                vacantSlots=15
            ),
            ParkingLot(
                id="parking-lot-4",
                name="Airport Parking - 2",
                lat=latitude + 0.04,
                lng=longitude - 0.04,
                vacantSlots=15
            ),
        ]

        # Use Haversine distance to keep and rank nearby lots.
        max_distance_km = 10.0
        lots_with_distance = [
            (lot, calculate_distance(latitude, longitude, lot.lat, lot.lng))
            for lot in mock_parking_lots
        ]

        nearby_lots = [
            lot for lot, distance_km in lots_with_distance if distance_km <= max_distance_km
        ]

        # nearby_lots.sort(
        #     key=lambda lot: calculate_distance(latitude, longitude, lot.lat, lot.lng)
        # )

        return FetchParkingResponse(parkingLots=nearby_lots)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch parking lots: {str(e)}"
        )
