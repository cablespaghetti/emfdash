import queue
from datetime import datetime

from rich.table import Table
from textual.widgets import RichLog, Static

from mqtt import MqttManager


class MQTTTile(Static):
    def __init__(self, topic: str, emoji: str, mqtt: MqttManager, **kwargs):
        super().__init__(**kwargs)
        self.topic = topic
        self.emoji = emoji
        self._mqtt = mqtt
        self._messages: list[tuple[str, str]] = []
        self._dirty = False

    def compose(self):
        yield Static(f"[bold]MQTT[/] [dim]— {self.topic}[/]", classes="tile-header")
        yield Static(id="log", classes="tile-log")

    def on_mount(self):
        self._log = self.query_one("#log", Static)
        self._mqtt.subscribe(self.topic, self._mqtt_on_message)
        self.set_interval(0.1, self._poll)

    def _mqtt_on_message(self, msg):
        try:
            payload = msg.payload.decode("utf-8")
        except UnicodeDecodeError:
            payload = str(msg.payload)
        ts = datetime.now().strftime("%H:%M:%S")
        try:
            self._messages.append((ts, payload))
            self._dirty = True
        except Exception:
            pass

    def _poll(self):
        if self._dirty:
            self._dirty = False
            self._redraw()

    def _redraw(self):
        table = Table.grid(padding=(0, 2), expand=True)
        table.add_column(width=4)
        table.add_column(ratio=1)
        table.add_column(width=8)
        for ts, payload in self._messages[-200:]:
            table.add_row(self.emoji, payload, ts)
        self._log.update(table)
        self._log.scroll_end(animate=False)
