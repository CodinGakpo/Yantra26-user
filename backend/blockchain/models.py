from django.db import models
from django.utils import timezone


class BlockchainTransaction(models.Model):
    EVENT_TYPES = [
        ('CREATED', 'Complaint Created'),
        ('ASSIGNED', 'Complaint Assigned'),
        ('STATUS_UPDATED', 'Status Updated'),
        ('ESCALATED', 'Complaint Escalated'),
        ('RESOLVED', 'Complaint Resolved'),
        ('EVIDENCE_ADDED', 'Evidence Added'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('FAILED', 'Failed'),
    ]
    
    complaint_id = models.CharField(max_length=100, db_index=True)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, db_index=True)
    event_hash = models.CharField(max_length=66, help_text="Keccak256 hash of event payload")
    tx_hash = models.CharField(max_length=66, unique=True, help_text="Ethereum transaction hash")
    block_number = models.BigIntegerField(null=True, blank=True)
    gas_used = models.BigIntegerField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    
    # Store the full event payload for verification
    event_payload = models.JSONField(help_text="Original event data that was hashed")
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['complaint_id', '-timestamp']),
            models.Index(fields=['event_type', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.complaint_id} - {self.event_type} - {self.tx_hash[:10]}..."


class EvidenceHash(models.Model):
    complaint_id = models.CharField(max_length=100, db_index=True)
    file_hash = models.CharField(max_length=64, help_text="SHA-256 hash of file content")
    file_path = models.CharField(max_length=500, help_text="Local file path (relative to MEDIA_ROOT)")
    tx_hash = models.CharField(max_length=66, help_text="Blockchain transaction hash")
    block_timestamp = models.BigIntegerField(help_text="Block timestamp from blockchain")
    verified = models.BooleanField(default=False, help_text="Has integrity been verified?")
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Optional: store file metadata
    file_name = models.CharField(max_length=255, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    content_type = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['complaint_id', '-created_at']),
            models.Index(fields=['file_path']),
        ]
    
    def __str__(self):
        return f"{self.complaint_id} - {self.file_name} - {self.file_path[:50]}..."


class SLATracker(models.Model):
    """
    Tracks SLA deadlines and escalations.
    
    Why this model?
    - Smart contract enforces SLA logic on-chain
    - This is a cache for quick queries without blockchain calls
    - Synced via event listeners
    """
    
    complaint_id = models.CharField(max_length=100, unique=True, db_index=True)
    sla_deadline = models.BigIntegerField(help_text="Unix timestamp of SLA deadline")
    escalated = models.BooleanField(default=False, db_index=True)
    escalation_tx_hash = models.CharField(max_length=66, blank=True)
    escalation_timestamp = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['sla_deadline']
        indexes = [
            models.Index(fields=['escalated', 'sla_deadline']),
        ]
    
    def __str__(self):
        return f"{self.complaint_id} - Deadline: {self.sla_deadline} - Escalated: {self.escalated}"
