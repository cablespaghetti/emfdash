# EMF Dash

![Screenshot](screenshot.png)

A TUI dashboard for EMF Camp, displaying live MQTT feeds in a split-panel terminal interface.

## Usage

```
mise run start
```

## Layout

```
┌────────────────────────────┬──────────────────┐
│                            │  Astley           │
│  Schedule (now & next)     │                  │
│                            ├──────────────────┤
│                            │  Ducks           │
│                            │                  │
├──────────────────┬─────────┼──────────────────┤
│  Weather         │ Phones  │  Films           │
│                  │         │                  │
└──────────────────┴─────────┴──────────────────┘
```

- **Left column (2/3)**: Schedule (top 2/3), Weather + Phones (bottom 1/3, side by side)
- **Right column (1/3)**: Astley, Ducks, Films stacked equally

## Data sources

| Tile | MQTT topic | Description |
|------|------------|-------------|
| Schedule | — | Talks schedule via HTTP API (now & next) |
| Weather | `emf/weather/#` + `weather/hq` | Live weather station data (temp, humidity, wind, rain, UV, pressure) |
| Phones | `phones/#` | Phone system stats (calls, answer rate, talk time, voicemail) |
| Astley | `open/astley` | Rick-roll themed MQTT live feed |
| Ducks | `open/the-ducks` | Duck-themed MQTT live feed |
| Films | — | Film schedule via HTTP API |

## Weather tile

Shows ASCII art (sun, clouds, rain, wind) next to live readings from two
sources: per-key messages on `emf/weather/#` or a single JSON blob on `weather/hq`.
Fields default to `---` until data arrives.

### Readings

- Outdoor temperature, feels-like, humidity
- Wind speed (mph) with direction arrow and gust
- UV index
- Rain rate (mm/hr), last hour, last 24h, event total
- Barometric pressure (mbar)

## Phones tile

Shows live phone system stats from the camp PBX:

- Phones online vs numbers assigned
- Calls in last 24h with answer rate
- Total calls answered
- Average and longest call duration
- Total talk time
- Voicemail messages

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

CSV fixture files in `tests/data/` contain sample MQTT messages per tile.
Each row represents a single MQTT message with columns: `Timestamp;Date;Value;Properties`.

Weather art sourced from [weathr](https://github.com/Veirt/weathr) by Veirt.
Additional ASCII art from [asciiart.eu](https://asciiart.eu).
