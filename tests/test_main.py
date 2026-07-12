"""Tests for EMF Camp Dashboard."""

import csv
import json
from unittest.mock import Mock

import pytest

from tiles import FilmTile, MQTTTile, PhoneTile, ScheduleTile, WeatherTile
from tiles.common import format_day
from constants import RICK, DUCK, SUNNY, RAINY, PARTLY, WINDY, CLOUDY
from tests.conftest import msg


def make_mqtt():
    return Mock()


class TestMQTTTile:
    @pytest.fixture
    def tile(self):
        t = MQTTTile("open/astley", RICK, make_mqtt())
        t._log = Mock()
        return t

    def test_init(self, tile):
        assert tile.topic == "open/astley"
        assert tile.emoji == RICK
        assert tile._queue.maxsize == 200

    def test_on_message_queues_string(self, tile):
        tile._mqtt_on_message(msg("open/astley", "hello world"))
        ts, payload = tile._queue.get_nowait()
        assert payload == "hello world"
        assert isinstance(ts, str) and len(ts) == 8

    def test_on_message_queues_bytes(self, tile):
        tile._mqtt_on_message(msg("open/astley", b"raw bytes"))
        ts, payload = tile._queue.get_nowait()
        assert payload == "raw bytes"
        assert isinstance(ts, str) and len(ts) == 8

    def test_on_message_full_queue_does_not_raise(self, tile):
        for i in range(200):
            tile._queue.put_nowait((f"{i:02}:00:00", str(i)))
        tile._mqtt_on_message(msg("open/astley", "overflow"))
        assert tile._queue.qsize() == 200

    def test_on_message_handles_bad_utf8(self, tile):
        m = msg("open/astley", b"\xff\xfe")
        tile._mqtt_on_message(m)
        ts, val = tile._queue.get_nowait()
        assert isinstance(val, str)
        assert isinstance(ts, str) and len(ts) == 8

    def test_poll_drains_to_log(self, tile):
        tile._mqtt_on_message(msg("open/astley", "one"))
        tile._mqtt_on_message(msg("open/astley", "two"))
        tile._poll()
        assert tile._queue.empty()
        assert tile._log.add_message.call_count == 2


CSV_FIXTURES = [
    ("open/astley", "tests/data/open_astley.csv", RICK),
    ("open/the-ducks", "tests/data/open_the-ducks.csv", DUCK),
]


PHONES_CSV_PATHS = [
    "tests/data/phones_answer-rate.csv",
    "tests/data/phones_avg-call-seconds.csv",
    "tests/data/phones_calls-24h.csv",
    "tests/data/phones_calls-answered.csv",
    "tests/data/phones_longest-call-seconds.csv",
    "tests/data/phones_numbers-assigned.csv",
    "tests/data/phones_numbers-by-service.csv",
    "tests/data/phones_phones-online.csv",
    "tests/data/phones_talk-seconds.csv",
    "tests/data/phones_voicemail-messages.csv",
]


class TestCsvFixtures:
    @pytest.mark.parametrize("topic,path,emoji", CSV_FIXTURES)
    def test_csv_parses(self, topic, path, emoji):
        with open(path, newline="") as f:
            reader = csv.DictReader(f, delimiter=";")
            rows = list(reader)
        assert len(rows) > 0
        for row in rows:
            assert row["Timestamp"]
            assert row["Date"]
            assert row["Value"]

    @pytest.mark.parametrize("topic,path,emoji", CSV_FIXTURES)
    def test_messages_can_be_queued(self, topic, path, emoji):
        tile = MQTTTile(topic, emoji, make_mqtt())
        tile._log = Mock()
        with open(path, newline="") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                tile._mqtt_on_message(msg(topic, row["Value"]))
        assert tile._queue.qsize() > 0
        tile._poll()
        assert tile._queue.empty()


class TestPhoneCsvFixtures:
    @pytest.mark.parametrize("path", PHONES_CSV_PATHS)
    def test_csv_parses(self, path):
        with open(path, newline="") as f:
            reader = csv.DictReader(f, delimiter=";")
            rows = list(reader)
        assert len(rows) > 0
        for row in rows:
            assert row["Timestamp"]
            assert row["Date"]
            assert row["Value"]

    @pytest.mark.parametrize("path", PHONES_CSV_PATHS)
    def test_messages_populate_data(self, path):
        key = path.removeprefix("tests/data/phones_").removesuffix(".csv")
        tile = PhoneTile(make_mqtt())
        tile._header = Mock()
        tile._content = Mock()
        with open(path, newline="") as f:
            reader = csv.DictReader(f, delimiter=";")
            rows = []
            for row in reader:
                rows.append(row)
                tile._mqtt_on_message(msg(f"phones/{key}", row["Value"]))
        assert tile._queue.qsize() > 0
        tile._poll()
        assert tile._data[key] == rows[-1]["Value"]


