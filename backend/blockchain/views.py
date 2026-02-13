"""
Additional views for blockchain integration.

Add these to your report/views.py or import them in urls.py
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings

import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_evidence_with_blockchain(request, tracking_id):
    """
    Upload evidence file locally and anchor hash on blockchain.
    
    POST /api/reports/{tracking_id}/evidence/
    
    Request body:
    - file: File upload
    
    Response:
    {
        "file_path": "uploads/...",
        "file_url": "/media/uploads/...",
        "file_hash": "abc123...",
        "tx_hash": "0x...",
        "message": "Evidence uploaded and anchored on blockchain"
    }
    """
    try:
        from report.models import IssueReport
        from blockchain.ipfs_service import get_local_storage_service
        from blockchain.services import get_blockchain_service
        from blockchain.signals import log_evidence_uploaded
        
        # Get complaint
        try:
            complaint = IssueReport.objects.get(tracking_id=tracking_id)
        except IssueReport.DoesNotExist:
            return Response(
                {"error": "Complaint not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check permission
        if complaint.user != request.user:
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get uploaded file
        if 'file' not in request.FILES:
            return Response(
                {"error": "No file provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        uploaded_file = request.FILES['file']
        file_content = uploaded_file.read()
        file_name = uploaded_file.name
        
        # Save to local storage
        storage_service = get_local_storage_service()
        file_path, file_url = storage_service.upload_file(
            file_content, 
            file_name,
            complaint_id=tracking_id
        )
        
        if not file_path:
            return Response(
                {"error": "Failed to save file locally"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Compute file hash
        file_hash = storage_service.compute_file_hash(file_content)
        
        # Trigger blockchain anchoring (async)
        log_evidence_uploaded(
            complaint_id=tracking_id,
            file_path=file_path,
            file_hash=file_hash,
            file_name=file_name
        )
        
        return Response({
            "file_path": file_path,
            "file_url": file_url,
            "file_hash": file_hash,
            "message": "Evidence uploaded locally. Blockchain anchoring in progress.",
            "note": "Check blockchain transaction status at /api/blockchain/status/{tracking_id}/"
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Evidence upload failed: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_evidence_integrity(request, tracking_id):
    """
    Verify evidence file integrity against blockchain record.
    
    POST /api/reports/{tracking_id}/evidence/verify/
    
    Request body:
    - file: File to verify
    
    Response:
    {
        "verified": true,
        "file_hash": "abc123...",
        "block_timestamp": 1234567890,
        "anchored_at": "2026-02-09T10:30:00Z",
        "ipfs_cid": "Qm..."
    }
    """
    try:
        from blockchain.services import get_blockchain_service
        
        # Get uploaded file
        if 'file' not in request.FILES:
            return Response(
                {"error": "No file provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        uploaded_file = request.FILES['file']
        file_content = uploaded_file.read()
        
        # Verify against blockchain
        service = get_blockchain_service()
        verified, details = service.verify_evidence_integrity(
            tracking_id,
            file_content
        )
        
        if verified:
            return Response({
                "verified": True,
                **details
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "verified": False,
                "error": details.get('error', 'Verification failed')
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Evidence verification failed: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_blockchain_status(request, tracking_id):
    """
    Get blockchain status for a complaint.
    
    GET /api/reports/{tracking_id}/blockchain/status/
    
    Response:
    {
        "blockchain_verified": true,
        "events": [...],
        "evidence": [...],
        "sla_status": {...},
        "latest_tx_hash": "0x..."
    }
    """
    try:
        from report.models import IssueReport
        from blockchain.models import BlockchainTransaction, EvidenceHash, SLATracker
        from blockchain.services import get_blockchain_service
        
        # Get complaint
        try:
            complaint = IssueReport.objects.get(tracking_id=tracking_id)
        except IssueReport.DoesNotExist:
            return Response(
                {"error": "Complaint not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get blockchain transactions
        transactions = BlockchainTransaction.objects.filter(
            complaint_id=tracking_id
        ).order_by('-timestamp')
        
        # Get evidence records
        evidence_records = EvidenceHash.objects.filter(
            complaint_id=tracking_id
        ).order_by('-created_at')
        
        # Get SLA status
        service = get_blockchain_service()
        sla_status = service.get_sla_status(tracking_id)
        
        # Import local storage service to generate URLs
        from blockchain.ipfs_service import get_local_storage_service
        storage_service = get_local_storage_service()
        
        return Response({
            "tracking_id": tracking_id,
            "blockchain_verified": complaint.blockchain_verified,
            "sla_escalated": complaint.sla_escalated,
            "latest_tx_hash": complaint.blockchain_tx_hash,
            "events": [
                {
                    "event_type": tx.event_type,
                    "tx_hash": tx.tx_hash,
                    "block_number": tx.block_number,
                    "timestamp": tx.timestamp,
                    "status": tx.status,
                    "explorer_url": f"{settings.BLOCKCHAIN_EXPLORER_URL}/tx/{tx.tx_hash}" if hasattr(settings, 'BLOCKCHAIN_EXPLORER_URL') else None
                }
                for tx in transactions
            ],
            "evidence": [
                {
                    "file_name": ev.file_name,
                    "file_path": ev.file_path,
                    "file_url": storage_service.get_file_url(ev.file_path),
                    "file_hash": ev.file_hash,
                    "tx_hash": ev.tx_hash,
                    "verified": ev.verified,
                    "block_timestamp": ev.block_timestamp,
                    "created_at": ev.created_at
                }
                for ev in evidence_records
            ],
            "sla_status": sla_status
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Failed to get blockchain status: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_complaint_audit_trail(request, tracking_id):
    """
    Get complete audit trail for a complaint from blockchain.
    
    GET /api/reports/{tracking_id}/audit-trail/
    
    Response:
    {
        "tracking_id": "ABC12345",
        "events": [
            {
                "event_type": "CREATED",
                "timestamp": "2026-02-09T10:00:00Z",
                "tx_hash": "0x...",
                "block_number": 12345,
                "event_hash": "0x...",
                "verified": true
            },
            ...
        ]
    }
    """
    try:
        from blockchain.models import BlockchainTransaction
        from blockchain.services import get_blockchain_service
        
        # Get all transactions for this complaint
        transactions = BlockchainTransaction.objects.filter(
            complaint_id=tracking_id,
            status='CONFIRMED'
        ).order_by('timestamp')
        
        service = get_blockchain_service()
        
        audit_trail = []
        
        for tx in transactions:
            # Verify each event on blockchain
            verified = service.verify_event(tracking_id, tx.event_hash)
            
            audit_trail.append({
                "event_type": tx.event_type,
                "timestamp": tx.timestamp.isoformat(),
                "tx_hash": tx.tx_hash,
                "block_number": tx.block_number,
                "event_hash": tx.event_hash,
                "verified_on_chain": verified,
                "gas_used": tx.gas_used,
                "explorer_url": f"{settings.BLOCKCHAIN_EXPLORER_URL}/tx/{tx.tx_hash}" if hasattr(settings, 'BLOCKCHAIN_EXPLORER_URL') else None
            })
        
        return Response({
            "tracking_id": tracking_id,
            "total_events": len(audit_trail),
            "events": audit_trail
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Failed to get audit trail: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
