import json
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

    def compose(self):
        yield Static("[bold]Weather[/] [dim]— from MQTT[/]", classes="tile-header")
        yield Static(id="weather-content")

    def on_mount(self):
        self._header = self.query_one(".tile-header", Static)
        self._content = self.query_one("#weather-content", Static)
        self._redraw()
        self._mqtt.subscribe("weather/hq", self._mqtt_on_hq_message)

    def _mqtt_on_hq_message(self, msg):
        try:
            payload = msg.payload.decode("utf-8")
        except UnicodeDecodeError:
            return
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return
        mapping = {
            "temp": "temp",
            "feelslike": "feelslike",
            "humidity": "humidity",
            "windspeed": "windspeed",
            "winddir": "winddir",
            "windgust": "windgust",
            "baromabs": "baromabs",
            "solarradiation": "solarradiation",
            "uv": "uv",
            "rainrate": "rrain_piezo",
            "hourlyrain": "hrain_piezo",
            "dailyrain": "drain_piezo",
            "weeklyrain": "wrain_piezo",
            "eventrain": "erain_piezo",
        }
        for target, source in mapping.items():
            val = data.get(source)
            if val is not None:
                self._data[target] = str(val)
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
        wind_gust = self._data.get("windgust")
        uv = self._data.get("uv")
        rain_rate = self._data.get("rainrate")
        hourly_rain = self._data.get("hourlyrain")
        daily_rain = self._data.get("dailyrain")
        event_rain = self._data.get("eventrain")
        pressure = self._data.get("baromabs")

        w = "[dim]Waiting...[/]"
        t = f"[bold]{temp}°C[/]" if temp is not None else w
        f = f"[bold]{feelslike}°C[/]" if feelslike is not None else w
        h = f"[bold]{humidity}%[/]" if humidity is not None else w
        u = f"[bold]{uv}[/]" if uv is not None else "[dim]---[/]"
        rr = f"[bold]{rain_rate} mm/hr[/]" if rain_rate is not None else "[dim]---[/]"
        hr = f"[bold]{hourly_rain} mm[/]" if hourly_rain is not None else "[dim]---[/]"
        dr = f"[bold]{daily_rain} mm[/]" if daily_rain is not None else "[dim]---[/]"
        er = f"[bold]{event_rain} mm[/]" if event_rain is not None else "[dim]---[/]"
        p = f"[bold]{pressure} mbar[/]" if pressure is not None else w

        if wind_speed is not None:
            gust = f" gust {wind_gust}" if wind_gust is not None else ""
            ws = f"[bold]{wind_speed} mph[/] {self._wind_arrow(wind_dir)}{gust}"
        else:
            ws = w

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
                f"  UV {u}",
                f"  Wind {ws}",
                f"  Rain {rr} | 1h {hr} | 24h {dr} | ev {er}",
                f"  Pressure {p}",
            ]
        )

        table = Table.grid(padding=(0, 1))
        table.add_column(width=15)
        table.add_column(ratio=1)
        table.add_row(f"[bold cyan]{art}[/]", data)
        self._content.update(table)
        self._header.update(f"[bold]Weather[/] [dim]— updated {last}[/]")
