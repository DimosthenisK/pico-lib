import time
import network


def _security_name(mode):
    # CYW43 reports auth_mode as a bitfield, not the 0-4 list in the docs.
    # bit 0: PSK or WEP, bit 1: WPA, bit 2: WPA2, bit 3: WPA3.
    if mode == 0:
        return "open"
    versions = []
    if mode & 0x02:
        versions.append("WPA")
    if mode & 0x04:
        versions.append("WPA2")
    if mode & 0x08:
        versions.append("WPA3")
    if not versions:
        if mode & 0x01:
            return "WEP"
        return "unknown"
    name = "/".join(versions)
    if mode & 0x01:
        name += "-PSK"
    return name

_FAILURES = {
    network.STAT_WRONG_PASSWORD: "wrong password",
    network.STAT_NO_AP_FOUND: "network not found",
    network.STAT_CONNECT_FAIL: "connect failed",
}


class Network:
    def __init__(self, ssid, security, rssi):
        self.ssid = ssid
        self.security = security
        self.rssi = rssi


class WiFi:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_wlan"):
            return
        self._wlan = network.WLAN(network.STA_IF)
        self._state = "disconnected"

    def connect(self, ssid, password=None, timeout=20):
        wlan = self._radio()
        # A failed join sticks as "wrong password" until disconnect, so a
        # later correct password is rejected without being tried.
        wlan.disconnect()
        time.sleep(0.2)
        if password is None:
            wlan.connect(ssid)
        else:
            wlan.connect(ssid, password)
        self._state = "connecting"
        deadline = time.ticks_add(time.ticks_ms(), int(timeout * 1000))
        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            if wlan.isconnected():
                self._state = "connected"
                return
            code = wlan.status()
            if code < 0:
                self._state = _FAILURES.get(code, "connect failed")
                raise OSError(self._state)
            time.sleep(0.25)
        self._state = "timed out"
        raise OSError(self._state)

    def scan(self):
        found = {}
        for ssid, _bssid, _channel, rssi, security, _hidden in self._radio().scan():
            name = ssid.decode() if isinstance(ssid, bytes) else ssid
            if not name:
                continue
            current = found.get(name)
            if current is None or rssi > current.rssi:
                found[name] = Network(name, _security_name(security), rssi)
        networks = list(found.values())
        networks.sort(key=lambda item: item.rssi, reverse=True)
        return networks

    def status(self):
        wlan = self._radio()
        if wlan.isconnected():
            ssid = wlan.config("ssid")
            ip = wlan.ifconfig()[0]
            return ssid + "\n" + ip
        return self._state

    def _radio(self):
        if not self._wlan.active():
            self._wlan.active(True)
            while not self._wlan.active():
                time.sleep(0.1)
        return self._wlan
