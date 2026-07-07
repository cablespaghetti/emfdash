import queue

from rich.panel import Panel
from rich.table import Table
from textual.widgets import RichLog, Static

from mqtt import MqttManager


class MQTTTile(Static):
    def __init__(self, topic: str, emoji: str, mqtt: MqttManager, **kwargs):
        super().__init__(**kwargs)
        self.topic = topic
        self.emoji = emoji
        self._mqtt = mqtt
        self._queue: queue.Queue = queue.Queue(maxsize=200)

    def compose(self):
        yield Static(f"[bold]MQTT[/] [dim]— {self.topic}[/]", classes="tile-header")
        yield RichLog(classes="tile-log", highlight=True, markup=True)

    def on_mount(self):
        self._log = self.query_one(RichLog)
        self._mqtt.subscribe(self.topic, self._mqtt_on_message)
        self.set_interval(0.1, self._poll)

    def _mqtt_on_message(self, msg):
        try:
            payload = msg.payload.decode("utf-8")
        except UnicodeDecodeError:
            payload = str(msg.payload)
        try:
            self._queue.put_nowait(payload)
        except queue.Full:
            pass

    def _poll(self):
        try:
            while True:
                payload = self._queue.get_nowait()
                self._display(payload)
        except queue.Empty:
            pass

    def _display(self, payload: str):
        table = Table.grid(padding=(0, 2))
        table.add_column(width=4)
        table.add_column(ratio=1)
        table.add_row(self.emoji, payload)
        self._log.write(Panel(table, padding=(0, 1)))
