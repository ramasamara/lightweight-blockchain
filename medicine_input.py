#!/usr/bin/env python3
"""
Simple Medicine Blockchain Input Script

This script allows users to input medicine information (name, expiration date, 
count, and user ID) and creates a blockchain block with that information.
"""

from blockchain import Blockchain
from transaction import Transaction
from blockchain_state import BlockchainState
import os
import json
import time

def main():
    """Main function to get medicine input and create a block."""
    print("\n===== Medicine Blockchain Input =====\n")
    
    # Create data directory if it doesn't exist
    data_dir = "./data"
    os.makedirs(data_dir, exist_ok=True)
    
    # Initialize blockchain
    blockchain = Blockchain(difficulty=3)
    state = BlockchainState(blockchain, data_dir=data_dir)
    
    # Try to load existing blockchain
    if not state.load_blockchain():
        print("No existing blockchain found. Creating new blockchain with genesis block.")
    
    # Get medicine information from user
    print("\nPlease enter the medicine information:")
    medicine_name = input("Medicine name: ").strip()
    expiration_date = input("Expiration date: ").strip()
    
    # Validate medicine count as integer
    while True:
        try:
            medicine_count = int(input("Medicine count: ").strip())
            break
        except ValueError:
            print("Please enter a valid number for medicine count.")
    
    user_id = input("User ID: ").strip()
    
    # Create transaction content as JSON
    content = json.dumps({
        "Medicine name": medicine_name,
        "Expiration date": expiration_date,
        "Medicine count": medicine_count,
        "user ID": user_id
    })
    
    # Create transaction
    tx = Transaction(
        content=content,
        device_id=f"medicine_input_{user_id}"
    )
    
    # Add transaction to blockchain and mine a block
    blockchain.add_transaction(tx)
    print("\nCreating block with medicine information...")
    block = blockchain.mine_pending_transactions(mining_reward_address=f"medicine_input_{user_id}")
    
    # Save blockchain
    state.save_blockchain()
    
    # Show success message
    print("Block successfully created and added to the blockchain!")
    print(f"Block index: {block.index}")
    print(f"Block hash: {block.hash}")
    print(f"Transaction ID: {tx.transaction_id}")
    
    # Show blockchain information
    print(f"\nTotal blocks in blockchain: {len(blockchain.chain)}")
    
    print("\nThank you for using the Medicine Blockchain Input System.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram interrupted. Exiting...")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
