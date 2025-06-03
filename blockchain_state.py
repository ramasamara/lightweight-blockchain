"""
Blockchain state management module for the Lightweight Blockchain Framework for IoT.

This module provides functionality for managing the state of the blockchain,
including persistence, recovery, and synchronization between nodes.
"""

import json
import os
import tempfile
import time
import threading
import logging
from blockchain import Blockchain
from block import Block
from transaction import Transaction

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('blockchain_state')


class BlockchainState:
    def __init__(self, blockchain, data_dir="./data", auto_save=True, save_interval=60):
        self.blockchain = blockchain
        self.data_dir = data_dir
        self.auto_save = auto_save
        self.save_interval = save_interval
        self.running = False
        self.save_thread = None

        os.makedirs(data_dir, exist_ok=True)

        if self.auto_save:
            self.start_auto_save()

    def save_blockchain(self, filename="blockchain.json"):
     try:
        filepath = os.path.join(self.data_dir, filename)
        blockchain_dict = self.blockchain.to_dict()

        # Save to temp file first
        with tempfile.NamedTemporaryFile("w", delete=False, dir=self.data_dir) as tmp_file:
            json.dump(blockchain_dict, tmp_file, indent=2)
            temp_name = tmp_file.name

        os.replace(temp_name, filepath)  # Atomic move

        return True

     except Exception as e:
        print("Error saving blockchain:", str(e))
        return False



    def load_blockchain(self, filename="blockchain.json"):
        try:
            filepath = os.path.join(self.data_dir, filename)
            if not os.path.exists(filepath):
                logger.warning(f"Blockchain file {filepath} not found")
                return False

            with open(filepath, 'r') as file:
                blockchain_dict = json.load(file)

            loaded_blockchain = Blockchain.from_dict(blockchain_dict)

            self.blockchain.chain = loaded_blockchain.chain
            self.blockchain.difficulty = loaded_blockchain.difficulty
            self.blockchain.pending_transactions = loaded_blockchain.pending_transactions
            self.blockchain.nodes = loaded_blockchain.nodes

            logger.info(f"Blockchain loaded from {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error loading blockchain: {str(e)}")
            return False

    def start_auto_save(self):
        if self.running:
            return False

        self.running = True
        self.save_thread = threading.Thread(target=self._auto_save_loop)
        self.save_thread.daemon = True
        self.save_thread.start()
        logger.info(f"Auto-save started with interval {self.save_interval} seconds")
        return True

    def stop_auto_save(self):
        if not self.running:
            return False

        self.running = False
        if self.save_thread:
            self.save_thread.join(timeout=1)
            self.save_thread = None
        logger.info("Auto-save stopped")
        return True

    def _auto_save_loop(self):
        while self.running:
            try:
                self.save_blockchain()
                for _ in range(self.save_interval):
                    if not self.running:
                        break
                    time.sleep(1)
            except Exception as e:
                logger.error(f"Error in auto-save loop: {str(e)}")
                time.sleep(5)

    def export_blockchain(self, filename="blockchain_export.json"):
        try:
            filepath = os.path.join(self.data_dir, filename)
            export_data = {
                "chain_length": len(self.blockchain.chain),
                "difficulty": self.blockchain.difficulty,
                "blocks": [block.to_dict() for block in self.blockchain.chain]
            }
            with open(filepath, 'w') as file:
                json.dump(export_data, file, indent=2)
            logger.info(f"Blockchain exported to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error exporting blockchain: {str(e)}")
            return False

    def get_blockchain_stats(self):
        try:
            transaction_count = 0
            for block in self.blockchain.chain:
                if "transactions" in block.data:
                    transaction_count += len(block.data["transactions"])

            avg_block_time = None
            if len(self.blockchain.chain) > 10:
                recent_blocks = self.blockchain.chain[-10:]
                times = [recent_blocks[i].timestamp - recent_blocks[i-1].timestamp for i in range(1, len(recent_blocks))]
                avg_block_time = sum(times) / len(times)

            latest_timestamp = self.blockchain.chain[-1].timestamp if self.blockchain.chain else None

            return {
                "chain_length": len(self.blockchain.chain),
                "difficulty": self.blockchain.difficulty,
                "transaction_count": transaction_count,
                "pending_transactions": len(self.blockchain.pending_transactions),
                "avg_block_time": avg_block_time,
                "latest_block_timestamp": latest_timestamp,
                "latest_block_hash": self.blockchain.chain[-1].hash if self.blockchain.chain else None
            }
        except Exception as e:
            logger.error(f"Error getting blockchain stats: {str(e)}")
            return {}

    def create_checkpoint(self, checkpoint_name=None):
        if not checkpoint_name:
            checkpoint_name = f"checkpoint_{int(time.time())}.json"

        filepath = os.path.join(self.data_dir, checkpoint_name)
        self.save_blockchain(checkpoint_name)
        logger.info(f"Checkpoint created: {checkpoint_name}")
        return checkpoint_name

    def restore_checkpoint(self, checkpoint_name):
        return self.load_blockchain(checkpoint_name)

    def list_checkpoints(self):
        try:
            return [f for f in os.listdir(self.data_dir) if f.startswith("checkpoint_") and f.endswith(".json")]
        except Exception as e:
            logger.error(f"Error listing checkpoints: {str(e)}")
            return []

    def cleanup_old_checkpoints(self, max_checkpoints=5):
        try:
            checkpoints = self.list_checkpoints()
            checkpoints.sort(key=lambda x: int(x.split('_')[1].split('.')[0]))
            removed = 0
            if len(checkpoints) > max_checkpoints:
                for checkpoint in checkpoints[:-max_checkpoints]:
                    filepath = os.path.join(self.data_dir, checkpoint)
                    os.remove(filepath)
                    removed += 1
                    logger.info(f"Removed old checkpoint: {checkpoint}")
            return removed
        except Exception as e:
            logger.error(f"Error cleaning up checkpoints: {str(e)}")
            return 0
