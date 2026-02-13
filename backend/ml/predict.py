# backend/ml/predict.py
# Add this to your backend's ml folder or create a new endpoint file

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import tensorflow as tf
import numpy as np
from PIL import Image
import io
import base64
from typing import Optional

router = APIRouter()

# Load the model once at startup
MODEL_PATH = "ml/model/civic_issue_imgmodel (1).keras"
CLASS_INDICES_PATH = "ml/model/class_indices.json"

try:
    model = tf.keras.models.load_model(MODEL_PATH)
    print(f"✓ Model loaded successfully from {MODEL_PATH}")
    
    with open(CLASS_INDICES_PATH, 'r') as f:
        import json
        class_indices = json.load(f)
    # Reverse the class_indices to get index -> department mapping
    index_to_department = {v: k for k, v in class_indices.items()}
    print(f"✓ Class indices loaded: {class_indices}")
except Exception as e:
    print(f"✗ Error loading model: {e}")
    model = None
    index_to_department = {}


class PredictRequest(BaseModel):
    """Request model for prediction"""
    image_base64: str
    
class PredictResponse(BaseModel):
    """Response model for prediction"""
    department: str
    confidence: float
    all_probabilities: Optional[dict] = None


def preprocess_image(image_base64: str) -> np.ndarray:
    """
    Preprocess the base64 image for model prediction
    
    Args:
        image_base64: Base64 encoded image string
        
    Returns:
        Preprocessed image array ready for model input
    """
    try:
        # Remove data URL prefix if present
        if ',' in image_base64:
            image_base64 = image_base64.split(',')[1]
        
        # Decode base64 to bytes
        image_bytes = base64.b64decode(image_base64)
        
        # Open image using PIL
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if necessary (handles RGBA, grayscale, etc.)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize to model's expected input size (224x224 for most CNNs)
        image = image.resize((224, 224))
        
        # Convert to numpy array
        image_array = np.array(image)
        
        # Normalize pixel values to [0, 1]
        image_array = image_array.astype('float32') / 255.0
        
        # Add batch dimension
        image_array = np.expand_dims(image_array, axis=0)
        
        return image_array
        
    except Exception as e:
        raise ValueError(f"Error preprocessing image: {str(e)}")


@router.post("/predict", response_model=PredictResponse)
async def predict_department(request: PredictRequest):
    """
    Predict the department responsible for the civic issue shown in the image
    
    Args:
        request: PredictRequest containing base64 encoded image
        
    Returns:
        PredictResponse with predicted department and confidence
    """
    if model is None:
        raise HTTPException(
            status_code=500, 
            detail="Model not loaded. Please contact administrator."
        )
    
    try:
        # Preprocess the image
        processed_image = preprocess_image(request.image_base64)
        
        # Make prediction
        predictions = model.predict(processed_image, verbose=0)
        
        # Get the predicted class index
        predicted_index = np.argmax(predictions[0])
        confidence = float(predictions[0][predicted_index])
        
        # Get the department name
        predicted_department = index_to_department.get(
            predicted_index, 
            "Manual"
        )
        
        # Create probability dictionary for all departments
        all_probabilities = {
            index_to_department.get(i, f"Unknown_{i}"): float(predictions[0][i])
            for i in range(len(predictions[0]))
        }
        
        return PredictResponse(
            department=predicted_department,
            confidence=confidence,
            all_probabilities=all_probabilities
        )
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Prediction failed: {str(e)}"
        )


# Include this router in your main FastAPI app:
# In your main app.py or similar:
# from ml.predict import router as predict_router
# app.include_router(predict_router, prefix="/ml", tags=["ML Prediction"])