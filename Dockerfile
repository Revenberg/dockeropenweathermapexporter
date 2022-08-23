FROM python:alpine3.7
ENV  PROMETHEUS_PREFIX openweathermap
ENV  APIKEY ''
ENV  WEATHER_COUNTRY NL
ENV  WEATHER_LANGUAGE NL
ENV  PROMETHEUS_PORT 9003
ENV  POLLING_INTERVAL_SECONDS 600

RUN pip install --upgrade pip && pip uninstall serial

COPY files/requirements.txt /app/

WORKDIR /app
RUN pip install -r requirements.txt

RUN mkdir -p /data/backup

COPY files/app* /app/

CMD python ./openweathermap-export.py