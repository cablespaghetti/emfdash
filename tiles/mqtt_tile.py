import queue
from datetime import datetime

from rich.text import Text
from textual.events import Resize
from textual.widgets import RichLog, Static

from mqtt import MqttManager


class MQTTLog(RichLog):
    def __init__(self, emoji: str, **kwargs):
        super().__init__(max_lines=200, wrap=True, min_width=0, **kwargs)
        self._emoji = emoji
        self._messages: list[tuple[str, str]] = []

    def add_message(self, ts: str, payload: str) -> None:
        self._messages.append((ts, payload))
        if len(self._messages) > 200:
            self._messages = self._messages[-200:]
        if self._size_known:
            self._render_messages()

    def on_resize(self, event: Resize) -> None:
        super().on_resize(event)
        self._render_messages()

    def _render_messages(self) -> None:
        if not self._messages:
            return
        self.lines.clear()
        self._line_cache.clear()
        self._widest_line_width = 0
        self._start_line = 0
        for ts, payload in self._messages:
            line = Text.assemble(
                (f"{self._emoji} {ts} │ ", "dim"),
                (payload, ""),
            )
            line.overflow = "fold"
            self.write(line, expand=True, shrink=True, scroll_end=False)
        self.scroll_end(animate=False, immediate=True)


class MQTTTile(Static):
    def __init__(self, topic: str, emoji: str, mqtt: MqttManager, **kwargs):
        super().__init__(**kwargs)
        self.topic = topic
        self.emoji = emoji
        self._mqtt = mqtt
        self._queue: queue.Queue = queue.Queue(maxsize=200)

    def compose(self):
        yield Static(f"[bold]MQTT[/] [dim]— {self.topic}[/]", classes="tile-header")
        yield MQTTLog(self.emoji, classes="tile-log")

    def on_mount(self):
        self._log = self.query_one(MQTTLog)
        self._mqtt.subscribe(self.topic, self._mqtt_on_message)
        self.set_interval(0.1, self._poll)

    def _mqtt_on_message(self, msg):
        try:
            payload = msg.payload.decode("utf-8")
        except UnicodeDecodeError:
            payload = str(msg.payload)
        ts = datetime.now().strftime("%H:%M:%S")
        try:
            self._queue.put_nowait((ts, payload))
        except queue.Full:
            pass

    def _poll(self):
        try:
            while True:
                ts, payload = self._queue.get_nowait()
                self._log.add_message(ts, payload)
        except queue.Empty:
            pass
