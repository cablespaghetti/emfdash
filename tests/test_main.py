"""Tests for EMF Camp Dashboard."""

import csv
from unittest.mock import Mock

import pytest

from tiles import MQTTTile, WeatherTile
from constants import RICK, DUCK, SUNNY, RAINY, PARTLY, WINDY, CLOUDY


def msg(topic, payload):
    m = Mock()
    m.topic = topic
    m.payload = payload.encode("utf-8") if isinstance(payload, str) else payload
    return m


class TestMQTTTile:
    @pytest.fixture
    def tile(self):
        t = MQTTTile("open/astley", RICK)
        t._log = Mock()
        return t

    def test_init(self, tile):
        assert tile.topic == "open/astley"
        assert tile.emoji == RICK
        assert tile._queue.maxsize == 200

    def test_on_message_queues_string(self, tile):
        tile._mqtt_on_message(None, None, msg("open/astley", "hello world"))
        assert tile._queue.get_nowait() == "hello world"

    def test_on_message_queues_bytes(self, tile):
        tile._mqtt_on_message(None, None, msg("open/astley", b"raw bytes"))
        assert tile._queue.get_nowait() == "raw bytes"

    def test_on_message_full_queue_does_not_raise(self, tile):
        for i in range(200):
            tile._queue.put_nowait(str(i))
        tile._mqtt_on_message(None, None, msg("open/astley", "overflow"))
        assert tile._queue.qsize() == 200

    def test_on_message_handles_bad_utf8(self, tile):
        m = msg("open/astley", b"\xff\xfe")
        tile._mqtt_on_message(None, None, m)
        val = tile._queue.get_nowait()
        assert isinstance(val, str)

    def test_poll_drains_queue(self, tile):
        tile._mqtt_on_message(None, None, msg("open/astley", "one"))
        tile._mqtt_on_message(None, None, msg("open/astley", "two"))
        tile._poll()
        assert tile._queue.empty()


class TestWeatherTile:
    @pytest.fixture
    def tile(self):
        t = WeatherTile()
        t._content = Mock()
        return t

    def test_init(self, tile):
        assert tile._data == {}
        assert tile._last_update is None

    def test_on_message_queues_tuple(self, tile):
        tile._mqtt_on_message(None, None, msg("emf/weather/temp", "22.5"))
        key, val = tile._queue.get_nowait()
        assert key == "temp"
        assert val == "22.5"

    def test_on_message_deep_topic(self, tile):
        tile._mqtt_on_message(None, None, msg("emf/weather/winddir", "180"))
        key, val = tile._queue.get_nowait()
        assert key == "winddir"

    def test_poll_updates_data(self, tile):
        tile._mqtt_on_message(None, None, msg("emf/weather/temp", "22.5"))
        tile._mqtt_on_message(None, None, msg("emf/weather/humidity", "60"))
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
        tile = MQTTTile(topic, emoji)
        tile._log = Mock()
        with open(path, newline="") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                tile._mqtt_on_message(None, None, msg(topic, row["Value"]))
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
        tile = WeatherTile()
        tile._content = Mock()
        with open(WEATHER_FIXTURE, newline="") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                tile._mqtt_on_message(None, None, msg(row["Topic"], row["Value"]))
        assert tile._queue.qsize() > 0
        tile._poll()
        assert tile._data["temp"] == "23.2"
        assert tile._data["humidity"] == "40"
        assert tile._data["windspeed"] == "7"
        assert tile._data["rainrate"] == "0.0"
        assert tile._data["solarradiation"] == "60000"

    def test_last_timestamp_sets_correct_art(self):
        tile = WeatherTile()
        tile._content = Mock()
        with open(WEATHER_FIXTURE, newline="") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                tile._mqtt_on_message(None, None, msg(row["Topic"], row["Value"]))
        tile._poll()
        assert tile._get_weather_art() == SUNNY
