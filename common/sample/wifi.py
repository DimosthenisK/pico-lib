import ntptime
import time

from ssd1306 import SSD1306
from wifi import WiFi

# Set these to join a network. Leave SSID as None to only scan.
SSID = "Sample"
PASSWORD = None

screen = SSD1306(sda=4, scl=5, width=128, height=64)
wifi = WiFi()


def internet_time():
    ntptime.timeout = 5
    last = OSError("time failed")
    for _ in range(3):
        try:
            ntptime.settime()
            break
        except OSError as err:
            last = err
            time.sleep(1)
    else:
        raise last
    year, month, day, hour, minute, second, *_ = time.localtime()
    return "{:04d}-{:02d}-{:02d}\n{:02d}:{:02d}:{:02d} UTC".format(
        year, month, day, hour, minute, second
    )


screen.text("scanning")
networks = wifi.scan()
for net in networks:
    print(net.ssid, net.security, net.rssi)

connected = False
if SSID:
    screen.text("connecting")
    try:
        wifi.connect(SSID, PASSWORD)
        connected = True
    except OSError as err:
        print(err)

status = wifi.status()
if connected:
    screen.text("time")
    try:
        status += "\n" + internet_time()
    except OSError as err:
        print(err)
        status += "\ntime failed"

print(status)
screen.text(status)
