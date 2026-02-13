"""
Django Signals for Blockchain Integration

Signals connect complaint lifecycle events to blockchain writes.

Why signals?
- Decoupling: Blockchain logic doesn't pollute main app code
- Flexibility: Easy to enable/disable blockchain features
- Async-friendly: Can dispatch to Celery tasks

Important: These signals should trigger async tasks in production
to avoid blocking HTTP responses.
"""

import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.conf import settings

logger = logging.getLogger(__name__)


# ============ Complaint Lifecycle Signals ============

@receiver(post_save, sender='report.IssueReport')
def log_complaint_created(sender, instance, created, **kwargs):
    """
    Log complaint creation to blockchain.
    
    Triggered when: New IssueReport is created
    Blockchain event: CREATED
    """
    if not created:
        return
    
    if not getattr(settings, 'BLOCKCHAIN_ENABLED', True):
        return
    
    try:
        from blockchain.utils import create_event_payload
        from blockchain.tasks import log_complaint_event_async
        
        # Create event payload with actual model fields
        payload = create_event_payload(
            complaint_id=instance.tracking_id,
            event_type='CREATED',
            data={
                'issue_title': instance.issue_title,
                'department': instance.department,
                'location': instance.location,  # Text field, not lat/lng
                'status': instance.status,
                'description': instance.issue_description,
                'confidence_score': instance.confidence_score,
            },
            actor=instance.user.email if instance.user else 'anonymous'
        )
        
        # Development fallback: run synchronously if DEBUG or no Celery broker or EAGER mode
        if getattr(settings, 'DEBUG', False) or getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False):
            logger.info(f"Running blockchain task synchronously (DEBUG/EAGER mode)")
            try:
                from blockchain.services import BlockchainService
                service = BlockchainService()
                blockchain_tx = service.log_complaint_event(instance.tracking_id, 'CREATED', payload)
                if blockchain_tx:
                    logger.info(f"✅ Blockchain event logged synchronously: {instance.tracking_id} - {blockchain_tx.tx_hash}")
                else:
                    logger.warning(f"⚠️  Blockchain event returned no transaction")
            except Exception as sync_e:
                logger.error(f"Synchronous blockchain logging failed: {sync_e}")
        else:
            # Production: dispatch async task
            task_result = log_complaint_event_async.delay(
                complaint_id=instance.tracking_id,
                event_type='CREATED',
                payload=payload
            )
            logger.info(f"📤 Dispatched blockchain event task: {instance.tracking_id} - CREATED (Task ID: {task_result.id})")
        
    except Exception as e:
        logger.error(f"Failed to dispatch blockchain event: {e}")


# Note: The following signals are disabled because they require FieldTracker
# from django-model-utils which is not currently installed.
# To enable, add 'from model_utils import FieldTracker' to the IssueReport model
# and add: tracker = FieldTracker()

# @receiver(post_save, sender='report.IssueReport')
# def log_complaint_assigned(sender, instance, created, **kwargs):
#     """
#     Log complaint assignment to blockchain.
#     
#     Triggered when: allocated_to field is set
#     Blockchain event: ASSIGNED
#     """
#     pass  # Disabled - requires FieldTracker


# @receiver(post_save, sender='report.IssueReport')
# def log_complaint_status_updated(sender, instance, created, **kwargs):
#     """
#     Log complaint status change to blockchain.
#     
#     Triggered when: status field changes
#     Blockchain event: STATUS_UPDATED or RESOLVED
#     """
#     pass  # Disabled - requires FieldTracker


# ============ Evidence Upload Signal ============

def log_evidence_uploaded(complaint_id: str, file_path: str, file_hash: str, file_name: str = None):
    """
    Log evidence upload to blockchain.
    
    This is called manually from the evidence upload view.
    
    Args:
        complaint_id: Complaint identifier
        file_path: Local file path (relative to MEDIA_ROOT)
        file_hash: SHA-256 hash of file
        file_name: Optional original filename
    """
    if not getattr(settings, 'BLOCKCHAIN_ENABLED', True):
        return
    
    try:
        from blockchain.tasks import anchor_evidence_async
        
        anchor_evidence_async.delay(
            complaint_id=complaint_id,
            file_hash=file_hash,
            file_path=file_path,
            file_metadata={
                'name': file_name or file_path.split('/')[-1],
                'path': file_path
            }
        )
        
        logger.info(f"Dispatched evidence anchoring: {complaint_id} - {file_path}")
        
    except Exception as e:
        logger.error(f"Failed to dispatch evidence anchoring: {e}")


# ============ Model Tracker Setup ============
# To track field changes, we need to add a tracker to the IssueReport model
# This requires installing django-model-utils

"""
Add to report/models.py:

from model_utils import FieldTracker

class IssueReport(models.Model):
    # ... existing fields ...
    
    # Add this at the end
    tracker = FieldTracker(fields=['allocated_to', 'status'])
"""
