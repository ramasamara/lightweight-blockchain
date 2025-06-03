import os
import time
import logging
import json
from blockchain import Blockchain
from blockchain_state import BlockchainState
from transaction import Transaction
from pow_miner import ProofOfWork, IoTOptimizedMiner

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('mining_node')

class MiningNode:
    def __init__(self, host, port, data_dir="./data", difficulty=3, node_id=None):
        self.host = host
        self.port = port
        self.data_dir = data_dir
        self.difficulty = difficulty
        self.node_id = node_id or f"mining_node_{int(time.time())}"
        os.makedirs(data_dir, exist_ok=True)

        self.blockchain = None
        self.blockchain_state = None
        self.pow_miner = None
        self.running = False
        self.mining = False

    def initialize(self):
        try:
            self.blockchain = Blockchain(difficulty=self.difficulty)
            self.blockchain_state = BlockchainState(
                blockchain=self.blockchain,
                data_dir=self.data_dir,
                auto_save=True,
                save_interval=60
            )
            if not self.blockchain_state.load_blockchain():
                logger.info("No existing blockchain found, using new chain with genesis block")
            pow = ProofOfWork(initial_difficulty=self.difficulty)
            self.pow_miner = IoTOptimizedMiner(pow_instance=pow)
            logger.info("Mining node initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing mining node: {str(e)}")
            return False

    def start(self):
        if self.running:
            logger.warning("Mining node is already running")
            return False

        try:
            if not self.blockchain_state.start_auto_save():
                logger.warning("Failed to start blockchain state auto-save")
            self.running = True
            logger.info("Mining node started successfully")
            return True
        except Exception as e:
            logger.error(f"Error starting mining node: {str(e)}")
            self.stop()
            return False

    def stop(self):
        try:
            if self.mining:
                self.stop_mining()
            if self.blockchain_state:
                self.blockchain_state.stop_auto_save()
                self.blockchain_state.save_blockchain()
            self.running = False
            logger.info("Mining node stopped successfully")
            return True
        except Exception as e:
            logger.error(f"Error stopping mining node: {str(e)}")
            return False

    def start_mining(self):
        if not self.running:
            logger.warning("Mining node is not running")
            return False
        if self.mining:
            logger.warning("Mining is already active")
            return False
        try:
            if not self.pow_miner.start_mining(self.blockchain, self.node_id):
                logger.error("Failed to start mining")
                return False
            self.mining = True
            logger.info("Mining started successfully")
            return True
        except Exception as e:
            logger.error(f"Error starting mining: {str(e)}")
            return False

    def stop_mining(self):
        if not self.mining:
            logger.warning("Mining is not active")
            return False
        try:
            if not self.pow_miner.stop_mining():
                logger.error("Failed to stop mining")
                return False
            self.mining = False
            logger.info("Mining stopped successfully")
            return True
        except Exception as e:
            logger.error(f"Error stopping mining: {str(e)}")
            return False

    def create_transaction(self, transaction_data):
        if not self.running:
            return None

        try:
            transaction = Transaction(
                content=transaction_data.get("content"),
                timestamp=time.time(),
                device_id=self.node_id,
            )

            self.blockchain.add_transaction(transaction)
            mined_block = self.blockchain.mine_pending_transactions(self.node_id)

            logger.info(f"Mined block {mined_block.index} with transaction {transaction.transaction_id}")

            return {
                "transaction": transaction.to_dict(),
                "block_index": mined_block.index
            }

        except Exception as e:
            logger.error(f"Error creating transaction: {str(e)}")
            return None

    def get_blockchain_info(self):
        if not self.blockchain:
            logger.warning("Blockchain not initialized")
            return None
        try:
            blockchain_stats = self.blockchain_state.get_blockchain_stats()
            mining_stats = self.pow_miner.get_status() if self.pow_miner else {}
            return {
                "node_type": "mining_node",
                "node_id": self.node_id,
                "is_running": self.running,
                "is_mining": self.mining,
                "blockchain": blockchain_stats,
                "mining": mining_stats
            }
        except Exception as e:
            logger.error(f"Error getting blockchain info: {str(e)}")
            return None

    def export_blockchain(self, filename=None):
        if not self.blockchain_state:
            logger.warning("Blockchain state not initialized")
            return None
        try:
            if not filename:
                filename = f"blockchain_export_{int(time.time())}.json"
            if self.blockchain_state.export_blockchain(filename):
                filepath = os.path.join(self.data_dir, filename)
                logger.info(f"Blockchain exported to {filepath}")
                return filepath
            else:
                logger.error("Failed to export blockchain")
                return None
        except Exception as e:
            logger.error(f"Error exporting blockchain: {str(e)}")
            return None

    def create_checkpoint(self):
        if not self.blockchain_state:
            logger.warning("Blockchain state not initialized")
            return None
        try:
            checkpoint_name = self.blockchain_state.create_checkpoint()
            logger.info(f"Checkpoint created: {checkpoint_name}")
            return checkpoint_name
        except Exception as e:
            logger.error(f"Error creating checkpoint: {str(e)}")
            return None

    def restore_checkpoint(self, checkpoint_name):
        if not self.blockchain_state:
            logger.warning("Blockchain state not initialized")
            return False
        try:
            was_mining = self.mining
            if was_mining:
                self.stop_mining()
            if self.blockchain_state.restore_checkpoint(checkpoint_name):
                logger.info(f"Checkpoint restored: {checkpoint_name}")
                if was_mining:
                    self.start_mining()
                return True
            else:
                logger.error(f"Failed to restore checkpoint: {checkpoint_name}")
                return False
        except Exception as e:
            logger.error(f"Error restoring checkpoint: {str(e)}")
            return False
