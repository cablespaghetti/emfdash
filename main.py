#!/usr/bin/env python3
"""EMF Camp Dashboard - TUI dashboard for MQTT feeds."""

import queue

import paho.mqtt.client as mqtt
from rich.panel import Panel
from rich.table import Table
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Header, RichLog, Static

HOST = "mqtt.emf.camp"
PORT = 1883

RICK = """\
   ╔═══════════╗
   ║  NEVER    ║
   ║  GONNA    ║
   ╚═══════════╝
   ┌─────────┐
   │  O   O  │
   │    ^    │
   │  ─────  │
   └─────────┘
"""

DUCK = """\
   ╔═══════════╗
   ║  QUACK    ║
   ║  QUACK    ║
   ╚═══════════╝
      .---.
     ( 'v' )
    (   _   )
      | |/
      | |\\
"""


class MQTTTile(Static):
    status = reactive("connecting")

    def __init__(self, topic: str, ascii_art: str, **kwargs):
        super().__init__(**kwargs)
        self.topic = topic
        self.ascii_art = ascii_art
        self._queue: queue.Queue = queue.Queue(maxsize=200)
        self._client = mqtt.Client()
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

    def compose(self):
        yield Static(classes="tile-header")
        yield RichLog(classes="tile-log", highlight=True, markup=True)

    def on_mount(self):
        self._log = self.query_one(RichLog)
        try:
            self._client.connect_async(HOST, PORT, 60)
            self._client.loop_start()
        except Exception as e:
            self._log.write(Panel(f"[red]Connection error: {e}[/]"))
        self.set_interval(0.1, self._poll)

    def watch_status(self, status: str):
        dot = {"connected": "●", "disconnected": "○", "connecting": "◐"}
        color = {"connected": "green", "disconnected": "red", "connecting": "yellow"}
        self.query_one(".tile-header", Static).update(
            f"[bold {color[status]}]{dot[status]} {self.topic}[/]"
        )

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            client.subscribe(self.topic)
            self.status = "connected"
        else:
            self.status = "disconnected"

    def _on_disconnect(self, client, userdata, rc):
        self.status = "disconnected"

    def _on_message(self, client, userdata, msg):
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
        table.add_column(width=16)
        table.add_column(ratio=1)
        table.add_row(self.ascii_art, payload)
        self._log.write(Panel(table, padding=(0, 1)))


class EmfDashApp(App):
    CSS = """
    Screen {
        background: #1a1b26;
    }

    Horizontal {
        height: 1fr;
    }

    MQTTTile {
        width: 1fr;
        height: 100%;
        border: round $primary;
        margin: 0 1;
    }

    MQTTTile:first-child {
        border: round #7dcfff;
    }

    MQTTTile:last-child {
        border: round #9ece6a;
    }

    .tile-header {
        text-align: center;
        padding: 1 0;
        background: $surface;
        text-style: bold;
    }

    .tile-log {
        height: 1fr;
    }
    """

    def compose(self):
        yield Header(show_clock=True)
        with Horizontal():
            yield MQTTTile("open/astley", RICK)
            yield MQTTTile("open/the-ducks", DUCK)

    def on_mount(self):
        self.title = "EMF Camp Dashboard"
        self.sub_title = "MQTT"


if __name__ == "__main__":
    app = EmfDashApp()
    app.run()
