"""
Pydantic models for request and response validation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class Coordinate(BaseModel):
    """Annotation coordinate model."""
    id: Optional[str] = None
    label: Optional[str] = None
    x: float
    y: float
    width: float
    height: float
    rotation: float = 0.0


class Snapshot(BaseModel):
    """Snapshot model for prediction."""
    cameraId: str
    cameraName: str
    image: str  # Base64 encoded image
    frame: Optional[int] = None
    annotations: Optional[List[Coordinate]] = []
    coordinates: Optional[List[Coordinate]] = []


class UpdateConfigRequest(BaseModel):
    """Request model for updating parking configuration."""
    uuid: str
    configUuid: Optional[str] = None
    config_uuid: Optional[str] = None
    parkingLotName: str
    parkingLotAddress: str
    parking_lot_name: Optional[str] = None
    parking_lot_address: Optional[str] = None


class UpdateConfigResponse(BaseModel):
    """Response model for configuration update."""
    uuid: str


class PredictRequest(BaseModel):
    """Request model for prediction."""
    uuid: str
    snapshots: List[Snapshot]


class LocationRequest(BaseModel):
    """Request model for location-based queries."""
    lat: float
    lng: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    current_location: Optional[dict] = None


class ParkingLot(BaseModel):
    """Parking lot information model."""
    id: str
    name: str
    lat: float
    lng: float
    vacantSlots: int = 0


class FetchParkingResponse(BaseModel):
    """Response model for fetching parking lots."""
    parkingLots: List[ParkingLot]
    parking_lots: Optional[List[ParkingLot]] = None
