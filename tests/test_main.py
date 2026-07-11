"""Tests for EMF Camp Dashboard."""

import csv
import json
from unittest.mock import Mock

import pytest

from tiles import MQTTTile, ScheduleTile, WeatherTile
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
        assert tile._log.rebuild.called


class TestWeatherTile:
    @pytest.fixture
    def tile(self):
        t = WeatherTile(make_mqtt())
        t._content = Mock()
        return t

    def test_init(self, tile):
        assert tile._data == {}
        assert tile._last_update is None

    def test_on_message_queues_tuple(self, tile):
        tile._mqtt_on_message(msg("emf/weather/temp", "22.5"))
        key, val = tile._queue.get_nowait()
        assert key == "temp"
        assert val == "22.5"

    def test_on_message_deep_topic(self, tile):
        tile._mqtt_on_message(msg("emf/weather/winddir", "180"))
        key, val = tile._queue.get_nowait()
        assert key == "winddir"

    def test_poll_updates_data(self, tile):
        tile._mqtt_on_message(msg("emf/weather/temp", "22.5"))
        tile._mqtt_on_message(msg("emf/weather/humidity", "60"))
        tile._poll()
        assert tile._data == {"temp": "22.5", "humidity": "60"}
        assert tile._last_update is not None

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


CSV_FIXTURES = [
    ("open/astley", "tests/data/open_astley.csv", RICK),
    ("open/the-ducks", "tests/data/open_the-ducks.csv", DUCK),
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


WEATHER_FIXTURE = "tests/data/emf_weather.csv"


class TestWeatherCsvFixture:
    def test_csv_parses(self):
        with open(WEATHER_FIXTURE, newline="") as f:
            reader = csv.DictReader(f, delimiter=";")
            rows = list(reader)
        assert len(rows) > 0
        for row in rows:
            assert row["Timestamp"]
            assert row["Date"]
            assert row["Topic"].startswith("emf/weather/")
            assert row["Value"]

    def test_messages_populate_data(self):
        tile = WeatherTile(make_mqtt())
        tile._content = Mock()
        with open(WEATHER_FIXTURE, newline="") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                tile._mqtt_on_message(msg(row["Topic"], row["Value"]))
        assert tile._queue.qsize() > 0
        tile._poll()
        assert tile._data["temp"] == "23.2"
        assert tile._data["humidity"] == "40"
        assert tile._data["windspeed"] == "7"
        assert tile._data["rainrate"] == "0.0"
        assert tile._data["solarradiation"] == "60000"

    def test_last_timestamp_sets_correct_art(self):
        tile = WeatherTile(make_mqtt())
        tile._content = Mock()
        with open(WEATHER_FIXTURE, newline="") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                tile._mqtt_on_message(msg(row["Topic"], row["Value"]))
        tile._poll()
        assert tile._get_weather_art() == SUNNY


SCHEDULE_FIXTURE = "tests/data/schedule_today.json"


class TestScheduleTile:
    @pytest.fixture
    def tile(self):
        t = ScheduleTile()
        t._header = Mock()
        t._content = Mock()
        return t

    def test_init_has_empty_films(self):
        t = ScheduleTile()
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
        assert ScheduleTile._format_day(ts) == expected
