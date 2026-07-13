from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static


class TalkDetailScreen(Screen):
    DEFAULT_CSS = """
    TalkDetailScreen {
        background: $surface;
        align: center middle;
    }

    #detail-box {
        width: 80%;
        height: auto;
        border: round $accent;
        padding: 2 3;
    }

    #detail-title {
        text-style: bold;
        padding-bottom: 1;
    }

    #detail-meta {
        padding-bottom: 1;
    }

    #detail-description {
        padding: 1 0;
    }

    #detail-hint {
        padding-top: 1;
        color: $text-disabled;
    }
    """

    def __init__(self, talk: dict, venue: str):
        super().__init__()
        self.talk = talk
        self.venue = venue

    def compose(self) -> ComposeResult:
        occ = self.talk["occurrences"][0]
        st = occ.get("start_time", "")
        et = occ.get("end_time", "")
        time_str = f"{st}\u2013{et}" if et else st
        title = self.talk.get("title", "?")
        speaker = self.talk.get("names", "")
        description = self.talk.get("description", "")

        with Static(id="detail-box"):
            yield Static(f"[bold]{title}[/]", id="detail-title")
            meta = f"{time_str}  [dim]at {self.venue}[/]"
            if speaker:
                meta = f"[dim]{speaker}[/]  {meta}"
            yield Static(meta, id="detail-meta")
            if description:
                yield Static(description, id="detail-description")
            yield Static("[dim]Press Escape or Enter to go back[/]", id="detail-hint")

    def on_key(self, event):
        if event.key in ("escape", "enter"):
            self.app.pop_screen()
