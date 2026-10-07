# Pico 2 W development on WSL

Develop MicroPython for a Raspberry Pi Pico 2 W from Cursor, with the board attached to Windows and the editor running in WSL 2.

The Pico in this setup enumerates as USB `2e8a:0005` (“MicroPython Board in FS mode”) and serves a serial REPL. These steps match that board: MicroPython 1.29, build `RPI_PICO2_W`.

## Layout

```text
common/scripts/     reset, push, REPL, new modules, and versions
common/sample/      example program
common/.venv/       host Python tools (mpremote)
common/typings/     MicroPython stubs for the editor
lib/onboard_led/    onboard LED package
lib/ssd1306/        SSD1306 package (wraps the micropython-lib driver)
lib/wifi/           station Wi-Fi: connect and scan
lib/access_point/   one access point: SSID and optional password
lib/webserver/      HTTP server, port 80 unless you choose another
lib/ble/            BLE connection that delivers incoming bytes as they arrive
```

`push.sh` copies each folder under `lib/` onto the Pico under the same name, so `import onboard_led` works.

## 1. Open the repo in Cursor on WSL

The workspace has to be the WSL copy of this folder, not the Windows path. Cursor’s WSL remote is what the Python interpreter setting and the serial port (`/dev/ttyACM0`) refer to.

Install the Python extension and MicroPico into that WSL remote:

```bash
cursor --install-extension ms-python.python --install-extension paulober.pico-w-go
```

Cursor type-checks with its own Pyright. The workspace settings already point that checker at `common/typings` and `lib`.

## 2. Host Python environment

The tools that talk to the board run on the PC, not on the Pico. They need Python 3.10 or newer. Ubuntu 20.04’s `/usr/bin/python3` is 3.8, which is too old; this machine uses Linuxbrew’s Python 3.10.8.

```bash
python3 --version
python3 -m venv common/.venv
common/.venv/bin/pip install --upgrade pip
common/.venv/bin/pip install -r common/requirements.txt
```

That installs `mpremote` 1.29.0. Check it with `common/.venv/bin/mpremote version`.

## 3. Editor stubs

`import machine` is not a desktop Python module. The editor only understands it after the MicroPython stubs are installed:

```bash
common/.venv/bin/pip install --target common/typings -r common/requirements-stubs.txt
rm -f common/typings/pyproject.toml
```

`requirements-stubs.txt` pins `micropython-rp2-stubs==1.29.0.post1`. That package also installs `micropython-stdlib-stubs` 1.29, and its merged `machine` stubs come from the Pico W rp2 build, which includes `Pin("LED")` and `Pin.board.LED`. Remove `common/typings/pyproject.toml` after install so that file is not treated as a second project.

Reload the Cursor window after the first install. `common/sample/blink.py` should then resolve `machine`, `Pin`, and `onboard_led`.

## 4. Attach the Pico to WSL

WSL 2 does not see USB devices on its own. Windows shares the Pico with [usbipd-win](https://github.com/dorssel/usbipd-win), and this kernel (`6.18.33.1-microsoft-standard-WSL2`) already has the USB/IP and CDC ACM drivers. You do not need a separate `usbip` client: usbipd 5.3 loads the WSL side itself.

Install usbipd on Windows (an administrator prompt appears):

```bash
winget.exe install --id dorssel.usbipd-win -e --source winget --accept-package-agreements --accept-source-agreements --disable-interactivity
```

Plug in the Pico. It must already be running MicroPython, not the BOOTSEL drive. In PowerShell:

```powershell
usbipd list
```

Find the row whose VID:PID is `2e8a:0005`. Note its BUSID (it was `2-2` on this machine, and it can change when you replug). Share it once, from an elevated PowerShell:

```powershell
usbipd bind --busid <BUSID>
```

Attach it to this distro. A WSL terminal has to be open so the distro stays running:

```powershell
usbipd attach --wsl --busid <BUSID>
```

`usbipd list` should show that row as `Attached`. Inside WSL, `lsusb` should show `2e8a:0005 MicroPython Board in FS mode`.

Two WSL quirks are handled by the scripts, so you usually do not run them by hand:

- The serial node does not appear until the `cdc-acm` module is loaded. `sudo` on this distro asks for a password, so the scripts load it with `wsl.exe -d Ubuntu-20.04 -u root modprobe cdc-acm`.
- WSL does not apply udev rules. `/dev/ttyACM0` is created as `root:root` mode `600`. The login needs to be in the `dialout` group (this account already is), and the scripts run `chgrp dialout` and `chmod 660` on the node before opening it.

After a hard reset the Pico drops out of WSL and comes back on Windows as `Shared`. The scripts attach it again and fix the permissions on the new node. The BUSID is read from `usbipd list`; it is not hardcoded.

## 5. Day to day

From the repo root:

```bash
./common/scripts/repl.sh
./common/scripts/reset.sh
./common/scripts/push.sh sample/blink.py
```

`repl.sh` opens the MicroPython prompt. Leave it with Ctrl-] or Ctrl-x.

