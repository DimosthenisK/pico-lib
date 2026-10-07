import asyncio

import aioble
import bluetooth

# Nordic UART Service. A phone writes the RX characteristic, and those bytes
# are what open() delivers.
_UART = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
_UART_RX = bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")


class Bluetooth:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_rx"):
            return
        self._rx = None
        self._on_data = None
        self._stop = False

    def open(self, on_data, name="Pico"):
        if not callable(on_data):
            raise TypeError("on_data must be callable")
        self._on_data = on_data
        self._stop = False
        self._ensure()
        asyncio.run(self._session(name))

    def close(self):
        self._stop = True

    def _ensure(self):
        if self._rx is not None:
            return
        service = aioble.Service(_UART)
        self._rx = aioble.Characteristic(
            service,
            _UART_RX,
            write=True,
            write_no_response=True,
            capture=True,
        )
        aioble.register_services(service)

    async def _session(self, name):
        while not self._stop:
            try:
                connection = await aioble.advertise(
                    250000,
                    name=name,
                    services=[_UART],
                    timeout_ms=1000,
                )
            except asyncio.TimeoutError:
                continue
            while not self._stop and connection.is_connected():
                try:
                    result = await self._rx.written(timeout_ms=1000)
                except asyncio.TimeoutError:
                    continue
                except aioble.DeviceDisconnectedError:
                    break
                data = result[1] if isinstance(result, tuple) else result
                if data is None:
                    data = b""
                try:
                    self._on_data(bytes(data))
                except Exception as err:
                    print(err)
