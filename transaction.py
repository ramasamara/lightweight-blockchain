"""
Transaction module for the Lightweight Blockchain Framework for IoT.

This module defines the Transaction class which represents a pharmaceutical product
transaction in the blockchain. It is optimized for the pharmaceutical supply chain.
"""

import time
import hashlib
import json

class Transaction:
    def __init__(self, content, timestamp=None, device_id=None):
        if timestamp is None:
            timestamp = time.time()

        self.content = content  # should be a dict
        self.timestamp = timestamp
        self.device_id = device_id
        self.transaction_id = self.calculate_transaction_id()

    def calculate_transaction_id(self):
        transaction_string = json.dumps({
            "content": self.content,
            "timestamp": self.timestamp,
            "device_id": self.device_id
        }, sort_keys=True).encode()

        return hashlib.sha256(transaction_string).hexdigest()

    def to_dict(self):
        return {
            "transaction_id": self.transaction_id,
            "content": self.content,
            "timestamp": self.timestamp,
            "device_id": self.device_id
        }

    @classmethod
    def from_dict(cls, transaction_dict):
        transaction = cls(
            content=transaction_dict["content"],
            timestamp=transaction_dict["timestamp"],
            device_id=transaction_dict["device_id"]
        )
        transaction.transaction_id = transaction_dict["transaction_id"]
        return transaction
