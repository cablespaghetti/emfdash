import queue
from datetime import datetime

from rich.table import Table
from textual.geometry import Size
from textual.scroll_view import ScrollView
from textual.strip import Strip
from textual.widgets import Static

from mqtt import MqttManager


class MQTTLog(ScrollView):
    def __init__(self, emoji: str, **kwargs):
        super().__init__(**kwargs)
        self._emoji = emoji
        self._messages: list[tuple[str, str]] = []
        self._dirty = False
        self._rendered_lines: list[Strip] = []

    def add_message(self, ts: str, payload: str) -> None:
        self._messages.append((ts, payload))
        self._dirty = True

    def rebuild(self) -> None:
        if not self._dirty or self.size.width <= 0:
            return
        self._dirty = False

        if len(self._messages) > 200:
            self._messages = self._messages[-200:]

        table = Table.grid(padding=(0, 2), expand=True)
        table.add_column(width=4)
        table.add_column(ratio=1)
        table.add_column(width=8)
        for ts, payload in self._messages:
            table.add_row(self._emoji, payload, ts)

        width = max(1, self.content_region.width)
        options = self.app.console.options.update(width=width)
        lines = self.app.console.render_lines(table, options)
        self._rendered_lines = [Strip(segments, width) for segments in lines]
        self.virtual_size = Size(width, len(self._rendered_lines))
        self.scroll_end(animate=False, immediate=True, x_axis=False)
        self.refresh()

    def render_line(self, y: int) -> Strip:
        scroll_x, scroll_y = self.scroll_offset
        real_y = scroll_y + y
        width = self.size.width
        rich_style = self.rich_style

        if real_y >= len(self._rendered_lines):
            return Strip.blank(width, rich_style)

        strip = self._rendered_lines[real_y]
        strip = strip.crop_extend(scroll_x, scroll_x + width, rich_style)
        return strip


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
        self._log.rebuild()
