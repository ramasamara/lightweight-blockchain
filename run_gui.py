from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox
from PyQt5.QtCore import pyqtSignal, QObject, Qt
from medicine_window import Ui_MainWindow
from blockchain import Blockchain
from transaction import Transaction
from blockchain_state import BlockchainState
import sys
import json
import threading
import paho.mqtt.client as mqtt
import ssl
import hashlib

# ---------- Password Hashing ----------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

stored_username = "admin"
stored_password_hash = hash_password("1234")

# ---------- Communicator ----------
class Communicator(QObject):
    message_received = pyqtSignal(str)

# ---------- MainApp ----------
class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.blockchain = Blockchain()
        if not self.blockchain.chain:
            self.blockchain.chain.append(self.blockchain.create_genesis_block())

        self.state = BlockchainState(self.blockchain, data_dir="./data")

        if self.state.load_blockchain():
            print("Blockchain loaded successfully.")
        else:
            print("No blockchain found. Starting new chain.")

        self.ui.addButton.clicked.connect(self.add_transaction)
        self.ui.showBlocksButton.clicked.connect(self.show_blocks)

        self.comm = Communicator()
        self.comm.message_received.connect(self.handle_mqtt_message)

        self.mqtt_thread = threading.Thread(target=self.start_mqtt_listener)
        self.mqtt_thread.daemon = True
        self.mqtt_thread.start()

    def add_transaction(self):
        name = self.ui.nameInput.text()
        expiry = self.ui.expiryInput.text()
        count = self.ui.countInput.text()
        user_id = self.ui.userIdInput.text()

        try:
            count = int(count)
        except ValueError:
            print("Invalid count. Must be a number.")
            return

        payload = {
            "Medicine name": name,
            "Expiration date": expiry,
            "Medicine count": count,
            "user ID": user_id
        }

        self.process_transaction(payload, f"GUI_{user_id}")

    def process_transaction(self, payload, device_id):
        tx = Transaction(content=json.dumps(payload), device_id=device_id)
        self.blockchain.add_transaction(tx)
        block = self.blockchain.mine_pending_transactions(mining_reward_address=device_id)
        self.state.save_blockchain()
        print(f"Block {block.index} added. Hash: {block.hash}")
        self.show_blocks()
        self.ui.StatusLabel.setText(f"Block {block.index} added successfully.")

    def show_blocks(self):
        self.ui.blockDisplay.clear()
        for block in self.blockchain.chain:
            text = f"""
Block {block.index}
Hash: {block.hash}
Previous: {block.previous_hash}
Timestamp: {block.timestamp}
"""
            for tx in block.data.get("transactions", []):
                content_str = tx["content"]
                try:
                    content = json.loads(content_str)
                    content_display = "\n".join([f"{k}: {v}" for k, v in content.items()])
                except:
                    content_display = content_str

                text += f"""
Transaction ID: {tx['transaction_id']}
{content_display}
Timestamp: {tx['timestamp']}
Device ID: {tx['device_id']}
{'-'*30}
"""

            text += "="*40
            self.ui.blockDisplay.append(text)

    def start_mqtt_listener(self):
        def on_connect(client, userdata, flags, rc):
            print("Connected with result code " + str(rc))
            client.subscribe("test")

        def on_message(client, userdata, msg):
            message = msg.payload.decode()
            print("Received from MQTT:", message)
            self.comm.message_received.emit(message)

        client = mqtt.Client()
        client.tls_set(
            ca_certs="rootCA.pem",
            certfile="certificate.pem.crt",
            keyfile="private.pem.key",
            tls_version=ssl.PROTOCOL_TLSv1_2
        )
        client.tls_insecure_set(True)
        client.on_connect = on_connect
        client.on_message = on_message

        client.connect("a3hda0ivrqvweg-ats.iot.eu-north-1.amazonaws.com", 8883, 60)
        client.loop_forever()

    def handle_mqtt_message(self, message):
        try:
            data = json.loads(message)
            print("Processing transaction from MQTT...")
            self.process_transaction(data, device_id="RPI_001")
        except Exception as e:
            print("Error processing MQTT message:", e)

# ---------- LoginWindow ----------
class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")
        self.setFixedSize(350, 220)
        self.setStyleSheet("""
            QWidget {
                background-color: #f2f2f2;
                font-family: Segoe UI;
                font-size: 14px;
            }
            QLabel {
                font-weight: bold;
                margin-top: 10px;
            }
            QLineEdit {
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

        self.username_label = QLabel("Username:")
        self.username_input = QLineEdit()

        self.password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.handle_login)

        layout = QVBoxLayout()
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)
        layout.addSpacing(15)
        layout.addWidget(self.login_button)
        layout.setAlignment(Qt.AlignTop)
        self.setLayout(layout)

    def handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        hashed_input = hash_password(password)

        if username == stored_username and hashed_input == stored_password_hash:
            self.hide()
            self.main_app = MainApp()
            self.main_app.show()
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid username or password")

# ---------- Run Application ----------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec_())
