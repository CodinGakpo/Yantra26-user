#!/usr/bin/env python
"""
Blockchain Integration Verification Script

This script verifies that all complaint events and evidence records in the database
have been successfully anchored on the Sepolia Ethereum blockchain.

Usage:
    python verify_blockchain_integration.py

Requirements:
    - Django environment properly configured
    - BLOCKCHAIN_NODE_URL, BLOCKCHAIN_CONTRACT_ADDRESS, BLOCKCHAIN_CONTRACT_ABI_PATH in settings
    - web3.py and colorama packages installed
"""

import os
import sys
import json
import django
from pathlib import Path
from typing import Dict, List, Tuple

# Setup Django environment
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'report_hub.settings.local')
django.setup()

from django.conf import settings
from web3 import Web3
from web3.middleware import geth_poa_middleware
from blockchain.models import BlockchainTransaction, EvidenceHash

# Import colorama for colored terminal output
try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    COLORS_ENABLED = True
except ImportError:
    print("Warning: colorama not installed. Install with 'pip install colorama' for colored output.")
    COLORS_ENABLED = False
    
    # Fallback if colorama not available
    class Fore:
        GREEN = RED = YELLOW = CYAN = MAGENTA = BLUE = ""
    
    class Style:
        RESET_ALL = BRIGHT = ""


