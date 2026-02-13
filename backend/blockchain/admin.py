from django.contrib import admin
from .models import BlockchainTransaction, EvidenceHash


@admin.register(BlockchainTransaction)
class BlockchainTransactionAdmin(admin.ModelAdmin):
    list_display = ['complaint_id', 'event_type', 'tx_hash', 'block_number', 'timestamp', 'status']
    list_filter = ['event_type', 'status', 'timestamp']
    search_fields = ['complaint_id', 'tx_hash']
    readonly_fields = ['tx_hash', 'block_number', 'gas_used', 'event_hash', 'timestamp']


@admin.register(EvidenceHash)
class EvidenceHashAdmin(admin.ModelAdmin):
    list_display = ['complaint_id', 'file_name', 'file_path', 'tx_hash', 'verified', 'created_at']
    list_filter = ['verified', 'created_at']
    search_fields = ['complaint_id', 'file_name', 'file_path', 'tx_hash']
    readonly_fields = ['file_hash', 'file_path', 'tx_hash', 'block_timestamp', 'created_at']
