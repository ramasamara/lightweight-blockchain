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
