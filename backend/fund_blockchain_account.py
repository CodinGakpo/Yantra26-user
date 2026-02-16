#!/usr/bin/env python3
"""
Script to fund the blockchain account with ETH from Ganache's pre-funded accounts.

This solves the "insufficient funds for gas * price + value" error by transferring
ETH from one of Ganache's default accounts to your working account.
"""

import os
import sys
import django
from pathlib import Path
from decimal import Decimal

# Setup Django environment
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'report_hub.settings.local')
django.setup()

from django.conf import settings
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account

# ANSI colors for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_header(text):
    print(f"\n{BLUE}{'='*60}")
    print(f"{text}")
    print(f"{'='*60}{RESET}\n")


def print_success(text):
    print(f"{GREEN}✓ {text}{RESET}")


def print_warning(text):
    print(f"{YELLOW}⚠ {text}{RESET}")


def print_error(text):
    print(f"{RED}✗ {text}{RESET}")


def connect_to_blockchain():
    """Connect to Ganache blockchain"""
    try:
        node_url = settings.BLOCKCHAIN_NODE_URL or os.getenv('BLOCKCHAIN_NODE_URL', 'http://127.0.0.1:7545')
        print(f"Connecting to blockchain at: {node_url}")
        
        w3 = Web3(Web3.HTTPProvider(node_url, request_kwargs={'timeout': 10}))
        
        if settings.BLOCKCHAIN_USE_POA:
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        if not w3.is_connected():
            raise ConnectionError("Cannot connect to blockchain node")
        
        print_success(f"Connected to blockchain (Chain ID: {w3.eth.chain_id})")
        return w3
        
    except Exception as e:
        print_error(f"Failed to connect to blockchain: {e}")
        print_warning("Make sure Ganache is running!")
        sys.exit(1)


def get_target_account():
    """Get the account that needs funding"""
    try:
        private_key = settings.BLOCKCHAIN_PRIVATE_KEY or os.getenv('BLOCKCHAIN_PRIVATE_KEY')
        
        if not private_key:
            print_error("BLOCKCHAIN_PRIVATE_KEY not set in settings or environment")
            sys.exit(1)
        
        account = Account.from_key(private_key)
        print_success(f"Target account: {account.address}")
        return account
        
    except Exception as e:
        print_error(f"Failed to load target account: {e}")
        sys.exit(1)


def get_ganache_accounts(w3):
    """Get the pre-funded accounts from Ganache"""
    try:
        accounts = w3.eth.accounts
        print_success(f"Found {len(accounts)} Ganache accounts")
        return accounts
        
    except Exception as e:
        print_error(f"Failed to get Ganache accounts: {e}")
        return []


def display_balances(w3, accounts, target_address):
    """Display current balances"""
    print_header("Current Account Balances")
    
    print(f"{'Address':<45} {'Balance (ETH)':<20} {'Status'}")
    print("-" * 85)
    
    for i, account in enumerate(accounts[:5]):  # Show first 5 Ganache accounts
        balance = w3.eth.get_balance(account)
        balance_eth = w3.from_wei(balance, 'ether')
        status = "🎯 TARGET" if account.lower() == target_address.lower() else ""
        print(f"{account:<45} {balance_eth:<20.4f} {status}")
    
    # Show target account if it's not in the list
    if target_address.lower() not in [acc.lower() for acc in accounts[:5]]:
        balance = w3.eth.get_balance(target_address)
        balance_eth = w3.from_wei(balance, 'ether')
        print(f"{target_address:<45} {balance_eth:<20.4f} 🎯 TARGET")
    
    print()


