import os
import gpsd
import time

import click
import logging
from prometheus_client import start_http_server, Gauge, Histogram

LONGITUDE = Gauge("longitude", "longitude measured")
LATITUDE = Gauge("latitude", "latitude measured")
SPEED = Gauge("speed", "Current speed")
ALTITUDE = Gauge("altitude", "Current Altitude in metres")
SAT_COUNT = Gauge("satcount", "Number of satellites")


def get_gpsd_data(unit, packet):
    """Set Prom Metrics"""
    LONGITUDE.set(packet.lon)
    LATITUDE.set(packet.lat)
    SPEED.set(speed_conversion(unit, packet.hspeed))
    ALTITUDE.set(packet.alt)
    SAT_COUNT.set(str(packet.sats))


def set_speed_units(unit):
    if unit == "mps" or unit == "knots" or unit == "mph" or unit == "kph":
        pass
    else:
        logging.info(f"I don't recognise {unit}. Use --help for more information")
        exit(1)


def speed_conversion(unit, mps):
    if unit == "knots":
        return 1.94384 * mps
    elif unit == "mph":
        return 2.237 * mps
    elif unit == "kph":
        return 3.6 * mps
    else:
        return mps


def make_json():
    """Collects all the data currently set"""
    sensor_data = {}
    sensor_data["longitude"] = LONGITUDE.collect()[0].samples[0].value
    sensor_data["latitude"] = LATITUDE.collect()[0].samples[0].value
    sensor_data["speed"] = SPEED.collect()[0].samples[0].value
    sensor_data["altitude"] = ALTITUDE.collect()[0].samples[0].value
    sensor_data["satcount"] = SAT_COUNT.collect()[0].samples[0].value
    return sensor_data


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
    "--speedunit",
    "-s",
    default="mps",
    type=str,
    help="""Units for speed. Defaults to mps (metres per second).
    Could set knots, mph (mile per hour) or kph (kilometers per hour)""",
)
@click.option(
    "--debug",
    "-d",
    is_flag=True,
    help="Turns on more verbose logging, prints output [default: False]",
)
@click.option(
    "--gpsd-host",
    "-H",
    type=str,
    help="Specify gpsd host address",
)
@click.option(
    "--gpsd-port",
    "-P",
    default=2947,
    type=int,
    help="Specify gpsd host port [default: 2947]",
)
def main(bind, port, debug, speedunit, gpsd_host, gpsd_port):

    logging.basicConfig(
        format="%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s",
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    set_speed_units(speedunit)
    logging.info(f"Listening on http://{bind}:{port}")
    logging.info(f"Reporting speed in {speedunit}")


    if not gpsd_host is None:
        logging.info(f"GPSD Host: {gpsd_host}:{gpsd_port}")
        gpsd.connect(host=gpsd_host, port=gpsd_port)
    else:
        gpsd.connect()

    start_http_server(addr=bind, port=port)

    while True:
        data = gpsd.get_current()
        get_gpsd_data(speedunit, data)
        time.sleep(1)
        if debug:
            logging.info(f"Sensor data: {make_json()}")

