# EMF Dash

![Screenshot](screenshot.png)

A TUI dashboard for EMF Camp, displaying live MQTT feeds in a split-panel terminal interface.

## Usage

```
mise run start
```

## Configuration

Create `config.toml` in the project root:

```toml
[favourites]
url = "https://www.emfcamp.org/favourites.json?token=your-token"

[[feeds]]
topic = "open/astley"
emoji = "🕺"

[[feeds]]
topic = "open/the-ducks"
emoji = "🦆"
```

If `favourites.url` is set, the schedule tile switches from the default
now & next view to your personal favourites schedule, filtered to the
current day.

MQTT feeds are configurable via `[[feeds]]` entries. Each entry specifies
a topic and emoji. Defaults match the example above.

## Data sources

| Tile | Source | Description |
|------|--------|-------------|
| Schedule | HTTP API | Talks schedule — now & next (default) or personal favourites |
| Weather | `weather/hq` | Live weather station data (temp, humidity, wind, rain, UV, pressure) |
| Phones | `phones/#` | Phone system stats (calls, answer rate, talk time, voicemail) |
| MQTT feeds | configurable | Live topic feeds with emoji (defaults: Astley, Ducks) |
| Films | HTTP API | Film schedule |

## Tasks

| Command | Description |
|---------|-------------|
| `mise run start` | Run the dashboard |
| `mise run lint` | Lint with ruff |
| `mise run fix` | Auto-fix lint issues |
| `mise run fmt` | Format with ruff |
| `mise run test` | Run tests |
| `mise run ci` | Lint + test |

## Honorable mentions

ASCII art from [asciiart.eu](https://asciiart.eu).
