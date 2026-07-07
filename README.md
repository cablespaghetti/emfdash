# EMF Dash

A TUI dashboard for EMF Camp, displaying live MQTT feeds in a split-panel ncurses-style interface.

## Usage

```
mise run start
```

## Data sources

| Tile | MQTT topic | Description |
|------|-----------|-------------|
| Astley | `open/astley` | Messages with dancer emoji |
| Weather | `emf/weather/#` | Live weather station data (temp, humidity, wind, rain, pressure, solar) |
| Ducks | `open/the-ducks` | Messages with duck emoji |

## Tasks

| Command | Description |
|---------|-------------|
| `mise run start` | Run the dashboard |
| `mise run lint` | Lint with ruff |
| `mise run fix` | Auto-fix lint issues |
| `mise run fmt` | Format with ruff |
| `mise run test` | Run tests |
| `mise run ci` | Lint + test |

## Test fixtures

CSV fixture files in `tests/data/` contain sample MQTT messages. Each row
represents a single MQTT message with columns: `Timestamp;Date;Value;Properties`.

## Weather tile

Shows ASCII art (sun, clouds, rain, wind) next to live readings. Fields default
to "Waiting..." until their value arrives over MQTT. A "Last updated" timestamp
appears once data is received.

Weather art sourced from [weathr](https://github.com/Veirt/weathr) by Veirt.
Additional ASCII art from [asciiart.eu](https://asciiart.eu).
