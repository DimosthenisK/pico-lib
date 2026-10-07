import time
import network


class AccessPoint:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_ap"):
            return
        self._ap = network.WLAN(network.AP_IF)
        self._ssid = ""
        self._state = "stopped"

    def start(self, ssid, password=None):
        if password is not None and len(password) < 8:
            raise ValueError("password must be at least 8 characters")
        ap = self._ap
        if ap.active():
            ap.active(False)
        if password is None:
            ap.config(ssid=ssid, security=network.WLAN.SEC_OPEN)
        else:
            ap.config(ssid=ssid, password=password, security=network.WLAN.SEC_WPA_WPA2)
        ap.active(True)
        deadline = time.ticks_add(time.ticks_ms(), 5000)
        while not ap.active():
            if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                self._state = "failed"
                raise OSError("access point failed")
            time.sleep(0.1)
        self._ssid = ssid
        self._state = "up"

    def status(self):
        if self._ap.active():
            return self._ssid + "\n" + self._ap.ifconfig()[0]
        return self._state
