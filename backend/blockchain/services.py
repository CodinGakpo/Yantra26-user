import json
import hashlib
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account

from .models import BlockchainTransaction, EvidenceHash, SLATracker

logger = logging.getLogger(__name__)


class BlockchainService:
    def __init__(self):
        """Initialize Web3 connection and contract instance"""
        self.w3 = self._connect_to_blockchain()
        self.contract = self._load_contract()
        self.account = self._load_account()
    
    def _connect_to_blockchain(self) -> Web3:
        """Establish connection to Amazon Managed Blockchain"""
        try:
            node_url = settings.BLOCKCHAIN_NODE_URL
            w3 = Web3(Web3.HTTPProvider(
                node_url,
                request_kwargs={'timeout': 60}
            ))
            
            # Add middleware for PoA chains if needed
            if settings.BLOCKCHAIN_USE_POA:
                w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            
            if not w3.is_connected():
                raise ConnectionError("Cannot connect to blockchain node")
            
            logger.info(f"Connected to blockchain (Chain ID: {w3.eth.chain_id})")
            return w3
            
        except Exception as e:
            logger.error(f"Blockchain connection failed: {e}")
            raise
    
    def _load_contract(self):
        """Load contract ABI and create contract instance"""
        try:
            # Load ABI from file
            abi_path = settings.BLOCKCHAIN_CONTRACT_ABI_PATH
            with open(abi_path, 'r') as f:
                contract_abi = json.load(f)
            
            # Create contract instance
            contract_address = settings.BLOCKCHAIN_CONTRACT_ADDRESS
            contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(contract_address),
                abi=contract_abi
            )
            
            logger.info(f"Contract loaded at {contract_address}")
            return contract
            
        except Exception as e:
            logger.error(f"Failed to load contract: {e}")
            raise
    
    def _load_account(self) -> Account:
        """Load account for signing transactions"""
        try:
            private_key = settings.BLOCKCHAIN_PRIVATE_KEY
            account = Account.from_key(private_key)
            logger.info(f"Account loaded: {account.address}")
            return account
            
        except Exception as e:
            logger.error(f"Failed to load account: {e}")
            raise
    
    def _build_and_send_transaction(self, function_call, event_type: str) -> Tuple[str, Dict]:
        try:
            # Build transaction
            tx = function_call.build_transaction({
                'from': self.account.address,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'gas': settings.BLOCKCHAIN_GAS_LIMIT,
                'gasPrice': self._get_gas_price(),
            })
            
            # Sign transaction
            signed_tx = self.account.sign_transaction(tx)
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            logger.info(f"{event_type} - Transaction sent: {tx_hash.hex()}")
            
            # Wait for receipt
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(
                tx_hash,
                timeout=settings.BLOCKCHAIN_TX_TIMEOUT
            )
            
            if tx_receipt['status'] == 1:
                logger.info(f"{event_type} - Transaction confirmed in block {tx_receipt['blockNumber']}")
            else:
                logger.error(f"{event_type} - Transaction failed")
                raise Exception("Transaction failed on-chain")
            
            return tx_hash.hex(), tx_receipt
            
        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            raise
    
    def _get_gas_price(self) -> int:
        """Get current gas price with optional multiplier"""
        base_price = self.w3.eth.gas_price
        multiplier = getattr(settings, 'BLOCKCHAIN_GAS_PRICE_MULTIPLIER', 1.1)
        return int(base_price * multiplier)
    
    @staticmethod
    def hash_event_payload(payload: Dict) -> str:
        json_str = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        hash_bytes = Web3.keccak(text=json_str)
        
        return hash_bytes.hex()
    
    @staticmethod
    def hash_file_content(file_content: bytes) -> str:
        return hashlib.sha256(file_content).hexdigest()
    
    def log_complaint_event(
        self,
        complaint_id: str,
        event_type: str,
        payload: Dict
    ) -> Optional[BlockchainTransaction]:
        try:
            # Hash the payload
            event_hash = self.hash_event_payload(payload)
            
            # Call smart contract
            function_call = self.contract.functions.logComplaintEvent(
                complaint_id,
                event_type,
                Web3.to_bytes(hexstr=event_hash)
            )
            
            # Send transaction
            tx_hash, tx_receipt = self._build_and_send_transaction(
                function_call,
                f"LOG_EVENT_{event_type}"
            )
            
            # Store in database
            blockchain_tx = BlockchainTransaction.objects.create(
                complaint_id=complaint_id,
                event_type=event_type,
                event_hash=event_hash,
                tx_hash=tx_hash,
                block_number=tx_receipt['blockNumber'],
                gas_used=tx_receipt['gasUsed'],
                status='CONFIRMED',
                event_payload=payload,
                timestamp=timezone.now()
            )
            
            logger.info(
                f"Complaint event logged: {complaint_id} - {event_type} - {tx_hash}"
            )
            
            return blockchain_tx
            
        except Exception as e:
            logger.error(f"Failed to log complaint event: {e}")
            
            # Store failed transaction for retry
            BlockchainTransaction.objects.create(
                complaint_id=complaint_id,
                event_type=event_type,
                event_hash=event_hash if 'event_hash' in locals() else '',
                tx_hash='',
                status='FAILED',
                event_payload=payload,
                timestamp=timezone.now()
            )
            
            return None
    
    def anchor_evidence(
        self,
        complaint_id: str,
        file_hash: str,
        file_path: str,
        file_metadata: Optional[Dict] = None
    ) -> Optional[EvidenceHash]:
        try:
            # Call smart contract
            function_call = self.contract.functions.anchorEvidence(
                complaint_id,
                Web3.to_bytes(hexstr=file_hash)
            )
            
            # Send transaction
            tx_hash, tx_receipt = self._build_and_send_transaction(
                function_call,
                "ANCHOR_EVIDENCE"
            )
            
            # Get block timestamp
            block = self.w3.eth.get_block(tx_receipt['blockNumber'])
            block_timestamp = block['timestamp']
            
            # Store in database
            evidence = EvidenceHash.objects.create(
                complaint_id=complaint_id,
                file_hash=file_hash,
                file_path=file_path,
                tx_hash=tx_hash,
                block_timestamp=block_timestamp,
                verified=False,
                file_name=file_metadata.get('name', '') if file_metadata else '',
                file_size=file_metadata.get('size') if file_metadata else None,
                content_type=file_metadata.get('content_type', '') if file_metadata else ''
            )
            
            logger.info(
                f"Evidence anchored: {complaint_id} - {file_path} - {tx_hash}"
            )
            
            return evidence
            
        except Exception as e:
            logger.error(f"Failed to anchor evidence: {e}")
            return None
    
    def set_sla_deadline(
        self,
        complaint_id: str,
        hours: int = 48
    ) -> Optional[SLATracker]:
        """
        Set SLA deadline for a complaint on blockchain.
        
        Why on-chain?
        - Trustless enforcement (no one can tamper with deadline)
        - Automated escalation via smart contract
        - Transparent audit trail
        
        Args:
            complaint_id: Complaint identifier
            hours: Hours until deadline (default 48)
            
        Returns:
            SLATracker instance or None if failed
        """
        try:
            # Calculate deadline timestamp
            deadline_dt = timezone.now() + timedelta(hours=hours)
            deadline_timestamp = int(deadline_dt.timestamp())
            
            # Call smart contract
            function_call = self.contract.functions.setSLADeadline(
                complaint_id,
                deadline_timestamp
            )
            
            # Send transaction
            tx_hash, tx_receipt = self._build_and_send_transaction(
                function_call,
                "SET_SLA_DEADLINE"
            )
            
            # Store in database
            sla_tracker, created = SLATracker.objects.update_or_create(
                complaint_id=complaint_id,
                defaults={
                    'sla_deadline': deadline_timestamp,
                    'escalated': False,
                    'escalation_tx_hash': '',
                    'escalation_timestamp': None
                }
            )
            
            logger.info(
                f"SLA deadline set: {complaint_id} - {deadline_dt} - {tx_hash}"
            )
            
            return sla_tracker
            
        except Exception as e:
            logger.error(f"Failed to set SLA deadline: {e}")
            return None
    
    def check_and_escalate(self, complaint_id: str) -> bool:
        """
        Check SLA and escalate if deadline breached.
        
        This calls the smart contract to perform the check and escalation.
        The contract is the source of truth.
        
        Args:
            complaint_id: Complaint to check
            
        Returns:
            True if escalation occurred, False otherwise
        """
        try:
            # Call smart contract
            function_call = self.contract.functions.checkAndEscalate(complaint_id)
            
            # Send transaction
            tx_hash, tx_receipt = self._build_and_send_transaction(
                function_call,
                "CHECK_AND_ESCALATE"
            )
            
            # Check if escalation occurred by parsing events
            escalated = False
            for log in tx_receipt['logs']:
                try:
                    event = self.contract.events.ComplaintEscalated().process_log(log)
                    if event['args']['complaintId'] == complaint_id:
                        escalated = True
                        
                        # Update database
                        SLATracker.objects.filter(
                            complaint_id=complaint_id
                        ).update(
                            escalated=True,
                            escalation_tx_hash=tx_hash,
                            escalation_timestamp=timezone.now()
                        )
                        
                        logger.warning(f"Complaint escalated: {complaint_id}")
                        break
                except:
                    continue
            
            return escalated
            
        except Exception as e:
            logger.error(f"Failed to check and escalate: {e}")
            return False
    
    def batch_check_and_escalate(self, complaint_ids: List[str]) -> int:
        """
        Batch check multiple complaints for SLA breach.
        
        More gas-efficient than individual checks.
        
        Args:
            complaint_ids: List of complaint IDs to check
            
        Returns:
            Number of complaints escalated
        """
        try:
            if not complaint_ids:
                return 0
            
            # Call smart contract
            function_call = self.contract.functions.batchCheckAndEscalate(
                complaint_ids
            )
            
            # Send transaction
            tx_hash, tx_receipt = self._build_and_send_transaction(
                function_call,
                "BATCH_CHECK_ESCALATE"
            )
            
            # Parse escalation events
            escalated_count = 0
            for log in tx_receipt['logs']:
                try:
                    event = self.contract.events.ComplaintEscalated().process_log(log)
                    complaint_id = event['args']['complaintId']
                    
                    # Update database
                    SLATracker.objects.filter(
                        complaint_id=complaint_id
                    ).update(
                        escalated=True,
                        escalation_tx_hash=tx_hash,
                        escalation_timestamp=timezone.now()
                    )
                    
                    escalated_count += 1
                    logger.warning(f"Complaint escalated: {complaint_id}")
                    
                except:
                    continue
            
            logger.info(f"Batch escalation: {escalated_count} of {len(complaint_ids)}")
            return escalated_count
            
        except Exception as e:
            logger.error(f"Failed batch escalation: {e}")
            return 0
    
    # ============ Verification Functions ============
    
    def verify_event(self, complaint_id: str, event_hash: str) -> bool:
        """
        Verify an event exists on blockchain.
        
        Args:
            complaint_id: Complaint identifier
            event_hash: Event hash to verify
            
        Returns:
            True if event exists on-chain
        """
        try:
            exists = self.contract.functions.verifyEvent(
                complaint_id,
                Web3.to_bytes(hexstr=event_hash)
            ).call()
            
            return exists
            
        except Exception as e:
            logger.error(f"Event verification failed: {e}")
            return False
    
    def verify_evidence_integrity(
        self,
        complaint_id: str,
        file_content: bytes,
    ) -> Tuple[bool, Optional[Dict]]:
        """
        Verify evidence file integrity against blockchain record.
        
        Process:
        1. Compute hash of provided file
        2. Query blockchain for this hash
        3. Compare timestamps
        
        Args:
            complaint_id: Complaint identifier
            file_content: Raw file bytes to verify
            
        Returns:
            (verified, details_dict)
        """
        try:
            # Compute hash of provided content
            computed_hash = self.hash_file_content(file_content)
            
            # Query blockchain
            block_timestamp = self.contract.functions.verifyEvidenceAnchor(
                complaint_id,
                Web3.to_bytes(hexstr=computed_hash)
            ).call()
            
            if block_timestamp == 0:
                return False, {'error': 'Hash not found on blockchain'}
            
            # Get local record
            evidence = EvidenceHash.objects.filter(
                complaint_id=complaint_id,
                file_hash=computed_hash
            ).first()
            
            if evidence:
                # Mark as verified
                evidence.verified = True
                evidence.save()
            
            details = {
                'verified': True,
                'file_hash': computed_hash,
                'block_timestamp': block_timestamp,
                'anchored_at': datetime.fromtimestamp(block_timestamp),
                'file_path': evidence.file_path if evidence else None
            }
            
            return True, details
            
        except Exception as e:
            logger.error(f"Evidence verification failed: {e}")
            return False, {'error': str(e)}
    
    def get_sla_status(self, complaint_id: str) -> Optional[Dict]:
        """
        Get SLA status from blockchain.
        
        Args:
            complaint_id: Complaint identifier
            
        Returns:
            Dictionary with deadline, escalated status, time_remaining
        """
        try:
            deadline, escalated, time_remaining = self.contract.functions.getSLAStatus(
                complaint_id
            ).call()
            
            return {
                'deadline': deadline,
                'deadline_datetime': datetime.fromtimestamp(deadline) if deadline > 0 else None,
                'escalated': escalated,
                'time_remaining_seconds': time_remaining,
                'should_escalate': time_remaining == 0 and not escalated
            }
            
        except Exception as e:
            logger.error(f"Failed to get SLA status: {e}")
            return None


# Singleton instance
_blockchain_service = None


def get_blockchain_service() -> BlockchainService:
    """Get singleton blockchain service instance"""
    global _blockchain_service
    
    if _blockchain_service is None:
        _blockchain_service = BlockchainService()
    
    return _blockchain_service
