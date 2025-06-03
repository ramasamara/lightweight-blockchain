# This script verifies the integrity of the blockchain stored on disk.
# It loads the blockchain from the "data" directory and checks if the chain is valid.
# If everything is consistent, it prints a success message with the block count.
# If not, it warns that the blockchain may have been tampered with.


from blockchain import Blockchain
from blockchain_state import BlockchainState

def main():
    print("\nVerifying blockchain integrity...")

    # Load blockchain
    blockchain = Blockchain()
    state = BlockchainState(blockchain, data_dir="./data")

    if not state.load_blockchain():
        print("Error: Could not load blockchain.")
        return

    # Run verification
    if blockchain.is_chain_valid():
        print("Blockchain is valid and consistent.")
        print(f"Total blocks: {len(blockchain.chain)}")
    else:
        print("Blockchain is INVALID. Possible tampering detected!")

if __name__ == "__main__":
    main()
