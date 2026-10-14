"""MQTT client."""

from umqtt.simple import MQTTClient


class MQTT:
    def __init__(self, client_id, server, user=None, password=None, port=1883):
        self._client = MQTTClient(
            _bytes(client_id),
            server,
            port=port,
            user=None if user is None else _bytes(user),
            password=None if password is None else _bytes(password),
        )
        self._on_message = None
        self._client.set_callback(self._deliver)

    def connect(self):
        self._client.connect()

    def disconnect(self):
        self._client.disconnect()

    def publish(self, topic, message, retain=False):
        self._client.publish(_bytes(topic), _bytes(message), retain=retain)

    def subscribe(self, topic, on_message):
        if not callable(on_message):
            raise TypeError("on_message must be callable")
        self._on_message = on_message
        self._client.subscribe(_bytes(topic))

    def check(self):
        self._client.check_msg()

    def _deliver(self, topic, message):
        if self._on_message is None:
            return
        try:
            self._on_message(_text(topic), _text(message))
        except Exception as err:
            print(err)


def _bytes(value):
    if isinstance(value, str):
        return value.encode()
    return value


def _text(value):
    if isinstance(value, str):
        return value
    try:
        return value.decode()
    except UnicodeError:
        return value