class BlockchainVerifier:
    """
    Verifies blockchain integration by checking transaction receipts and events.
    """
    
    def __init__(self):
        """Initialize Web3 connection and contract instance"""
        self.w3 = None
        self.contract = None
        self.stats = {
            'total_transactions': 0,
            'total_evidence': 0,
            'tx_success': 0,
            'tx_failed': 0,
            'tx_pending': 0,
            'evidence_success': 0,
            'evidence_failed': 0,
            'hash_mismatches': 0,
            'errors': []
        }
        
        self._connect_to_blockchain()
        self._load_contract()
    
    def _connect_to_blockchain(self):
        """Establish connection to Sepolia Ethereum network"""
        try:
            node_url = settings.BLOCKCHAIN_NODE_URL
            
            if not node_url:
                raise ValueError("BLOCKCHAIN_NODE_URL not configured in settings")
            
            print(f"{Fore.CYAN}🔗 Connecting to Sepolia network...")
            print(f"{Fore.CYAN}   Node URL: {node_url}")
            
            # Connect to Web3
            self.w3 = Web3(Web3.HTTPProvider(
                node_url,
                request_kwargs={'timeout': 60}
            ))
            
            # Add middleware for PoA chains (Sepolia is PoS but some testnets use PoA)
            if hasattr(settings, 'BLOCKCHAIN_USE_POA') and settings.BLOCKCHAIN_USE_POA:
                self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            
            # Check connection
            if not self.w3.is_connected():
                raise ConnectionError("Failed to connect to blockchain node")
            
            # Display network info
            chain_id = self.w3.eth.chain_id
            latest_block = self.w3.eth.block_number
            
            print(f"{Fore.GREEN}✓ Connected successfully!")
            print(f"{Fore.GREEN}   Chain ID: {chain_id} (Sepolia: 11155111)")
            print(f"{Fore.GREEN}   Latest block: {latest_block}")
            print()
            
        except Exception as e:
            print(f"{Fore.RED}✗ Blockchain connection failed: {e}")
            sys.exit(1)
    
    def _load_contract(self):
        """Load smart contract ABI and create contract instance"""
        try:
            contract_address = settings.BLOCKCHAIN_CONTRACT_ADDRESS
            abi_path = settings.BLOCKCHAIN_CONTRACT_ABI_PATH
            
            if not contract_address:
                raise ValueError("BLOCKCHAIN_CONTRACT_ADDRESS not configured in settings")
            
            print(f"{Fore.CYAN}📄 Loading smart contract...")
            print(f"{Fore.CYAN}   Address: {contract_address}")
            print(f"{Fore.CYAN}   ABI Path: {abi_path}")
            
            # Load ABI from file
            if not os.path.exists(abi_path):
                print(f"{Fore.YELLOW}⚠ Warning: ABI file not found at {abi_path}")
                print(f"{Fore.YELLOW}   Contract verification will be limited to transaction receipts only")
                self.contract = None
                return
            
            with open(abi_path, 'r') as f:
                contract_abi = json.load(f)
            
            # Validate ABI
            if not contract_abi or (isinstance(contract_abi, list) and len(contract_abi) == 0):
                print(f"{Fore.YELLOW}⚠ Warning: ABI file is empty")
                print(f"{Fore.YELLOW}   Contract verification will be limited to transaction receipts only")
                self.contract = None
                return
            
            # Create contract instance
            checksum_address = Web3.to_checksum_address(contract_address)
            self.contract = self.w3.eth.contract(
                address=checksum_address,
                abi=contract_abi
            )
            
            print(f"{Fore.GREEN}✓ Contract loaded successfully!")
            print()
            
        except Exception as e:
            print(f"{Fore.YELLOW}⚠ Warning: Failed to load contract: {e}")
            print(f"{Fore.YELLOW}   Contract verification will be limited to transaction receipts only")
            self.contract = None
    
    def _get_transaction_receipt(self, tx_hash: str) -> Tuple[bool, dict, str]:
        """
        Fetch transaction receipt from blockchain.
        
        Returns:
            (success, receipt, error_message)
        """
        try:
            # Convert to bytes if needed
            if isinstance(tx_hash, str):
                if not tx_hash.startswith('0x'):
                    tx_hash = '0x' + tx_hash
                tx_hash_bytes = bytes.fromhex(tx_hash[2:])
            else:
                tx_hash_bytes = tx_hash
            
            # Get receipt from blockchain
            receipt = self.w3.eth.get_transaction_receipt(tx_hash_bytes)
            
            if receipt is None:
                return False, None, "Transaction pending or not found"
            
            return True, receipt, ""
            
        except Exception as e:
            return False, None, str(e)
    
    def _verify_transaction_status(self, receipt: dict) -> bool:
        """
        Check if transaction succeeded (status == 1).
        
        Args:
            receipt: Transaction receipt from blockchain
            
        Returns:
            True if transaction succeeded, False otherwise
        """
        # Status field: 1 = success, 0 = failure
        status = receipt.get('status', 0)
        return status == 1
    
    def _get_complaint_event_from_logs(self, receipt: dict, complaint_id: str) -> Tuple[bool, str]:
        """
        Extract ComplaintEvent or EvidenceAnchored event from transaction logs.
        
        Returns:
            (found, event_hash)
        """
        if not self.contract:
            return False, ""
        
        try:
            # Get logs from receipt
            logs = receipt.get('logs', [])
            
            for log in logs:
                # Try to decode as ComplaintEvent
                try:
                    event = self.contract.events.ComplaintEvent().process_log(log)
                    if event['args']['complaintId'] == complaint_id:
                        event_hash = event['args']['eventHash'].hex()
                        return True, event_hash
                except Exception:
                    pass
                
                # Try to decode as EvidenceAnchored
                try:
                    event = self.contract.events.EvidenceAnchored().process_log(log)
                    if event['args']['complaintId'] == complaint_id:
                        evidence_hash = event['args']['evidenceHash'].hex()
                        return True, evidence_hash
                except Exception:
                    pass
            
            return False, ""
            
        except Exception as e:
            print(f"{Fore.YELLOW}   Warning: Failed to decode events: {e}")
            return False, ""
    
    def _get_evidence_event_from_logs(self, receipt: dict, expected_hash: str) -> Tuple[bool, str]:
        """
        Extract EvidenceAnchored event from transaction logs.
        
        Returns:
            (found, evidence_hash)
        """
        if not self.contract:
            return False, ""
        
        try:
            # Get logs from receipt
            logs = receipt.get('logs', [])
            
            for log in logs:
                try:
                    event = self.contract.events.EvidenceAnchored().process_log(log)
                    evidence_hash = event['args']['evidenceHash'].hex()
                    return True, evidence_hash
                except Exception:
                    pass
            
            return False, ""
            
        except Exception as e:
            print(f"{Fore.YELLOW}   Warning: Failed to decode events: {e}")
            return False, ""
    
    def verify_blockchain_transaction(self, tx: BlockchainTransaction) -> bool:
        """
        Verify a single BlockchainTransaction record.
        
        Steps:
        1. Fetch transaction receipt
        2. Check transaction status
        3. Verify event hash matches (if contract loaded)
        
        Args:
            tx: BlockchainTransaction instance
            
        Returns:
            True if verification passed, False otherwise
        """
        print(f"{Fore.CYAN}🔍 Verifying complaint: {tx.complaint_id}")
        print(f"   Event Type: {tx.event_type}")
        print(f"   TX Hash: {tx.tx_hash}")
        print(f"   DB Status: {tx.status}")
        
        try:
            # Step 1: Fetch transaction receipt
            success, receipt, error = self._get_transaction_receipt(tx.tx_hash)
            
            if not success:
                if "not found" in error.lower() or "pending" in error.lower():
                    print(f"{Fore.YELLOW}   ⏳ Transaction pending or not found")
                    self.stats['tx_pending'] += 1
                    return False
                else:
                    print(f"{Fore.RED}   ✗ Error fetching receipt: {error}")
                    self.stats['tx_failed'] += 1
                    self.stats['errors'].append(f"{tx.complaint_id}: {error}")
                    return False
            
            # Step 2: Check transaction status (1 = success, 0 = failure)
            tx_succeeded = self._verify_transaction_status(receipt)
            
            if not tx_succeeded:
                print(f"{Fore.RED}   ✗ Transaction failed on-chain (status = 0)")
                print(f"{Fore.RED}   Block: {receipt.get('blockNumber', 'N/A')}")
                print(f"{Fore.RED}   Gas Used: {receipt.get('gasUsed', 'N/A')}")
                self.stats['tx_failed'] += 1
                return False
            
            print(f"{Fore.GREEN}   ✓ Transaction confirmed on-chain (status = 1)")
            print(f"{Fore.GREEN}   Block: {receipt.get('blockNumber', 'N/A')}")
            print(f"{Fore.GREEN}   Gas Used: {receipt.get('gasUsed', 'N/A')}")
            
            # Step 3: Verify event hash (if contract loaded)
            if self.contract:
                found, on_chain_hash = self._get_complaint_event_from_logs(receipt, tx.complaint_id)
                
                if found:
                    # Normalize hashes for comparison
                    db_hash = tx.event_hash.lower()
                    if db_hash.startswith('0x'):
                        db_hash = db_hash[2:]
                    
                    if on_chain_hash.startswith('0x'):
                        on_chain_hash = on_chain_hash[2:]
                    
                    if db_hash == on_chain_hash:
                        print(f"{Fore.GREEN}   ✓ Event hash matches: {db_hash[:16]}...")
                    else:
                        print(f"{Fore.RED}   ✗ Hash mismatch!")
                        print(f"{Fore.RED}     DB Hash:     {db_hash}")
                        print(f"{Fore.RED}     On-chain:    {on_chain_hash}")
                        self.stats['hash_mismatches'] += 1
                        return False
                else:
                    print(f"{Fore.YELLOW}   ⚠ Event not found in logs (contract may not have emitted expected event)")
            
            self.stats['tx_success'] += 1
            return True
            
        except Exception as e:
            print(f"{Fore.RED}   ✗ Verification error: {e}")
            self.stats['tx_failed'] += 1
            self.stats['errors'].append(f"{tx.complaint_id}: {str(e)}")
            return False
        finally:
            print()  # Blank line for readability
    
    def verify_evidence_hash(self, evidence: EvidenceHash) -> bool:
        """
        Verify a single EvidenceHash record.
        
        Steps:
        1. Fetch transaction receipt
        2. Check transaction status
        3. Verify evidence hash matches (if contract loaded)
        
        Args:
            evidence: EvidenceHash instance
            
        Returns:
            True if verification passed, False otherwise
        """
        print(f"{Fore.CYAN}🔍 Verifying evidence: {evidence.file_name or 'Unnamed'}")
        print(f"   Complaint ID: {evidence.complaint_id}")
        print(f"   File Hash: {evidence.file_hash[:16]}...")
        print(f"   TX Hash: {evidence.tx_hash}")
        
        try:
            # Step 1: Fetch transaction receipt
            success, receipt, error = self._get_transaction_receipt(evidence.tx_hash)
            
            if not success:
                if "not found" in error.lower() or "pending" in error.lower():
                    print(f"{Fore.YELLOW}   ⏳ Transaction pending or not found")
                    return False
                else:
                    print(f"{Fore.RED}   ✗ Error fetching receipt: {error}")
                    self.stats['evidence_failed'] += 1
                    self.stats['errors'].append(f"Evidence {evidence.id}: {error}")
                    return False
            
            # Step 2: Check transaction status
            tx_succeeded = self._verify_transaction_status(receipt)
            
            if not tx_succeeded:
                print(f"{Fore.RED}   ✗ Transaction failed on-chain (status = 0)")
                print(f"{Fore.RED}   Block: {receipt.get('blockNumber', 'N/A')}")
                self.stats['evidence_failed'] += 1
                return False
            
            print(f"{Fore.GREEN}   ✓ Transaction confirmed on-chain (status = 1)")
            print(f"{Fore.GREEN}   Block: {receipt.get('blockNumber', 'N/A')}")
            
            # Step 3: Verify evidence hash (if contract loaded)
            if self.contract:
                found, on_chain_hash = self._get_evidence_event_from_logs(receipt, evidence.file_hash)
                
                if found:
                    # Normalize hashes for comparison
                    db_hash = evidence.file_hash.lower()
                    if db_hash.startswith('0x'):
                        db_hash = db_hash[2:]
                    
                    if on_chain_hash.startswith('0x'):
                        on_chain_hash = on_chain_hash[2:]
                    
                    if db_hash == on_chain_hash:
                        print(f"{Fore.GREEN}   ✓ Evidence hash matches: {db_hash[:16]}...")
                    else:
                        print(f"{Fore.RED}   ✗ Hash mismatch!")
                        print(f"{Fore.RED}     DB Hash:     {db_hash}")
                        print(f"{Fore.RED}     On-chain:    {on_chain_hash}")
                        self.stats['hash_mismatches'] += 1
                        return False
                else:
                    print(f"{Fore.YELLOW}   ⚠ Event not found in logs")
            
            self.stats['evidence_success'] += 1
            return True
            
        except Exception as e:
            print(f"{Fore.RED}   ✗ Verification error: {e}")
            self.stats['evidence_failed'] += 1
            self.stats['errors'].append(f"Evidence {evidence.id}: {str(e)}")
            return False
        finally:
            print()  # Blank line for readability
    
    def run_verification(self):
        """
        Main verification workflow.
        Iterates through all blockchain records and verifies each one.
        """
        print(f"{Fore.MAGENTA}{'='*80}")
        print(f"{Fore.MAGENTA}  BLOCKCHAIN INTEGRATION VERIFICATION")
        print(f"{Fore.MAGENTA}{'='*80}")
        print()
        
        # ========== Verify BlockchainTransaction records ==========
        print(f"{Fore.BLUE}{Style.BRIGHT}📊 CHECKING COMPLAINT LIFECYCLE EVENTS...")
        print()
        
        transactions = BlockchainTransaction.objects.all().order_by('-timestamp')
        self.stats['total_transactions'] = transactions.count()
        
        if self.stats['total_transactions'] == 0:
            print(f"{Fore.YELLOW}   No transactions found in database")
            print()
        else:
            print(f"   Found {self.stats['total_transactions']} transaction(s) to verify")
            print()
            
            for tx in transactions:
                self.verify_blockchain_transaction(tx)
        
        # ========== Verify EvidenceHash records ==========
        print(f"{Fore.BLUE}{Style.BRIGHT}📊 CHECKING EVIDENCE ANCHORING...")
        print()
        
        evidence_records = EvidenceHash.objects.all().order_by('-created_at')
        self.stats['total_evidence'] = evidence_records.count()
        
        if self.stats['total_evidence'] == 0:
            print(f"{Fore.YELLOW}   No evidence records found in database")
            print()
        else:
            print(f"   Found {self.stats['total_evidence']} evidence record(s) to verify")
            print()
            
            for evidence in evidence_records:
                self.verify_evidence_hash(evidence)
        
        # ========== Print Summary ==========
        self._print_summary()
    
    def _print_summary(self):
        """Print verification summary with colored output"""
        print(f"{Fore.MAGENTA}{'='*80}")
        print(f"{Fore.MAGENTA}  VERIFICATION SUMMARY")
        print(f"{Fore.MAGENTA}{'='*80}")
        print()
        
        # Transaction summary
        print(f"{Fore.BLUE}{Style.BRIGHT}Complaint Lifecycle Events:")
        print(f"   Total Records:    {self.stats['total_transactions']}")
        print(f"{Fore.GREEN}   ✓ Confirmed:      {self.stats['tx_success']}")
        print(f"{Fore.RED}   ✗ Failed:         {self.stats['tx_failed']}")
        print(f"{Fore.YELLOW}   ⏳ Pending:        {self.stats['tx_pending']}")
        print()
        
        # Evidence summary
        print(f"{Fore.BLUE}{Style.BRIGHT}Evidence Anchoring:")
        print(f"   Total Records:    {self.stats['total_evidence']}")
        print(f"{Fore.GREEN}   ✓ Confirmed:      {self.stats['evidence_success']}")
        print(f"{Fore.RED}   ✗ Failed:         {self.stats['evidence_failed']}")
        print()
        
        # Hash mismatches
        if self.stats['hash_mismatches'] > 0:
            print(f"{Fore.RED}{Style.BRIGHT}⚠ Hash Mismatches:  {self.stats['hash_mismatches']}")
            print()
        
        # Overall status
        total_verified = self.stats['tx_success'] + self.stats['evidence_success']
        total_failed = self.stats['tx_failed'] + self.stats['evidence_failed']
        total_pending = self.stats['tx_pending']
        total_records = self.stats['total_transactions'] + self.stats['total_evidence']
        
        print(f"{Fore.BLUE}{Style.BRIGHT}Overall:")
        print(f"   Total Records:    {total_records}")
        print(f"{Fore.GREEN}   ✓ Verified:       {total_verified}")
        print(f"{Fore.RED}   ✗ Failed:         {total_failed}")
        print(f"{Fore.YELLOW}   ⏳ Pending:        {total_pending}")
        
        if self.stats['hash_mismatches'] > 0:
            print(f"{Fore.RED}   ⚠ Hash Mismatches: {self.stats['hash_mismatches']}")
        
        print()
        
        # Success rate
        if total_records > 0:
            success_rate = (total_verified / total_records) * 100
            
            if success_rate == 100:
                print(f"{Fore.GREEN}{Style.BRIGHT}✓ SUCCESS RATE: {success_rate:.1f}%")
            elif success_rate >= 80:
                print(f"{Fore.YELLOW}{Style.BRIGHT}⚠ SUCCESS RATE: {success_rate:.1f}%")
            else:
                print(f"{Fore.RED}{Style.BRIGHT}✗ SUCCESS RATE: {success_rate:.1f}%")
        
        print()
        
        # Errors
        if self.stats['errors']:
            print(f"{Fore.RED}{Style.BRIGHT}Errors encountered:")
            for error in self.stats['errors'][:10]:  # Show first 10 errors
                print(f"{Fore.RED}   • {error}")
            
            if len(self.stats['errors']) > 10:
                print(f"{Fore.RED}   ... and {len(self.stats['errors']) - 10} more")
            print()
        
        print(f"{Fore.MAGENTA}{'='*80}")


def main():
    """Main entry point"""
    try:
        # Create verifier instance and run
        verifier = BlockchainVerifier()
        verifier.run_verification()
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Verification interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
