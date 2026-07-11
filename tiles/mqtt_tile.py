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
        self._queue: queue.Queue = queue.Queue(maxsize=200)

    def compose(self):
        yield Static(f"[bold]MQTT[/] [dim]— {self.topic}[/]", classes="tile-header")
        yield RichLog(classes="tile-log", highlight=True, markup=True, wrap=True)

    def on_mount(self):
        self._log = self.query_one(RichLog)
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
                self._display(ts, payload)
        except queue.Empty:
            pass

    def _display(self, timestamp: str, payload: str):
        table = Table.grid(expand=True)
        table.add_column(width=4)
        table.add_column(ratio=1)
        table.add_column(width=8, justify="right")
        table.add_row(self.emoji, payload, timestamp)
        self._log.write(table)
