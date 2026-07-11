from textual.app import App, Content
from textual.containers import Horizontal, Vertical
from textual.widgets import Header

from constants import DUCK, RICK
from mqtt import MqttManager
from tiles import MQTTTile, ScheduleTile, TalksTile, WeatherTile


class EmfDashApp(App):
    CSS = """
    Screen {
        background: #1a1b26;
    }

    Horizontal {
        height: 1fr;
        width: 1fr;
    }

    Vertical {
        width: 1fr;
        height: 100%;
    }

    #astley {
        height: 1fr;
        border: round #7dcfff;
        margin: 0 1 0 1;
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
        padding: 1 2;
        overflow-y: auto;
        overflow-x: hidden;
    }

    #talks {
        height: 1fr;
        border: round #7aa2f7;
        margin: 0 1 1 1;
    }

    #weather-content, #schedule-content, #talks-content {
        height: 1fr;
        padding: 1 2;
    }

    #schedule {
        height: 1fr;
        border: round #bb9af7;
        margin: 0 1 1 1;
    }
    """

    def __init__(self):
        super().__init__()
        self._mqtt = MqttManager()
        self._mqtt.on_status_change(self._on_mqtt_status)

    def compose(self):
        yield Header(show_clock=True)
        with Horizontal():
            with Vertical():
                yield MQTTTile("open/astley", RICK, self._mqtt, id="astley")
                yield MQTTTile("open/the-ducks", DUCK, self._mqtt, id="ducks")
            with Vertical():
                yield WeatherTile(self._mqtt, id="weather")
                yield TalksTile(id="talks")
                yield ScheduleTile(id="schedule")

    def on_mount(self):
        self.title = "EMFDash"
        self._mqtt.start()
        self.set_interval(15, self._check_mqtt)

    def format_title(self, title: str, sub_title: str) -> Content:
        title_content = Content(title)
        sub_title_content = Content.from_markup(sub_title)
        if sub_title_content:
            return Content.assemble(
                title_content,
                (" — ", "dim"),
                sub_title_content.stylize("dim"),
            )
        return title_content

    def _check_mqtt(self):
        self._mqtt.check_health()

    def _on_mqtt_status(self, status: str):
        color = {"connected": "green", "disconnected": "red", "connecting": "yellow"}
        self.sub_title = f"MQTT Status: [{color[status]}]{status}[/]"
