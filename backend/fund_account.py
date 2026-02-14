"""
Automatic Account Funding Script
This will send 10 ETH from Ganache Account #0 to your account
"""

from web3 import Web3

def fund_account():
    print("=" * 70)
    print("FUNDING YOUR ACCOUNT")
    print("=" * 70)
    print()
    
    # Connect to Ganache
    ganache_url = "http://127.0.0.1:7545"
    w3 = Web3(Web3.HTTPProvider(ganache_url))
    
    if not w3.is_connected():
        print("❌ Cannot connect to Ganache")
        return False
    
    print(f"✅ Connected to Ganache (Chain ID: {w3.eth.chain_id})")
    print()
    
    # Sender: Ganache Account #0 (has 100 ETH)
    sender = "0x776FBf217DC979936B52fe756627a51A0fDa5E84"
    
    # Receiver: Your account (currently has 0 ETH)
    receiver = "0x3d97Ac3318bd24d481a62b9ee6c31DcDB1dDa4d0"
    
    # Amount to send: 10 ETH (more than enough for testing)
    amount_eth = 70
    amount_wei = w3.to_wei(amount_eth, 'ether')
    
    print(f"Sender (Ganache #0): {sender}")
    sender_balance = w3.from_wei(w3.eth.get_balance(sender), 'ether')
    print(f"  Balance: {sender_balance} ETH")
    print()
    
    print(f"Receiver (Your Account): {receiver}")
    receiver_balance_before = w3.from_wei(w3.eth.get_balance(receiver), 'ether')
    print(f"  Balance: {receiver_balance_before} ETH")
    print()
    
    print(f"Sending {amount_eth} ETH...")
    print()
    
    try:
        # Send transaction
        # Ganache doesn't require private key for its default accounts
        tx_hash = w3.eth.send_transaction({
            'from': sender,
            'to': receiver,
            'value': amount_wei,
            'gas': 21000,
            'gasPrice': w3.eth.gas_price
        })
        
        print(f"✅ Transaction sent: {tx_hash.hex()}")
        print()
        
        # Wait for confirmation
        print("Waiting for confirmation...")
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if tx_receipt['status'] == 1:
            print(f"✅ Transaction confirmed in block {tx_receipt['blockNumber']}")
            print()
            
            # Check new balance
            receiver_balance_after = w3.from_wei(w3.eth.get_balance(receiver), 'ether')
            
            print("-" * 70)
            print("FINAL BALANCES:")
            print("-" * 70)
            print(f"Your Account: {receiver}")
            print(f"  Before: {receiver_balance_before} ETH")
            print(f"  After:  {receiver_balance_after} ETH")
            print(f"  Change: +{receiver_balance_after - receiver_balance_before} ETH")
            print()
            
            print("=" * 70)
            print("✅ SUCCESS! YOUR ACCOUNT IS NOW FUNDED")
            print("=" * 70)
            print()
            print("Next steps:")
            print("1. Clean the database:")
            print("   python manage.py shell < 2_fix_database.py")
            print()
            print("2. Replace services.py with improved version:")
            print("   cp 3_improved_services.py blockchain/services.py")
            print()
            print("3. Restart Django and test!")
            print()
            
            return True
        else:
            print("❌ Transaction failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        print("This might happen if:")
        print("1. Ganache requires unlocking accounts (try Ganache UI)")
        print("2. Network settings are different")
        print()
        print("ALTERNATIVE: Use FIX OPTION 1 from the diagnostic")
        print("Copy Ganache Account #0's private key to your settings")
        return False

if __name__ == "__main__":
    fund_account()