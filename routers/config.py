"""
Controllers for parking configuration endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from db_models import ParkingConfiguration
from models import UpdateConfigRequest, UpdateConfigResponse
import uuid as uuid_lib

router = APIRouter(tags=["Configuration"])


@router.post("/update_config", response_model=UpdateConfigResponse)
async def update_parking_configuration(config: UpdateConfigRequest, db: Session = Depends(get_db)):
    """
    Update parking lot configuration.
    
    Args:
        config: Configuration update request containing parking lot name, address, and UUID
        
    Returns:
        UpdateConfigResponse with the configuration UUID
        
    Raises:
        HTTPException: If configuration is invalid
    """
    try:
        # Extract UUID - try all possible field names from frontend
        config_uuid = (config.uuid or config.configUuid or config.config_uuid or "").strip()
        
        if not config_uuid:
            # Generate new UUID if none provided
            config_uuid = str(uuid_lib.uuid4())
        
        parking_lot_name = (config.parkingLotName or config.parking_lot_name or "").strip()
        parking_lot_address = (config.parkingLotAddress or config.parking_lot_address or "").strip()
        
        if not parking_lot_name or not parking_lot_address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parking lot name and address are required"
            )
        
        existing_record = db.query(ParkingConfiguration).filter(ParkingConfiguration.uuid == config_uuid).first()

        if existing_record:
            existing_record.parking_lot_name = parking_lot_name
            existing_record.parking_lot_address = parking_lot_address
        else:
            db.add(
                ParkingConfiguration(
                    uuid=config_uuid,
                    parking_lot_name=parking_lot_name,
                    parking_lot_address=parking_lot_address,
                    vacant_lot=0,
                )
            )

        db.commit()

        return UpdateConfigResponse(uuid=config_uuid)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update parking configuration: {str(e)}"
        )
