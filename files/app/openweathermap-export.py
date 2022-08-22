"""Application exporter"""

import os
import time
from prometheus_client import start_http_server, Gauge, Enum, Info
import logging
from pyowm import OWM
from pyowm.utils import config
from pyowm.utils import timestamps

LOG_LEVEL = os.getenv("LOG_LEVEL", "WARN")

PROMETHEUS_PREFIX = os.getenv("PROMETHEUS_PREFIX", "openweathermap")
PROMETHEUS_PORT   = int(os.getenv("PROMETHEUS_PORT", "9003"))

APIKEY           = os.getenv("APIKEY", "")
WEATHER_COUNTRY  = os.getenv("WEATHER_COUNTRY", "Surhuisterveen,NL")
WEATHER_LANGUAGE = os.getenv("WEATHER_LANGUAGE", "NL")
polling_interval_seconds = int(os.getenv("POLLING_INTERVAL_SECONDS", "600"))    

LOGFORMAT = '%(asctime)-15s %(message)s'

logging.basicConfig(level=LOG_LEVEL, format=LOGFORMAT)
LOG = logging.getLogger("openweathermap-export")

class AppMetrics:
    """
    Representation of Prometheus metrics and loop to fetch and transform
    application metrics into Prometheus metrics.
    """

    def __init__(self, PROMETHEUS_PREFIX='', APIKEY='', WEATHER_COUNTRY='NL', WEATHER_LANGUAGE='NL', polling_interval_seconds=5):

        if PROMETHEUS_PREFIX != '':
            PROMETHEUS_PREFIX = PROMETHEUS_PREFIX + "_"

        config_dict = config.get_default_config()
        config_dict['language'] = WEATHER_LANGUAGE

        self.PROMETHEUS_PREFIX = PROMETHEUS_PREFIX
        self.APIKEY = APIKEY
        self.config_dict = config_dict
        self.WEATHER_COUNTRY = WEATHER_COUNTRY        
        
        self.polling_interval_seconds = polling_interval_seconds

        # Prometheus metrics to collect
        self.status = Info(PROMETHEUS_PREFIX + 'status', 'status')
        self.wind_speed = Gauge(PROMETHEUS_PREFIX + 'wind_speed', 'wind_speed')
        self.wind_direction_deg = Gauge(PROMETHEUS_PREFIX + 'wind_direction_deg', 'wind_direction_deg')
        self.humidity = Gauge(PROMETHEUS_PREFIX + 'humidity', 'humidity')
        self.temp = Gauge(PROMETHEUS_PREFIX + 'temp', 'temp')
        self.pressure = Gauge(PROMETHEUS_PREFIX + 'pressure', 'pressure')
        self.clouds = Gauge(PROMETHEUS_PREFIX + 'clouds', 'clouds')
        self.sunrise = Gauge(PROMETHEUS_PREFIX + 'sunrise', 'sunrise')
        self.sunset = Gauge(PROMETHEUS_PREFIX + 'sunset', 'sunset')
        self.weather_icon_code = Gauge(PROMETHEUS_PREFIX + 'weather_icon_code', 'weather_icon_code')
        self.weather_icon_name = Info(PROMETHEUS_PREFIX + 'weather_icon_name', 'weather_icon_name')
        self.visibility_distance = Gauge(PROMETHEUS_PREFIX + 'visibility_distance', 'visibility_distance')
        self.lastrain = Gauge(PROMETHEUS_PREFIX + 'lastrain', 'lastrain')
        self.lastsnow = Gauge(PROMETHEUS_PREFIX + 'lastsnow', 'lastsnow')
        self.location = Info(PROMETHEUS_PREFIX + 'location', 'location')
        self.uvi = Gauge(PROMETHEUS_PREFIX + 'uvi', 'uvi')

    def run_metrics_loop(self):
        """Metrics fetching loop"""

        while True:
            self.fetch()
            time.sleep(self.polling_interval_seconds)

    def fetch(self):
        """
        Get metrics from application and refresh Prometheus metrics with
        new values.
        """

        # Weather details from INTERNET
        owm = OWM(self.APIKEY, self.config_dict)
        mgr = owm.weather_manager()

        observation = mgr.weather_at_place(self.WEATHER_COUNTRY)
        w = observation.weather

        wind  = w.wind()
        temperature  = w.temperature('celsius')
        location = observation.location.name
        rain = w.rain
        snow = w.snow

        # UV index
        s = WEATHER_COUNTRY.split(",")
        reg = owm.city_id_registry()
        list_of_locations = reg.locations_for(s[0], country=s[1])
        myLocation = list_of_locations[0]

        uvimgr = owm.uvindex_manager()

        uvi = uvimgr.uvindex_around_coords(myLocation.lat, myLocation.lon )

        self.location.info( { 'location': location } )
        self.status.info( { 'status': w.status, 'detaild_status': w.detailed_status })
        self.wind_speed.set(wind ["speed"])
        self.wind_direction_deg.set(wind ["deg"])
        self.humidity.set(w.humidity)
        self.temp.set(temperature["temp"])
        self.pressure.set(w.pressure['press'])
        self.clouds.set( w.clouds)
        self.sunrise.set(w.sunrise_time()*1000)
        self.sunset.set(w.sunset_time()*1000)
        self.weather_icon_code.set(w.weather_code)
        self.weather_icon_name.info({ 'icon': w.weather_icon_name } )
        self.visibility_distance.set(w.visibility_distance)
        
        #If there is no data recorded from rain then return 0, otherwise #return the actual data
        if len(rain) == 0:
            self.lastrain.set(0)
        else:
            if "3h" in rain:
                self.lastrain.set( rain["3h"] )
            if "1h" in rain:
                self.lastrain.set( rain["1h"] )
    
        #If there is no data recorded from rain then return 0, otherwise #return the actual data
        if len(snow) == 0:
            self.lastsnow.set(0)
        else:
            if "3h" in snow:
                self.lastsnow.set( snow["3h"] )
            if "1h" in snow:
                self.lastsnow.set( snow["1h"] )

        self.uvi.set( uvi.value )

        LOG.info("Update prometheus")

def main():
    """Main entry point"""    
    
    app_metrics = AppMetrics(
        PROMETHEUS_PREFIX=PROMETHEUS_PREFIX,
        APIKEY=APIKEY,
        WEATHER_COUNTRY=WEATHER_COUNTRY,
        WEATHER_LANGUAGE=WEATHER_LANGUAGE, 
        polling_interval_seconds=polling_interval_seconds
    )
    start_http_server(PROMETHEUS_PORT)
    LOG.info("start prometheus port: %s", PROMETHEUS_PORT)
    app_metrics.run_metrics_loop()

if __name__ == "__main__":
    main()