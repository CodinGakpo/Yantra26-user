"""
Ganache Diagnostic Script
Run this to diagnose the insufficient funds issue
"""

from web3 import Web3
import sys

def diagnose_ganache():
    print("=" * 70)
    print("GANACHE BLOCKCHAIN DIAGNOSTIC")
    print("=" * 70)
    
    # Connect to Ganache
    ganache_url = "http://127.0.0.1:7545"  # Default Ganache UI port
    # If using Ganache CLI, try: "http://127.0.0.1:8545"
    
    try:
        w3 = Web3(Web3.HTTPProvider(ganache_url))
        
        # Check connection
        if not w3.is_connected():
            print("❌ Cannot connect to Ganache at", ganache_url)
            print("\nTroubleshooting:")
            print("1. Make sure Ganache is running")
            print("2. Check if Ganache is on port 7545 (UI) or 8545 (CLI)")
            print("3. Try the other port if this doesn't work")
            return False
        
        print(f"✅ Connected to Ganache")
        print(f"   URL: {ganache_url}")
        print(f"   Chain ID: {w3.eth.chain_id}")
        print(f"   Latest Block: {w3.eth.block_number}")
        print()
        
        # Your current account from the error log
        your_account = "0x3d97Ac3318bd24d481a62b9ee6c31DcDB1dDa4d0"
        
        print("-" * 70)
        print("YOUR CURRENT ACCOUNT:")
        print("-" * 70)
        
        try:
            balance = w3.eth.get_balance(your_account)
            balance_eth = w3.from_wei(balance, 'ether')
            
            print(f"Address: {your_account}")
            print(f"Balance: {balance_eth} ETH")
            
            if balance_eth < 0.1:
                print("❌ INSUFFICIENT FUNDS!")
                print(f"   You have: {balance_eth} ETH")
                print(f"   Typical gas cost: 0.001 - 0.01 ETH per transaction")
                print(f"   You need at least: 0.1 ETH")
            else:
                print(f"✅ Sufficient balance")
            
        except Exception as e:
            print(f"❌ Error checking your account: {e}")
            print("   This account might not exist in Ganache")
        
        print()
        print("-" * 70)
        print("GANACHE DEFAULT ACCOUNTS (First 5):")
        print("-" * 70)
        
        # Get all Ganache accounts
        accounts = w3.eth.accounts
        
        if not accounts:
            print("❌ No accounts found in Ganache!")
            return False
        
        print(f"Found {len(accounts)} accounts\n")
        
        for i, account in enumerate(accounts[:5]):
            balance = w3.eth.get_balance(account)
            balance_eth = w3.from_wei(balance, 'ether')
            
            is_your_account = account.lower() == your_account.lower()
            marker = " ← YOUR ACCOUNT" if is_your_account else ""
            
            print(f"Account #{i}: {account}{marker}")
            print(f"  Balance: {balance_eth} ETH")
            print()
        
        print("-" * 70)
        print("RECOMMENDATIONS:")
        print("-" * 70)
        
        # Check if your account exists and has funds
        your_balance = w3.eth.get_balance(your_account)
        your_balance_eth = w3.from_wei(your_balance, 'ether')
        
        if your_balance_eth < 0.1:
            print("\n🔧 FIX OPTION 1: Use a pre-funded Ganache account")
            print("   Replace your private key in settings with one from Ganache's default accounts")
            print(f"   Ganache Account #0: {accounts[0]}")
            print("   To get the private key:")
            print("   1. Open Ganache UI")
            print("   2. Click the key icon next to the account")
            print("   3. Copy the private key")
            print("   4. Update BLOCKCHAIN_PRIVATE_KEY in your settings")
            
            print("\n🔧 FIX OPTION 2: Fund your current account")
            print("   You can send ETH from a funded account to your account")
            print("   (Requires using Ganache UI or web3 script)")
            
            print("\n🔧 FIX OPTION 3: Reset Ganache")
            print("   1. Close Ganache")
            print("   2. Restart it (this will reset all accounts to 100 ETH)")
            print("   3. Redeploy your contract")
        else:
            print("\n✅ Your account has sufficient funds!")
            print("   The issue might be:")
            print("   1. Database has duplicate empty tx_hash entries")
            print("   2. Gas price is too high")
            print("   3. Contract address is incorrect")
        
        print("\n" + "=" * 70)
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = diagnose_ganache()
    sys.exit(0 if success else 1)