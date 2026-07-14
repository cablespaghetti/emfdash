# EMF Dash

![Screenshot](screenshot.png)

An ncurses-style TUI dashboard for EMF Camp. Currently supporting schedule, personal favourites, films, weather, phones and arbitrary MQTT feed data.

## Usage

[You'll need mise installed](https://mise.jdx.dev/installing-mise.html), which will then setup python with all the dependencies for you.

Just run:
```
mise run start
```

## Configuration

There is a `config.yaml` in the project root which configures the layout of the tiles and the various data sources. Tweak it to your heart's content and let us know what fun bugs you find. For example, uncomment the favourites section with your own favourites.json URL to add a tile with your personal schedule.

## Tile types

| Type | Description | Extra fields |
|------|-------------|-------------|
| `schedule` | Talks schedule — now & next (default) or favourites | `mode`, `url` |
| `weather` | Live weather: temp, humidity, wind, rain, UV, pressure | — |
| `phones` | Phone system stats: calls, answer rate, talk time | — |
| `feed` | Live MQTT topic feed with emoji | `topic`, `emoji` |
| `films` | Film schedule via HTTP API | — |
| `fediverse` | RSS feed from GoToSocial accounts on social.emfcamp.org | `accounts` list |

Weights control proportional sizing (`fr` units) — a tile with `weight: 2`
takes twice the space of one with `weight: 1`.

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
