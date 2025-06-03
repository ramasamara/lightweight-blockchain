
# Lightweight Blockchain for Pharmaceutical Supply Chain (with IoT Integration)

## Introduction

This project implements a lightweight blockchain framework specifically designed for tracking pharmaceutical products throughout the supply chain. Optimized for Internet of Things (IoT) devices, it provides a secure and transparent ledger to record medicine-related transactions like manufacturing details, shipment information, and delivery confirmations.

The system includes:
- A GUI for manual data entry and blockchain visualization.
- MQTT integration for real-time data ingestion.
- A Raspberry Pi script that triggers transactions via physical button presses.
- A lightweight Proof-of-Work (PoW) consensus mechanism suitable for IoT environments.

## Features

- **Lightweight Blockchain Core**: Optimized for IoT using `blockchain.py`, `block.py`, and `transaction.py`.
- **Proof-of-Work Consensus**: Adjustable algorithm implemented in `pow_miner.py`.
- **IoT Optimizations**: `IoTOptimizedMiner` in `pow_miner.py` monitors CPU and adapts power usage.
- **Graphical User Interface (GUI)**: PyQt5-based GUI in `run_gui.py`, `medicine_window.py`, and `medicine_window.ui`.
- **MQTT Integration**: Used by both the GUI and Raspberry Pi for real-time data exchange.
- **Raspberry Pi Integration**: `raspberrynode/push_putton.py` uses GPIO to trigger medicine transactions with LED feedback.
- **Persistent State**: Saves blockchain state in `blockchain.json` with support for checkpoints via `blockchain_state.py`.
- **Node Management**: Mining nodes are supported via `mining_node.py`.
- **Secure Login**: Simple login with hashed password (not secure for production).

## Architecture

### Core Modules

- `block.py`: Block class.
- `transaction.py`: Transaction class.
- `blockchain.py`: Blockchain logic.
- `pow_miner.py`: ProofOfWork and IoTOptimizedMiner.
- `mining_node.py`: Mining node management.
- `blockchain_state.py`: Save/load blockchain state.
- `run_gui.py`: GUI entry point.
- `medicine_window.py`, `medicine_window.ui`: GUI layout and behavior.
- `raspberrynode/push_putton.py`: Raspberry Pi GPIO/MQTT trigger script.

## Dependencies

Install general dependencies:

```bash
pip install PyQt5 paho-mqtt psutil
```

On Raspberry Pi:

```bash
sudo apt-get update && sudo apt-get install python3-rpi.gpio
pip install paho-mqtt
```

## Setup

1. Clone or download the project.
2. Install dependencies.
3. Ensure `certificate.pem.crt`, `private.pem.key`, and `rootCA.pem` are in the correct folders.
4. Connect button to GPIO 23 and LED to GPIO 17 on Raspberry Pi.

## Usage

### Run GUI (Laptop)

```bash
python run_gui.py
```

- Login: `admin / 1234`
- Use GUI to add transactions or view blockchain.
- GUI listens to MQTT topic `test`.

### Run Raspberry Pi Node

```bash
cd raspberrynode
sudo python push_putton.py
```

- Publishes JSON transactions to MQTT.
- Uses GPIO 23 for input and GPIO 17 for LED output.
- Requires MQTT certificates in `raspberrynode/`.

## Project Structure

```
lightweightblockchain/
├── data/blockchain.json
├── raspberrynode/
│   ├── push_putton.py
│   ├── certificate.pem.crt
│   ├── private.pem.key
│   └── rootCA.pem
├── block.py
├── blockchain.py
├── blockchain_state.py
├── certificate.pem.crt
├── medicine_window.py
├── medicine_window.ui
├── mining_node.py
├── pow_miner.py
├── private.pem.key
├── rootCA.pem
├── run_gui.py
├── transaction.py
└── README.md
```

## Consensus Mechanism

- Lightweight Proof-of-Work with difficulty adjustment.
- `IoTOptimizedMiner` can adapt mining to system resources.

## Data Persistence

- Blockchain saved to `data/blockchain.json` using `BlockchainState`.

## Security Considerations

- TLS MQTT encryption enabled.
- Simple login uses SHA-256 but hardcoded credentials (improve for production).
- No transaction signatures; consider adding for real-world use.
- Raspberry Pi script requires `sudo`.

