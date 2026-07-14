from datetime import datetime, timezone
from html import unescape
import re

import feedparser
import httpx

from rich.box import SQUARE
from rich.panel import Panel
from rich.text import Text
from textual.widgets import ListItem, ListView, Static


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    return text.strip()


class FediverseTile(Static):
    def __init__(self, accounts: list[str], **kwargs):
        super().__init__(**kwargs)
        self.can_focus = True
        self._accounts = accounts
        self._entries: list[dict] = []
        self._error: str | None = None

    def compose(self):
        yield Static(id="fediverse-header", classes="tile-header")
        yield ListView(id="fediverse-content")

    async def on_mount(self):
        self._header = self.query_one("#fediverse-header", Static)
        self._content = self.query_one("#fediverse-content", ListView)
        self._header.update("[bold]EMFCamp Fediverse[/] [dim]— Loading\u2026[/]")
        self.set_interval(300, self._fetch)
        await self._fetch()

    async def _fetch(self):
        all_entries: list[dict] = []
        for account in self._accounts:
            try:
                url = f"https://social.emfcamp.org/@{account}/feed.rss"
                async with httpx.AsyncClient(
                    follow_redirects=True, timeout=10
                ) as client:
                    r = await client.get(url)
                    r.raise_for_status()
                    feed = feedparser.parse(r.text)
                for entry in feed.entries:
                    content = ""
                    if hasattr(entry, "content") and entry.content:
                        content = entry.content[0].get("value", "")
                    if not content:
                        content = entry.get("summary", "")
                    all_entries.append(
                        {
                            "published": entry.get("published", ""),
                            "published_parsed": entry.get("published_parsed"),
                            "title": entry.get("title", ""),
                            "content": content,
                            "account": account,
                        }
                    )
            except Exception:
                pass

        all_entries.sort(
            key=lambda e: (
                datetime(*e["published_parsed"][:6], tzinfo=timezone.utc)
                if e["published_parsed"]
                else datetime.min.replace(tzinfo=timezone.utc)
            ),
            reverse=True,
        )
        self._entries = all_entries[:50]
        self._redraw()

    def _fmt_ts(self, e: dict) -> str:
        parsed = e.get("published_parsed")
        if parsed:
            dt = datetime(*parsed[:6], tzinfo=timezone.utc).astimezone()
            return dt.isoformat()
        raw = e.get("published", "")
        if raw:
            try:
                dt = datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone()
                return dt.isoformat()
            except (ValueError, TypeError):
                pass
        return ""

    def _redraw(self):
        if not self._entries:
            self._header.update("[bold]EMFCamp Fediverse[/] [dim]— No posts[/]")
            self._content.clear()
            return

        self._header.update("[bold]EMFCamp Fediverse[/]")
        self._content.clear()
        for e in self._entries:
            ts = self._fmt_ts(e)
            header_text = f"@{e['account']}" + (f" — {ts}" if ts else "")
            body = _strip_html(e.get("content", ""))

            t = Text()
            t.append(header_text, style="bold")
            if body:
                t.append("\n")
                t.append(body)
            panel = Panel(t, box=SQUARE, border_style="white")
            self._content.append(ListItem(Static(panel, expand=True)))
