from ble import Bluetooth
from ssd1306 import SSD1306
from wifi import WiFi

# A central writes the network name, a newline, and the password.
# Those two parts can arrive in one write or as two writes.
# An empty password joins an open network.
screen = SSD1306(sda=4, scl=5, width=128, height=64)
wifi = WiFi()
radio = Bluetooth()
ssid = None
joined = False


def show(text):
    print(text)
    screen.text(text)


def join(name, password):
    global joined
    show("connecting\n" + name)
    try:
        wifi.connect(name, password)
    except OSError as err:
        show(str(err))
        return
    joined = True
    show(wifi.status())


def incoming(data):
    global ssid
    text = data.decode().replace("\r\n", "\n").replace("\r", "\n")
    if "\n" in text:
        name, password = text.split("\n", 1)
        name = name.strip() or ssid
        password = password.strip() or None
        ssid = None
        if not name:
            show("need ssid")
            return
        join(name, password)
        return
    text = text.strip()
    if ssid is None:
        if not text:
            show("need ssid")
            return
        ssid = text
        show("password\n" + ssid)
        return
    join(ssid, text or None)
    ssid = None


def connected(up):
    global ssid
    if up:
        show("BLE\nconnected")
        return
    ssid = None
    if not joined:
        show("BLE\nwaiting")


show("BLE\nwaiting")
print("write ssid, a newline, and the password")
radio.open(incoming, name="Pico WiFi", on_connect=connected)
