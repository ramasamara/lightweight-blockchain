"""
Proof of Work module for the Lightweight Blockchain Framework for IoT.

This module provides an optimized Proof of Work implementation suitable for
resource-constrained IoT devices, with configurable difficulty and
adaptive adjustment mechanisms.
"""

import hashlib
import time
import random
import threading
import logging
from block import Block

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('pow_miner')


class ProofOfWork:
    """
    ProofOfWork class implements a lightweight mining algorithm optimized for IoT devices.
    
    Features:
    - Configurable difficulty level
    - Adaptive difficulty adjustment
    - Resource-aware mining with pause/resume capability
    - Low memory footprint
    """
    
    def __init__(self, initial_difficulty=3, target_time=10, adjustment_factor=0.2):
        """
        Initialize a new ProofOfWork instance.
        
        Args:
            initial_difficulty (int): Initial number of leading zeros required in hash
            target_time (int): Target time in seconds for mining a block
            adjustment_factor (float): How quickly difficulty adjusts (0.1-0.5 recommended)
        """
        self.difficulty = initial_difficulty
        self.target_time = target_time
        self.adjustment_factor = adjustment_factor
        self.mining_stats = {
            'blocks_mined': 0,
            'total_time': 0,
            'average_time': 0,
            'last_difficulties': []
        }
        self.mining_thread = None
        self.stop_mining = threading.Event()
    
    def calculate_hash(self, block):
        """
        Calculate the hash of a block.
        
        Args:
            block (Block): Block to hash
            
        Returns:
            str: Hexadecimal string representation of the block hash
        """
        return block.calculate_hash()
    
    def check_difficulty(self, hash_string, difficulty):
        """
        Check if a hash meets the difficulty requirement.
        
        Args:
            hash_string (str): Hash to check
            difficulty (int): Number of leading zeros required
            
        Returns:
            bool: True if the hash meets the difficulty requirement
        """
        return hash_string.startswith('0' * difficulty)
    
    def mine_block(self, block, max_nonce=1000000):
        """
        Mine a block by finding a hash with the required number of leading zeros.
        
        Args:
            block (Block): Block to mine
            max_nonce (int): Maximum nonce value to try before giving up
            
        Returns:
            tuple: (success, nonce, hash, time_taken)
        """
        start_time = time.time()
        nonce = 0
        
        # Try different nonce values until a valid hash is found
        while nonce < max_nonce:
            block.nonce = nonce
            hash_result = self.calculate_hash(block)
            
            # Check if the hash meets the difficulty requirement
            if self.check_difficulty(hash_result, self.difficulty):
                time_taken = time.time() - start_time
                block.hash = hash_result
                
                # Update mining statistics
                self.mining_stats['blocks_mined'] += 1
                self.mining_stats['total_time'] += time_taken
                self.mining_stats['average_time'] = (
                    self.mining_stats['total_time'] / self.mining_stats['blocks_mined']
                )
                self.mining_stats['last_difficulties'].append(self.difficulty)
                if len(self.mining_stats['last_difficulties']) > 10:
                    self.mining_stats['last_difficulties'].pop(0)
                
                logger.info(f"Block mined in {time_taken:.2f} seconds with nonce {nonce}")
                return True, nonce, hash_result, time_taken
            
            nonce += 1
            
            # Periodically yield to prevent CPU hogging
            if nonce % 10000 == 0:
                time.sleep(0.001)
        
        time_taken = time.time() - start_time
        logger.warning(f"Failed to mine block after {max_nonce} attempts ({time_taken:.2f} seconds)")
        return False, nonce, None, time_taken
    
    def adjust_difficulty(self, time_taken):
        """
        Adjust the mining difficulty based on the time taken to mine the last block.
        
        Args:
            time_taken (float): Time in seconds taken to mine the last block
            
        Returns:
            int: New difficulty level
        """
        # Only adjust after we have some mining history
        if self.mining_stats['blocks_mined'] < 3:
            return self.difficulty
        
        # Calculate adjustment based on target time
        ratio = time_taken / self.target_time
        
        # If mining was too fast, increase difficulty
        if ratio < 0.8:
            self.difficulty += self.adjustment_factor
        # If mining was too slow, decrease difficulty
        elif ratio > 1.2:
            self.difficulty -= self.adjustment_factor
        
        # Ensure difficulty is at least 1
        self.difficulty = max(1, self.difficulty)
        
        # Round to nearest 0.5
        self.difficulty = round(self.difficulty * 2) / 2
        
        logger.info(f"Adjusted difficulty to {self.difficulty} (mining took {time_taken:.2f}s, target: {self.target_time}s)")
        return self.difficulty
    
    def start_mining_thread(self, blockchain, miner_address):
        """
        Start mining in a separate thread.
        
        Args:
            blockchain (Blockchain): Blockchain to mine on
            miner_address (str): Address to receive mining rewards
            
        Returns:
            bool: True if the thread was started
        """
        if self.mining_thread and self.mining_thread.is_alive():
            logger.warning("Mining thread is already running")
            return False
        
        self.stop_mining.clear()
        self.mining_thread = threading.Thread(
            target=self._mining_loop,
            args=(blockchain, miner_address)
        )
        self.mining_thread.daemon = True
        self.mining_thread.start()
        
        logger.info(f"Mining thread started with difficulty {self.difficulty}")
        return True
    
    def stop_mining_thread(self):
        """
        Stop the mining thread.
        
        Returns:
            bool: True if the thread was stopped
        """
        if not self.mining_thread or not self.mining_thread.is_alive():
            logger.warning("No mining thread is running")
            return False
        
        self.stop_mining.set()
        self.mining_thread.join(timeout=2)
        self.mining_thread = None
        
        logger.info("Mining thread stopped")
        return True
    
    def _mining_loop(self, blockchain, miner_address):
        """
        Mining loop that runs in a separate thread.
        
        Args:
            blockchain (Blockchain): Blockchain to mine on
            miner_address (str): Address to receive mining rewards
        """
        while not self.stop_mining.is_set():
            try:
                # Check if there are pending transactions
                if not blockchain.pending_transactions:
                    logger.info("No pending transactions, waiting...")
                    time.sleep(1)
                    continue
                
                # Mine a new block
                new_block = blockchain.mine_pending_transactions(miner_address)
                
                # Adjust difficulty based on mining time
                if hasattr(new_block, 'mining_time'):
                    self.adjust_difficulty(new_block.mining_time)
                
                # Small delay between mining attempts
                time.sleep(0.5)
            
            except Exception as e:
                logger.error(f"Error in mining loop: {str(e)}")
                time.sleep(5)  # Sleep for a short time before retrying
    
    def get_mining_stats(self):
        """
        Get statistics about the mining process.
        
        Returns:
            dict: Dictionary of mining statistics
        """
        return {
            'current_difficulty': self.difficulty,
            'target_time': self.target_time,
            'blocks_mined': self.mining_stats['blocks_mined'],
            'average_time': self.mining_stats['average_time'],
            'is_mining': self.mining_thread is not None and self.mining_thread.is_alive(),
            'difficulty_history': self.mining_stats['last_difficulties']
        }


