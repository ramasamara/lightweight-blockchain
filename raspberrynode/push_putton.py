import time
import paho.mqtt.client as mqtt
import ssl
import json
import RPi.GPIO as GPIO


# Certificate files (download from AWS IoT Core)

CA_FILE = "rootCA.pem"          # Amazon root CA

CERT_FILE = "certificate.pem.crt"      # Your device certificate

PRIVATE_KEY_FILE = "private.pem.key"  # Your private key

# Define Variables

TOPIC = "device/control"
MQTT_TOPIC="device/data"

MQTT_MSG = "Hello from RPI"

Button_PIN=23 #  bush Button 

LED_PIN = 17      # GPIO pin connected to LED

NUM_USER=0

GPIO.setmode(GPIO.BCM)

GPIO.setup(Button_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

GPIO.setup(LED_PIN, GPIO.OUT)



def on_connect(client, userdata, flags, rc):

    print(f"Connected with result code {rc}")

    client.subscribe(TOPIC)

    print(f"Subscribed to topic: {TOPIC}")



# Callback when a message is received

def on_message(client, userdata, msg):

    message = msg.payload.decode().strip().upper()

    print(f"Received message: '{message}' on topic '{msg.topic}'")




# MQTT Client Setup

client = mqtt.Client()

client.on_connect = on_connect

client.on_message = on_message



# SSL/TLS configuration

client.tls_set(ca_certs=CA_FILE,

               certfile=CERT_FILE,

               keyfile=PRIVATE_KEY_FILE,

               tls_version=ssl.PROTOCOL_TLSv1_2)

client.tls_insecure_set(True)



# Connect to AWS IoT

print("Connecting to AWS IoT Core...")

client.connect("a3hda0ivrqvweg-ats.iot.eu-north-1.amazonaws.com", 8883, 60) #Taken from REST API endpoint - Use your own. 



client.loop_start()

try:

    #client.publish(MQTT_TOPIC, payload="Hello to System" , qos=1, retain=True)

    print("System Initialized")

    print("Waiting for push button ...")

    while True:
        button_state = GPIO.input(23)
        if button_state == False: # Button is pressed
            print('Button Pressed...')
            GPIO.output(LED_PIN, GPIO.HIGH)  # Turn LED ON
            print("LED turned ON")
            NUM_USER+=1
            Medicine_name="test_medicine"+ str(NUM_USER)
            # JSON payload
            payload = {
                "Medicine name": Medicine_name,
                "Expiration date": "22-10-2030",
                "Medicine count": 30,
                "user ID": NUM_USER
            }

            client.publish(MQTT_TOPIC, payload=json.dumps(payload), qos=1, retain=False)
            print("Message sent to AWS:", payload)

            # Delay to avoid multiple triggers
            time.sleep(5)
        else:
            GPIO.output(LED_PIN, GPIO.LOW)  # Turn LED OFF
            print("LED turned OFF")

except KeyboardInterrupt:

    print("Exiting System...")

finally:

    GPIO.output(LED_PIN, GPIO.LOW)  # Ensure LED is turned off

    GPIO.cleanup()  # Clean up all GPIO pins

    client.loop_stop()

    client.disconnect()

 



