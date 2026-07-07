from textual.app import App
from textual.containers import Horizontal, Vertical
from textual.widgets import Header

from constants import DUCK, RICK
from mqtt import MqttManager
from tiles import MQTTTile, WeatherTile


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

    def __init__(self):
        super().__init__()
        self._mqtt = MqttManager()
        self._mqtt.on_status_change(self._on_mqtt_status)

    def compose(self):
        yield Header(show_clock=True)
        with Horizontal():
            yield MQTTTile("open/astley", RICK, self._mqtt, id="astley")
            with Vertical():
                yield WeatherTile(self._mqtt, id="weather")
                yield MQTTTile("open/the-ducks", DUCK, self._mqtt, id="ducks")

    def on_mount(self):
        self.title = "EMFDash"
        self._mqtt.start()

    def _on_mqtt_status(self, status: str):
        dot = {"connected": "●", "disconnected": "○", "connecting": "◐"}
        color = {"connected": "green", "disconnected": "red", "connecting": "yellow"}
        self.sub_title = f"[{color[status]}]{dot[status]}[/] MQTT"
