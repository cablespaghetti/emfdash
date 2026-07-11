import queue
from datetime import datetime

from rich.table import Table
from textual.widgets import Static

from constants import CLOUDY, PARTLY, RAINY, SUNNY, WINDY
from mqtt import MqttManager


class WeatherTile(Static):
    def __init__(self, mqtt: MqttManager, **kwargs):
        super().__init__(**kwargs)
        self.can_focus = True
        self._mqtt = mqtt
        self._data: dict[str, str] = {}
        self._last_update: datetime | None = None
        self._queue: queue.Queue = queue.Queue(maxsize=200)

    def compose(self):
        yield Static("[bold]Weather[/] [dim]— from MQTT[/]", classes="tile-header")
        yield Static(id="weather-content")

    def on_mount(self):
        self._header = self.query_one(".tile-header", Static)
        self._content = self.query_one("#weather-content", Static)
        self._redraw()
        self._mqtt.subscribe("emf/weather/#", self._mqtt_on_message)
        self.set_interval(0.1, self._poll)

    def _mqtt_on_message(self, msg):
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
            self._last_update = datetime.now()
            self._redraw()

    def _wind_arrow(self, degrees) -> str:
        if degrees is None:
            return ""
        try:
            d = float(degrees) % 360
        except ValueError, TypeError:
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
        art = self._get_weather_art() if self._data else SUNNY

        temp = self._data.get("temp")
        feelslike = self._data.get("feelslike")
        humidity = self._data.get("humidity")
        wind_speed = self._data.get("windspeed")
        wind_dir = self._data.get("winddir")
        daily_rain = self._data.get("dailyrain")
        pressure = self._data.get("baromabs")

        t = f"[bold]{temp}°C[/]" if temp is not None else "[dim]Waiting...[/]"
        f = f"[bold]{feelslike}°C[/]" if feelslike is not None else "[dim]Waiting...[/]"
        h = f"[bold]{humidity}%[/]" if humidity is not None else "[dim]Waiting...[/]"
        ws = (
            f"[bold]{wind_speed}[/] {self._wind_arrow(wind_dir)}"
            if wind_speed is not None
            else "[dim]Waiting...[/]"
        )
        r = (
            f"[bold]{daily_rain} mm[/]"
            if daily_rain is not None
            else "[dim]Waiting...[/]"
        )
        p = (
            f"[bold]{pressure} mbar[/]"
            if pressure is not None
            else "[dim]Waiting...[/]"
        )
        last = (
            self._last_update.strftime("%H:%M:%S")
            if self._last_update
            else "[dim]never[/]"
        )

        data = "\n".join(
            [
                f"  Temp {t}",
                f"  Feels like {f}",
                f"  Humidity {h}",
                f"  Wind {ws}",
                f"  Rain {r}",
                f"  Pressure {p}",
            ]
        )

        table = Table.grid(padding=(2, 2))
        table.add_column(width=22)
        table.add_column(ratio=1)
        table.add_row(f"[bold cyan]{art}[/]", data)
        self._content.update(table)
        self._header.update(f"[bold]Weather[/] [dim]— updated {last}[/]")
