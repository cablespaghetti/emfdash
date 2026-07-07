#!/usr/bin/env python3
"""EMF Camp Dashboard - TUI dashboard for MQTT feeds."""

import queue

import paho.mqtt.client as mqtt
from rich.panel import Panel
from rich.table import Table
from textual.app import App
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Header, RichLog, Static

HOST = "mqtt.emf.camp"
PORT = 1883

RICK = "🕺"
DUCK = "🦆"

SUNNY = """\
      ;   :   ;
   .   \\_,!,_/   ,
    `.,'     `.,'
     /         \\
~ -- :         : -- ~
     \\         /
    ,'`._   _.'`.
   '   / `!` \\   '
      ;   :   ;"""

CLOUDY = """\
     .--.
  .-(    ).
 (___.__)__)"""

RAINY = """\
     .--.
  .-(    ).
 (___.__)__)
  |  |  |  |
  |  |  |  |"""

PARTLY = """\
   .--.
 .-(    ).
(___.__)_)"""

WINDY = """\
      _  _
    ( `   )_
   (    )    `)
    \\_  (___  )"""


class MQTTTile(Static):
    status = reactive("connecting")

    def __init__(self, topic: str, emoji: str, **kwargs):
        super().__init__(**kwargs)
        self.topic = topic
        self.emoji = emoji
        self._queue: queue.Queue = queue.Queue(maxsize=200)
        self._client = mqtt.Client()
        self._client.on_connect = self._mqtt_on_connect
        self._client.on_disconnect = self._mqtt_on_disconnect
        self._client.on_message = self._mqtt_on_message

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
            f"[bold]MQTT[/] [dim]— {self.topic}[/]  [{color[status]}]{dot[status]}[/]"
        )

    def _mqtt_on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            client.subscribe(self.topic)
            self.status = "connected"
        else:
            self.status = "disconnected"

    def _mqtt_on_disconnect(self, client, userdata, rc):
        self.status = "disconnected"

    def _mqtt_on_message(self, client, userdata, msg):
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


class WeatherTile(Static):
    status = reactive("connecting")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._data: dict[str, str] = {}
        self._queue: queue.Queue = queue.Queue(maxsize=200)
        self._client = mqtt.Client()
        self._client.on_connect = self._mqtt_on_connect
        self._client.on_disconnect = self._mqtt_on_disconnect
        self._client.on_message = self._mqtt_on_message

    def compose(self):
        yield Static(classes="tile-header")
        yield Static(id="weather-content")

    def on_mount(self):
        self._content = self.query_one("#weather-content", Static)
        self._content.update("[dim]Waiting for weather data...[/]")
        try:
            self._client.connect_async(HOST, PORT, 60)
            self._client.loop_start()
        except Exception as e:
            self._content.update(f"[red]Connection error: {e}[/]")
        self.set_interval(0.1, self._poll)

    def watch_status(self, status: str):
        dot = {"connected": "●", "disconnected": "○", "connecting": "◐"}
        color = {"connected": "green", "disconnected": "red", "connecting": "yellow"}
        self.query_one(".tile-header", Static).update(
            f"[bold]MQTT[/] [dim]— emf/weather[/]  [{color[status]}]{dot[status]}[/]"
        )

    def _mqtt_on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            client.subscribe("emf/weather/#")
            self.status = "connected"
        else:
            self.status = "disconnected"

    def _mqtt_on_disconnect(self, client, userdata, rc):
        self.status = "disconnected"

    def _mqtt_on_message(self, client, userdata, msg):
        key = msg.topic.split("/")[-1]
        try:
            payload = msg.payload.decode("utf-8")
        except UnicodeDecodeError:
            payload = str(msg.payload)
        try:
            self._queue.put_nowait((key, payload))
        except queue.Full:
            pass

    def _poll(self):
        updated = False
        try:
            while True:
                key, value = self._queue.get_nowait()
                self._data[key] = value
                updated = True
        except queue.Empty:
            pass
        if updated:
            self._redraw()

    def _wind_arrow(self, degrees: str) -> str:
        try:
            d = float(degrees) % 360
        except (ValueError, TypeError):
            return "?"
        dirs = ["↑", "↗", "→", "↘", "↓", "↙", "←", "↖"]
        return dirs[round(d / 45) % 8]

    def _get_weather_art(self) -> str:
        try:
            rain = float(self._data.get("rainrate", "0"))
        except ValueError:
            rain = 0
        try:
            solar = float(self._data.get("solarradiation", "0"))
        except ValueError:
            solar = 0
        try:
            wind = float(self._data.get("windspeed", "0"))
        except ValueError:
            wind = 0

        if rain > 0:
            return RAINY
        if solar > 50000:
            return SUNNY
        if solar > 10000:
            return PARTLY
        if wind > 20:
            return WINDY
        return CLOUDY

    def _redraw(self):
        art = self._get_weather_art()

        temp = self._data.get("temp", "?")
        feelslike = self._data.get("feelslike", "?")
        humidity = self._data.get("humidity", "?")
        wind_speed = self._data.get("windspeed", "?")
        wind_dir = self._data.get("winddir", "?")
        daily_rain = self._data.get("dailyrain", "?")
        pressure = self._data.get("baromabs", "?")

        display = (
            f"[bold cyan]{art}[/]\n"
            f"\n"
            f"  [bold]{temp}°C[/]    Feels [bold]{feelslike}°C[/]\n"
            f"  Hum [bold]{humidity}%[/]  Wind [bold]{wind_speed}[/] {self._wind_arrow(wind_dir)}\n"
            f"  Rain [bold]{daily_rain} mm[/]  [bold]{pressure} mbar[/]\n"
        )
        self._content.update(display)


class EmfDashApp(App):
    CSS = """
    Screen {
        background: #1a1b26;
    }

    Horizontal {
        height: 1fr;
    }

    Vertical {
        width: 1fr;
        height: 100%;
    }

    #astley {
        width: 1fr;
        height: 100%;
        border: round #7dcfff;
        margin: 0 1;
    }

    #weather {
        height: 1fr;
        border: round #e0af68;
        margin: 0 1 0 1;
    }

    #ducks {
        height: 1fr;
        border: round #9ece6a;
        margin: 0 1 1 1;
    }

    .tile-header {
        padding: 0 1;
        background: $panel;
        color: $text;
    }

    .tile-log {
        height: 1fr;
    }

    #weather-content {
        height: 1fr;
        padding: 1 2;
    }
    """

    def compose(self):
        yield Header(show_clock=True)
        with Horizontal():
            yield MQTTTile("open/astley", RICK, id="astley")
            with Vertical():
                yield WeatherTile(id="weather")
                yield MQTTTile("open/the-ducks", DUCK, id="ducks")

    def on_mount(self):
        self.title = "EMFDash"


if __name__ == "__main__":
    app = EmfDashApp()
    app.run()
