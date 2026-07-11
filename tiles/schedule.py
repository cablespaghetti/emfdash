import httpx
from datetime import datetime

from rich.table import Table
from textual.events import Resize
from textual.widgets import ListItem, ListView, Static

from tiles.common import format_day

NOW_AND_NEXT_URL = "https://www.emfcamp.org/schedule/now-and-next.json"

STAGE_PREFIX = "Stage "
WORKSHOP_PREFIX = "Workshop "


def _venue_sort_key(venue: str) -> tuple:
    if venue.startswith(STAGE_PREFIX):
        return (0, venue)
    if venue.startswith(WORKSHOP_PREFIX):
        return (1, venue)
    return (2, venue)


class ScheduleTile(Static):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.can_focus = True
        self._stages: dict[str, list[dict]] = {}
        self._label = ""
        self._day_label = ""

    def compose(self):
        yield Static(id="talks-header", classes="tile-header")
        yield ListView(id="talks-content")

    async def on_mount(self):
        self._header = self.query_one("#talks-header", Static)
        self._content = self.query_one("#talks-content", ListView)
        self._header.update("[bold]Schedule[/] [dim]— Loading\u2026[/]")
        self.set_interval(120, self._fetch_schedule)
        await self._fetch_schedule()

    def on_resize(self, event: Resize) -> None:
        if self._stages:
            self._redraw()

    async def _fetch_schedule(self):
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
                r = await client.get(NOW_AND_NEXT_URL)
                r.raise_for_status()
                data = r.json()
        except Exception:
            self._header.update("[bold]Schedule[/] [dim]— Error[/]")
            return

        self._process_now_next(data)

    def _process_now_next(self, data: dict) -> None:
        today = datetime.now().strftime("%Y-%m-%d")

        raw: dict[str, list[dict]] = {}
        for slug, talks in data.items():
            if not talks:
                continue
            venue = talks[0].get("occurrences", [{}])[0].get("venue", slug)
            seen = set()
            unique = []
            for t in talks:
                if t["id"] not in seen:
                    seen.add(t["id"])
                    unique.append(t)
            if unique:
                raw[venue] = unique

        if not raw:
            return

        target_date = self._find_target_date(raw, today)
        if not target_date:
            return

        self._stages = {}
        for venue, talks in raw.items():
            filtered = []
            seen = set()
            for t in talks:
                if t["id"] in seen:
                    continue
                for occ in t.get("occurrences", []):
                    if occ.get("start_date", "").startswith(target_date):
                        seen.add(t["id"])
                        filtered.append(t)
                        break
            if filtered:
                self._stages[venue] = filtered

        if not self._stages:
            return

        self._stages = dict(
            sorted(self._stages.items(), key=lambda kv: _venue_sort_key(kv[0]))
        )
        self._label = "Now & Next"
        if target_date == today:
            self._day_label = "Today"
        else:
            self._day_label = format_day(datetime.strptime(target_date, "%Y-%m-%d"))
        self._redraw()

    @staticmethod
    def _find_target_date(raw: dict[str, list[dict]], today: str) -> str | None:
        earliest: str | None = None
        for talks in raw.values():
            for t in talks:
                for occ in t.get("occurrences", []):
                    sd = occ.get("start_date", "")
                    if not sd:
                        continue
                    d = sd[:10]
                    if d == today:
                        return today
                    if earliest is None or d < earliest:
                        earliest = d
        return earliest

    def _redraw(self):
        day_part = f" — {self._day_label}" if self._day_label else ""
        self._header.update(f"[bold]Schedule[/] [dim]— {self._label}{day_part}[/]")
        self._content.clear()

        for venue, talks in self._stages.items():
            header = ListItem(Static(f"[bold]{venue}[/]"), classes="venue-header")
            self._content.append(header)

            for talk in talks:
                occ = talk.get("occurrences", [{}])[0]
                st = occ.get("start_time", "")
                et = occ.get("end_time", "")
                time_str = f"{st}\u2013{et}" if et else st
                title = talk.get("title", "?")
                speaker = talk.get("names", "")

                table = Table.grid(padding=0, expand=True)
                table.add_column(ratio=1)
                table.add_column(width=12, justify="right")
                table.add_column(width=3)

                left = title
                if speaker:
                    left += f"  [dim]{speaker}[/]"
                table.add_row(f"  {left}", time_str, "")

                item = ListItem(Static(table, expand=True))
                item.talk_data = talk
                item.venue = venue
                self._content.append(item)

        if self._content.children:
            try:
                for i, child in enumerate(self._content.children):
                    if hasattr(child, "talk_data"):
                        self._content.index = i
                        break
            except TypeError:
                pass

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item = event.item
        talk = getattr(item, "talk_data", None)
        venue = getattr(item, "venue", None)
        if talk is not None:
            from tiles.talk_detail import TalkDetailScreen

            self.app.push_screen(TalkDetailScreen(talk, venue))
