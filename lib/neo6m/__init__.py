"""u-blox NEO-6M GPS."""

from machine import Pin
from machine import UART

# TX pin, RX pin, and the UART they belong to.
_PINS = {
    (0, 1): 0,
    (12, 13): 0,
    (16, 17): 0,
    (4, 5): 1,
    (8, 9): 1,
}


class Fix:
    def __init__(self, latitude, longitude, altitude, satellites, time, date):
        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude
        self.satellites = satellites
        self.time = time
        self.date = date


class NEO6M:
    def __init__(self, tx, rx, baud=9600):
        uart = _PINS.get((tx, rx))
        if uart is None:
            raise ValueError("pins are not a uart pair")
        self._uart = UART(
            uart,
            baudrate=baud,
            tx=Pin(tx),
            rx=Pin(rx),
            rxbuf=1024,
            timeout=0,
            timeout_char=20,
        )
        self._latitude = None
        self._longitude = None
        self._altitude = None
        self._satellites = None
        self._time = None
        self._date = None
        self._valid = False

    def read(self):
        uart = self._uart
        while uart.any():
            line = uart.readline()
            if line:
                self._sentence(line)
        if not self._valid or self._latitude is None or self._longitude is None:
            return None
        return Fix(
            self._latitude,
            self._longitude,
            self._altitude,
            self._satellites,
            self._time,
            self._date,
        )

    def _sentence(self, line):
        try:
            text = line.decode().strip()
        except UnicodeError:
            return
        if not text.startswith("$") or "*" not in text:
            return
        body, _, given = text[1:].partition("*")
        if len(given) < 2:
            return
        checksum = 0
        for char in body:
            checksum ^= ord(char)
        if "{:02X}".format(checksum) != given[:2].upper():
            return
        fields = body.split(",")
        kind = fields[0]
        if kind.endswith("RMC") and len(fields) >= 10:
            self._rmc(fields)
        elif kind.endswith("GGA") and len(fields) >= 10:
            self._gga(fields)

    def _rmc(self, fields):
        self._time = _clock(fields[1])
        self._date = _day(fields[9])
        if fields[2] != "A":
            self._valid = False
            return
        latitude = _degrees(fields[3], fields[4])
        longitude = _degrees(fields[5], fields[6])
        if latitude is None or longitude is None:
            self._valid = False
            return
        self._latitude = latitude
        self._longitude = longitude
        self._valid = True

    def _gga(self, fields):
        clock = _clock(fields[1])
        if clock is not None:
            self._time = clock
        self._satellites = _count(fields[7])
        self._altitude = _meters(fields[9])
        if not fields[6] or fields[6] == "0":
            self._valid = False
            return
        latitude = _degrees(fields[2], fields[3])
        longitude = _degrees(fields[4], fields[5])
        if latitude is None or longitude is None:
            self._valid = False
            return
        self._latitude = latitude
        self._longitude = longitude
        self._valid = True


def _degrees(raw, hemisphere):
    if not raw or hemisphere not in ("N", "S", "E", "W"):
        return None
    dot = raw.find(".")
    if dot < 2:
        return None
    try:
        minutes = float(raw[dot - 2 :])
        degrees = int(raw[: dot - 2])
    except ValueError:
        return None
    value = degrees + minutes / 60
    if hemisphere in ("S", "W"):
        value = -value
    return value


def _clock(raw):
    if len(raw) < 6:
        return None
    return raw[0:2] + ":" + raw[2:4] + ":" + raw[4:6]


def _day(raw):
    if len(raw) < 6:
        return None
    return raw[0:2] + "/" + raw[2:4] + "/20" + raw[4:6]


def _count(raw):
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def _meters(raw):
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None