def fund_account(w3, source_account, target_account, amount_eth=10):
    """Transfer ETH from source to target account"""
    try:
        target_address = target_account.address
        
        # Get current balances
        source_balance = w3.eth.get_balance(source_account)
        target_balance = w3.eth.get_balance(target_address)
        
        source_balance_eth = w3.from_wei(source_balance, 'ether')
        target_balance_eth = w3.from_wei(target_balance, 'ether')
        
        print_header(f"Funding Account")
        print(f"Source: {source_account}")
        print(f"  Balance: {source_balance_eth:.4f} ETH")
        print(f"\nTarget: {target_address}")
        print(f"  Balance: {target_balance_eth:.4f} ETH")
        print(f"\nAmount to transfer: {amount_eth} ETH\n")
        
        # Check if source has enough balance
        if source_balance_eth < amount_eth:
            print_error(f"Source account doesn't have enough ETH ({source_balance_eth:.4f} < {amount_eth})")
            return False
        
        # Build transaction
        tx = {
            'from': source_account,
            'to': target_address,
            'value': w3.to_wei(amount_eth, 'ether'),
            'gas': 21000,
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(source_account),
        }
        
        print("Sending transaction...")
        
        # Send transaction (Ganache auto-signs for its default accounts)
        tx_hash = w3.eth.send_transaction(tx)
        print(f"Transaction hash: {tx_hash.hex()}")
        
        # Wait for receipt
        print("Waiting for confirmation...")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=30)
        
        if receipt['status'] == 1:
            print_success(f"✅ Transaction confirmed in block {receipt['blockNumber']}")
            
            # Display new balances
            new_target_balance = w3.eth.get_balance(target_address)
            new_target_balance_eth = w3.from_wei(new_target_balance, 'ether')
            
            print(f"\n{GREEN}New target balance: {new_target_balance_eth:.4f} ETH{RESET}")
            print(f"{GREEN}Funded successfully! Added {amount_eth} ETH{RESET}\n")
            return True
        else:
            print_error("Transaction failed!")
            return False
            
    except Exception as e:
        print_error(f"Failed to fund account: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function to fund the blockchain account"""
    print_header("🔥 Blockchain Account Funding Tool")
    
    # Parse command line arguments
    amount_eth = 10  # Default amount
    if len(sys.argv) > 1:
        try:
            amount_eth = float(sys.argv[1])
        except ValueError:
            print_error(f"Invalid amount: {sys.argv[1]}")
            print("Usage: python fund_blockchain_account.py [amount_in_eth]")
            sys.exit(1)
    
    # Step 1: Connect to blockchain
    w3 = connect_to_blockchain()
    
    # Step 2: Get target account
    target_account = get_target_account()
    
    # Step 3: Get Ganache accounts
    ganache_accounts = get_ganache_accounts(w3)
    
    if not ganache_accounts:
        print_error("No Ganache accounts found!")
        sys.exit(1)
    
    # Step 4: Display current balances
    display_balances(w3, ganache_accounts, target_account.address)
    
    # Step 5: Check if target is already one of the Ganache accounts
    if target_account.address in ganache_accounts:
        print_warning("Target account is already a Ganache default account!")
        current_balance = w3.eth.get_balance(target_account.address)
        current_balance_eth = w3.from_wei(current_balance, 'ether')
        print(f"Current balance: {current_balance_eth:.4f} ETH")
        
        if current_balance_eth > 1:
            print_success("Account has sufficient funds!")
            sys.exit(0)
    
    # Step 6: Select source account (first Ganache account with funds)
    source_account = None
    for account in ganache_accounts:
        balance = w3.eth.get_balance(account)
        balance_eth = w3.from_wei(balance, 'ether')
        
        # Skip if this is the target account
        if account.lower() == target_account.address.lower():
            continue
        
        # Use account if it has enough funds
        if balance_eth >= amount_eth + 0.1:  # Extra 0.1 for gas
            source_account = account
            break
    
    if not source_account:
        print_error("No Ganache account found with enough funds!")
        sys.exit(1)
    
    # Step 7: Fund the account
    success = fund_account(w3, source_account, target_account, amount_eth)
    
    if success:
        print_success("🎉 Account funded successfully!")
        print("\nYou can now run your blockchain transactions.")
        sys.exit(0)
    else:
        print_error("Failed to fund account!")
        sys.exit(1)


if __name__ == '__main__':
    main()
