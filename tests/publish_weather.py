#!/usr/bin/env python3
"""Publish weather test fixture data to MQTT.

Each row in the CSV is a single MQTT message with Topic and Value columns,
matching how the real weather station publishes each metric separately.
"""

import csv
import time

import paho.mqtt.client as mqtt

HOST = "mqtt.emf.camp"
PORT = 1883


def main():
    client = mqtt.Client()
    client.connect(HOST, PORT, 60)

    with open("tests/data/emf_weather.csv") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            topic = row["Topic"]
            value = row["Value"]
            client.publish(topic, value)
            print(f"{topic} <- {value}")
            time.sleep(0.2)

    client.disconnect()


if __name__ == "__main__":
    main()