`reset.sh` runs `machine.reset()`, waits until `2e8a:0005` is back in WSL, and prints the serial port.

`push.sh` copies every package under `lib/` and everything under `common/sample/`, then runs the file you name. Output stays on screen until the program finishes. Ctrl-C stops following. A program that loops, such as the sample, keeps the port open; Ctrl-C ends the host session, and `reset.sh` stops the board.

`push.sh` with no arguments runs `sample/blink.py`.

Only that entry file is started. Other files are on the Pico so the entry file can import them. A package directory needs `__init__.py`.

## Packages

Each folder under `lib/` is a MicroPython package. Its `package.json` tells `mip` which files to copy onto a board. The `urls` list is pairs of `[path on the Pico, file next to package.json]`. `version` is `major.minor.patch`.

This repo’s `push.sh` still copies `lib/` straight onto the attached Pico. Another project installs only what it needs, from GitHub, once this repository’s `main` branch is the project root:

```bash
common/.venv/bin/mpremote mip install github:DimosthenisK/pico-lib/lib/onboard_led@main
common/.venv/bin/mpremote mip install github:DimosthenisK/pico-lib/lib/ssd1306@main
common/.venv/bin/mpremote mip install github:DimosthenisK/pico-lib/lib/wifi@main
common/.venv/bin/mpremote mip install github:DimosthenisK/pico-lib/lib/access_point@main
common/.venv/bin/mpremote mip install github:DimosthenisK/pico-lib/lib/webserver@main
common/.venv/bin/mpremote mip install github:DimosthenisK/pico-lib/lib/ble@main
```

`@main` is the git ref `mpremote` 1.29 fetches. Without it, the request uses `HEAD`, which `raw.githubusercontent.com` does not serve. After you tag a release, `@v0.1.0` pins that tag. The install lands in the board’s `/lib`, which is already on the import path.

`mip` does not copy the sources into the other project. Point that project’s `extraPaths` at a clone of this `lib/` directory so the editor can resolve the imports.

Add a package:

```bash
./common/scripts/new-module.sh sensor
```

That creates `lib/sensor/__init__.py` and `lib/sensor/package.json` at version `0.1.0`. The name is a lowercase Python identifier. If you add more `.py` files later, add a `urls` entry for each one. The first element is the path under the board’s `/lib`.

Set or bump the version:

```bash
./common/scripts/version.sh wifi 0.2.0
./common/scripts/version.sh wifi patch
./common/scripts/version.sh wifi minor
./common/scripts/version.sh wifi major
```

`patch`, `minor`, and `major` require a `major.minor.patch` version. A bump changes `package.json` only. Tag the commit when you want installs to be able to request that version.

## Sample

`common/sample/blink.py` uses the onboard LED package:

```bash
./common/scripts/push.sh sample/blink.py
```

You should see `blinking`. The LED turns on and off in half-second steps. `OnboardLED.blink(duration)` is one on/off cycle, and each half lasts `duration` seconds. `on()` and `off()` set the LED directly.

`common/sample/screen.py` constructs `SSD1306` with the SDA pin, SCL pin, and screen size. `text` clears the panel, draws the string, and shows it. `drawPixel`, `drawLine`, `drawRect`, `fillRect`, and `drawBitmap` add to what is already on the panel and show it. `drawBitmap` reads horizontal rows, with the high bit on the left. `clear` wipes the panel. The driver underneath is micropython-lib's `SSD1306_I2C`, on SoftI2C, because the hardware I2C peripheral returns `EIO` for this panel. This screen is SDA GP4, SCL GP5, 128x64, address `0x3C`.

```bash
./common/scripts/push.sh sample/screen.py
```

`common/sample/wifi.py` scans, prints each network as SSID, security, and signal strength, then shows `WiFi.status()` on the display. Set `SSID` and optionally `PASSWORD` in that file to connect before the status is shown. After it connects, the sample asks an NTP server for the time and adds the UTC date and clock to that display.

```bash
./common/scripts/push.sh sample/wifi.py
```

`common/sample/setup.py` starts an access point named `Pico Setup`. Join that network from a phone or computer and open `http://192.168.4.1`. The page lists scanned networks. Choose one, enter its password if it has one, and the Pico connects as a station. The access point stays up so the browser can show the result. Set `AP_PASSWORD` in that file to protect the setup network; a password must be at least 8 characters, and `None` leaves it open.

```bash
./common/scripts/push.sh sample/setup.py
```

`common/sample/ble.py` advertises as `Pico`. Connect with a BLE serial app that speaks the Nordic UART Service and write to the RX characteristic. Each write is passed to `on_data` as `bytes` and shown on the display. `Bluetooth.open` runs until `close()`. The package is `ble` so it does not cover the firmware `bluetooth` module.

```bash
./common/scripts/push.sh sample/ble.py
```
