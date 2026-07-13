"""Shared MQTT connection manager."""

import paho.mqtt.client as mqtt

from constants import HOST, PORT


class MqttManager:
    def __init__(self):
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message
        self._client.reconnect_delay_set(min_delay=1, max_delay=60)
        self._handlers: list[tuple[str, callable]] = []
        self._status = "connecting"
        self._status_listeners: list[callable] = []

    @property
    def status(self) -> str:
        return self._status

    def on_status_change(self, listener: callable):
        self._status_listeners.append(listener)
        listener(self._status)

    def subscribe(self, topic_filter: str, handler: callable):
        self._client.subscribe(topic_filter)
        self._handlers.append((topic_filter, handler))

    def start(self):
        self._client.connect_async(HOST, PORT, 15)
        self._client.loop_start()

    def stop(self):
        self._client.loop_stop()
        self._client.disconnect()

    def _notify_status(self):
        for listener in self._status_listeners:
            listener(self._status)

    def _subscribe_all(self):
        for topic_filter, _ in self._handlers:
            self._client.subscribe(topic_filter)

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            self._status = "connected"
            self._subscribe_all()
        else:
            self._status = "disconnected"
        self._notify_status()

    def _on_disconnect(
        self, client, userdata, disconnect_flags, reason_code, properties
    ):
        self._status = "disconnected"
        self._notify_status()

    def _on_message(self, client, userdata, msg):
        for topic_filter, handler in self._handlers:
            if topic_filter.endswith("/#"):
                if msg.topic.startswith(topic_filter[:-2]):
                    handler(msg)
                    return
            elif topic_filter == msg.topic:
                handler(msg)
                return
