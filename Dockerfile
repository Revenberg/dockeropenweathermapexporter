FROM python:alpine3.7
ARG PROMETHEUS_PREFIX=openweathermap
ARG APIKEY
ARG WEATHER_COUNTRY="NL"
ARG WEATHER_LANGUAGE="NL"
ARG PROMETHEUS_PORT=9003
ARG POLLING_INTERVAL_SECONDS=600

RUN pip install --upgrade pip && pip uninstall serial

COPY files/requirements.txt /app/

WORKDIR /app
RUN pip install -r requirements.txt

RUN mkdir -p /data/backup

COPY files/app* /app/

CMD python ./openweathermap-export.py