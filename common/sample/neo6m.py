import time

from neo6m import NEO6M
from ssd1306 import SSD1306

# Module RX to GP0, module TX to GP1. Share ground and power VCC.
TX = 0
RX = 1

screen = SSD1306(sda=4, scl=5, width=128, height=64)


def show(text):
    print(text)
    screen.text(text)


def changed(event):
    show(event)


gps = NEO6M(TX, RX, on_event=changed)

while True:
    fix = gps.read()
    if fix is not None:
        satellites = fix.satellites if fix.satellites is not None else 0
        show("{:.5f}\n{:.5f}\n{} sats".format(fix.latitude, fix.longitude, satellites))
    time.sleep(1)
