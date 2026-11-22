"""Небольшая обёртка над paho-mqtt (>=2.0, CallbackAPIVersion.VERSION2)."""

import json
import logging
from collections.abc import Callable
from typing import Any

import paho.mqtt.client as mqtt

log = logging.getLogger(__name__)

Handler = Callable[[str, Any], None]


class MqttBus:
    def __init__(
        self,
        host: str,
        port: int,
        username: str = "",
        password: str = "",
        client_id: str = "bus",
    ) -> None:
        self.host = host
        self.port = port
        self._handlers: dict[str, Handler] = {}

        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=client_id,
        )
        if username:
            self.client.username_pw_set(username, password)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    # ---- paho callbacks -----------------------------------------------------

    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        log.info("MQTT connected (%s:%d), reason=%s", self.host, self.port, reason_code)
        for topic in self._handlers:
            client.subscribe(topic)

    def _on_message(self, client, userdata, msg):
        for topic, handler in self._handlers.items():
            if mqtt.topic_matches_sub(topic, msg.topic):
                try:
                    payload = json.loads(msg.payload.decode("utf-8"))
                except json.JSONDecodeError:
                    payload = msg.payload.decode("utf-8", errors="replace")
                handler(msg.topic, payload)

    # ---- public API ---------------------------------------------------------

    def subscribe(self, topic: str, handler: Handler) -> None:
        self._handlers[topic] = handler
        if self.client.is_connected():
            self.client.subscribe(topic)

    def publish(self, topic: str, payload: Any, qos: int = 1) -> None:
        if isinstance(payload, str):
            data = payload
        else:
            data = json.dumps(payload, ensure_ascii=False)
        self.client.publish(topic, data, qos=qos)

    def connect(self) -> None:
        self.client.connect(self.host, self.port, keepalive=30)
        self.client.loop_start()

    def disconnect(self) -> None:
        self.client.loop_stop()
        self.client.disconnect()
