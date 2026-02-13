#!/usr/bin/env python
"""
Pre-flight check for blockchain verification script

This script validates that all prerequisites are met before running
the main verification script.
"""

import sys
import os
from pathlib import Path

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def check_mark(passed):
    return f"{GREEN}✓{RESET}" if passed else f"{RED}✗{RESET}"

def print_header(text):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

def main():
    print_header("Blockchain Verification Pre-flight Check")
    
    all_passed = True
    
    # Check 1: Python version
    print("1️⃣  Checking Python version...")
    py_version = sys.version_info
    py_ok = py_version.major == 3 and py_version.minor >= 8
    print(f"   {check_mark(py_ok)} Python {py_version.major}.{py_version.minor}.{py_version.micro}")
    if not py_ok:
        print(f"   {YELLOW}⚠  Python 3.8+ required{RESET}")
        all_passed = False
    
    # Check 2: Required packages
    print("\n2️⃣  Checking required packages...")
    
    packages = {
        'django': 'Django',
        'web3': 'Web3.py',
        'eth_account': 'eth-account',
        'colorama': 'colorama (optional - for colored output)'
    }
    
    for module, name in packages.items():
        try:
            __import__(module)
            print(f"   {check_mark(True)} {name}")
        except ImportError:
            optional = "optional" in name.lower()
            print(f"   {check_mark(False)} {name}")
            if not optional:
                all_passed = False
    
    # Check 3: Django setup
    print("\n3️⃣  Checking Django setup...")
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'report_hub.settings.local')
        import django
        django.setup()
        from django.conf import settings
        print(f"   {check_mark(True)} Django configured")
        
        # Check 4: Environment variables
        print("\n4️⃣  Checking environment variables...")
        
        env_vars = {
            'BLOCKCHAIN_NODE_URL': getattr(settings, 'BLOCKCHAIN_NODE_URL', None),
            'BLOCKCHAIN_CONTRACT_ADDRESS': getattr(settings, 'BLOCKCHAIN_CONTRACT_ADDRESS', None),
            'BLOCKCHAIN_CONTRACT_ABI_PATH': getattr(settings, 'BLOCKCHAIN_CONTRACT_ABI_PATH', None),
        }
        
        for var, value in env_vars.items():
            has_value = value and len(str(value).strip()) > 0
            print(f"   {check_mark(has_value)} {var}")
            if has_value:
                # Show partial value for security
                if 'ADDRESS' in var:
                    display = f"{value[:10]}...{value[-6:]}" if len(value) > 20 else value
                else:
                    display = f"{value[:30]}..." if len(value) > 30 else value
                print(f"      └─ {display}")
            else:
                print(f"      └─ {YELLOW}Not set or empty{RESET}")
                all_passed = False
        
        # Check 5: ABI file
        print("\n5️⃣  Checking ABI file...")
        abi_path = env_vars.get('BLOCKCHAIN_CONTRACT_ABI_PATH')
        if abi_path:
            abi_exists = os.path.exists(abi_path)
            print(f"   {check_mark(abi_exists)} ABI file exists")
            if abi_exists:
                print(f"      └─ {abi_path}")
                # Check if file is not empty
                file_size = os.path.getsize(abi_path)
                if file_size > 0:
                    print(f"      └─ Size: {file_size} bytes")
                else:
                    print(f"      └─ {YELLOW}⚠  File is empty{RESET}")
                    print(f"      └─ {YELLOW}Run: cd blockchain/contracts && solc --abi ComplaintRegistry.sol -o build/{RESET}")
        else:
            print(f"   {check_mark(False)} ABI path not configured")
        
        # Check 6: Database models
        print("\n6️⃣  Checking database models...")
        try:
            from blockchain.models import BlockchainTransaction, EvidenceHash
            tx_count = BlockchainTransaction.objects.count()
            ev_count = EvidenceHash.objects.count()
            print(f"   {check_mark(True)} Models accessible")
            print(f"      └─ BlockchainTransaction: {tx_count} records")
            print(f"      └─ EvidenceHash: {ev_count} records")
            
            if tx_count == 0 and ev_count == 0:
                print(f"      └─ {YELLOW}⚠  No records to verify (empty database){RESET}")
        except Exception as e:
            print(f"   {check_mark(False)} Cannot query models: {e}")
            all_passed = False
        
        # Check 7: Web3 connection (optional test)
        print("\n7️⃣  Testing blockchain connection...")
        node_url = env_vars.get('BLOCKCHAIN_NODE_URL')
        if node_url:
            try:
                from web3 import Web3
                w3 = Web3(Web3.HTTPProvider(node_url, request_kwargs={'timeout': 10}))
                is_connected = w3.is_connected()
                print(f"   {check_mark(is_connected)} Connection test")
                if is_connected:
                    try:
                        chain_id = w3.eth.chain_id
                        latest_block = w3.eth.block_number
                        print(f"      └─ Chain ID: {chain_id} {'(Sepolia ✓)' if chain_id == 11155111 else ''}")
                        print(f"      └─ Latest block: {latest_block}")
                    except Exception as e:
                        print(f"      └─ {YELLOW}Connected but cannot fetch details: {e}{RESET}")
                else:
                    print(f"      └─ {YELLOW}Cannot connect to node{RESET}")
                    print(f"      └─ {YELLOW}Check your BLOCKCHAIN_NODE_URL{RESET}")
            except Exception as e:
                print(f"   {check_mark(False)} Connection test failed: {e}")
        else:
            print(f"   {check_mark(False)} Cannot test (BLOCKCHAIN_NODE_URL not set)")
    
    except Exception as e:
        print(f"   {check_mark(False)} Django setup failed: {e}")
        all_passed = False
    
    # Final verdict
    print_header("Pre-flight Check Results")
    
    if all_passed:
        print(f"{GREEN}✓ All checks passed!{RESET}")
        print(f"\n{GREEN}Ready to run verification:{RESET}")
        print(f"   python verify_blockchain_integration.py")
    else:
        print(f"{RED}✗ Some checks failed{RESET}")
        print(f"\n{YELLOW}Please fix the issues above before running verification.{RESET}")
        print(f"\n{YELLOW}Common fixes:{RESET}")
        print(f"   • Install packages: pip install web3 colorama")
        print(f"   • Set environment variables in .env file")
        print(f"   • Generate ABI: cd blockchain/contracts && solc --abi ComplaintRegistry.sol -o build/")
        print(f"   • Check Django settings import blockchain_settings")
        
        sys.exit(1)

if __name__ == "__main__":
    main()