class IoTOptimizedMiner:
    """
    IoTOptimizedMiner extends the basic ProofOfWork with additional optimizations
    specifically for IoT devices.
    
    Features:
    - Resource monitoring to prevent overheating
    - Adaptive mining based on device capabilities
    - Power-saving modes
    """
    
    def __init__(self, pow_instance, max_temperature=70, max_cpu_percent=80):
        """
        Initialize a new IoTOptimizedMiner.
        
        Args:
            pow_instance (ProofOfWork): ProofOfWork instance to use
            max_temperature (float): Maximum CPU temperature in Celsius
            max_cpu_percent (float): Maximum CPU usage percentage
        """
        self.pow = pow_instance
        self.max_temperature = max_temperature
        self.max_cpu_percent = max_cpu_percent
        self.power_mode = "normal"  # "low", "normal", "high"
        self.monitoring_thread = None
        self.stop_monitoring = threading.Event()
    
    def start_mining(self, blockchain, miner_address):
        """
        Start mining with resource monitoring.
        
        Args:
            blockchain (Blockchain): Blockchain to mine on
            miner_address (str): Address to receive mining rewards
            
        Returns:
            bool: True if mining was started
        """
        # Start resource monitoring
        self.start_monitoring()
        
        # Start mining
        return self.pow.start_mining_thread(blockchain, miner_address)
    
    def stop_mining(self):
        """
        Stop mining and resource monitoring.
        
        Returns:
            bool: True if mining was stopped
        """
        # Stop resource monitoring
        self.stop_monitoring.set()
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2)
            self.monitoring_thread = None
        
        # Stop mining
        return self.pow.stop_mining_thread()
    
    def start_monitoring(self):
        """
        Start monitoring system resources.
        
        Returns:
            bool: True if monitoring was started
        """
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            logger.warning("Monitoring thread is already running")
            return False
        
        self.stop_monitoring.clear()
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
        logger.info("Resource monitoring started")
        return True
    
    def _monitoring_loop(self):
        """
        Resource monitoring loop that runs in a separate thread.
        """
        try:
            import psutil
        except ImportError:
            logger.warning("psutil not available, resource monitoring limited")
            psutil = None
        
        while not self.stop_monitoring.is_set():
            try:
                # Get CPU temperature (if available)
                temperature = None
                if psutil:
                    if hasattr(psutil, "sensors_temperatures"):
                        temps = psutil.sensors_temperatures()
                        if temps:
                            for name, entries in temps.items():
                                for entry in entries:
                                    if entry.current > 0:
                                        temperature = entry.current
                                        break
                                if temperature:
                                    break
                
                # Get CPU usage
                cpu_percent = None
                if psutil:
                    cpu_percent = psutil.cpu_percent(interval=1)
                
                # Adjust mining based on resources
                self._adjust_mining_for_resources(temperature, cpu_percent)
                
                # Sleep for a while
                time.sleep(5)
            
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(5)
    
    def _adjust_mining_for_resources(self, temperature, cpu_percent):
        """
        Adjust mining parameters based on system resources.
        
        Args:
            temperature (float): CPU temperature in Celsius
            cpu_percent (float): CPU usage percentage
        """
        # Skip if we don't have resource information
        if temperature is None and cpu_percent is None:
            return
        
        old_mode = self.power_mode
        
        # Check temperature
        if temperature is not None:
            if temperature > self.max_temperature:
                self.power_mode = "low"
                logger.warning(f"High temperature detected ({temperature}°C), switching to low power mode")
            elif temperature > self.max_temperature * 0.9:
                self.power_mode = "normal"
                logger.info(f"Elevated temperature ({temperature}°C), maintaining normal power mode")
            else:
                # Only set to high if CPU usage allows
                if cpu_percent is None or cpu_percent < self.max_cpu_percent * 0.8:
                    self.power_mode = "high"
        
        # Check CPU usage
        if cpu_percent is not None:
            if cpu_percent > self.max_cpu_percent:
                self.power_mode = "low"
                logger.warning(f"High CPU usage detected ({cpu_percent}%), switching to low power mode")
            elif cpu_percent > self.max_cpu_percent * 0.9:
                self.power_mode = "normal"
                logger.info(f"Elevated CPU usage ({cpu_percent}%), maintaining normal power mode")
        
        # Apply power mode changes
        if old_mode != self.power_mode:
            self._apply_power_mode()
    
    def _apply_power_mode(self):
        """
        Apply the current power mode to the mining parameters.
        """
        if self.power_mode == "low":
            # Reduce mining difficulty and increase target time
            self.pow.difficulty = max(1, self.pow.difficulty - 1)
            self.pow.target_time = self.pow.target_time * 1.5
            logger.info(f"Low power mode: difficulty={self.pow.difficulty}, target_time={self.pow.target_time}")
        
        elif self.power_mode == "normal":
            # Use default settings
            self.pow.target_time = 10  # Reset to default
            logger.info(f"Normal power mode: difficulty={self.pow.difficulty}, target_time={self.pow.target_time}")
        
        elif self.power_mode == "high":
            # Increase mining difficulty and decrease target time
            self.pow.difficulty = self.pow.difficulty + 0.5
            self.pow.target_time = max(5, self.pow.target_time * 0.8)
            logger.info(f"High power mode: difficulty={self.pow.difficulty}, target_time={self.pow.target_time}")
    
    def get_status(self):
        """
        Get the current status of the miner.
        
        Returns:
            dict: Dictionary with miner status information
        """
        return {
            'power_mode': self.power_mode,
            'is_mining': self.pow.mining_thread is not None and self.pow.mining_thread.is_alive(),
            'is_monitoring': self.monitoring_thread is not None and self.monitoring_thread.is_alive(),
            'difficulty': self.pow.difficulty,
            'target_time': self.pow.target_time,
            'mining_stats': self.pow.get_mining_stats()
        }
