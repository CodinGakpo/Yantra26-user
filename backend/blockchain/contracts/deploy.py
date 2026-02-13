from solcx import compile_source, install_solc
import json
import os
import sys
from web3 import Web3
    


def compile_contract():
    try:
        install_solc('0.8.19')
    except Exception as e:
        print(f"Solc already installed or error: {e}")
    
    contract_path = os.path.join(
        os.path.dirname(__file__),
        'ComplaintRegistry.sol'
    )
    
    with open(contract_path, 'r') as f:
        contract_source = f.read()
    
    compiled = compile_source(
        contract_source,
        output_values=['abi', 'bin'],
        solc_version='0.8.19'
    )
    
    contract_id, contract_interface = compiled.popitem()
    
    build_dir = os.path.join(os.path.dirname(__file__), 'build')
    os.makedirs(build_dir, exist_ok=True)
    
    with open(os.path.join(build_dir, 'ComplaintRegistry_abi.json'), 'w') as f:
        json.dump(contract_interface['abi'], f, indent=2)
    
    with open(os.path.join(build_dir, 'ComplaintRegistry_bytecode.txt'), 'w') as f:
        f.write(contract_interface['bin'])
    
    print("✓ Contract compiled successfully")
    print(f"  ABI saved to: {build_dir}/ComplaintRegistry_abi.json")
    print(f"  Bytecode saved to: {build_dir}/ComplaintRegistry_bytecode.txt")
    
    return contract_interface


def deploy_contract(w3, account, private_key):
    contract_interface = compile_contract()
    Contract = w3.eth.contract(
        abi=contract_interface['abi'],
        bytecode=contract_interface['bin']
    )

    tx = Contract.constructor().build_transaction({
        'from': account,
        'nonce': w3.eth.get_transaction_count(account),
        'gas': 3000000,
        'gasPrice': w3.eth.gas_price,
    })
    
    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    
    print("Deploying contract...")
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    
    print(f"Transaction hash: {tx_hash.hex()}")
    print("Waiting for confirmation...")
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    contract_address = tx_receipt['contractAddress']
    print(f"✓ Contract deployed at: {contract_address}")
    
    return contract_address


if __name__ == '__main__':

    if '--deploy' in sys.argv:
        node_url = os.getenv('BLOCKCHAIN_NODE_URL')
        account = os.getenv('DEPLOYER_ADDRESS')
        private_key = os.getenv('DEPLOYER_PRIVATE_KEY')
        
        if not all([node_url, account, private_key]):
            print("Error: Set BLOCKCHAIN_NODE_URL, DEPLOYER_ADDRESS, and DEPLOYER_PRIVATE_KEY")
            sys.exit(1)
        
        w3 = Web3(Web3.HTTPProvider(node_url))
        
        if not w3.is_connected():
            print("Error: Cannot connect to blockchain node")
            sys.exit(1)
        
        print(f"Connected to blockchain (Chain ID: {w3.eth.chain_id})")
        contract_address = deploy_contract(w3, account, private_key)
        
        print("\n" + "="*60)
        print("IMPORTANT: Save this contract address to your .env file:")
        print(f"BLOCKCHAIN_CONTRACT_ADDRESS={contract_address}")
        print("="*60)
    else:
        compile_contract()
