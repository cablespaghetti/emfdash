import httpx
from datetime import datetime

from rich.table import Table
from textual.widgets import Static

NOW_AND_NEXT_URL = "https://www.emfcamp.org/schedule/now-and-next.json"
FULL_SCHEDULE_URL = "https://www.emfcamp.org/schedule/2026.json"

STAGE_SLUGS = {
    "stage-a": "Stage A",
    "stage-b": "Stage B",
    "stage-c": "Stage C",
    "stage-d": "Stage D",
}


class TalksTile(Static):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._stages: dict[str, list[dict]] = {}
        self._label = ""

    def compose(self):
        yield Static(id="talks-header", classes="tile-header")
        yield Static(id="talks-content")

    async def on_mount(self):
        self._header = self.query_one("#talks-header", Static)
        self._content = self.query_one("#talks-content", Static)
        self._header.update("[bold]Schedule[/] [dim]— Loading\u2026[/]")
        self.set_interval(120, self._fetch_schedule)
        await self._fetch_schedule()

    async def _fetch_schedule(self):
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
                r = await client.get(NOW_AND_NEXT_URL)
                r.raise_for_status()
                data = r.json()
        except Exception:
            await self._fallback()
            return

        self._process_now_next(data)
        if not self._stages:
            await self._fallback()

    def _process_now_next(self, data: dict) -> None:
        self._stages = {}
        for slug, talks in data.items():
            display = STAGE_SLUGS.get(slug)
            if display is None or not talks:
                continue
            seen = set()
            unique = []
            for t in talks:
                if t["id"] not in seen:
                    seen.add(t["id"])
                    unique.append(t)
            self._stages[display] = unique

        if self._stages:
            self._label = "Now & Next"
            self._redraw()

    async def _fallback(self):
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
                r = await client.get(FULL_SCHEDULE_URL)
                r.raise_for_status()
                items = r.json()
        except Exception:
            self._header.update("[bold]Schedule[/] [dim]— Error[/]")
            self._content.update("[dim]Unable to load schedule[/]")
            return

        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        self._process_full_schedule(items, today)

    def _process_full_schedule(self, items: list, today: str) -> None:
        by_venue: dict[str, list[tuple[str, dict]]] = {}
        seen_ids: dict[str, set[int]] = {}

        for item in items:
            for occ in item.get("occurrences", []):
                venue = occ.get("venue", "")
                slug = venue.lower().replace(" ", "-")
                display = STAGE_SLUGS.get(slug)
                if display is None:
                    continue
                start_date = occ.get("start_date", "")
                if start_date[:10] != today:
                    continue
                if display not in by_venue:
                    by_venue[display] = []
                    seen_ids[display] = set()
                if item["id"] not in seen_ids[display]:
                    seen_ids[display].add(item["id"])
                    by_venue[display].append((occ.get("start_time", ""), item))

        if not by_venue:
            candidates = []
            for item in items:
                for occ in item.get("occurrences", []):
                    venue = occ.get("venue", "")
                    slug = venue.lower().replace(" ", "-")
                    if slug not in STAGE_SLUGS:
                        continue
                    start_date = occ.get("start_date", "")
                    if start_date[:10] > today:
                        candidates.append((start_date[:10], item))

            if candidates:
                next_day = min(c[0] for c in candidates)
                by_venue = {}
                seen_ids = {}
                for sd, item in candidates:
                    if sd == next_day:
                        for occ in item.get("occurrences", []):
                            od = occ.get("start_date", "")
                            if od[:10] != next_day:
                                continue
                            venue = occ.get("venue", "")
                            slug = venue.lower().replace(" ", "-")
                            display = STAGE_SLUGS.get(slug)
                            if display is None:
                                continue
                            if display not in by_venue:
                                by_venue[display] = []
                                seen_ids[display] = set()
                            if item["id"] not in seen_ids[display]:
                                seen_ids[display].add(item["id"])
                                by_venue[display].append(
                                    (occ.get("start_time", ""), item)
                                )
                self._label = "Next day"
            else:
                self._header.update("[bold]Schedule[/] [dim]— No talks[/]")
                self._content.update("[dim]No talks scheduled[/]")
                self._stages = {}
                return
        else:
            self._label = "Today"

        self._stages = {}
        for display in sorted(
            by_venue, key=lambda d: list(STAGE_SLUGS.values()).index(d)
        ):
            by_venue[display].sort(key=lambda x: x[0])
            self._stages[display] = [item for _, item in by_venue[display]]

        self._redraw()

    def _redraw(self):
        self._header.update(f"[bold]Schedule[/] [dim]— {self._label}[/]")
        table = Table.grid(padding=(0, 2))
        table.add_column(ratio=1)

        for venue in STAGE_SLUGS.values():
            if venue not in self._stages:
                continue
            talks = self._stages[venue]
            lines = [f"[bold]{venue}[/]"]
            for talk in talks:
                occ = talk.get("occurrences", [{}])[0]
                st = occ.get("start_time", "")
                et = occ.get("end_time", "")
                time_str = f"{st}\u2013{et}" if et else st
                title = talk.get("title", "?")
                speaker = talk.get("names", "")
                row = f"  {time_str}  {title}"
                if speaker:
                    row += f"  [dim]{speaker}[/]"
                lines.append(row)
            table.add_row("\n".join(lines))

        self._content.update(table)