WEATHER_HQ_FIXTURE = "tests/data/weather_hq.csv"


class TestWeatherHqCsvFixture:
    def test_csv_parses(self):
        with open(WEATHER_HQ_FIXTURE, newline="") as f:
            reader = csv.DictReader(f, delimiter=";")
            rows = list(reader)
        assert len(rows) > 0
        for row in rows:
            assert row["Timestamp"]
            assert row["Date"]
            import json

            assert json.loads(row["Value"])

    def test_hq_message_updates_data(self):
        tile = WeatherTile(make_mqtt())
        tile._header = Mock()
        tile._content = Mock()
        with open(WEATHER_HQ_FIXTURE, newline="") as f:
            reader = csv.DictReader(f, delimiter=";")
            row = next(reader)
            tile._mqtt_on_hq_message(msg("weather/hq", row["Value"]))
        assert tile._data["temp"] == "20.6"
        assert tile._data["feelslike"] == "20.6"
        assert tile._data["humidity"] == "66.0"
        assert tile._data["windspeed"] == "3.96"
        assert tile._data["winddir"] == "96.0"
        assert tile._data["baromabs"] == "1010.5"
        assert tile._data["solarradiation"] == "0.0"
        assert tile._data["dailyrain"] == "0.0"
        assert tile._data["rainrate"] == "0.0"
        assert tile._data["hourlyrain"] == "0.0"
        assert tile._data["weeklyrain"] == "0.0"
        assert tile._data["eventrain"] == "0.0"
        assert tile._data["uv"] == "0.0"
        assert tile._data["windgust"] == "10.07"


PHONES_TOPICS = {
    "phones-online": "5",
    "numbers-assigned": "1934",
    "calls-24h": "708",
    "answer-rate": "0.713",
    "calls-answered": "5129",
    "avg-call-seconds": "35",
    "longest-call-seconds": "6342",
    "talk-seconds": "179683",
    "voicemail-messages": "21",
}


class TestPhoneTile:
    @pytest.fixture
    def tile(self):
        t = PhoneTile(make_mqtt())
        t._header = Mock()
        t._content = Mock()
        return t

    def test_init(self, tile):
        assert tile._data == {}
        assert tile._last_update is None

    def test_on_message_queues_by_key(self, tile):
        tile._mqtt_on_message(msg("phones/phones-online", "5"))
        key, val = tile._queue.get_nowait()
        assert key == "phones-online"
        assert val == "5"

    def test_poll_updates_data(self, tile):
        for k, v in PHONES_TOPICS.items():
            tile._mqtt_on_message(msg(f"phones/{k}", v))
        tile._poll()
        assert tile._data["phones-online"] == "5"
        assert tile._data["calls-24h"] == "708"
        assert tile._data["talk-seconds"] == "179683"
        assert tile._last_update is not None

    def test_redraw_with_data(self, tile):
        for k, v in PHONES_TOPICS.items():
            tile._mqtt_on_message(msg(f"phones/{k}", v))
        tile._poll()
        tile._content.update.assert_called_once()
        output = tile._content.update.call_args[0][0]
        assert "5" in output
        assert "1,934" in output
        assert "71%" in output
        assert "35s" in output
        assert "1h" in output and "45m" in output or "longest" in output.lower()

    def test_redraw_without_data_shows_waiting(self, tile):
        tile._redraw()
        output = tile._content.update.call_args[0][0]
        assert "---" in output


