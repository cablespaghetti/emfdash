import queue
from datetime import datetime

from textual.widgets import Static

from mqtt import MqttManager


def _format_duration(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins:02d}m"


def _fmt(n: str | None) -> tuple[str, bool]:
    """Format a phone stat value, returning (display, has_data)."""
    if n is None:
        return "[dim]---[/]", False
    try:
        v = int(float(n))
        return f"[bold]{v:,}[/]", True
    except (ValueError, TypeError):
        return f"[bold]{n}[/]", True


class PhoneTile(Static):
    def __init__(self, mqtt: MqttManager, **kwargs):
        super().__init__(**kwargs)
        self.can_focus = True
        self._mqtt = mqtt
        self._data: dict[str, str] = {}
        self._last_update: datetime | None = None
        self._queue: queue.Queue = queue.Queue(maxsize=200)

    def compose(self):
        yield Static("[bold]Phones[/] [dim]— from MQTT[/]", classes="tile-header")
        yield Static(id="phone-content")

    def on_mount(self):
        self._header = self.query_one(".tile-header", Static)
        self._content = self.query_one("#phone-content", Static)
        self._redraw()
        self._mqtt.subscribe("phones/#", self._mqtt_on_message)
        self.set_interval(0.1, self._poll)

    def _mqtt_on_message(self, msg):
        key = msg.topic.split("/")[-1]
        try:
            payload = msg.payload.decode("utf-8")
        except UnicodeDecodeError:
            payload = str(msg.payload)
        try:
            self._queue.put_nowait((key, payload))
        except queue.Full:
            pass

    def _poll(self):
        updated = False
        try:
            while True:
                key, value = self._queue.get_nowait()
                self._data[key] = value
                updated = True
        except queue.Empty:
            pass
        if updated:
            self._last_update = datetime.now()
            self._redraw()

    def _redraw(self):
        online_val, _ = _fmt(self._data.get("phones-online"))
        assigned_val, _ = _fmt(self._data.get("numbers-assigned"))
        calls_val, _ = _fmt(self._data.get("calls-24h"))
        answer_rate = self._data.get("answer-rate")
        if answer_rate is not None:
            try:
                pct = float(answer_rate) * 100
                answer_val = f"[bold]{pct:.0f}%[/]"
            except (ValueError, TypeError):
                answer_val = "[dim]---[/]"
        else:
            answer_val = "[dim]---[/]"
        answered_val, has_answered = _fmt(self._data.get("calls-answered"))

        avg_raw = self._data.get("avg-call-seconds")
        avg_val = _format_duration(int(float(avg_raw))) if avg_raw else "[dim]---[/]"
        longest_raw = self._data.get("longest-call-seconds")
        longest_val = (
            _format_duration(int(float(longest_raw))) if longest_raw else "[dim]---[/]"
        )
        talk_raw = self._data.get("talk-seconds")
        talk_val = _format_duration(int(float(talk_raw))) if talk_raw else "[dim]---[/]"
        voicemail_val, _ = _fmt(self._data.get("voicemail-messages"))

        last = (
            self._last_update.strftime("%H:%M:%S")
            if self._last_update
            else "[dim]never[/]"
        )

        lines = [
            f"Online      {online_val}  [dim]of[/] {assigned_val}",
            f"Calls 24h   {calls_val}",
            f"Answer rate {answer_val}",
            f"Answered    {answered_val}",
            f"Avg call    {avg_val}",
            f"Longest     {longest_val}",
            f"Total talk  {talk_val}",
            f"Voicemail   {voicemail_val}",
        ]

        self._content.update("\n".join(lines))
        self._header.update(f"[bold]Phones[/] [dim]— updated {last}[/]")
