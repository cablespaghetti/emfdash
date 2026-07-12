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
```

If `favourites.url` is set, the schedule tile switches from the default
now & next view to your personal favourites schedule, filtered to the
current day.

## Data sources

| Tile | Source | Description |
|------|--------|-------------|
| Schedule | HTTP API | Talks schedule — now & next (default) or personal favourites |
| Weather | `weather/hq` | Live weather station data (temp, humidity, wind, rain, UV, pressure) |
| Phones | `phones/#` | Phone system stats (calls, answer rate, talk time, voicemail) |
| Astley | `open/astley` | Rick Astley themed MQTT nonsense |
| Ducks | `open/the-ducks` | Duck-themed MQTT nonsense |
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
