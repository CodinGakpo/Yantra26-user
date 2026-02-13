# backend/ml/urls.py
# URL configuration for ML prediction endpoints

from django.urls import path
from . import views

app_name = 'ml'

urlpatterns = [
    # Main prediction endpoint
    path('predict/', views.predict_department, name='predict'),
    
    # Health check endpoint
    path('health/', views.ml_health_check, name='health'),
]