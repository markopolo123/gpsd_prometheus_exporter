import os
import gpsd
import time

import click
import logging
from prometheus_client import start_http_server, Gauge, Histogram

LONGITUDE = Gauge("longitude", "longitude measured")
LATITUDE = Gauge("latitude", "latitude measured")
SPEED = Gauge("speed", "Current speed in knots")
ALTITUDE = Gauge("altitude", "Current Altitude in metres")
SAT_COUNT = Gauge("satcount", "Number of satellites")

def gps_connect():
    gpsd.connect()
    # Get gps position
    data = gpsd.get_current()
    return data

def get_gpsd_data(packet):
    """Set Prom Metrics"""
    LONGITUDE.set(packet.lon)
    LATITUDE.set(packet.lat)
    SPEED.set(mps_to_knots(packet.hspeed))
    ALTITUDE.set(packet.alt)
    SAT_COUNT.set(str(packet.sats))


def mps_to_knots(mps):
    return 1.94384 * mps


def make_json():
    """Collects all the data currently set"""
    sensor_data = {}
    sensor_data["longitude"] = LONGITUDE.collect()[0].samples[0].value
    sensor_data["latitude"] = LATITUDE.collect()[0].samples[0].value
    sensor_data["speed"] = SPEED.collect()[0].samples[0].value
    sensor_data["altitude"] = ALTITUDE.collect()[0].samples[0].value
    sensor_data["satcount"] = SAT_COUNT.collect()[0].samples[0].value
    return sensor_data


def str_to_bool(value):
    if value.lower() in {"false", "f", "0", "no", "n"}:
        return False
    elif value.lower() in {"true", "t", "1", "yes", "y"}:
        return True
    raise ValueError(f"{value} is not a valid boolean value")


@click.command()
@click.option(
    "--bind",
    "-b",
    default="0.0.0.0",
    type=str,
    help="Specify alternate bind address [default: 0.0.0.0]",
)
@click.option(
    "--port",
    "-p",
    default=8000,
    type=int,
    help="Specify alternate port [default: 8000]",
)
@click.option(
    "--debug",
    "-d",
    is_flag=True,
    help="Turns on more verbose logging, prints output [default: False]",
)
def main(bind, port, debug):

    logging.basicConfig(
        format="%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s",
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.info(f"Listening on http://{bind}:{port}")
    start_http_server(addr=bind, port=port)

    while True:
        data = gps_connect()
        get_gpsd_data(data)
        time.sleep(1)
        if debug:
            logging.info(f"Sensor data: {make_json()}")
