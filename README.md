# EMF Dash

A TUI dashboard for EMF Camp, displaying live MQTT feeds in a split-panel ncurses-style interface.

## Usage

```
uv run python3 main.py
```

## Data sources

| Tile | MQTT topic | Description |
|------|-----------|-------------|
| Astley | `open/astley` | Messages with dancer emoji |
| Weather | `emf/weather/#` | Live weather station data |
| Ducks | `open/the-ducks` | Messages with duck emoji |

## Credits

Weather ASCII art sourced from [weathr](https://github.com/Veirt/weathr) by Veirt.
Additional ASCII art from [asciiart.eu](https://asciiart.eu).
