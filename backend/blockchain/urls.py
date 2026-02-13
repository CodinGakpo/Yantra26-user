"""
URL Configuration for Blockchain API endpoints
"""

from django.urls import path
from . import views

app_name = 'blockchain'

urlpatterns = [
    # Evidence management
    path(
        'reports/<str:tracking_id>/evidence/',
        views.upload_evidence_with_blockchain,
        name='upload-evidence'
    ),
    path(
        'reports/<str:tracking_id>/evidence/verify/',
        views.verify_evidence_integrity,
        name='verify-evidence'
    ),
    
    # Blockchain status and audit
    path(
        'reports/<str:tracking_id>/status/',
        views.get_blockchain_status,
        name='blockchain-status'
    ),
    path(
        'reports/<str:tracking_id>/audit-trail/',
        views.get_complaint_audit_trail,
        name='audit-trail'
    ),
]
