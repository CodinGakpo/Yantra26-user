# backend/ml/views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import tensorflow as tf
import numpy as np
from PIL import Image
import io
import base64
import json
from pathlib import Path

from .hybrid_classifier import hybrid_classify


BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "model" / "civic_issue_imgmodel (1).keras"
CLASS_INDICES_PATH = BASE_DIR / "model" / "class_indices.json"
CONFIDENCE_THRESHOLD = 0.45

_model = None
_index_to_department = {}


def load_model():
    """
    Load the ML model and class indices.
    This is called once when Django starts.
    """
    global _model, _index_to_department
    
    if _model is not None:
        return
    try:
        _model = tf.keras.models.load_model(str(MODEL_PATH))
        print(f"ML Model loaded successfully from {MODEL_PATH}")
        
        with open(CLASS_INDICES_PATH, 'r') as f:
            class_indices = json.load(f)
        
        _index_to_department = {v: k for k, v in class_indices.items()}
        print(f"Class indices loaded: {class_indices}")
        
    except Exception as e:
        print(f"Error loading ML model: {e}")
        _model = None
        _index_to_department = {}

load_model()


def preprocess_image(image_base64):
    """
    Preprocess the base64 image for model prediction.
    
    Args:
        image_base64: Base64 encoded image string
        
    Returns:
        Preprocessed image array ready for model input
        
    Raises:
        ValueError: If image preprocessing fails
    """
    try:
        if ',' in image_base64:
            image_base64 = image_base64.split(',')[1]

        image_bytes = base64.b64decode(image_base64)
        
        image = Image.open(io.BytesIO(image_bytes))
        
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        image = image.resize((224, 224))
        
        image_array = np.array(image)
        
        image_array = image_array.astype('float32') / 255.0
        
        image_array = np.expand_dims(image_array, axis=0)
        
        return image_array
        
    except Exception as e:
        raise ValueError(f"Error preprocessing image: {str(e)}")


@api_view(['POST'])
@permission_classes([IsAuthenticated])
# @permission_classes([AllowAny])
def predict_department(request):
    """
    HYBRID API endpoint: Combines image and text classification
    
    Request body:
        {
            "image_base64": "base64_encoded_image_string",
            "title": "Issue title",
            "description": "Issue description"
        }
    
    Response:
        {
            "department": "Public Works Department",
            "confidence": 0.95,
            "is_valid": true,
            "method": "HYBRID_AGREEMENT",
            "reason": "Image and text agree",
            "image_result": {...},
            "text_result": {...}
        }
    """
    if _model is None:
        return Response(
            {
                "error": "ML model not loaded",
                "detail": "The ML model failed to load. Please contact the administrator."
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    image_base64 = request.data.get('image_base64')
    title = request.data.get('title', '').strip()
    description = request.data.get('description', '').strip()
    if not image_base64:
        return Response(
            {
                "error": "Missing image_base64",
                "detail": "Please provide 'image_base64' in the request body."
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        print("=" * 60)
        print("HYBRID CLASSIFICATION STARTED")
        print(f"Title: {title[:50]}...")
        print(f"Description: {description[:50]}...")
        
        print("\n STEP 1: Image Classification")
        
        processed_image = preprocess_image(image_base64)
        print(" Image preprocessed")
        
        predictions = _model.predict(processed_image, verbose=0)
        
        predicted_index = np.argmax(predictions[0])
        image_confidence = float(predictions[0][predicted_index])
        
        image_department = _index_to_department.get(predicted_index, "Manual")
        
        if image_confidence < CONFIDENCE_THRESHOLD:
            image_department = "Manual"
        
        print(f"Image Result: {image_department} (confidence: {image_confidence:.3f})")
        
        print("\nSTEP 2: Hybrid Classification")
        
        hybrid_result = hybrid_classify(
            image_department=image_department,
            image_confidence=image_confidence,
            title=title,
            description=description,
            image_threshold=CONFIDENCE_THRESHOLD
        )
        
        print(f"    Method: {hybrid_result['method']}")
        print(f"    Final Department: {hybrid_result['final_department']}")
        print(f"    Confidence: {hybrid_result['confidence']:.3f}")
        print(f"    Reason: {hybrid_result['reason']}")
        
        final_dept = hybrid_result["final_department"]
        final_conf = hybrid_result["confidence"]
        
        response_data = {
            "department": final_dept,
            "confidence": final_conf,
            "is_valid": final_dept != "Manual",
            "method": hybrid_result["method"],
            "reason": hybrid_result["reason"],
            "image_result": hybrid_result.get("image_result"),
            "text_result": hybrid_result.get("text_result")
        }
        
        print(f"\nFINAL: {final_dept} (valid: {final_dept != 'Manual'})")
        print("=" * 60)
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    except ValueError as ve:
        print(f"ValueError: {ve}")
        return Response(
            {
                "error": "Invalid image",
                "detail": str(ve)
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        print(f"Prediction error: {e}")
        import traceback
        traceback.print_exc()
        return Response(
            {
                "error": "Prediction failed",
                "detail": str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def ml_health_check(request):
    """
    Check if the ML model is loaded and ready.
    Also checks Ollama connectivity.
    """
    ollama_healthy = False
    try:
        import requests
        resp = requests.get("http://localhost:11434/api/tags", timeout=2)
        ollama_healthy = resp.status_code == 200
    except:
        pass
    
    return Response(
        {
            "status": "healthy" if (_model is not None and ollama_healthy) else "degraded",
            "image_model_loaded": _model is not None,
            "departments_count": len(_index_to_department),
            "ollama_available": ollama_healthy,
            "text_classification": "enabled" if ollama_healthy else "disabled"
        },
        status=status.HTTP_200_OK
    )