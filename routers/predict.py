"""
Controllers for prediction endpoints.
"""

import base64
import numpy as np
from io import BytesIO
from PIL import Image
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from db_models import ParkingConfiguration
from models import PredictRequest
from typing import Dict, Any


def decode_base64_image(image_str: str) -> Image.Image:
    """
    Decode a base64 encoded image string to a PIL Image.
    
    Args:
        image_str: Base64 encoded image string
        
    Returns:
        PIL Image object
        
    Raises:
        ValueError: If image decoding fails
    """
    try:
        # Remove data URI prefix if present (e.g., "data:image/png;base64,")
        if "," in image_str:
            image_str = image_str.split(",", 1)[1]
        
        image_data = base64.b64decode(image_str)
        image = Image.open(BytesIO(image_data))
        return image.convert("RGB")
    except Exception as e:
        raise ValueError(f"Failed to decode image: {str(e)}")


def crop_bounding_box(image: Image.Image, x: float, y: float, width: float, height: float) -> Image.Image:
    """
    Crop a bounding box region from an image.
    
    Args:
        image: PIL Image object
        x: X coordinate of top-left corner (normalized 0-1 or pixel value)
        y: Y coordinate of top-left corner (normalized 0-1 or pixel value)
        width: Width of bounding box (normalized 0-1 or pixel value)
        height: Height of bounding box (normalized 0-1 or pixel value)
        
    Returns:
        Cropped PIL Image object
    """
    img_width, img_height = image.size
    
    # Check if coordinates are normalized (0-1) and convert to pixel coordinates
    if x <= 1 and y <= 1 and width <= 1 and height <= 1:
        x = int(x * img_width)
        y = int(y * img_height)
        width = int(width * img_width)
        height = int(height * img_height)
    else:
        x = int(x)
        y = int(y)
        width = int(width)
        height = int(height)
    
    # Define crop box (left, top, right, bottom)
    left = max(0, x)
    top = max(0, y)
    right = min(img_width, x + width)
    bottom = min(img_height, y + height)
    
    return image.crop((left, top, right, bottom))


def predict_vehicle_in_slot(image: Image.Image) -> int:
    """
    Placeholder binary classifier to predict if a parking slot is empty or filled.
    
    Args:
        image: PIL Image object (cropped parking slot)
        
    Returns:
        1 if slot is empty, 0 if slot is filled
    """
    # TODO: Replace with actual ML model inference
    # For now, return a placeholder value based on image analysis
    # This can be replaced with a real classifier that uses TensorFlow, PyTorch, etc.
    
    # Placeholder logic: analyzing image properties
    # In production, this would call a pre-trained model
    img_array = np.array(image)
    
    # Simple heuristic for placeholder: average brightness
    # (Empty slots tend to be brighter, but this is just a placeholder)
    avg_brightness = np.mean(img_array)
    
    # Placeholder decision (replace with actual model)
    is_empty = avg_brightness > 100  # arbitrary threshold for demo
    
    return 1 if is_empty else 0


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
        
        # Process snapshots and make predictions
        total_empty_slots = 0
        results = []
        
        for snapshot in snapshots:
            try:
                # Decode the base64 image
                image = decode_base64_image(snapshot.image)
                
                # Process bounding boxes and make predictions
                slot_predictions = []
                empty_count = 0
                
                if snapshot.coordinates and len(snapshot.coordinates) > 0:
                    for coord in snapshot.coordinates:
                        try:
                            # Crop the bounding box from the image
                            cropped_image = crop_bounding_box(
                                image, 
                                coord.x, coord.y, 
                                coord.width, coord.height
                            )
                            
                            # Get prediction for this slot (1=empty, 0=filled)
                            prediction = predict_vehicle_in_slot(cropped_image)
                            slot_predictions.append({
                                "id": coord.id,
                                "label": coord.label,
                                "prediction": prediction,
                                "is_empty": prediction == 1
                            })
                            
                            if prediction == 1:
                                empty_count += 1
                        except Exception as e:
                            # Log error for individual coordinate but continue processing
                            slot_predictions.append({
                                "id": coord.id,
                                "label": coord.label,
                                "error": str(e)
                            })
                    
                    total_empty_slots += empty_count
                
                results.append({
                    "cameraId": snapshot.cameraId,
                    "cameraName": snapshot.cameraName,
                    "empty_slots": empty_count,
                    "total_slots": len(snapshot.coordinates),
                    "predictions": slot_predictions
                })
                
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to process snapshot from camera {snapshot.cameraName}: {str(e)}"
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error processing snapshot from camera {snapshot.cameraName}: {str(e)}"
                )
        
        # Update database with total empty slots count
        parking_configuration.vacant_lot = total_empty_slots
        db.commit()

        prediction_results = {
            "uuid": config_uuid,
            "status": "success",
            "total_empty_slots": total_empty_slots,
            "snapshots_processed": len(snapshots),
            "vacant_lot": total_empty_slots,
            "results": results
        }
        
        return prediction_results
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )
