import httpx
from datetime import datetime

from rich.table import Table
from textual.widgets import Static

SCHEDULE_URL = "https://films.emfcamp.org/schedule.json"
_ORDINALS = {1: "st", 2: "nd", 3: "rd", 21: "st", 22: "nd", 23: "rd", 31: "st"}


class ScheduleTile(Static):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._films: list[dict] = []
        self._day_label = ""
        self._error: str | None = None

    def compose(self):
        yield Static(id="schedule-header", classes="tile-header")
        yield Static(id="schedule-content")

    async def on_mount(self):
        self._header = self.query_one("#schedule-header", Static)
        self._content = self.query_one("#schedule-content", Static)
        self._header.update("[bold]Films[/] [dim]— Loading…[/]")
        self.set_interval(300, self._fetch_schedule)
        await self._fetch_schedule()

    async def _fetch_schedule(self):
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(SCHEDULE_URL)
                r.raise_for_status()
                data = r.json()
        except Exception:
            self._header.update("[bold]Films[/] [dim]— Error[/]")
            self._content.update("[dim]Unable to load schedule[/]")
            return
        self._load_data(data)

    def _load_data(self, data: dict, today: str | None = None):
        if today is None:
            today = datetime.now().date().isoformat()

        all_films = [f for f in data.get("films", []) if f.get("display", False)]
        all_films.sort(key=lambda f: f["showing"]["timestamp"])

        today_films = [f for f in all_films if f["showing"]["timestamp"][:10] == today]

        if today_films:
            self._films = today_films
            self._day_label = "Today"
        else:
            next_day = None
            for f in all_films:
                fd = f["showing"]["timestamp"][:10]
                if fd > today:
                    next_day = fd
                    break
            if next_day:
                self._films = [
                    f for f in all_films if f["showing"]["timestamp"][:10] == next_day
                ]
                self._day_label = self._format_day(
                    self._films[0]["showing"]["timestamp"]
                )
            else:
                self._films = []
                self._day_label = ""
        self._redraw()

    def _redraw(self):
        if not self._films:
            self._header.update("[bold]Films[/] [dim]— No upcoming films[/]")
            self._content.update("[dim]No upcoming films scheduled[/]")
            return

        self._header.update(f"[bold]Films[/] [dim]— {self._day_label}[/]")
        table = Table.grid(padding=(0, 2))
        table.add_column(width=4)
        table.add_column(ratio=1)
        table.add_column(width=8)
        table.add_column(width=8)

        for f in self._films:
            ts = f["showing"]["timestamp"]
            time_str = ts[11:16]
            table.add_row("🎬", f["title"], time_str, f["runTime"]["text"])

        self._content.update(table)

    @staticmethod
    def _format_day(ts: str) -> str:
        d = datetime.fromisoformat(ts)
        suffix = _ORDINALS.get(d.day, "th")
        return f"{d.strftime('%A')} {d.day}{suffix}"
