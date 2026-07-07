from unittest.mock import Mock


def msg(topic, payload):
    m = Mock()
    m.topic = topic
    m.payload = payload.encode("utf-8") if isinstance(payload, str) else payload
    return m
