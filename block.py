"""
Block module for the Lightweight Blockchain Framework for IoT.

This module defines the Block class which is optimized for IoT devices with limited
resources. The block structure is designed to be lightweight while maintaining
the essential properties of a blockchain block.
"""

import hashlib
import time
import json


class Block:
    """
    Block class represents a single block in the blockchain.
    
    Optimized for IoT devices with minimal memory and processing requirements.
    """
    
    def __init__(self, index, timestamp, data, previous_hash, device_id):
        """
        Initialize a new Block.
        
        Args:
            index (int): Block number in the chain
            timestamp (float): Time when the block was created
            data (dict): Barcode data and transaction details
            previous_hash (str): Hash of the previous block
            device_id (str): ID of the device that created the block
        """
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.device_id = device_id
        self.nonce = 0
        self.hash = self.calculate_hash()
    
    def calculate_hash(self):
        """
        Calculate the hash of the block using SHA-256.
        
        Returns:
            str: Hexadecimal string representation of the block hash
        """
        # Convert block data to a string and encode it
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "device_id": self.device_id,
            "nonce": self.nonce
        }, sort_keys=True).encode()
        
        # Calculate SHA-256 hash
        return hashlib.sha256(block_string).hexdigest()
    
    def mine_block(self, difficulty):
        """
        Mine the block by finding a hash with the required number of leading zeros.
        
        Lightweight PoW algorithm suitable for IoT devices.
        
        Args:
            difficulty (int): Number of leading zeros required in the hash
            
        Returns:
            str: The calculated hash after mining
        """
        target = '0' * difficulty
        
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
            
            # Optional: Add a small sleep to prevent CPU overuse on IoT devices
            if self.nonce % 100 == 0:
                time.sleep(0.001)
        
        print(f"Block mined: {self.hash}")
        return self.hash
    
    def to_dict(self):
        """
        Convert the block to a dictionary for serialization.
        
        Returns:
            dict: Dictionary representation of the block
        """
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "device_id": self.device_id,
            "nonce": self.nonce,
            "hash": self.hash
        }
    
    @classmethod
    def from_dict(cls, block_dict):
        """
        Create a Block instance from a dictionary.
        
        Args:
            block_dict (dict): Dictionary representation of a block
            
        Returns:
            Block: A new Block instance
        """
        block = cls(
            block_dict["index"],
            block_dict["timestamp"],
            block_dict["data"],
            block_dict["previous_hash"],
            block_dict["device_id"],
        )
        block.nonce = block_dict["nonce"]
        block.hash = block_dict["hash"]
        return block
    
    def is_valid(self):
        """
        Verify that the block's hash is valid.
        
        Returns:
            bool: True if the stored hash matches the calculated hash
        """
        return self.hash == self.calculate_hash()
