"""Editor stub for micropython-lib umqtt.simple."""

from collections.abc import Callable

class MQTTClient:
    def __init__(
        self,
        client_id: bytes | str,
        server: str,
        port: int = 0,
        user: bytes | str | None = None,
        password: bytes | str | None = None,
        keepalive: int = 0,
        ssl: object | None = None,
        ssl_params: dict | None = None,
    ) -> None: ...
    def set_callback(self, callback: Callable[[bytes, bytes], None]) -> None: ...
    def connect(self, clean_session: bool = True, timeout: int | None = None) -> int | None: ...
    def disconnect(self) -> None: ...
    def publish(
        self,
        topic: bytes | str,
        msg: bytes | str,
        retain: bool = False,
        qos: int = 0,
    ) -> None: ...
    def subscribe(self, topic: bytes | str, qos: int = 0) -> None: ...
    def check_msg(self) -> int | None: ...
