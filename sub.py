# This script connects a device (like a Raspberry Pi) to AWS IoT Core using MQTT over TLS.
# It listens to a topic ("test") for incoming messages.
# When a valid JSON message is received, it creates a new transaction, adds it to the blockchain,
# mines a new block, and saves the updated blockchain state.
# Additionally, it sends a message to the topic every 5 seconds with a count,
# simulating periodic "button press" events.


import time
import paho.mqtt.client as mqtt
import ssl
import json
#import RPi.GPIO as GPIO
from blockchain import Blockchain
from transaction import Transaction
from blockchain_state import BlockchainState


blockchain = Blockchain()
state = BlockchainState(blockchain)
state.load_blockchain()
print("Blockchain loaded. Current length:", len(blockchain.chain))


# Certificate files
CA_FILE = "rootCA.pem"
CERT_FILE = "certificate.pem.crt"
PRIVATE_KEY_FILE = "private.pem.key"

# Topics
TOPIC = "test"
Count = 0

# GPIO setup
LED_PIN = 17
#GPIO.setmode(GPIO.BCM)
#GPIO.setup(LED_PIN, GPIO.OUT)

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe(TOPIC)
    print(f"Subscribed to topic: {TOPIC}")

def on_message(client, userdata, msg):
    # Silently handle JSON parsing without showing any debug messages
    try:
        payload = msg.payload.decode()
        # Only attempt to parse if payload is not empty
        if payload.strip():
            data = json.loads(payload)
            # Only print successful JSON messages
            print(f"Received JSON message: {data} on topic '{msg.topic}'")

            # Uncomment the following code when ready to process valid messages
            tx = Transaction(content="Button Pressed", device_id="device-01")
            blockchain.add_transaction(tx)
            block = blockchain.mine_pending_transactions(mining_reward_address="device-01")
            state.save_blockchain()
            print("Blockchain saved.")
            print(f"New block mined! Index: {block.index}, Hash: {block.hash}")
    except json.JSONDecodeError:
        # Silently ignore JSON decoding errors
        pass
    except Exception:
        # Silently ignore other exceptions
        pass

# MQTT Client Setup
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# SSL/TLS config
client.tls_set(ca_certs=CA_FILE,
               certfile=CERT_FILE,
               keyfile=PRIVATE_KEY_FILE,
               tls_version=ssl.PROTOCOL_TLSv1_2)
client.tls_insecure_set(True)

try:
    print("Connecting to AWS IoT Core...")
    client.connect("a3hda0ivrqvweg-ats.iot.eu-north-1.amazonaws.com", 8883, 60)
    client.loop_start()

    while True:
        Payload_MSG = f"Button Pressed {Count} times"
        client.publish(TOPIC , payload=Payload_MSG, qos=1, retain=False)
        time.sleep(5)

except KeyboardInterrupt:
    print("Exiting Button Press System...")

finally:
    client.loop_stop()
    client.disconnect()
    #GPIO.cleanup()

