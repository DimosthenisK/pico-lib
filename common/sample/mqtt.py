import time

from mqtt import MQTT
from ssd1306 import SSD1306
from wifi import WiFi

# Join this network, then talk to the broker on port 1883.
SSID = "Sample"
PASSWORD = None
BROKER = "broker.local"
USER = None
MQTT_PASSWORD = None
TOPIC = "pico/status"

screen = SSD1306(sda=4, scl=5, width=128, height=64)
wifi = WiFi()


def show(text):
    print(text)
    screen.text(text)


def incoming(topic, message):
    show(topic + "\n" + message)


show("wifi\nconnecting")
try:
    wifi.connect(SSID, PASSWORD)
except OSError as err:
    show(str(err))
    raise

show(wifi.status())
client = MQTT("pico", BROKER, user=USER, password=MQTT_PASSWORD)
show("mqtt\nconnecting")
try:
    client.connect()
except OSError as err:
    show(str(err))
    raise

show("mqtt\nconnected")
client.subscribe(TOPIC, incoming)
client.publish(TOPIC, "hello")
show("mqtt\npublished")

while True:
    try:
        client.check()
    except OSError as err:
        show(str(err))
    time.sleep(0.5)
