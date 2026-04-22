"""
Controllers for prediction endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from db_models import ParkingConfiguration
from models import PredictRequest
from typing import Dict, Any

router = APIRouter(tags=["Prediction"])


@router.post("/predict")
async def predict_parked_vehicles(request: PredictRequest, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Send snapshots for vehicle detection and prediction.
    
    Args:
        request: Prediction request containing configuration UUID and camera snapshots
        
    Returns:
        Prediction results as JSON or processed response
        
    Raises:
        HTTPException: If prediction fails or invalid snapshots provided
    """
    try:
        config_uuid = request.uuid
        snapshots = request.snapshots
        
        if not config_uuid or not config_uuid.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Configuration UUID is required"
            )
        
        if not snapshots or len(snapshots) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one snapshot is required for prediction"
            )

        parking_configuration = (
            db.query(ParkingConfiguration).filter(ParkingConfiguration.uuid == config_uuid).first()
        )

        if parking_configuration is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parking configuration not found"
            )
        
        # Validate snapshots
        for snapshot in snapshots:
            if not snapshot.image:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Each snapshot must contain an image"
                )
            if not snapshot.cameraId or not snapshot.cameraName:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Each snapshot must have cameraId and cameraName"
                )
        
        # TODO: Implement actual vehicle detection logic here
        # This would typically:
        # 1. Decode base64 images
        # 2. Run ML model inference
        # 3. Process coordinates and annotations
        # 4. Return prediction results
        
        vacant_lot = len(snapshots)
        parking_configuration.vacant_lot = vacant_lot
        db.commit()

        prediction_results = {
            "uuid": config_uuid,
            "status": "success",
            "detected_vehicles": len(snapshots),
            "snapshots_processed": len(snapshots),
            "vacant_lot": vacant_lot,
            "results": [
                {
                    "cameraId": snapshot.cameraId,
                    "cameraName": snapshot.cameraName,
                    "detection_count": 0,
                    "predictions": []
                }
                for snapshot in snapshots
            ]
        }
        
        return prediction_results
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )
