import logging
from typing import Dict, List
from datetime import datetime

from django.utils import timezone
from web3 import Web3

from .services import get_blockchain_service
from .models import BlockchainTransaction, SLATracker

logger = logging.getLogger(__name__)


def sync_events_from_blockchain(
    from_block: int = None,
    to_block: int = None
) -> Dict:
    try:
        service = get_blockchain_service()
        
        # Determine block range
        if to_block is None:
            to_block = service.w3.eth.block_number
        
        if from_block is None:
            # Get last synced block from database
            last_tx = BlockchainTransaction.objects.filter(
                status='CONFIRMED'
            ).order_by('-block_number').first()
            
            if last_tx and last_tx.block_number:
                from_block = last_tx.block_number + 1
            else:
                # Default to last 1000 blocks if no data
                from_block = max(0, to_block - 1000)
        
        logger.info(f"Syncing events from block {from_block} to {to_block}")
        
        stats = {
            'complaint_events': 0,
            'evidence_events': 0,
            'escalation_events': 0,
            'sla_events': 0,
            'errors': 0
        }
        
        # Sync ComplaintEvent
        complaint_events = sync_complaint_events(service, from_block, to_block)
        stats['complaint_events'] = len(complaint_events)
        
        # Sync EvidenceAnchored
        evidence_events = sync_evidence_events(service, from_block, to_block)
        stats['evidence_events'] = len(evidence_events)
        
        # Sync ComplaintEscalated
        escalation_events = sync_escalation_events(service, from_block, to_block)
        stats['escalation_events'] = len(escalation_events)
        
        # Sync SLADeadlineSet
        sla_events = sync_sla_events(service, from_block, to_block)
        stats['sla_events'] = len(sla_events)
        
        logger.info(f"Sync complete: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Event sync failed: {e}")
        return {'error': str(e)}


def sync_complaint_events(service, from_block: int, to_block: int) -> List[Dict]:
    """Sync ComplaintEvent emissions"""
    try:
        event_filter = service.contract.events.ComplaintEvent.create_filter(
            fromBlock=from_block,
            toBlock=to_block
        )
        
        events = event_filter.get_all_entries()
        
        for event in events:
            complaint_id = event['args']['complaintId']
            event_type = event['args']['eventType']
            event_hash = event['args']['eventHash'].hex()
            timestamp = event['args']['timestamp']
            
            tx_hash = event['transactionHash'].hex()
            block_number = event['blockNumber']
            
            # Check if already exists
            if BlockchainTransaction.objects.filter(tx_hash=tx_hash).exists():
                continue
            
            # Get transaction receipt for gas info
            tx_receipt = service.w3.eth.get_transaction_receipt(tx_hash)
            
            # Create or update
            BlockchainTransaction.objects.update_or_create(
                tx_hash=tx_hash,
                defaults={
                    'complaint_id': complaint_id,
                    'event_type': event_type,
                    'event_hash': event_hash,
                    'block_number': block_number,
                    'gas_used': tx_receipt['gasUsed'],
                    'status': 'CONFIRMED',
                    'timestamp': datetime.fromtimestamp(timestamp, tz=timezone.utc),
                    'event_payload': {}  # We don't have the original payload
                }
            )
            
            logger.info(f"Synced complaint event: {complaint_id} - {event_type}")
        
        return events
        
    except Exception as e:
        logger.error(f"Failed to sync complaint events: {e}")
        return []


def sync_evidence_events(service, from_block: int, to_block: int) -> List[Dict]:
    """Sync EvidenceAnchored emissions"""
    try:
        event_filter = service.contract.events.EvidenceAnchored.create_filter(
            fromBlock=from_block,
            toBlock=to_block
        )
        
        events = event_filter.get_all_entries()
        
        for event in events:
            complaint_id = event['args']['complaintId']
            evidence_hash = event['args']['evidenceHash'].hex()
            timestamp = event['args']['timestamp']
            
            tx_hash = event['transactionHash'].hex()
            
            # Update evidence record if exists
            from .models import EvidenceHash
            
            EvidenceHash.objects.filter(
                complaint_id=complaint_id,
                file_hash=evidence_hash
            ).update(
                block_timestamp=timestamp,
                verified=True
            )
            
            logger.info(f"Synced evidence event: {complaint_id} - {evidence_hash[:16]}...")
        
        return events
        
    except Exception as e:
        logger.error(f"Failed to sync evidence events: {e}")
        return []


