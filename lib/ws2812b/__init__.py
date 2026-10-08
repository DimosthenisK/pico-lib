"""64-LED WS2812B string."""

from machine import Pin
from machine import bitstream

# One data line, 64 RGB LEDs. Bytes on the wire are green, red, blue.
_LEDS = 64
_BPP = 3
# 800 kHz. Each pair is high then low, in nanoseconds, for bit 0 then bit 1.
_TIMING = (400, 850, 800, 450)


class WS2812B:
    def __init__(self, pin):
        self._pin = Pin(pin, Pin.OUT)
        self._buf = bytearray(_LEDS * _BPP)
        self.show()

    def set(self, index, red, green, blue):
        if not 0 <= index < _LEDS:
            raise IndexError("led out of range")
        offset = index * _BPP
        self._buf[offset] = green
        self._buf[offset + 1] = red
        self._buf[offset + 2] = blue

    def fill(self, red, green, blue):
        buf = self._buf
        for offset in range(0, len(buf), _BPP):
            buf[offset] = green
            buf[offset + 1] = red
            buf[offset + 2] = blue

    def clear(self):
        self.fill(0, 0, 0)

    def show(self):
        bitstream(self._pin, 0, _TIMING, self._buf)
