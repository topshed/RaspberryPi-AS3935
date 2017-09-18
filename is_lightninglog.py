#!/usr/bin/env python
from RPi_AS3935 import RPi_AS3935
from ISStreamer.Streamer import Streamer
import RPi.GPIO as GPIO
import time
import logzero
from logzero import logger
from datetime import datetime

GPIO.setmode(GPIO.BCM)
logzero.logfile('/home/pi/lightning.log')
credentials_file = "/home/pi/weather-station/credentials.initialstate"
f = open(credentials_file, "r")
credentials = json.load(f)

CITY = ""
BUCKET_NAME = ":partly_sunny:  Weather Station"
BUCKET_KEY = credentials['X-IS-BucketKey']
ACCESS_KEY = credentials['X-IS-AccessKey']
SENSOR_LOCATION_NAME = ""

# Rev. 1 Raspberry Pis should leave bus set at 0, while rev. 2 Pis should set
# bus equal to 1. The address should be changed to match the address of the
# sensor. (Common implementations are in README.md)
sensor = RPi_AS3935.RPi_AS3935(address=0x03, bus=1)

sensor.set_indoors(True)
sensor.set_noise_floor(0)
sensor.calibrate(tun_cap=0x0F)


def handle_interrupt(channel):
    time.sleep(0.003)
    global sensor
    reason = sensor.get_interrupt()
    if reason == 0x01:
        logger.info("Noise level too high - adjusting")
        sensor.raise_noise_floor()
    elif reason == 0x04:
        logger.info("Disturber detected - masking")
        sensor.set_mask_disturber(True)
    elif reason == 0x08:
        now = datetime.now().strftime('%H:%M:%S - %Y/%m/%d')
        distance = sensor.get_distance()
        logger.info("We sensed lightning!")
        logger.info("It was " + str(distance) + "km away. (%s)" % now)
        logger.info("")
        streamer = Streamer(bucket_name=BUCKET_NAME, bucket_key=BUCKET_KEY, access_key=ACCESS_KEY)
        streamer.log(":zap: Strike (km away)", "str(distance)")
        streamer.flush()

pin = 17

GPIO.setup(pin, GPIO.IN)
GPIO.add_event_detect(pin, GPIO.RISING, callback=handle_interrupt)

logger.info("Waiting for lightning - or at least something that looks like it")

while True:
    time.sleep(1.0)
