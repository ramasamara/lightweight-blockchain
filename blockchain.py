"""
Blockchain module for the Lightweight Blockchain Framework for IoT.

This module defines the Blockchain class which manages the chain of blocks,
handles consensus, and provides methods for adding and validating blocks.
It is optimized for IoT devices with limited resources.
"""

import time
import json
from block import Block
from transaction import Transaction


class Blockchain:
    """
    Blockchain class manages the chain of blocks and implements consensus mechanisms.
    
    Optimized for IoT devices with minimal memory and processing requirements.
    """
    
    def __init__(self, difficulty=3, mining_reward=1.0):
        self.chain = []
        self.difficulty = difficulty
        self.mining_reward = mining_reward
        self.pending_transactions = []
        self.nodes = set()
    
    def create_genesis_block(self):
        genesis_block = Block(
            index=0,
            timestamp=time.time(),
            data={"message": "Genesis Block for Pharmaceutical Supply Chain"},
            previous_hash="0",
            device_id="genesis_node"
        )
        return genesis_block
    
    def get_latest_block(self):
        return self.chain[-1] if self.chain else None
    
    def add_transaction(self, transaction):
        if not isinstance(transaction, Transaction):
            if isinstance(transaction, dict):
                transaction = Transaction.from_dict(transaction)
            else:
                raise TypeError("Transaction must be a Transaction object or dictionary")
        
        self.pending_transactions.append(transaction)
        if self.chain:
            return self.get_latest_block().index + 1
        else:
            return 1
    
    def mine_pending_transactions(self, mining_reward_address):
        previous_hash = self.get_latest_block().hash if self.chain else "0"
        index = len(self.chain)
        
        block = Block(
            index=index,
            timestamp=time.time(),
            data={
                "transactions": [tx.to_dict() for tx in self.pending_transactions],
                "count": len(self.pending_transactions)
            },
            previous_hash=previous_hash,
            device_id=mining_reward_address
        )

        block.mine_block(self.difficulty)
        self.chain.append(block)
        self.pending_transactions = []
        return block
    
    def is_chain_valid(self):
     for i in range(1, len(self.chain)):
        current_block = self.chain[i]
        previous_block = self.chain[i - 1]

        recalculated_hash = current_block.calculate_hash()
        if current_block.hash != recalculated_hash:
            print(f"Hash mismatch at block {i}")
            print(f"Stored hash:      {current_block.hash}")
            print(f"Recalculated hash:{recalculated_hash}")
            return False

        if current_block.previous_hash != previous_block.hash:
            print(f"Previous hash mismatch at block {i}")
            print(f"Expected: {previous_block.hash}")
            print(f"Found:    {current_block.previous_hash}")
            return False

        if not current_block.hash.startswith("0" * self.difficulty):
            print(f"Block {i} does not meet difficulty requirement")
            print(f"Hash: {current_block.hash}")
            return False

     return True

    
    def add_block(self, block):
        if not isinstance(block, Block):
            if isinstance(block, dict):
                block = Block.from_dict(block)
            else:
                raise TypeError("Block must be a Block object or dictionary")
        
        if self.chain and block.previous_hash != self.get_latest_block().hash:
            return False
        
        if block.hash != block.calculate_hash():
            return False
        
        if not block.hash.startswith("0" * self.difficulty):
            return False
        
        self.chain.append(block)
        return True
    
    def register_node(self, node_address):
        self.nodes.add(node_address)
    
    def resolve_conflicts(self, get_chain_function):
        new_chain = None
        max_length = len(self.chain)
        
        for node in self.nodes:
            chain = get_chain_function(node)
            
            if chain and len(chain) > max_length:
                temp_blockchain = Blockchain()
                temp_blockchain.chain = [Block.from_dict(block) for block in chain]
                
                if temp_blockchain.is_chain_valid():
                    max_length = len(chain)
                    new_chain = chain
        
        if new_chain:
            self.chain = [Block.from_dict(block) for block in new_chain]
            return True
        
        return False
    
    def to_dict(self):
        return {
            "chain": [block.to_dict() for block in self.chain],
            "pending_transactions": [tx.to_dict() for tx in self.pending_transactions],
            "difficulty": self.difficulty,
            "nodes": list(self.nodes)
        }
    
    @classmethod
    def from_dict(cls, blockchain_dict):
        blockchain = cls(blockchain_dict.get("difficulty", 3))
        blockchain.chain = [Block.from_dict(block) for block in blockchain_dict["chain"]]
        blockchain.pending_transactions = [
            Transaction.from_dict(tx) for tx in blockchain_dict.get("pending_transactions", [])
        ]
        for node in blockchain_dict.get("nodes", []):
            blockchain.register_node(node)
        return blockchain
    
    def get_transaction_history(self, barcode):
        transactions = []
        for block in self.chain:
            if "transactions" in block.data:
                for tx_dict in block.data["transactions"]:
                    if tx_dict.get("barcode") == barcode:
                        tx = Transaction.from_dict(tx_dict)
                        transactions.append({
                            "transaction": tx.to_dict(),
                            "block_index": block.index,
                            "block_hash": block.hash,
                            "timestamp": block.timestamp
                        })
        return transactions
    
    def adjust_difficulty(self, target_time=10):
        if len(self.chain) < 10:
            return self.difficulty
        
        recent_blocks = self.chain[-10:]
        times = [recent_blocks[i].timestamp - recent_blocks[i-1].timestamp 
                 for i in range(1, len(recent_blocks))]
        
        avg_time = sum(times) / len(times)
        
        if avg_time < target_time * 0.8:
            self.difficulty += 1
        elif avg_time > target_time * 1.2:
            self.difficulty = max(1, self.difficulty - 1)
        
        return self.difficulty
