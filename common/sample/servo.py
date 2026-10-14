import time

from servo import Servo
from ssd1306 import SSD1306

# Signal pin. Power the servo from 5 V and share ground with the Pico.
PIN = 16

screen = SSD1306(sda=4, scl=5, width=128, height=64)
horn = Servo(PIN)


def show(text):
    print(text)
    screen.text(text)


while True:
    for degrees in (0, 90, 180, 90):
        show("servo\n{} deg".format(degrees))
        horn.angle(degrees)
        time.sleep(1)
