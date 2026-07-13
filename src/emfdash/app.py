from textual.app import App, Content
from textual.containers import Horizontal, Vertical
from textual.widgets import Header

from .config import Config, TileDef
from .mqtt import MqttManager
from .tiles import FilmTile, MQTTTile, PhoneTile, ScheduleTile, WeatherTile


class EmfDashApp(App):
    CSS = """
    Screen {
        background: #1a1b26;
    }

    Vertical {
        height: 100%;
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

    #weather-content, #schedule-content, #phone-content {
        height: 1fr;
        padding: 1 2;
        overflow-y: auto;
    }

    #talks-content {
        height: 1fr;
        padding: 0 2;
        overflow-y: auto;
        overflow-x: hidden;
    }

    #talks-content > ListItem {
        padding: 0 1;
    }

    #talks-content > ListItem:focus {
        background: $accent 30%;
    }

    #talks-content > ListItem.venue-header {
        padding: 1 1 0 0;
    }

    #talks-content > ListItem.venue-header:focus {
        background: $boost;
    }

    .tile-schedule {
        border: round #7aa2f7;
        margin: 0 1 1 1;
    }

    .tile-schedule:focus {
        border: round $accent;
    }

    .tile-weather {
        border: round #e0af68;
    }

    .tile-weather:focus {
        border: round $accent;
    }

    .tile-phones {
        border: round #f7768e;
    }

    .tile-phones:focus {
        border: round $accent;
    }

    .tile-feed {
        border: round #7dcfff;
        margin: 0 1 1 1;
    }

    .tile-feed:focus {
        border: round $accent;
    }

    .tile-films {
        border: round #bb9af7;
        margin: 0 1 1 1;
    }

    .tile-films:focus {
        border: round $accent;
    }

    .hsplit {
        margin: 0 1 1 1;
    }
    """

    def __init__(self, config: Config | None = None):
        super().__init__()
        self._config = config or Config.load()
        self._mqtt = MqttManager()
        self._mqtt.on_status_change(self._on_mqtt_status)

    def compose(self):
        yield Header(show_clock=True)
        with Horizontal(id="main-layout"):
            for col in self._config.layout.columns:
                with Vertical() as cv:
                    cv.styles.width = f"{col.weight}fr"
                    for row in col.rows:
                        if len(row.tiles) > 1:
                            with Horizontal(classes="hsplit") as h:
                                h.styles.height = f"{row.weight}fr"
                                for tile in row.tiles:
                                    w = self._make_tile(tile)
                                    w.styles.width = f"{tile.weight}fr"
                                    yield w
                        else:
                            w = self._make_tile(row.tiles[0])
                            w.styles.height = f"{row.weight}fr"
                            yield w

    def _make_tile(self, tile: TileDef):
        classes = f"tile-{tile.type}"
        if tile.type == "schedule":
            return ScheduleTile(tile.mode or "nowandnext", tile.url, classes=classes)
        if tile.type == "weather":
            return WeatherTile(self._mqtt, classes=classes)
        if tile.type == "phones":
            return PhoneTile(self._mqtt, classes=classes)
        if tile.type == "feed":
            return MQTTTile(tile.topic, tile.emoji, self._mqtt, classes=classes)
        if tile.type == "films":
            return FilmTile(classes=classes)
        raise ValueError(f"Unknown tile type: {tile.type}")

    def on_mount(self):
        self.title = "EMFDash"
        self._mqtt.start()

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

    def _on_mqtt_status(self, status: str):
        color = {"connected": "green", "disconnected": "red", "connecting": "yellow"}
        self.sub_title = f"MQTT Status: [{color[status]}]{status}[/]"
