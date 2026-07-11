"""Tests for shared MQTT connection manager."""

from unittest.mock import Mock

from mqtt import MqttManager
from tests.conftest import msg


class TestMqttManager:
    def test_init_status(self):
        m = MqttManager()
        assert m.status == "connecting"

    def test_status_listeners_notified_on_connect(self):
        m = MqttManager()
        events = []
        m.on_status_change(events.append)
        m._on_connect(m._client, None, None, 0, None)
        assert events == ["connecting", "connected"]

    def test_status_listeners_notified_on_disconnect(self):
        m = MqttManager()
        events = []
        m.on_status_change(events.append)
        m._on_connect(m._client, None, None, 0, None)
        m._on_disconnect(m._client, None, None, 0, None)
        assert events == ["connecting", "connected", "disconnected"]

    def test_dispatch_exact_topic(self):
        m = MqttManager()
        handler = Mock()
        m.subscribe("test/topic", handler)
        m._on_message(m._client, None, msg("test/topic", "hello"))
        handler.assert_called_once()

    def test_dispatch_wildcard_matches_subtopic(self):
        m = MqttManager()
        handler = Mock()
        m.subscribe("test/#", handler)
        m._on_message(m._client, None, msg("test/foo/bar", "hello"))
        handler.assert_called_once()

    def test_dispatch_wildcard_no_match(self):
        m = MqttManager()
        handler = Mock()
        m.subscribe("other/#", handler)
        m._on_message(m._client, None, msg("test/topic", "hello"))
        handler.assert_not_called()

    def test_dispatch_first_matching_handler_wins(self):
        m = MqttManager()
        h1 = Mock()
        h2 = Mock()
        m.subscribe("test/#", h1)
        m.subscribe("test/topic", h2)
        m._on_message(m._client, None, msg("test/topic", "hello"))
        h1.assert_called_once()
        h2.assert_not_called()

    def test_on_connect_bad_rc(self):
        m = MqttManager()
        m._on_connect(m._client, None, None, 5, None)
        assert m.status == "disconnected"

    def test_connect_failure_notifies_listeners(self):
        m = MqttManager()
        events = []
        m.on_status_change(events.append)
        m._on_connect(m._client, None, None, 5, None)
        assert events == ["connecting", "disconnected"]

    def test_stop_disconnects(self):
        m = MqttManager()
        m._client = Mock()
        m.stop()
        m._client.loop_stop.assert_called_once()
        m._client.disconnect.assert_called_once()
