from ble import Bluetooth
from ssd1306 import SSD1306

screen = SSD1306(sda=4, scl=5, width=128, height=64)
radio = Bluetooth()


def incoming(data):
    text = data.decode()
    print(text)
    screen.text(text)


screen.text("Pico\nwaiting")
print("waiting for a Bluetooth connection")
radio.open(incoming, name="Pico")