def sync_escalation_events(service, from_block: int, to_block: int) -> List[Dict]:
    """Sync ComplaintEscalated emissions"""
    try:
        event_filter = service.contract.events.ComplaintEscalated.create_filter(
            fromBlock=from_block,
            toBlock=to_block
        )
        
        events = event_filter.get_all_entries()
        
        for event in events:
            complaint_id = event['args']['complaintId']
            deadline = event['args']['deadline']
            escalation_time = event['args']['escalationTime']
            
            tx_hash = event['transactionHash'].hex()
            
            # Update SLA tracker
            SLATracker.objects.update_or_create(
                complaint_id=complaint_id,
                defaults={
                    'escalated': True,
                    'escalation_tx_hash': tx_hash,
                    'escalation_timestamp': datetime.fromtimestamp(
                        escalation_time,
                        tz=timezone.utc
                    )
                }
            )
            
            # Also log as blockchain transaction
            BlockchainTransaction.objects.update_or_create(
                tx_hash=tx_hash,
                defaults={
                    'complaint_id': complaint_id,
                    'event_type': 'ESCALATED',
                    'event_hash': '',
                    'block_number': event['blockNumber'],
                    'status': 'CONFIRMED',
                    'timestamp': datetime.fromtimestamp(
                        escalation_time,
                        tz=timezone.utc
                    ),
                    'event_payload': {
                        'deadline': deadline,
                        'escalation_time': escalation_time
                    }
                }
            )
            
            logger.warning(f"Synced escalation event: {complaint_id}")
        
        return events
        
    except Exception as e:
        logger.error(f"Failed to sync escalation events: {e}")
        return []


def sync_sla_events(service, from_block: int, to_block: int) -> List[Dict]:
    """Sync SLADeadlineSet emissions"""
    try:
        event_filter = service.contract.events.SLADeadlineSet.create_filter(
            fromBlock=from_block,
            toBlock=to_block
        )
        
        events = event_filter.get_all_entries()
        
        for event in events:
            complaint_id = event['args']['complaintId']
            deadline = event['args']['deadline']
            
            SLATracker.objects.update_or_create(
                complaint_id=complaint_id,
                defaults={
                    'sla_deadline': deadline
                }
            )
            
            logger.info(f"Synced SLA event: {complaint_id} - deadline: {deadline}")
        
        return events
        
    except Exception as e:
        logger.error(f"Failed to sync SLA events: {e}")
        return []

class BlockchainEventListener:
    def __init__(self):
        from django.conf import settings
        
        # Use WebSocket provider for real-time events
        ws_url = getattr(settings, 'BLOCKCHAIN_WS_URL', None)
        
        if not ws_url:
            raise ValueError("BLOCKCHAIN_WS_URL not configured")
        
        from web3 import Web3
        self.w3 = Web3(Web3.WebsocketProvider(ws_url))
        
        service = get_blockchain_service()
        self.contract = service.contract
    
    def start(self):
        logger.info("Starting real-time event listener...")
        
        complaint_filter = self.contract.events.ComplaintEvent.create_filter(
            fromBlock='latest'
        )
        
        escalation_filter = self.contract.events.ComplaintEscalated.create_filter(
            fromBlock='latest'
        )
        
        while True:
            try:
                for event in complaint_filter.get_new_entries():
                    self._handle_complaint_event(event)
                
                for event in escalation_filter.get_new_entries():
                    self._handle_escalation_event(event)
                
                import time
                time.sleep(2)
                
            except KeyboardInterrupt:
                logger.info("Stopping event listener...")
                break
            except Exception as e:
                logger.error(f"Event listener error: {e}")
                import time
                time.sleep(10)
    
    def _handle_complaint_event(self, event):
        """Handle ComplaintEvent"""
        complaint_id = event['args']['complaintId']
        event_type = event['args']['eventType']
        
        logger.info(f"📥 Real-time event: {complaint_id} - {event_type}")
        
        # Trigger any real-time actions (notifications, webhooks, etc.)
    
    def _handle_escalation_event(self, event):
        """Handle ComplaintEscalated"""
        complaint_id = event['args']['complaintId']
        
        logger.warning(f"🚨 Real-time escalation: {complaint_id}")
        

def run_event_listener_daemon():
    listener = BlockchainEventListener()
    listener.start()