class TestWeatherTile:
    @pytest.fixture
    def tile(self):
        t = WeatherTile(make_mqtt())
        t._header = Mock()
        t._content = Mock()
        return t

    @pytest.mark.parametrize(
        "deg,arrow",
        [
            (0, "↑"),
            (45, "↗"),
            (90, "→"),
            (135, "↘"),
            (180, "↓"),
            (225, "↙"),
            (270, "←"),
            (315, "↖"),
            (360, "↑"),
            (22, "↑"),
            (23, "↗"),
            (None, ""),
            ("abc", "?"),
        ],
    )
    def test_wind_arrow(self, tile, deg, arrow):
        assert tile._wind_arrow(deg) == arrow

    @pytest.mark.parametrize(
        "data,expected",
        [
            ({"rainrate": "2.0"}, RAINY),
            ({"rainrate": "0", "solarradiation": "60000"}, SUNNY),
            ({"rainrate": "0", "solarradiation": "20000"}, PARTLY),
            ({"rainrate": "0", "solarradiation": "5000", "windspeed": "30"}, WINDY),
            ({"rainrate": "0", "solarradiation": "5000", "windspeed": "5"}, CLOUDY),
            ({}, CLOUDY),
        ],
    )
    def test_get_weather_art(self, tile, data, expected):
        tile._data = data
        result = tile._get_weather_art()
        assert result == expected

    def test_bad_values_fall_back_safely(self, tile):
        tile._data = {"rainrate": "bad", "solarradiation": "bad", "windspeed": "bad"}
        assert tile._get_weather_art() == CLOUDY


SCHEDULE_FIXTURE = "tests/data/schedule_today.json"


class TestFilmTile:
    @pytest.fixture
    def tile(self):
        t = FilmTile()
        t._header = Mock()
        t._content = Mock()
        return t

    def test_init_has_empty_films(self):
        t = FilmTile()
        assert t._films == []
        assert t._day_label == ""

    def test_loads_today_only(self, tile):
        with open(SCHEDULE_FIXTURE) as f:
            data = json.load(f)
        tile._load_data(data, today="2026-07-16")
        assert len(tile._films) == 2
        assert tile._films[0]["slug"] == "apollo11"
        assert tile._films[1]["slug"] == "spinaltap"
        assert tile._day_label == "Today"

    def test_shows_next_day_when_today_empty(self, tile):
        with open(SCHEDULE_FIXTURE) as f:
            data = json.load(f)
        tile._load_data(data, today="2026-07-15")
        assert len(tile._films) == 2
        assert tile._films[0]["slug"] == "apollo11"
        assert tile._day_label == "Thursday 16th"

    def test_no_upcoming_films(self, tile):
        with open(SCHEDULE_FIXTURE) as f:
            data = json.load(f)
        tile._load_data(data, today="2026-07-20")
        assert tile._films == []
        assert tile._day_label == ""

    def test_redraw(self, tile):
        with open(SCHEDULE_FIXTURE) as f:
            data = json.load(f)
        tile._load_data(data, today="2026-07-16")
        from rich.table import Table

        assert isinstance(tile._content.update.call_args[0][0], Table)

    @pytest.mark.parametrize(
        "ts,expected",
        [
            ("2026-07-16T19:00:00+01:00", "Thursday 16th"),
            ("2026-07-17T08:00:00+01:00", "Friday 17th"),
            ("2026-07-18T08:30:00+01:00", "Saturday 18th"),
            ("2026-07-19T20:15:00+01:00", "Sunday 19th"),
        ],
    )
    def test_format_day(self, ts, expected):
        from datetime import datetime

        assert format_day(datetime.fromisoformat(ts)) == expected


NOW_AND_NEXT_FIXTURE = "tests/data/now_and_next.json"


