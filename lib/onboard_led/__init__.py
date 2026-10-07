import time
from machine import Pin


class OnboardLED:
    def __init__(self):
        self._pin = Pin("LED", Pin.OUT)
        self.off()

    def on(self):
        self._pin.on()

    def off(self):
        self._pin.off()

    def blink(self, duration):
        """One blink: on for `duration` seconds, then off for `duration` seconds."""
        self.on()
        time.sleep(duration)
        self.off()
        time.sleep(duration)
