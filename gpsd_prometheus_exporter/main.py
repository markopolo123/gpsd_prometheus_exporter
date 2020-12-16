import os
import gpsd
import time
from threading import Thread

import argparse
import logging
from prometheus_client import start_http_server, Gauge, Histogram

LONGITUDE = Gauge('longitude','longitude measured')
LATITUDE = Gauge('latitude','latitude measured')
SPEED = Gauge('speed','Current speed in knots')
ALTITUDE = Gauge('altitude','Current Altitude in metres')
SAT_COUNT = Gauge('satcount','Number of satellites')


def get_gpsd_data():
    """Get gpsd data"""
    gpsd.connect()
    # Get gps position
    packet = gpsd.get_current()
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
    sensor_data['longitude'] = LONGITUDE.collect()[0].samples[0].value
    sensor_data['latitude'] = LATITUDE.collect()[0].samples[0].value
    sensor_data['speed'] = SPEED.collect()[0].samples[0].value
    sensor_data['altitude'] = ALTITUDE.collect()[0].samples[0].value
    sensor_data['satcount'] = SAT_COUNT.collect()[0].samples[0].value

    return sensor_data

def str_to_bool(value):
    if value.lower() in {'false', 'f', '0', 'no', 'n'}:
        return False
    elif value.lower() in {'true', 't', '1', 'yes', 'y'}:
        return True
    raise ValueError(f'{value} is not a valid boolean value')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--bind", metavar='ADDRESS', default='0.0.0.0', help="Specify alternate bind address [default: 0.0.0.0]")
    parser.add_argument("-p", "--port", metavar='PORT', default=8000, type=int, help="Specify alternate port [default: 8000]")
    parser.add_argument("-d", "--debug", metavar='DEBUG', type=str_to_bool, help="Turns on more verbose logging, showing sensor output and post responses [default: false]")
    args = parser.parse_args()

    logging.basicConfig(
        format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    DEBUG = False
    if args.debug:
        DEBUG = True
    logging.info(f"Listening on http://{args.bind}:{args.port}")
    start_http_server(addr=args.bind, port=args.port)

    while True:
        get_gpsd_data()
        time.sleep(1)
        if DEBUG:
            logging.info(f'Sensor data: {make_json()}')
