#!/usr/bin/env python3
"""openweathermap-export"""
from pyowm import OWM
from pyowm.utils import config
from pyowm.utils import timestamps

import logging
import json
import sys
import os
import time
from datetime import datetime, timedelta
from prometheus_client import Counter, Gauge, start_http_server

LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")

PROMETHEUS_PREFIX = os.getenv("PROMETHEUS_PREFIX", "openweathermap")
PROMETHEUS_PORT   = int(os.getenv("PROMETHEUS_PORT", "9003"))
PROMETHEUS_LABEL  = os.getenv("PROMETHEUS_LABEL", "openweathermap")

APIKEY           = os.getenv("APIKEY", "")
WEATHER_COUNTRY  = os.getenv("WEATHER_COUNTRY", "Surhuisterveen,NL")
WEATHER_LANGUAGE = os.getenv("WEATHER_LANGUAGE", "NL")

LOGFORMAT = '%(asctime)-15s %(message)s'

logging.basicConfig(level=LOG_LEVEL, format=LOGFORMAT)
LOG = logging.getLogger("openweathermap-export")

# global variable
prom_metrics = {}  # pylint: disable=C0103
prom_msg_counter = Counter(
    f"{PROMETHEUS_PREFIX}message_total", "Counter of received messages", [PROMETHEUS_LABEL]
)

pool_frequency = int(os.getenv("POOL_FREQUENCY", "300"))

config_dict = config.get_default_config()
config_dict['language'] = WEATHER_LANGUAGE

def getData(config_dict):
    owm = OWM(APIKEY, config_dict)
    mgr = owm.weather_manager()

    # Here put your city and Country ISO 3166 country codes
    observation = mgr.weather_at_place(WEATHER_COUNTRY)

    w = observation.weather
    # Weather details from INTERNET

    prom_metric_name=PROMETHEUS_PREFIX
    if not prom_metrics.get(prom_metric_name):
        prom_metrics[prom_metric_name] = Gauge(
            prom_metric_name, "metric generated from openWeather message.", [PROMETHEUS_LABEL]
        )
        LOG.info("creating prometheus metric: %s", prom_metric_name)

    # increment received message counter
    prom_msg_counter.labels(**{PROMETHEUS_PREFIX: PROMETHEUS_LABEL}).inc()

    # expose the metric to prometheus
    

    LOG.debug("new value for %s: %s", prom_metric_name, i)

    values = dict()
    prom_metrics[prom_metric_name].labels(**{PROMETHEUS_LABEL: PROMETHEUS_LABEL}).set( {"status" : w.status} )

    values['detailed_status']  = w.detailed_status  # detailed version of status (eg. 'light rain')

    wind  = w.wind()

    values['wind_speed']  = wind ["speed"]
    values['wind_direction_deg']  = wind ["deg"]
    values['humidity']  = w.humidity

    temperature  = w.temperature('celsius')
    values['temp']  = temperature["temp"]
    values['pressure'] = w.pressure['press']

    values['clouds'] = w.clouds #Cloud coverage
    values["sunrise"] = w.sunrise_time()*1000 #Sunrise time (GMT UNIXtime or ISO 8601)
    values["sunset"] = w.sunset_time()*1000 #Sunset time (GMT UNIXtime or ISO 8601)
    values["weather_code"] =  w.weather_code

    values["weather_icon"] = w.weather_icon_name
    values["visibility_distance"] = w.visibility_distance

    location = observation.location.name
    values["location"] = location

    rain = w.rain
    #If there is no data recorded from rain then return 0, otherwise #return the actual data
    if len(rain) == 0:
        values['lastrain'] = float("0")
    else:
        if "3h" in rain:
            values['lastrain'] = rain["3h"]
        if "1h" in rain:
            values['lastrain'] = rain["1h"]

    snow = w.snow
    #If there is no data recorded from rain then return 0, otherwise #return the actual data
    if len(snow) == 0:
        values['lastsnow'] = float("0")
    else:
        if "3h" in snow:
            values['lastsnow'] = snow["3h"]
        if "1h" in snow:
            values['lastsnow'] = snow["1h"]

#       UV index
    s = WEATHER_COUNTRY.split(",")
    reg = owm.city_id_registry()
    list_of_locations = reg.locations_for(s[0], country=s[1])
    myLocation = list_of_locations[0]

    uvimgr = owm.uvindex_manager()

    uvi = uvimgr.uvindex_around_coords(myLocation.lat, myLocation.lon )
    values['uvi'] = uvi.value

    # Print the data
    LOG.debug(values)
   
try:
    while True:
        getData(config_dict)
        time.sleep(pool_frequency)
except Exception as e:
    print(e)
    pass