"""MG90S hobby servo."""

from machine import Pin
from machine import PWM

# 50 Hz frame. A 500 µs pulse is 0°, and a 2400 µs pulse is 180°.
_FREQ = 50
_MIN_US = 500
_MAX_US = 2400
_SPAN = 180


class Servo:
    def __init__(self, pin):
        self._pwm = PWM(Pin(pin))
        self._pwm.freq(_FREQ)
        self.angle(90)

    def angle(self, degrees):
        if not 0 <= degrees <= _SPAN:
            raise ValueError("angle out of range")
        pulse = _MIN_US + int(degrees * (_MAX_US - _MIN_US) / _SPAN)
        self._pwm.duty_ns(pulse * 1000)

    def off(self):
        self._pwm.duty_ns(0)
