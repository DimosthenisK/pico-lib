from machine import Pin, SoftI2C
from ssd1306.ssd1306 import SSD1306_I2C


class SSD1306:
    def __init__(self, sda, scl, width, height, addr=0x3C):
        i2c = SoftI2C(sda=Pin(sda), scl=Pin(scl), freq=400000)
        self._display = SSD1306_I2C(width, height, i2c, addr)

    def text(self, string, x=0, y=0):
        self._display.fill(0)
        for line in string.split("\n"):
            self._display.text(line, x, y)
            y += 8
        self._display.show()