class TestScheduleTile:
    @pytest.fixture
    def tile(self):
        t = ScheduleTile()
        t._header = Mock()
        t._content = Mock()
        return t

    def test_init(self):
        t = ScheduleTile()
        assert t._stages == {}
        assert t._label == ""

    def test_process_now_next_populates_stages(self, tile):
        with open(NOW_AND_NEXT_FIXTURE) as f:
            data = json.load(f)
        tile._process_now_next(data)
        assert "Stage A" in tile._stages
        assert "Stage B" in tile._stages
        assert "Workshop 1" in tile._stages
        assert len(tile._stages["Stage A"]) == 2
        assert tile._stages["Stage A"][0]["id"] == 1
        assert tile._stages["Stage A"][1]["id"] == 2
        assert tile._stages["Stage B"][0]["id"] == 3
        assert tile._label == "Now & Next"

    def test_process_now_next_deduplicates(self, tile):
        occ = [
            {
                "start_time": "10:00",
                "venue": "Stage A",
                "start_date": "2026-07-17 10:00:00",
            }
        ]
        data = {
            "stage-a": [
                {"id": 1, "title": "A", "occurrences": occ},
                {"id": 1, "title": "A dup", "occurrences": occ},
                {"id": 2, "title": "B", "occurrences": occ},
            ]
        }
        tile._process_now_next(data)
        assert len(tile._stages["Stage A"]) == 2

    def test_process_now_next_includes_all_venues(self, tile):
        occ = [
            {
                "start_time": "10:00",
                "venue": "Stage A",
                "start_date": "2026-07-17 10:00:00",
            }
        ]
        wocc = [
            {
                "start_time": "12:00",
                "venue": "Workshop 1",
                "start_date": "2026-07-17 12:00:00",
            }
        ]
        data = {
            "stage-a": [{"id": 1, "title": "A", "occurrences": occ}],
            "stage-c": [],
            "workshop-1": [{"id": 99, "title": "W", "occurrences": wocc}],
        }
        tile._process_now_next(data)
        assert list(tile._stages.keys()) == ["Stage A", "Workshop 1"]

    def test_process_now_next_empty_does_not_redraw(self, tile):
        tile._process_now_next({})
        assert tile._stages == {}
        assert tile._label == ""
        tile._content.append.assert_not_called()

    def test_redraw(self, tile):
        with open(NOW_AND_NEXT_FIXTURE) as f:
            data = json.load(f)
        tile._process_now_next(data)

        calls = tile._content.append.call_args_list
        assert len(calls) > 0
        items = [c[0][0] for c in calls]
        talk_items = [i for i in items if hasattr(i, "talk_data")]
        assert len(talk_items) == 4

    def test_first_redraw_header_and_content(self, tile):
        tile._process_now_next(
            {
                "stage-a": [
                    {
                        "id": 1,
                        "title": "T",
                        "occurrences": [
                            {
                                "start_time": "10:00",
                                "end_time": "11:00",
                                "venue": "Stage A",
                                "start_date": "2026-07-17 10:00:00",
                            }
                        ],
                    }
                ]
            }
        )
        tile._header.update.assert_called_once()
        header = tile._header.update.call_args[0][0]
        assert "Now & Next" in header


FAVOURITES_FIXTURE = "tests/data/favourites.json"


class TestScheduleFavourites:
    @pytest.fixture
    def tile(self):
        t = ScheduleTile()
        t._header = Mock()
        t._content = Mock()
        return t

    def test_process_favourites_grouped_by_venue(self, tile):
        with open(FAVOURITES_FIXTURE) as f:
            data = json.load(f)
        tile._process_favourites(data)
        assert "Stage C" in tile._stages
        assert tile._label == "Favourites"

    def test_process_favourites_filters_to_today(self, tile):
        with open(FAVOURITES_FIXTURE) as f:
            data = json.load(f)
        tile._process_favourites(data)
        for venue, talks in tile._stages.items():
            for talk in talks:
                for occ in talk.get("occurrences", []):
                    assert occ.get("start_date", "").startswith("2026-07-16")

    def test_process_favourites_deduplicates(self, tile):
        talks = [
            {
                "id": 1,
                "title": "A",
                "occurrences": [
                    {
                        "start_time": "10:00",
                        "venue": "Stage A",
                        "start_date": "2026-07-16 10:00:00",
                    }
                ],
            },
            {
                "id": 1,
                "title": "A dup",
                "occurrences": [
                    {
                        "start_time": "10:00",
                        "venue": "Stage A",
                        "start_date": "2026-07-16 10:00:00",
                    }
                ],
            },
        ]
        tile._process_favourites(talks)
        assert len(tile._stages["Stage A"]) == 1

    def test_process_favourites_redraws(self, tile):
        with open(FAVOURITES_FIXTURE) as f:
            data = json.load(f)
        tile._process_favourites(data)
        tile._header.update.assert_called_once()
        header = tile._header.update.call_args[0][0]
        assert "Favourites" in header


class TestConfig:
    def test_load_missing_returns_defaults(self, tmp_path):
        from config import Config

        cfg = Config.load(tmp_path / "nonexistent.toml")
        assert cfg.favourites_url is None

    def test_load_with_favourites_url(self, tmp_path):
        from config import Config

        p = tmp_path / "config.toml"
        p.write_text('[favourites]\nurl = "https://example.com/fav.json?token=abc"\n')
        cfg = Config.load(p)
        assert cfg.favourites_url == "https://example.com/fav.json?token=abc"

    def test_load_empty_toml(self, tmp_path):
        from config import Config

        p = tmp_path / "config.toml"
        p.write_text("")
        cfg = Config.load(p)
        assert cfg.favourites_url is None

    def test_load_no_favourites_section(self, tmp_path):
        from config import Config

        p = tmp_path / "config.toml"
        p.write_text('[other]\nkey = "val"\n')
        cfg = Config.load(p)
        assert cfg.favourites_url is None
