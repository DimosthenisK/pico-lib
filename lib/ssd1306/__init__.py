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

    def clear(self):
        self._display.fill(0)
        self._display.show()

    def drawPixel(self, x, y, color=1):
        self._display.pixel(x, y, color)
        self._display.show()

    def drawLine(self, x1, y1, x2, y2, color=1):
        self._display.line(x1, y1, x2, y2, color)
        self._display.show()

    def drawRect(self, x, y, width, height, color=1):
        self._display.rect(x, y, width, height, color)
        self._display.show()

    def fillRect(self, x, y, width, height, color=1):
        self._display.rect(x, y, width, height, color, True)
        self._display.show()

    def drawBitmap(self, x, y, bitmap, width, height, color=1, background=None):
        # Horizontal rows, most significant bit on the left, padded to whole bytes.
        stride = (width + 7) // 8
        for row in range(height):
            for col in range(width):
                byte = bitmap[row * stride + (col >> 3)]
                on = byte & (0x80 >> (col & 7))
                if on:
                    self._display.pixel(x + col, y + row, color)
                elif background is not None:
                    self._display.pixel(x + col, y + row, background)
        self._display.show()
